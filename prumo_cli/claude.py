"""Ponte para o Claude Code em modo não interativo (`claude -p`), usada pela CLI, pelo PowerShell e pela interface."""

import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from . import validacao
from .util import ErroPrumo, gravar, gravar_json, progresso

LEITURA = ["Read", "Glob", "Grep"]
ESCRITA = LEITURA + ["Write", "Edit", "MultiEdit"]
WEB = ["WebSearch", "WebFetch"]
GIT_LEITURA = ["Bash(git status:*)", "Bash(git diff:*)", "Bash(git log:*)", "Bash(git show:*)"]

AVISO_NAO_INTERATIVO = (
    "Esta execução é não interativa (disparada pelo Prumo via terminal/PowerShell): ninguém vai responder perguntas. "
    "Onde precisaria perguntar algo sobre o negócio, registre a pergunta na tabela da seção 9 de docs/00-briefing.md e siga com o restante. "
    "Os comandos do Prumo (validar, rastreabilidade, orcamento) rodam automaticamente depois desta execução: "
    "ignore as instruções das skills de rodá-los e não tente executá-los. Para criar ADRs ou pedidos de mudança, copie o modelo "
    "docs/adr/_modelo.md ou docs/mudancas/_modelo.md para o próximo número livre (ADR-001-titulo.md, CM-001-titulo.md). "
    "Economize tokens: leia só o necessário, não releia o que já está no contexto e, ao preencher um modelo, reescreva o "
    "arquivo de uma vez em vez de fazer dezenas de edições pequenas. "
    "Termine com um resumo de no máximo 10 linhas em português: arquivos alterados, pendências e as perguntas novas mais "
    "importantes para o cliente."
)

REGRAS_ESPECIFICACAO = (
    "Regras desta especificação:\n"
    "- **Fidelidade:** o pedido do cliente (docs/00-briefing.md) é a única fonte de fatos do negócio. Não descreva problemas, "
    "números, públicos ou motivações que o cliente não disse. O que você precisar supor para especificar vira premissa "
    "explícita (\"Premissa:\" no texto ou \"Premissa\" na coluna Origem), ligada a uma pergunta. A stack padrão do perfil é "
    "sugestão técnica, não restrição do cliente.\n"
    "- **Proporcionalidade:** o tamanho da especificação acompanha o tamanho do pedido. O que o cliente não pediu "
    "(monitoramento, CI elaborado, painéis extras, rotinas de LGPD além do necessário, funções \"seria bom ter\") entra com "
    "prioridade Could, fora do escopo base. Seção do modelo que não se aplica: escreva \"Não se aplica\" e o motivo em uma linha.\n"
    "- **Concisão:** siga a seção \"Escrita dos documentos\" do AGENTS.md. Tabelas e listas antes de prosa, um fato em um só lugar "
    "(cite o ID em vez de repetir), sem frases de enchimento. Avisos \"estilo:\" do `prumo validar` indicam o que enxugar.\n"
    "- **Perguntas ao cliente:** uma linha por pergunta na tabela da seção 9 do briefing (IDs P-01, P-02...), marcando as que "
    "bloqueiam a proposta. Não repita perguntas já registradas."
)

DICAS_VALIDACAO = (
    "Como corrigir: \"definido de novo\" significa que o ID abre mais de um título ou primeira coluna de tabela; mantenha só a "
    "definição no documento dele e, nas outras ocorrências, cite o ID no meio do texto ou em outra coluna (ex.: "
    "\"### Épico EP-01 — ...\", \"| Cobre | RF-001 |\"). \"Citado mas não está definido\": defina o item no documento dele ou "
    "corrija a citação. Mermaid inválido: corrija a sintaxe do bloco. Não leia o código do Prumo; edite só os documentos."
)

