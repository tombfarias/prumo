"""Linha de comando do Prumo."""

import argparse
import json
import os
import runpy
import sys
from pathlib import Path

from . import claude, figma, geracao, mapear, formulario, gestao, projeto as mod_projeto, rastreio, seguranca, validacao
from .util import (
    CONGELADO, RAIZ_KIT, VERSAO, ErroPrumo, configurar_console, formatar_horas, formatar_moeda, info,
    config_freelancer, ler, ler_json, gravar_json, tabela_console, agora_iso,
)

JSON = False


def saida(dados, texto=None):
    """Imprime JSON (com --json) ou o texto legível."""
    if JSON:
        print(json.dumps(dados, ensure_ascii=False, indent=2, default=str))
    elif texto is not None:
        info(texto)


def abrir_projeto(args):
    p = mod_projeto.Projeto.localizar(args.projeto) if args.projeto else mod_projeto.Projeto.localizar()
    registrar_recente(p)
    return p


# ---------------------------------------------------------------- projetos recentes

def _arquivo_recentes():
    return RAIZ_KIT / "config" / "projetos.json"


def registrar_recente(p):
    try:
        lista = ler_json(_arquivo_recentes(), []) or []
        lista = [x for x in lista if x.get("caminho") != str(p.raiz)]
        lista.insert(0, {"caminho": str(p.raiz), "nome": p.config.get("projeto"), "cliente": p.config.get("cliente"),
                         "perfil": p.config.get("perfil"), "aberto_em": agora_iso()})
        gravar_json(_arquivo_recentes(), lista[:30])
    except Exception:
        pass


def cmd_projetos(args):
    if args.remover:
        alvo = str(Path(args.remover).resolve())
        lista = [x for x in (ler_json(_arquivo_recentes(), []) or []) if str(Path(x["caminho"]).resolve()) != alvo]
        gravar_json(_arquivo_recentes(), lista)
    lista = [x for x in (ler_json(_arquivo_recentes(), []) or []) if Path(x["caminho"], "projeto.prumo.json").exists()]
    saida(lista, tabela_console(["Projeto", "Cliente", "Pasta"], [[x["nome"], x.get("cliente", ""), x["caminho"]] for x in lista])
          if lista else "Nenhum projeto recente.")


# ---------------------------------------------------------------- comandos

def cmd_perfis(args):
    perfis = mod_projeto.listar_perfis()
    saida(perfis, "\n".join(f"{p['id']:<20} {p['nome']}\n{'':<20} {p['descricao']}\n{'':<20} stack: {p['stack']}\n" for p in perfis))


def _comandos_args(lista):
    """--comando formatar="..." (repetível) -> dict."""
    saida = {}
    for item in lista or []:
        chave, sep, valor = item.partition("=")
        if not sep or chave.strip() not in ("formatar", "lint", "testar"):
            raise ErroPrumo(f"Use --comando formatar=\"...\", lint=\"...\" ou testar=\"...\" (recebido: {item}).")
        saida[chave.strip()] = valor.strip()
    return saida


def cmd_novo(args):
    figma_flag = True if args.com_figma else (False if args.sem_figma else None)
    p = mod_projeto.criar_projeto(
        args.pasta, args.perfil, nome=args.nome, cliente=args.cliente, stack=args.stack, autor=args.autor,
        figma=figma_flag, figma_url=args.figma or "", git=not args.sem_git, python=args.python,
        hooks_absolutos=args.hooks_absolutos, hooks_via=args.hooks_via, forcar=args.forcar,
        comandos=_comandos_args(args.comando),
    )
    registrar_recente(p)
    if JSON:
        saida({"caminho": str(p.raiz), "config": p.config})
    else:
        mod_projeto.instrucoes_iniciais(p)


def cmd_ferramentas(args):
    if args.stack:
        ids = mapear.ferramentas_da_stack(" ".join(args.stack))
        cmds = mapear.comandos_das_ferramentas(ids)
        saida({"ferramentas": ids, "comandos": cmds},
              ("Ferramentas: " + (", ".join(ids) or "nenhuma reconhecida (defina os comandos com --comando)") + "\n"
               + "\n".join(f"  {k:<9} {v or '—'}" for k, v in cmds.items())))
        return
    itens = mapear._ferramentas()
    saida(itens, "\n".join(f"{f['id']:<12} {f['nome']}  (" + ", ".join(f.get("marcadores", [])) + ")" for f in itens))


