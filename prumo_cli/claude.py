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
    "Onde precisaria perguntar algo sobre o negócio, registre a pergunta na seção 9 de docs/00-briefing.md e siga com o restante. "
    "Os comandos do Prumo (validar, rastreabilidade, orcamento) são executados automaticamente depois desta etapa; "
    "não é preciso rodá-los. Para criar ADRs ou pedidos de mudança, copie o modelo docs/adr/_modelo.md ou "
    "docs/mudancas/_modelo.md para o próximo número livre (ADR-001-titulo.md, CM-001-titulo.md). "
    "Economize tokens: leia só o necessário e faça edições pontuais. "
    "Termine com um resumo curto em português: o que foi feito, arquivos alterados, pendências e perguntas para o cliente."
)

# tarefa -> (skill, descrição, ferramentas, documentos que indicam se a etapa existe no projeto)
TAREFAS = {
    "requisitos": ("levantar-requisitos", "Visão e requisitos", ESCRITA, ["01-visao", "02-requisitos"]),
    "casos-de-uso": ("especificar-casos-de-uso", "Casos de uso", ESCRITA, ["03-casos-de-uso"]),
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
ETAPAS_ESPECIFICACAO = ["requisitos", "casos-de-uso", "uml", "banco", "arquitetura", "backlog", "testes", "proposta"]


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


def montar_prompt(projeto, tarefa, alvo="", texto=""):
    skill, descricao, _f, _d = TAREFAS[tarefa]
    nome = projeto.config.get("projeto")
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


def ferramentas(projeto, tarefa, extras=None):
    lista = list(TAREFAS[tarefa][2])
    cfg = projeto.config
    testar = ((cfg.get("comandos") or {}).get("testar") or "").strip()
    if testar and tarefa in ("implementar", "revisar", "seguranca"):
        lista.append(f"Bash({testar}:*)")
    lista += (cfg.get("claude") or {}).get("ferramentas_extras") or []
    lista += extras or []
    return list(dict.fromkeys(lista))


def montar_comando(projeto, tarefa, continuar=False, sessao=None, modelo=None, max_turnos=None, extras=None,
                   modo=None, formato="stream-json"):
    cfg = projeto.config.get("claude") or {}
    exe = executavel_claude()
    base = [sys.executable, exe] if exe.lower().endswith(".py") else [exe]  # .py: dublê usado nos testes
    args = base + ["-p", "--output-format", formato]
    if formato == "stream-json":
        args.append("--verbose")
    modo = modo or ("default" if tarefa == "revisar" else "acceptEdits")
    args += ["--permission-mode", modo, "--allowedTools", ",".join(ferramentas(projeto, tarefa, extras))]
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


def executar(projeto, tarefa, alvo="", texto="", continuar=False, sessao=None, modelo=None, max_turnos=None,
             extras=None, modo=None, simular=False, ao_evento=None):
    """Roda uma tarefa no Claude Code e devolve o resultado (dict). `ao_evento(linha)` recebe o progresso legível."""
    if tarefa not in TAREFAS:
        raise ErroPrumo(f"Tarefa desconhecida: {tarefa}. Opções: especificar, {', '.join(TAREFAS)}")
    emitir = ao_evento or progresso
    prompt = montar_prompt(projeto, tarefa, alvo, texto)
    if simular:
        try:
            args = montar_comando(projeto, tarefa, continuar, sessao, modelo, max_turnos, extras, modo)
        except ErroPrumo:
            args = ["claude", "-p", "..."]
        return {"simulado": True, "tarefa": tarefa, "comando": args, "prompt": prompt, "cwd": str(projeto.raiz)}
    args = montar_comando(projeto, tarefa, continuar, sessao, modelo, max_turnos, extras, modo)

    pasta_log = projeto.raiz / ".prumo" / "claude"
    pasta_log.mkdir(parents=True, exist_ok=True)
    carimbo = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    inicio = time.time()
    emitir(f"[Prumo] Claude: {TAREFAS[tarefa][1]}{' · ' + alvo if alvo else ''}")
    resultado = {"tarefa": tarefa, "alvo": alvo, "inicio": datetime.now().astimezone().isoformat(timespec="seconds")}
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
    erros = proc.stderr.read().decode("utf-8", "replace").strip()
    codigo = proc.wait()
    resultado["codigo_saida"] = codigo
    resultado["duracao_s"] = round(time.time() - inicio, 1)
    resultado["resumo"] = texto_final
    if codigo != 0:
        resultado["erro"] = True
        if erros:
            resultado["stderr"] = erros[-2000:]
            emitir(erros[-1000:])
    if resultado.get("sessao"):
        gravar(pasta_log / "ultima_sessao.txt", resultado["sessao"])
    log = pasta_log / f"{carimbo}_{tarefa}.md"
    gravar(log, f"# {TAREFAS[tarefa][1]} — {carimbo}\n\n## Comando\n\n```\n{' '.join(args)}\n```\n\n"
                f"## Prompt\n\n{prompt}\n\n## Resultado\n\n{texto_final or '(sem resumo)'}\n\n"
                f"```json\n{json.dumps({k: v for k, v in resultado.items() if k != 'resumo'}, ensure_ascii=False, indent=2)}\n```\n")
    resultado["log"] = projeto.rel(log)
    with open(pasta_log / "historico.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({k: v for k, v in resultado.items() if k not in ("resumo", "stderr")}, ensure_ascii=False) + "\n")
    return resultado


def especificar(projeto, de=None, ate=None, pausar=None, ao_evento=None, corrigir=True, **kw):
    """Roda as etapas de especificação em sequência, validando entre elas."""
    from . import gestao, rastreio
    emitir = ao_evento or progresso
    etapas = [e for e in ETAPAS_ESPECIFICACAO if etapa_existe(projeto, e)]
    if de:
        etapas = etapas[etapas.index(de):] if de in etapas else etapas
    if ate and ate in etapas:
        etapas = etapas[:etapas.index(ate) + 1]
    if pausar is None:
        pausar = sys.stdin.isatty() and ao_evento is None
    resultados = []
    for n, etapa in enumerate(etapas, 1):
        emitir(f"\n=== Etapa {n}/{len(etapas)}: {TAREFAS[etapa][1]} ===")
        r = executar(projeto, etapa, ao_evento=ao_evento, **kw)
        resultados.append(r)
        if r.get("erro"):
            emitir(f"[Prumo] A etapa '{etapa}' terminou com erro; parando. Veja {r.get('log')}.")
            break
        problemas = [m for g, m in validacao.validar(projeto) if g == "erro"]
        if problemas and corrigir and r.get("sessao"):
            emitir(f"[Prumo] validar encontrou {len(problemas)} erro(s); pedindo correção ao Claude.")
            executar(projeto, "livre", texto="O `prumo validar` encontrou estes erros. Corrija-os nos documentos:\n- "
                     + "\n- ".join(problemas[:30]), sessao=r["sessao"], ao_evento=ao_evento)
        if etapa == "backlog":
            try:
                o = gestao.orcamento(projeto)
                emitir(f"[Prumo] Orçamento: {o['horas_total']:.1f}h no total ({o['arquivo']}).")
            except ErroPrumo as e:
                emitir(f"[Prumo] Orçamento não gerado: {e}")
        if pausar and n < len(etapas):
            resposta = input(f"Revise os documentos. Seguir para '{TAREFAS[etapas[n]][1]}'? [S/n] ").strip().lower()
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