# tarefa -> (skill, descrição, ferramentas, documentos que indicam se a etapa existe no projeto)
TAREFAS = {
    "mapear": ("mapear-projeto-existente", "Mapear projeto existente", ESCRITA + GIT_LEITURA, []),
    "requisitos": ("levantar-requisitos", "Visão e requisitos", ESCRITA, ["01-visao", "02-requisitos"]),
    "casos-de-uso": ("especificar-casos-de-uso", "Casos de uso", ESCRITA, ["03-casos-de-uso"]),
    "interface": ("especificar-interface", "Interface e telas", ESCRITA, ["05-interface"]),
    "uml": ("modelar-uml", "Diagramas UML", ESCRITA, ["04-uml/"]),
    "banco": ("modelar-banco", "Banco de dados", ESCRITA, ["06-banco-de-dados"]),
    "arquitetura": ("planejar-arquitetura", "Arquitetura e ADRs", ESCRITA + WEB, ["07-arquitetura"]),
    "backlog": ("gerar-backlog", "Backlog e estimativas", ESCRITA, ["08-backlog"]),
    "testes": ("planejar-testes", "Plano de testes", ESCRITA, ["09-plano-de-testes"]),
    "proposta": ("proposta-comercial", "Proposta comercial", ESCRITA, ["10-proposta-comercial"]),
    "implementar": ("implementar-historia", "Implementar história", ESCRITA + GIT_LEITURA, []),
    "revisar": ("revisar-conformidade", "Revisão de conformidade", LEITURA + GIT_LEITURA, []),
    "documentar": ("atualizar-documentacao", "Atualizar documentação", ESCRITA + GIT_LEITURA, []),
    "seguranca": ("revisar-seguranca", "Revisão de segurança", ESCRITA + GIT_LEITURA, ["12-seguranca"]),
    "mudanca": ("controle-de-mudancas", "Pedido de mudança", ESCRITA, []),
    "tela": ("implementar-tela-figma", "Implementar tela do Figma", ESCRITA + ["mcp__figma"], []),
    "figjam": ("diagramas-figjam", "Diagramas no FigJam", LEITURA + ["Write", "Edit", "mcp__figma"], []),
    "livre": (None, "Comando livre", ESCRITA, []),
}
# Mensagens do próprio Claude Code quando a cota da conta acaba (só são procuradas se a execução falhou).
RE_LIMITE = re.compile(r"(?:you'?ve|you have) (?:hit|reached) your .{0,40}limit|usage limit reached", re.I)
ETAPAS_ESPECIFICACAO = ["requisitos", "casos-de-uso", "interface", "uml", "banco", "arquitetura", "backlog", "testes",
                        "proposta"]
# Como `prumo claude especificar` distribui as etapas em sessões do Claude Code. Cada sessão nova paga de novo o
# contexto fixo (instruções, ferramentas, AGENTS.md) e relê os documentos; menos sessões gastam menos tokens.
# A proposta fica sempre numa sessão própria: ela usa o docs/orcamento.md, que o Prumo gera entre as sessões.
GRUPOS_ESPECIFICACAO = [
    ["requisitos", "casos-de-uso", "interface"],   # análise: o que o cliente pediu
    ["uml", "banco", "arquitetura"],                # solução: como será construído
    ["backlog", "testes"],                          # planejamento: quanto trabalho e como será verificado
    ["proposta"],                                   # comercial: precisa do orçamento gerado pelo Prumo
]
MODOS_SESSAO = {
    "grupos": "quatro sessões (análise, solução, planejamento e proposta)",
    "unica": "uma sessão para as etapas e outra para a proposta, que usa o orçamento",
    "etapa": "uma sessão por etapa",
}


def planejar_sessoes(etapas, modo="grupos"):
    """Divide as etapas (já filtradas e em ordem) em sessões, conforme o modo."""
    if modo not in MODOS_SESSAO:
        raise ErroPrumo(f"Modo de sessões desconhecido: {modo}. Opções: {', '.join(MODOS_SESSAO)}")
    if modo == "etapa":
        return [[e] for e in etapas]
    if modo == "unica":
        blocos = [list(etapas)]
    else:
        blocos = [[e for e in grupo if e in etapas] for grupo in GRUPOS_ESPECIFICACAO]
        blocos += [[e] for e in etapas if not any(e in g for g in GRUPOS_ESPECIFICACAO)]
    saida = []
    for bloco in blocos:
        if "proposta" in bloco and len(bloco) > 1:
            saida += [[e for e in bloco if e != "proposta"], ["proposta"]]
        elif bloco:
            saida.append(bloco)
    return saida