def cmd_mapear(args):
    pasta = args.pasta or (args.projeto if getattr(args, "projeto", None) else ".")
    if args.simular:
        det = mapear.detectar(pasta)
        saida(det, mapear.texto_mapa(det))
        return
    if args.atualizar:
        p, det = mapear.atualizar_mapa(mod_projeto.Projeto.localizar(pasta))
        saida({"caminho": str(p.raiz), "deteccao": det}, f"Mapa atualizado: {p.raiz / mapear.MAPA}")
        return
    figma_flag = True if args.com_figma else (False if args.sem_figma else None)
    p, det = mapear.mapear_projeto(pasta, perfil_id=args.perfil, nome=args.nome, cliente=args.cliente,
                                   stack=args.stack, autor=args.autor, comandos=_comandos_args(args.comando),
                                   python=args.python, hooks_via=args.hooks_via, figma=figma_flag)
    registrar_recente(p)
    pulados = getattr(p, "pulados", [])
    if JSON:
        saida({"caminho": str(p.raiz), "deteccao": det, "preservados": pulados, "config": p.config})
        return
    pr = mod_projeto.comando_prumo(p.config.get("python"))
    linhas = [f"Prumo instalado no projeto existente {p.raiz}", "",
              f"Stack detectada: {det['stack']}", f"Perfil: {p.config['perfil']}",
              "Comandos dos hooks: " + (", ".join(f"{k}={v}" for k, v in p.config["comandos"].items() if v) or "nenhum detectado"),
              f"Mapa do código: {mapear.MAPA}"]
    if pulados:
        linhas.append("Arquivos que já existiam e foram preservados: " + ", ".join(pulados))
    linhas += ["", "Próximo passo: abra o Claude Code na pasta e rode /mapear-projeto-existente",
               f"  (ou {pr} claude mapear) para descrever o sistema como ele é hoje em docs/."]
    info("\n".join(linhas))


def cmd_status(args):
    p = abrir_projeto(args)
    docs, contagem = validacao.status(p)
    dados = {"projeto": p.config.get("projeto"), "cliente": p.config.get("cliente"), "perfil": p.config.get("perfil"),
             "caminho": str(p.raiz), "stack": p.config.get("stack"), "figma": p.figma_ativo(),
             "documentos": docs, "ids": contagem, "aprovados": p.config.get("aprovados") or {}}
    pendentes = sum(d["lacunas"] for d in docs)
    texto = [f"{dados['projeto']} · cliente: {dados['cliente']} · perfil: {dados['perfil']}", "",
             tabela_console(["Documento", "Lacunas", "Estado"], [[d["documento"], d["lacunas"], d["estado"]] for d in docs]), "",
             "IDs: " + (", ".join(f"{k} {v}" for k, v in contagem.items()) or "nenhum ainda"),
             f"Lacunas [PREENCHER] no total: {pendentes}"]
    proximo = next((d["documento"] for d in docs if d["estado"] == "em andamento"), None)
    if proximo:
        texto.append(f"Próximo documento a completar: {proximo}")
    saida(dados, "\n".join(texto))


def cmd_validar(args):
    p = abrir_projeto(args)
    resultado = validacao.validar(p, estrito=args.estrito, mmdc=args.mmdc)
    erros = [m for g, m in resultado if g == "erro"]
    avisos = [m for g, m in resultado if g == "aviso"]
    texto = [f"erro:  {m}" for m in erros] + [f"aviso: {m}" for m in avisos]
    texto.append(f"\n{len(erros)} erro(s), {len(avisos)} aviso(s).")
    saida({"erros": erros, "avisos": avisos}, "\n".join(texto))
    return 1 if erros else 0


def _separar(problemas):
    return ([m for g, m in problemas if g == "erro"], [m for g, m in problemas if g == "aviso"])


def _texto_problemas(erros, avisos):
    return [f"erro:  {m}" for m in erros] + [f"aviso: {m}" for m in avisos]


def cmd_formulario(args):
    p = abrir_projeto(args)
    if args.acao == "salvar":
        if not args.arquivo:
            raise ErroPrumo("Informe o arquivo: prumo formulario salvar <arquivo.json>")
        dados = ler_json(args.arquivo, None)
        if dados is None:
            raise ErroPrumo(f"Arquivo não encontrado: {args.arquivo}")
        r = formulario.salvar(p, dados)
        erros, avisos = _separar(r.pop("problemas"))
        texto = [f"Formulário gravado em {r['arquivo']}."]
        if r["ids_criados"]:
            texto.append("IDs criados: " + ", ".join(r["ids_criados"]))
        texto += _texto_problemas(erros, avisos)
        if erros or avisos:
            texto.append(f"{len(erros)} erro(s), {len(avisos)} aviso(s).")
        if args.gerar:
            r["geracao"] = geracao.gerar(p)
            texto += ["", *_texto_geracao(r["geracao"])]
        saida(dict(r, erros=erros, avisos=avisos), "\n".join(texto))
        return 0
    if args.acao == "validar":
        dados, existe = formulario.carregar(p)
        erros, avisos = _separar(formulario.validar(dados, ids_documentos=formulario.ids_dos_documentos(p),
                                                    documentos=p.config.get("documentos")))
        texto = _texto_problemas(erros, avisos) + [f"\n{len(erros)} erro(s), {len(avisos)} aviso(s)."]
        if not existe:
            texto = [f"{formulario.ARQUIVO} ainda não existe (preencha o formulário na interface)."]
        saida({"existe": existe, "erros": erros, "avisos": avisos}, "\n".join(texto))
        return 1 if erros else 0
    r = formulario.resumo(p)
    erros, avisos = _separar(r.pop("problemas"))
    estado = "" if r["existe"] else " (ainda não existe)"
    texto = [f"Formulário: {r['arquivo']}{estado}", "",
             tabela_console(["Passo", "Preenchido"], [[f"{n}. {x['titulo']}", f"{x['preenchidos']}/{x['total']}"]
                                                      for n, x in enumerate(r["passos"], 1)])]
    itens = {k: v for k, v in r["itens"].items() if v}
    if itens:
        texto += ["", "Itens: " + ", ".join(f"{formulario.LISTAS[k].rotulo.lower()} {v}" for k, v in itens.items())]
    if erros or avisos:
        texto += ["", f"{len(erros)} erro(s), {len(avisos)} aviso(s): veja com `prumo formulario validar`."]
    saida(dict(r, erros=erros, avisos=avisos), "\n".join(texto))
    return 0


ESTADOS_GERACAO = {"gerado": "preenchido agora", "atualizado": "atualizado", "igual": "sem mudança",
                   "limpo": "voltou a ser lacuna", "editado": "editado no documento (mantido)",
                   "vazio": "sem dados no formulário", "aprovado": "documento aprovado (não tocado)"}


def _texto_geracao(r):
    if not r["existe"]:
        return [f"{formulario.ARQUIVO} ainda não existe: preencha o formulário na interface."]
    texto = []
    for doc, blocos in r["documentos"].items():
        texto.append(doc + (" (simulação)" if r.get("simulado") else ""))
        texto += [f"  {b}: {ESTADOS_GERACAO.get(e, e)}" for b, e in blocos.items()]
    texto.append("Gravado: " + ", ".join(r["alterados"]) if r["alterados"] and not r.get("simulado")
                 else "Nada a gravar." if not r["alterados"] else "Mudaria: " + ", ".join(r["alterados"]))
    return texto


def cmd_gerar(args):
    p = abrir_projeto(args)
    r = geracao.gerar(p, simular=args.simular)
    saida(r, "\n".join(_texto_geracao(r)))
    return 0


def cmd_rastreabilidade(args):
    p = abrir_projeto(args)
    destino, problemas = rastreio.gerar_matriz(p)
    saida({"arquivo": p.rel(destino), "problemas": [{"gravidade": g, "mensagem": m} for g, m in problemas]},
          f"Matriz gerada em {p.rel(destino)} ({len(problemas)} problema(s)).")


def cmd_contexto(args):
    p = abrir_projeto(args)
    texto = validacao.contexto(p, [i.upper() for i in args.ids], args.profundidade)
    saida({"contexto": texto}, texto)


def cmd_aprovar(args):
    p = abrir_projeto(args)
    feitos = mod_projeto.aprovar(p, args.arquivos, forcar=args.forcar)
    saida({"aprovados": feitos}, "\n".join(f"Aprovado: {f}" for f in feitos))


def cmd_desaprovar(args):
    p = abrir_projeto(args)
    feitos = mod_projeto.desaprovar(p, args.arquivos)
    saida({"desaprovados": feitos}, "\n".join(f"Liberado para edição: {f}" for f in feitos) or "Nada alterado.")


def cmd_registro(tipo):
    def executar(args):
        p = abrir_projeto(args)
        ident, rel = mod_projeto.novo_registro(p, tipo, " ".join(args.titulo))
        saida({"id": ident, "arquivo": rel}, f"{ident} criado em {rel}")
    return executar


def cmd_doc(args):
    p = abrir_projeto(args)
    if args.listar or not args.id:
        existentes = {d for d in p.config.get("documentos") or []}
        linhas = [[d, "sim" if f"docs/{d}.md" in existentes else "", mod_projeto.DESCRICOES.get(d, "")]
                  for d in mod_projeto.documentos_disponiveis()]
        saida([{"id": l[0], "no_projeto": bool(l[1]), "descricao": l[2]} for l in linhas],
              tabela_console(["Documento", "No projeto", "Conteúdo"], linhas))
        return
    rel = mod_projeto.adicionar_documento(p, args.id)
    saida({"arquivo": rel}, f"Documento criado: {rel}")


def cmd_agentes(args):
    p = abrir_projeto(args)
    if args.acao == "listar":
        itens = p.listar_kit()
        saida(itens, tabela_console(["Tipo", "Nome", "Estado", "Arquivo"], [[i["tipo"], i["nome"], i["estado"], i["arquivo"]] for i in itens]))
        return
    if args.acao == "exportar":
        escritos = gestao.exportar_agentes(p, args.alvos.split(",") if args.alvos else None)
        saida({"arquivos": escritos}, "Exportado: " + ", ".join(escritos))
    else:
        escritos = p.instalar_kit_agentes(incluir_settings=args.incluir_settings, forcar=args.forcar)
        texto = f"{len(escritos)} arquivo(s) do kit de agentes atualizados."
        if p.kit_preservados:
            texto += (f"\n{len(p.kit_preservados)} arquivo(s) editados por você foram mantidos: "
                      + ", ".join(p.kit_preservados)
                      + "\nA versão nova de cada um está em .prumo/kit-novo/ (compare e junte, ou rode com --forcar).")
        if p.kit_backups:
            texto += "\nCópias de segurança antes de sobrescrever: " + ", ".join(p.kit_backups)
        saida({"arquivos": escritos, "preservados": p.kit_preservados, "backups": p.kit_backups}, texto)