def _corpo_skill(projeto, skill):
    """Texto da skill do projeto sem o frontmatter e com os títulos rebaixados, para transcrever no prompt."""
    arq = projeto.raiz / ".claude" / "skills" / skill / "SKILL.md"
    if not arq.exists():
        return None
    texto = arq.read_text(encoding="utf-8")
    texto = re.sub(r"\A---\r?\n.*?\r?\n---\r?\n", "", texto, flags=re.S).strip()
    return re.sub(r"^(#+) ", lambda m: "##" + m.group(1) + " ", texto, flags=re.M)


def executavel_claude():
    exe = os.environ.get("PRUMO_CLAUDE") or shutil.which("claude")
    if not exe:
        raise ErroPrumo(
            "Claude Code não encontrado no PATH. Instale com `npm install -g @anthropic-ai/claude-code` "
            "(ou o instalador oficial) e rode `claude` uma vez para entrar na sua conta."
        )
    return exe


def etapa_existe(projeto, tarefa):
    docs = TAREFAS[tarefa][3]
    if not docs:
        return True
    lista = projeto.config.get("documentos") or []
    return any(any(d in doc for d in docs) for doc in lista)


def montar_prompt_etapas(projeto, etapas, texto=""):
    """Prompt de uma sessão de especificação com uma ou mais etapas, já com o texto das skills transcrito."""
    nome = projeto.config.get("projeto")
    descricoes = ", ".join(TAREFAS[e][1] for e in etapas)
    if len(etapas) == 1:
        partes = [f"Projeto \"{nome}\" gerenciado pelo Prumo. Tarefa: {descricoes}."]
    else:
        partes = [
            f"Projeto \"{nome}\" gerenciado pelo Prumo. Tarefa: especificação, etapas {descricoes}.",
            "Execute as etapas abaixo nesta ordem, nesta mesma sessão. Conclua cada uma antes de começar a seguinte e "
            "aproveite o que já leu e escreveu nas anteriores, sem reler.",
        ]
    for n, etapa in enumerate(etapas, 1):
        skill, descricao = TAREFAS[etapa][0], TAREFAS[etapa][1]
        corpo = _corpo_skill(projeto, skill)
        titulo = f"## Etapa {n} de {len(etapas)}: {descricao}" if len(etapas) > 1 else f"## {descricao}"
        if corpo:
            partes.append(f"{titulo} (skill `{skill}`, transcrita abaixo; não é preciso abrir o SKILL.md)\n\n{corpo}")
        else:
            partes.append(f"{titulo}\n\nSiga a skill `{skill}`: leia .claude/skills/{skill}/SKILL.md e execute o procedimento.")
    partes.append(REGRAS_ESPECIFICACAO)
    if texto:
        partes.append(f"Instruções adicionais do usuário: {texto.strip()}")
    partes.append(AVISO_NAO_INTERATIVO)
    return "\n\n".join(partes)


def montar_prompt(projeto, tarefa, alvo="", texto=""):
    skill, descricao, _f, _d = TAREFAS[tarefa]
    nome = projeto.config.get("projeto")
    if tarefa in ETAPAS_ESPECIFICACAO and not alvo:
        return montar_prompt_etapas(projeto, [tarefa], texto)
    if tarefa == "livre":
        if not texto.strip():
            raise ErroPrumo("Informe o comando para o Claude (texto do pedido).")
        return f"Projeto \"{nome}\" (Prumo; siga AGENTS.md).\n\n{texto.strip()}\n\nTermine com um resumo curto do que foi feito."
    partes = [
        f"Projeto \"{nome}\" gerenciado pelo Prumo. Tarefa: {descricao}.",
        f"Siga a skill `{skill}`: leia .claude/skills/{skill}/SKILL.md e execute o procedimento.",
    ]
    if alvo:
        partes.append(f"Alvo: {alvo}.")
    if texto:
        partes.append(f"Instruções adicionais do usuário: {texto.strip()}")
    if tarefa in ("implementar", "revisar", "documentar") and alvo and re.fullmatch(r"[A-Z]{2,3}-\d{2,4}", alvo):
        try:
            pacote = validacao.contexto(projeto, [alvo])
            partes.append("Trilha da especificação já extraída (não é preciso reler os documentos inteiros):\n\n" + pacote)
        except ErroPrumo:
            pass
    if tarefa == "mudanca" and not texto:
        raise ErroPrumo("Descreva a mudança pedida pelo cliente (ex.: prumo claude mudanca --texto \"incluir boleto\").")
    partes.append(AVISO_NAO_INTERATIVO)
    return "\n\n".join(partes)