def cmd_orcamento(args):
    p = abrir_projeto(args)
    o = gestao.orcamento(p, args.valor_hora, args.contingencia)
    texto = [f"Orçamento gerado em {o['arquivo']}",
             f"  Histórias: {o['historias']}  ·  horas: {formatar_horas(o['horas_base'])} + {o['contingencia']}% = {formatar_horas(o['horas_total'])}"]
    if o["valor_total"] is not None:
        texto.append(f"  Valor total: {formatar_moeda(o['valor_total'], o['moeda'])}")
    else:
        texto.append("  Valor da hora não configurado (use --valor-hora ou config/freelancer.json).")
    if o.get("opcionais"):
        texto.append(f"  Opcionais (Could, fora do total): {len(o['opcionais'])} história(s), {formatar_horas(o['horas_opcionais'])}")
    if o["sem_estimativa"]:
        texto.append(f"  Sem estimativa: {', '.join(o['sem_estimativa'])}")
    saida(o, "\n".join(texto))


def cmd_horas(args):
    p = abrir_projeto(args)
    dias = gestao.horas(p, args.de, args.ate, args.pausa)
    total = sum(d["horas"] for d in dias.values())
    linhas = [[dia, d["sessoes"], formatar_horas(d["horas"])] for dia, d in dias.items()]
    saida({"dias": dias, "total_horas": total},
          tabela_console(["Dia", "Sessões", "Horas"], linhas) + f"\n\nTotal: {formatar_horas(total)}"
          + "\n(estimativa a partir da atividade registrada pelos hooks; pausas acima de "
          + f"{args.pausa} min encerram a sessão)")


def cmd_seguranca(args):
    p = abrir_projeto(args)
    achados = seguranca.varrer(p, arquivos=args.arquivos or None)
    if not achados:
        saida({"achados": []}, "Nenhum padrão de risco encontrado pela varredura estática. "
                               "Complete com a revisão manual (skill revisar-seguranca).")
        return 0
    linhas = [[a["gravidade"], f"{a['arquivo']}:{a['linha']}", a["descricao"]] for a in achados]
    texto = tabela_console(["Gravidade", "Local", "Problema"], linhas)
    texto += "\n\nConfirme cada item (pode ser falso positivo). Para silenciar uma linha revisada, adicione o comentário 'prumo:ignorar'."
    saida({"achados": achados}, texto)
    ordem = seguranca.ORDEM
    limite = ordem.get(args.falhar_em) if args.falhar_em else None
    return 1 if limite is not None and any(ordem[a["gravidade"]] <= limite for a in achados) else 0


def cmd_diagramas(args):
    p = abrir_projeto(args)
    gerados = validacao.extrair_diagramas(p)
    saida({"arquivos": gerados}, "\n".join(gerados) + f"\n{len(gerados)} diagrama(s) extraído(s) para docs/diagramas/.")


def cmd_figma(args):
    p = abrir_projeto(args)
    if args.acao == "ativar":
        escritos = mod_projeto.ativar_figma(p, args.url or "")
        saida({"arquivos": escritos}, "Figma ativado (.mcp.json, skills e 05-interface.md). No Claude Code: /mcp → figma → autenticar.")
        return
    r = figma.sincronizar_telas(p, args.url, args.token, args.imagens, args.escala)
    saida(r, f"{r['telas']} tela(s) do arquivo '{r['arquivo']}' sincronizadas em {r['documento']}"
             + (f"; {r['imagens']} imagem(ns) baixada(s) em docs/telas/." if r["imagens"] else "."))


def _texto_do_args(args):
    if getattr(args, "texto_arquivo", None):
        return ler(args.texto_arquivo)
    return args.texto or ""


def cmd_claude(args):
    if args.tarefa == "historico":
        p = abrir_projeto(args)
        h = claude.historico(p, args.limite)
        saida(h, tabela_console(["Início", "Tarefa", "Alvo", "Duração", "Tokens", "Saída", "Custo US$", "Erro"],
                                [[x.get("inicio", ""), x.get("tarefa"), x.get("alvo", ""), f"{x.get('duracao_s', '')}s",
                                  (x.get("tokens") or {}).get("total", ""), (x.get("tokens") or {}).get("saida", ""),
                                  x.get("custo_usd") or "", "sim" if x.get("erro") else ""] for x in h]) if h else "Sem execuções ainda.")
        return 0
    p = abrir_projeto(args)
    opcoes = dict(continuar=args.continuar, sessao=args.sessao, modelo=args.modelo, max_turnos=args.max_turnos,
                  extras=args.permitir, modo=args.modo, simular=args.simular)
    texto = _texto_do_args(args)
    alvo = " ".join(args.alvo) if args.alvo else ""
    if args.tarefa == "livre" and not texto and alvo:
        texto, alvo = alvo, ""
    if args.tarefa == "especificar":
        if args.simular:
            etapas = claude.etapas_do_projeto(p, args.de, args.ate)
            modo = claude.modo_sessoes(p, args.sessoes)
            blocos = claude.planejar_sessoes(etapas, modo)
            saida({"etapas": etapas, "modo": modo, "sessoes": blocos},
                  f"Modo: {claude.MODOS_SESSAO[modo]}.\n" + "\n".join(
                      f"  Sessão {n}: {', '.join(b)}" for n, b in enumerate(blocos, 1)))
            return 0
        resultados = claude.especificar(p, de=args.de, ate=args.ate, pausar=False if args.sem_pausa else None,
                                        sessoes=args.sessoes, texto=texto,
                                        **{k: v for k, v in opcoes.items() if k != "simular"})
        saida(resultados, "\nConcluído. Resumos e logs em .prumo/claude/.")
        return 1 if any(r.get("erro") for r in resultados) else 0
    r = claude.executar(p, args.tarefa, alvo=alvo, texto=texto, **opcoes)
    if r.get("simulado"):
        saida(r, "Comando:\n  " + " ".join(r["comando"]) + f"\nPasta: {r['cwd']}\n\nPrompt (enviado pela entrada padrão):\n{r['prompt']}")
        return 0
    custo = f" · US$ {r['custo_usd']:.4f}" if isinstance(r.get("custo_usd"), (int, float)) else ""
    saida(r, f"\n{r.get('resumo') or '(sem resumo)'}\n\n[{r['duracao_s']}s{custo} · log: {r['log']}]")
    return 1 if r.get("erro") else 0


def cmd_hook(args):
    """Executa um hook do projeto com o Python embutido (usado pelo prumo.exe quando não há Python instalado)."""
    nome = args.nome[:-3] if args.nome.endswith(".py") else args.nome
    candidatos = []
    if os.environ.get("CLAUDE_PROJECT_DIR"):
        candidatos.append(Path(os.environ["CLAUDE_PROJECT_DIR"]) / ".claude" / "hooks" / f"{nome}.py")
    try:
        candidatos.append(mod_projeto.Projeto.localizar().raiz / ".claude" / "hooks" / f"{nome}.py")
    except ErroPrumo:
        pass
    candidatos.append(mod_projeto.TEMPLATES / "agentes" / "claude" / "hooks" / f"{nome}.py")
    script = next((c for c in candidatos if c.exists()), None)
    if not script:
        print(f"[Prumo] hook não encontrado: {nome}", file=sys.stderr)
        return 0
    sys.path.insert(0, str(script.parent))
    sys.argv = [str(script), *args.args]
    try:
        runpy.run_path(str(script), run_name="__main__")
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 0
    return 0


def cmd_gui(args):
    from . import servidor
    return servidor.iniciar(porta=args.porta, abrir_janela=not args.sem_janela, projeto_inicial=args.projeto)


def cmd_escolher_pasta(args):
    try:
        import tkinter
        from tkinter import filedialog
        raiz = tkinter.Tk()
        raiz.withdraw()
        raiz.attributes("-topmost", True)
        pasta = filedialog.askdirectory(title=args.titulo or "Escolha a pasta")
        raiz.destroy()
    except Exception:
        pasta = ""
    print(json.dumps({"pasta": pasta or ""}))


# ---------------------------------------------------------------- configurações

FREELANCER = {"nome": str, "email": str, "valor_hora": float, "moeda": str, "contingencia_percentual": float}
PROJETO_CAMPOS = {
    "projeto": str, "cliente": str, "stack": str,
    "comandos.formatar": str, "comandos.lint": str, "comandos.testar": str,
    "hooks.registrar_horas": bool, "hooks.testes_ao_parar": bool, "hooks.revisao_pos_mudanca": bool,
    "hooks.limite_arquivos": int, "hooks.limite_linhas": int, "hooks.comandos_permitidos": list,
    "orcamento.valor_hora": float, "orcamento.contingencia_percentual": float,
    "claude.modelo": str, "claude.max_turnos": int, "pastas_codigo": list,
}