def ferramentas(projeto, tarefa, extras=None, etapas=None):
    lista = [f for t in (etapas or [tarefa]) for f in TAREFAS[t][2]]
    cfg = projeto.config
    testar = ((cfg.get("comandos") or {}).get("testar") or "").strip()
    if testar and tarefa in ("implementar", "revisar", "seguranca"):
        lista.append(f"Bash({testar}:*)")
    lista += (cfg.get("claude") or {}).get("ferramentas_extras") or []
    lista += extras or []
    return list(dict.fromkeys(lista))


def montar_comando(projeto, tarefa, continuar=False, sessao=None, modelo=None, max_turnos=None, extras=None,
                   modo=None, formato="stream-json", etapas=None):
    cfg = projeto.config.get("claude") or {}
    exe = executavel_claude()
    base = [sys.executable, exe] if exe.lower().endswith(".py") else [exe]  # .py: dublê usado nos testes
    args = base + ["-p", "--output-format", formato]
    if formato == "stream-json":
        args.append("--verbose")
    modo = modo or ("default" if tarefa == "revisar" else "acceptEdits")
    args += ["--permission-mode", modo, "--allowedTools", ",".join(ferramentas(projeto, tarefa, extras, etapas))]
    modelo = modelo or cfg.get("modelo")
    if modelo:
        args += ["--model", modelo]
    max_turnos = max_turnos or cfg.get("max_turnos")
    if max_turnos:
        args += ["--max-turns", str(max_turnos)]
    if sessao:
        args += ["--resume", sessao]
    elif continuar:
        ultima = ultima_sessao(projeto)
        args += ["--resume", ultima] if ultima else ["--continue"]
    return args


def ultima_sessao(projeto):
    arq = projeto.raiz / ".prumo" / "claude" / "ultima_sessao.txt"
    return arq.read_text(encoding="utf-8").strip() if arq.exists() else None


def _resumir_ferramenta(bloco):
    nome = bloco.get("name", "?")
    entrada = bloco.get("input") or {}
    alvo = entrada.get("file_path") or entrada.get("path") or entrada.get("pattern") or entrada.get("command") or ""
    alvo = str(alvo).replace("\n", " ")
    return f"  → {nome} {alvo[:100]}".rstrip()


def _resumir_tokens(ev):
    """Soma os tokens do evento `result` (todos os modelos da sessão, inclusive subagentes)."""
    por_modelo = ev.get("modelUsage") or {}
    campos = {"entrada": "inputTokens", "saida": "outputTokens",
              "cache_leitura": "cacheReadInputTokens", "cache_escrita": "cacheCreationInputTokens"}
    if por_modelo:
        total = {k: sum(int((m or {}).get(c) or 0) for m in por_modelo.values()) for k, c in campos.items()}
        total["modelos"] = sorted(por_modelo)
    else:
        uso = ev.get("usage") or {}
        if not uso:
            return None
        nomes = {"entrada": "input_tokens", "saida": "output_tokens",
                 "cache_leitura": "cache_read_input_tokens", "cache_escrita": "cache_creation_input_tokens"}
        total = {k: int(uso.get(c) or 0) for k, c in nomes.items()}
    total["total"] = total["entrada"] + total["saida"] + total["cache_leitura"] + total["cache_escrita"]
    return total