def _converter(valor, tipo, chave):
    """Converte o texto vindo da linha de comando (ou JSON vindo da interface) para o tipo do campo."""
    if isinstance(valor, str):
        bruto = valor.strip()
        if bruto == "" and tipo is not str:
            return None
        if tipo is bool:
            if bruto.lower() in ("1", "true", "sim", "s", "on"):
                return True
            if bruto.lower() in ("0", "false", "nao", "não", "n", "off"):
                return False
            raise ErroPrumo(f"{chave}: use sim ou não.")
        if tipo is list:
            try:
                valor = json.loads(bruto)
            except json.JSONDecodeError:
                return [x.strip() for x in bruto.splitlines() if x.strip()]
        elif tipo in (int, float):
            try:
                return tipo(bruto.replace(",", "."))
            except ValueError:
                raise ErroPrumo(f"{chave}: número inválido ({bruto}).") from None
        else:
            return bruto
    if valor is None:
        return None
    if tipo is list:
        if not isinstance(valor, list):
            raise ErroPrumo(f"{chave}: esperava uma lista.")
        return [str(x) for x in valor]
    if tipo is bool:
        return bool(valor)
    if tipo in (int, float):
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise ErroPrumo(f"{chave}: número inválido.")
        if valor < 0:
            raise ErroPrumo(f"{chave}: o valor não pode ser negativo.")
        return tipo(valor)
    return str(valor)


def _ler_caminho(dados, chave):
    for parte in chave.split("."):
        if not isinstance(dados, dict):
            return None
        dados = dados.get(parte)
    return dados


def _definir_caminho(dados, chave, valor):
    partes = chave.split(".")
    for parte in partes[:-1]:
        if not isinstance(dados.get(parte), dict):
            dados[parte] = {}
        dados = dados[parte]
    dados[partes[-1]] = valor


def cmd_config(args):
    arq_freelancer = RAIZ_KIT / "config" / "freelancer.json"
    try:
        p = abrir_projeto(args)
    except ErroPrumo:
        p = None
    if args.definir:
        pessoal = ler_json(arq_freelancer, {}) or {}
        mudou_freelancer = mudou_projeto = False
        for item in args.definir:
            if "=" not in item:
                raise ErroPrumo(f"Use chave=valor (recebido: {item}).")
            chave, valor = item.split("=", 1)
            chave = chave.strip()
            if chave.startswith("freelancer."):
                campo = chave[len("freelancer."):]
                if campo not in FREELANCER:
                    raise ErroPrumo(f"Campo desconhecido: {chave}")
                pessoal[campo] = _converter(valor, FREELANCER[campo], chave)
                mudou_freelancer = True
            elif chave.startswith("projeto."):
                campo = chave[len("projeto."):]
                if campo not in PROJETO_CAMPOS:
                    raise ErroPrumo(f"Campo desconhecido: {chave}")
                if p is None:
                    raise ErroPrumo("Informe o projeto com --projeto para alterar campos do projeto.")
                _definir_caminho(p.config, campo, _converter(valor, PROJETO_CAMPOS[campo], chave))
                mudou_projeto = True
            else:
                raise ErroPrumo(f"A chave deve começar com freelancer. ou projeto. (recebido: {chave})")
        if mudou_freelancer:
            gravar_json(arq_freelancer, pessoal)
        if mudou_projeto:
            p.salvar()
    dados = {"freelancer": {k: config_freelancer().get(k) for k in FREELANCER},
             "arquivo_freelancer": str(arq_freelancer)}
    if p is not None:
        dados["projeto"] = {k: _ler_caminho(p.config, k) for k in PROJETO_CAMPOS}
        dados["comandos_sugeridos"] = p.config.get("comandos_sugeridos") or {}
    linhas = [f"freelancer.{k} = {v}" for k, v in dados["freelancer"].items()]
    linhas += [f"projeto.{k} = {v}" for k, v in (dados.get("projeto") or {}).items()]
    saida(dados, "\n".join(linhas))


def cmd_versao(args):
    saida({"versao": VERSAO, "kit": str(RAIZ_KIT), "executavel": CONGELADO}, f"Prumo {VERSAO} ({RAIZ_KIT})")


# ---------------------------------------------------------------- parser

def montar_parser():
    ap = argparse.ArgumentParser(prog="prumo", description="Prumo: especificação, agentes de IA e gestão de projetos freelance.")
    ap.add_argument("--projeto", help="pasta do projeto (padrão: a atual ou uma acima)")
    ap.add_argument("--json", action="store_true", help="saída em JSON (para scripts, PowerShell e a interface)")
    ap.add_argument("--versao", action="store_true", help="mostra a versão")
    sub = ap.add_subparsers(dest="comando", metavar="comando")
    comum = argparse.ArgumentParser(add_help=False)  # permite --projeto/--json também depois do comando
    comum.add_argument("--projeto", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    comum.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)

    def novo(nome, funcao, ajuda):
        s = sub.add_parser(nome, help=ajuda, description=ajuda, parents=[comum])
        s.set_defaults(funcao=funcao)
        return s

    novo("perfis", cmd_perfis, "lista os perfis (templates) de projeto")
    s = novo("projetos", cmd_projetos, "lista os projetos abertos recentemente")
    s.add_argument("--remover", metavar="PASTA", help="tira um projeto da lista de recentes (não apaga nada)")
    s = novo("config", cmd_config, "mostra ou altera seus dados e as configurações do projeto")
    s.add_argument("--definir", action="append", metavar="CHAVE=VALOR",
                   help="ex.: freelancer.valor_hora=150 ou projeto.comandos.testar=\"npm test\"")
    s = novo("novo", cmd_novo, "cria um projeto com documentos, kit de agentes e git")
    s.add_argument("pasta")
    s.add_argument("--perfil", "-p", default="web-fullstack")
    s.add_argument("--nome")
    s.add_argument("--cliente", default="")
    s.add_argument("--stack")
    s.add_argument("--autor")
    s.add_argument("--figma", metavar="URL", help="URL do arquivo do Figma (ativa a integração)")
    s.add_argument("--com-figma", action="store_true")
    s.add_argument("--sem-figma", action="store_true")
    s.add_argument("--sem-git", action="store_true")
    s.add_argument("--python", help="comando do Python usado nos hooks (padrão: detectado)")
    s.add_argument("--hooks-absolutos", action="store_true", help="caminhos absolutos nos hooks em vez de $CLAUDE_PROJECT_DIR")
    s.add_argument("--hooks-via", choices=["python", "prumo"], help="executar hooks pelo Python ou pelo prumo.exe")
    s.add_argument("--forcar", action="store_true")
    s.add_argument("--comando", action="append", metavar="USO=CMD",
                   help='comando dos hooks para stack fora dos perfis: formatar="mix format {arquivo}", lint=..., testar=...')
    s = novo("mapear", cmd_mapear, "instala o Prumo num projeto que já existe: detecta a stack e não sobrescreve nada")
    s.add_argument("pasta", nargs="?", help="pasta do projeto (padrão: a atual)")
    s.add_argument("--perfil", "-p", help="padrão: sugerido pela detecção")
    s.add_argument("--nome")
    s.add_argument("--cliente", default="")
    s.add_argument("--stack", help="padrão: a detectada")
    s.add_argument("--autor")
    s.add_argument("--comando", action="append", metavar="USO=CMD", help="sobrepõe um comando detectado")
    s.add_argument("--com-figma", action="store_true")
    s.add_argument("--sem-figma", action="store_true")
    s.add_argument("--python")
    s.add_argument("--hooks-via", choices=["python", "prumo"])
    s.add_argument("--simular", action="store_true", help="só mostra o que foi detectado, sem gravar nada")
    s.add_argument("--atualizar", action="store_true", help="refaz docs/00-mapa-do-codigo.md num projeto já mapeado")
    s = novo("ferramentas", cmd_ferramentas, "ferramentas por linguagem (stacks fora dos perfis)")
    s.add_argument("--stack", nargs="+", help="texto da stack: mostra as ferramentas e os comandos que ela implica")
    novo("status", cmd_status, "resumo dos documentos, lacunas e IDs")
    s = novo("validar", cmd_validar, "verifica lacunas, Mermaid, IDs e documentos aprovados")
    s.add_argument("--estrito", action="store_true", help="avisos também contam como erro")
    s.add_argument("--mmdc", action="store_true", help="valida os diagramas com o mermaid-cli, se instalado")
    s = novo("formulario", cmd_formulario, "formulário de especificação (especificacao.prumo.json)")
    s.add_argument("acao", nargs="?", default="mostrar", choices=["mostrar", "salvar", "validar"])
    s.add_argument("arquivo", nargs="?", help="em salvar: JSON com o formulário")
    s.add_argument("--gerar", action="store_true", help="em salvar: em seguida preenche os documentos (prumo gerar)")
    s = novo("gerar", cmd_gerar, "preenche os documentos com o formulário (hoje: o briefing)")
    s.add_argument("--simular", action="store_true", help="só mostra o que mudaria")
    novo("rastreabilidade", cmd_rastreabilidade, "gera docs/rastreabilidade.md")
    s = novo("contexto", cmd_contexto, "imprime só a trilha ligada a um ou mais IDs (economiza tokens)")
    s.add_argument("ids", nargs="+")
    s.add_argument("--profundidade", type=int, default=1)
    s = novo("aprovar", cmd_aprovar, "marca documentos como aprovados pelo cliente (somente leitura)")
    s.add_argument("arquivos", nargs="+")
    s.add_argument("--forcar", action="store_true")
    s = novo("desaprovar", cmd_desaprovar, "libera documentos aprovados para edição")
    s.add_argument("arquivos", nargs="+")
    s = novo("adr", cmd_registro("adr"), "cria um registro de decisão arquitetural")
    s.add_argument("titulo", nargs="+")
    s = novo("mudanca", cmd_registro("mudanca"), "cria um pedido de mudança de escopo")
    s.add_argument("titulo", nargs="+")
    s = novo("doc", cmd_doc, "adiciona um documento do catálogo ao projeto")
    s.add_argument("id", nargs="?")
    s.add_argument("--listar", action="store_true")
    s = novo("agentes", cmd_agentes, "exporta instruções para outros agentes ou atualiza o kit")
    s.add_argument("acao", choices=["listar", "exportar", "atualizar"])
    s.add_argument("--alvos", help="gemini,copilot,cursor (padrão: todos)")
    s.add_argument("--incluir-settings", action="store_true", help="na atualização, sobrescreve .claude/settings.json")
    s.add_argument("--forcar", action="store_true",
                   help="sobrescreve também arquivos do kit editados por você (guarda cópia em .prumo/backup/)")
    s = novo("orcamento", cmd_orcamento, "soma as estimativas do backlog e gera docs/orcamento.md")
    s.add_argument("--valor-hora", type=float)
    s.add_argument("--contingencia", type=float)
    s = novo("horas", cmd_horas, "horas trabalhadas a partir do registro dos hooks")
    s.add_argument("--de", help="AAAA-MM-DD")
    s.add_argument("--ate", help="AAAA-MM-DD")
    s.add_argument("--pausa", type=int, default=30, help="minutos sem atividade que encerram uma sessão")
    s = novo("seguranca", cmd_seguranca, "varredura estática de falhas comuns de segurança")
    s.add_argument("arquivos", nargs="*")
    s.add_argument("--falhar-em", choices=["Crítica", "Alta", "Média", "Baixa"], help="sai com erro a partir desta gravidade")
    novo("diagramas", cmd_diagramas, "extrai os diagramas Mermaid para docs/diagramas/*.mmd")
    s = novo("figma", cmd_figma, "integração com o Figma")
    s.add_argument("acao", choices=["telas", "ativar"])
    s.add_argument("url", nargs="?")
    s.add_argument("--token", help="token pessoal (padrão: variável FIGMA_TOKEN)")
    s.add_argument("--imagens", action="store_true", help="baixa a imagem de cada tela para docs/telas/")
    s.add_argument("--escala", type=float, default=1)
    s = novo("claude", cmd_claude, "envia uma tarefa ao Claude Code (modo não interativo)")
    s.add_argument("tarefa", choices=["especificar", "historico", *claude.TAREFAS])
    s.add_argument("alvo", nargs="*", help="ID (HU-003, TL-002...) ou, na tarefa livre, o próprio pedido")
    s.add_argument("--texto", "-t", help="pedido ou instruções adicionais")
    s.add_argument("--texto-arquivo", help="lê o pedido de um arquivo UTF-8 (usado pelo PowerShell)")
    s.add_argument("--continuar", "-c", action="store_true", help="continua a última sessão")
    s.add_argument("--sessao", help="retoma uma sessão específica")
    s.add_argument("--modelo")
    s.add_argument("--max-turnos", type=int)
    s.add_argument("--permitir", action="append", help="ferramenta extra permitida (ex.: \"Bash(npm test:*)\")")
    s.add_argument("--modo", choices=["default", "acceptEdits", "plan", "bypassPermissions"])
    s.add_argument("--simular", action="store_true", help="mostra o comando e o prompt sem executar")
    s.add_argument("--de", choices=claude.ETAPAS_ESPECIFICACAO)
    s.add_argument("--ate", choices=claude.ETAPAS_ESPECIFICACAO)
    s.add_argument("--sem-pausa", action="store_true", help="na especificação, não pergunta entre as etapas")
    s.add_argument("--sessoes", choices=list(claude.MODOS_SESSAO),
                   help="na especificação: grupos (padrão, 3 sessões), unica (1 sessão) ou etapa (uma por etapa)")
    s.add_argument("--limite", type=int, default=20, help="itens do histórico")
    s = novo("hook", cmd_hook, "executa um hook do Claude Code (uso interno)")
    s.add_argument("nome")
    s.add_argument("args", nargs="*")
    s = novo("gui", cmd_gui, "abre a interface gráfica")
    s.add_argument("--porta", type=int, default=0)
    s.add_argument("--sem-janela", action="store_true", help="só inicia o servidor e mostra o endereço")
    s = sub.add_parser("_escolher-pasta", parents=[comum])
    s.add_argument("--titulo")
    s.set_defaults(funcao=cmd_escolher_pasta)
    novo("versao", cmd_versao, "mostra a versão")
    return ap


def main(argv=None):
    global JSON
    configurar_console()
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv and CONGELADO:
        argv = ["gui"]  # duplo clique no prumo.exe abre a interface
    parser = montar_parser()
    args = parser.parse_args(argv)
    JSON = args.json
    if args.versao:
        return cmd_versao(args) or 0
    if not getattr(args, "funcao", None):
        parser.print_help()
        return 0
    try:
        codigo = args.funcao(args)
        return codigo or 0
    except ErroPrumo as e:
        if JSON:
            print(json.dumps({"erro": str(e)}, ensure_ascii=False))
        else:
            print(f"erro: {e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\ninterrompido.", file=sys.stderr)
        return 130