def _descontar_sessao_anterior(historico, resultado):
    """Numa sessão retomada, o Claude Code informa custo e tokens acumulados desde o início da sessão.
    Desconta o que já foi registrado para a mesma sessão, para o histórico não contar duas vezes."""
    sessao = resultado.get("sessao")
    if not sessao or not historico.exists():
        return
    anteriores = []
    for linha in historico.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(linha)
        except json.JSONDecodeError:
            continue
        if item.get("sessao") == sessao:
            anteriores.append(item)
    if not anteriores:
        return
    if isinstance(resultado.get("custo_usd"), (int, float)):
        resultado["custo_usd_sessao"] = resultado["custo_usd"]
        resultado["custo_usd"] = round(max(0.0, resultado["custo_usd"] - sum(a.get("custo_usd") or 0 for a in anteriores)), 6)
    tokens = resultado.get("tokens")
    if tokens:
        for k in ("entrada", "saida", "cache_leitura", "cache_escrita", "total"):
            tokens[k] = max(0, tokens.get(k, 0) - sum((a.get("tokens") or {}).get(k, 0) for a in anteriores))


def executar(projeto, tarefa, alvo="", texto="", continuar=False, sessao=None, modelo=None, max_turnos=None,
             extras=None, modo=None, simular=False, ao_evento=None, etapas=None):
    """Roda uma tarefa no Claude Code e devolve o resultado (dict). `ao_evento(linha)` recebe o progresso legível.

    Com `etapas` (lista de etapas de especificação), roda todas na mesma sessão; `tarefa` é ignorada."""
    if etapas:
        desconhecidas = [e for e in etapas if e not in ETAPAS_ESPECIFICACAO]
        if desconhecidas:
            raise ErroPrumo(f"Etapa desconhecida: {', '.join(desconhecidas)}. Opções: {', '.join(ETAPAS_ESPECIFICACAO)}")
        etapas = list(etapas)
        tarefa = "+".join(etapas)
        descricao = ", ".join(TAREFAS[e][1] for e in etapas)
        prompt = montar_prompt_etapas(projeto, etapas, texto)
        base_tarefa = etapas[0]
    else:
        if tarefa not in TAREFAS:
            raise ErroPrumo(f"Tarefa desconhecida: {tarefa}. Opções: especificar, {', '.join(TAREFAS)}")
        descricao = TAREFAS[tarefa][1]
        prompt = montar_prompt(projeto, tarefa, alvo, texto)
        base_tarefa = tarefa
    emitir = ao_evento or progresso
    if simular:
        try:
            args = montar_comando(projeto, base_tarefa, continuar, sessao, modelo, max_turnos, extras, modo, etapas=etapas)
        except ErroPrumo:
            args = ["claude", "-p", "..."]
        return {"simulado": True, "tarefa": tarefa, "comando": args, "prompt": prompt, "cwd": str(projeto.raiz)}
    args = montar_comando(projeto, base_tarefa, continuar, sessao, modelo, max_turnos, extras, modo, etapas=etapas)

    pasta_log = projeto.raiz / ".prumo" / "claude"
    pasta_log.mkdir(parents=True, exist_ok=True)
    carimbo = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    inicio = time.time()
    emitir(f"[Prumo] Claude: {descricao}{' · ' + alvo if alvo else ''}")
    resultado = {"tarefa": tarefa, "alvo": alvo, "inicio": datetime.now().astimezone().isoformat(timespec="seconds")}
    if etapas:
        resultado["etapas"] = etapas
    texto_final, eventos_brutos = "", []
    try:
        proc = subprocess.Popen(args, cwd=str(projeto.raiz), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
    except OSError as e:
        raise ErroPrumo(f"Não consegui iniciar o Claude Code ({args[0]}): {e}") from e
    proc.stdin.write(prompt.encode("utf-8"))
    proc.stdin.close()
    for bruto in proc.stdout:
        linha = bruto.decode("utf-8", "replace").strip()
        if not linha:
            continue
        eventos_brutos.append(linha)
        try:
            ev = json.loads(linha)
        except json.JSONDecodeError:
            emitir(linha)
            continue
        tipo = ev.get("type")
        if tipo == "system" and ev.get("subtype") == "init":
            resultado["sessao"] = ev.get("session_id")
            emitir(f"  sessão {ev.get('session_id', '?')} · modelo {ev.get('model', '?')}")
        elif tipo == "assistant":
            for bloco in (ev.get("message") or {}).get("content") or []:
                if bloco.get("type") == "text" and bloco.get("text", "").strip():
                    emitir(bloco["text"].strip())
                elif bloco.get("type") == "tool_use":
                    emitir(_resumir_ferramenta(bloco))
        elif tipo == "result":
            texto_final = ev.get("result") or ""
            resultado.update({
                "sessao": ev.get("session_id") or resultado.get("sessao"),
                "erro": bool(ev.get("is_error")) or ev.get("subtype") not in (None, "success"),
                "subtipo": ev.get("subtype"),
                "custo_usd": ev.get("total_cost_usd"),
                "turnos": ev.get("num_turns"),
            })
            tokens = _resumir_tokens(ev)
            if tokens:
                resultado["tokens"] = tokens
    erros = proc.stderr.read().decode("utf-8", "replace").strip()
    codigo = proc.wait()
    resultado["codigo_saida"] = codigo
    resultado["duracao_s"] = round(time.time() - inicio, 1)
    resultado["resumo"] = texto_final
    falhou = resultado.get("erro") or codigo != 0
    if falhou and (RE_LIMITE.search(texto_final or "") or RE_LIMITE.search(erros or "")):
        resultado["erro"] = True
        resultado["limite_atingido"] = True
    if codigo != 0:
        resultado["erro"] = True
        if erros:
            resultado["stderr"] = erros[-2000:]
            emitir(erros[-1000:])
    if "--resume" in args or "--continue" in args:
        _descontar_sessao_anterior(pasta_log / "historico.jsonl", resultado)
    if resultado.get("sessao"):
        gravar(pasta_log / "ultima_sessao.txt", resultado["sessao"])
    log = pasta_log / f"{carimbo}_{tarefa}.md"
    gravar(log, f"# {descricao} — {carimbo}\n\n## Comando\n\n```\n{' '.join(args)}\n```\n\n"
                f"## Prompt\n\n{prompt}\n\n## Resultado\n\n{texto_final or '(sem resumo)'}\n\n"
                f"```json\n{json.dumps({k: v for k, v in resultado.items() if k != 'resumo'}, ensure_ascii=False, indent=2)}\n```\n")
    resultado["log"] = projeto.rel(log)
    with open(pasta_log / "historico.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({k: v for k, v in resultado.items() if k not in ("resumo", "stderr")}, ensure_ascii=False) + "\n")
    return resultado


def etapas_do_projeto(projeto, de=None, ate=None):
    """Etapas de especificação que existem no perfil do projeto, de `de` até `ate` (inclusive), na ordem padrão.
    Se `de` ou `ate` não existir no perfil, vale a posição dela na ordem (ex.: --de uml num site começa na arquitetura)."""
    ordem = ETAPAS_ESPECIFICACAO
    for nome in (de, ate):
        if nome and nome not in ordem:
            raise ErroPrumo(f"Etapa desconhecida: {nome}. Opções: {', '.join(ordem)}")
    etapas = [e for e in ordem if etapa_existe(projeto, e)]
    if de:
        etapas = [e for e in etapas if ordem.index(e) >= ordem.index(de)]
    if ate:
        etapas = [e for e in etapas if ordem.index(e) <= ordem.index(ate)]
    return etapas


def _comando_retomar(de, ate=None, sessoes=None):
    partes = ["prumo claude especificar", f"--de {de}"]
    if ate:
        partes.append(f"--ate {ate}")
    if sessoes:
        partes.append(f"--sessoes {sessoes}")
    return " ".join(partes)


def modo_sessoes(projeto, sessoes=None):
    return sessoes or (projeto.config.get("claude") or {}).get("sessoes_especificacao") or "grupos"


def especificar(projeto, de=None, ate=None, pausar=None, ao_evento=None, corrigir=True, sessoes=None, **kw):
    """Roda as etapas de especificação, agrupadas em sessões conforme `sessoes` (grupos, unica ou etapa),
    validando e corrigindo entre uma sessão e a seguinte."""
    from . import gestao, rastreio
    emitir = ao_evento or progresso
    blocos = planejar_sessoes(etapas_do_projeto(projeto, de, ate), modo_sessoes(projeto, sessoes))
    if pausar is None:
        pausar = sys.stdin.isatty() and ao_evento is None
    resultados = []

    def gerar_orcamento():
        try:
            o = gestao.orcamento(projeto)
        except ErroPrumo as e:
            emitir(f"[Prumo] Orçamento não gerado: {e}")
            return
        opc = f" + {o['horas_opcionais']:.1f}h de opcionais fora do total" if o.get("opcionais") else ""
        emitir(f"[Prumo] Orçamento: {o['horas_total']:.1f}h no total{opc} ({o['arquivo']}).")

    for n, bloco in enumerate(blocos, 1):
        emitir(f"\n=== Sessão {n}/{len(blocos)}: {', '.join(TAREFAS[e][1] for e in bloco)} ===")
        if "proposta" in bloco and "backlog" not in bloco:
            gerar_orcamento()  # a proposta usa os totais do orçamento atual do backlog
        r = executar(projeto, bloco[0], etapas=bloco, ao_evento=ao_evento, **kw)
        resultados.append(r)
        if r.get("limite_atingido"):
            emitir(f"[Prumo] Limite de uso do Claude atingido ({(r.get('resumo') or '').strip()[:120]}). "
                   f"Quando o limite renovar, retome com: {_comando_retomar(bloco[0], ate, sessoes)}")
            break
        if r.get("erro"):
            emitir(f"[Prumo] A sessão ({', '.join(bloco)}) terminou com erro; parando. Veja {r.get('log')}.")
            break
        problemas = [m for g, m in validacao.validar(projeto) if g == "erro"]
        if problemas and corrigir and r.get("sessao"):
            emitir(f"[Prumo] validar encontrou {len(problemas)} erro(s); pedindo correção ao Claude.")
            c = executar(projeto, "livre", texto="O `prumo validar` encontrou estes erros. Corrija-os nos documentos:\n- "
                         + "\n- ".join(problemas[:30]) + "\n\n" + DICAS_VALIDACAO,
                         sessao=r["sessao"], ao_evento=ao_evento)
            resultados.append(c)
            if c.get("limite_atingido"):
                if n < len(blocos):
                    dica = f"rode `prumo validar` e retome com: {_comando_retomar(blocos[n][0], ate, sessoes)}"
                else:
                    dica = "rode `prumo validar` e corrija o que faltar (ou `prumo claude livre --continuar \"corrija os erros do validar\"`)"
                emitir(f"[Prumo] Limite de uso do Claude atingido durante a correção. Quando renovar, {dica}")
                break
        if "backlog" in bloco:
            gerar_orcamento()
        if pausar and n < len(blocos):
            seguinte = ", ".join(TAREFAS[e][1] for e in blocos[n])
            resposta = input(f"Revise os documentos. Seguir para '{seguinte}'? [S/n] ").strip().lower()
            if resposta in ("n", "nao", "não"):
                break
    destino, _ = rastreio.gerar_matriz(projeto)
    emitir(f"[Prumo] Rastreabilidade atualizada em {projeto.rel(destino)}.")
    return resultados


def historico(projeto, limite=20):
    arq = projeto.raiz / ".prumo" / "claude" / "historico.jsonl"
    if not arq.exists():
        return []
    linhas = arq.read_text(encoding="utf-8").splitlines()[-limite:]
    saida = []
    for l in linhas:
        try:
            saida.append(json.loads(l))
        except json.JSONDecodeError:
            pass
    return saida
