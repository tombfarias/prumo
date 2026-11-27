"""Orçamento a partir do backlog, horas trabalhadas e exportação das instruções para outros agentes."""

import re
from collections import OrderedDict
from datetime import datetime, timedelta

from . import rastreio
from .util import (
    ErroPrumo, config_freelancer, formatar_horas, formatar_moeda, gravar, hoje_br, ler, tabela_markdown,
)


# ---------------------------------------------------------------- orçamento

def orcamento(projeto, valor_hora=None, contingencia=None):
    analise = rastreio.analisar_projeto(projeto)
    historias = analise.do_tipo("HU")
    if not historias:
        raise ErroPrumo("Nenhuma história (HU-xxx) encontrada em docs/08-backlog.md.")
    freelancer = config_freelancer()
    cfg = projeto.config.get("orcamento") or {}
    valor_hora = next((v for v in (valor_hora, cfg.get("valor_hora"), freelancer.get("valor_hora")) if v), 0)
    contingencia = next((v for v in (contingencia, cfg.get("contingencia_percentual"),
                                     freelancer.get("contingencia_percentual")) if v is not None), 20)
    moeda = freelancer.get("moeda", "BRL")
    epicos = {e.id: e.titulo for e in analise.do_tipo("EP")}

    por_epico = OrderedDict()
    sem_estimativa, opcionais, fora = [], [], []
    for hu in historias:
        horas = rastreio.estimativa_horas(hu)
        prio = rastreio.prioridade(hu)
        if prio == "wont":  # fora desta entrega: não entra no orçamento
            fora.append(hu.id)
            continue
        if horas is None:
            sem_estimativa.append(hu.id)
        if prio == "could":  # opcional: orçado à parte, fora do total
            opcionais.append((hu, horas or 0.0))
            continue
        epico = next((r for r in rastreio.ordenar(hu.refs) if rastreio.tipo_de(r) == "EP"), "—")
        por_epico.setdefault(epico, []).append((hu, horas or 0.0))

    base = sum(h for itens in por_epico.values() for _, h in itens)
    horas_opcionais = sum(h for _, h in opcionais)
    extra = base * float(contingencia) / 100
    total = base + extra
    partes = [
        f"# Orçamento — {projeto.config.get('projeto')}",
        "",
        f"> Gerado por `prumo orcamento` em {hoje_br()} a partir de `docs/08-backlog.md`. Não edite à mão.",
        "",
        "## Parâmetros",
        "",
        tabela_markdown(["Parâmetro", "Valor"], [
            ["Valor da hora", formatar_moeda(valor_hora, moeda) if valor_hora else "não configurado"],
            ["Contingência", f"{contingencia}%"],
            ["Histórias", len(historias)],
        ]),
        "",
        "## Estimativas por épico (escopo base: Must e Should)",
        "",
    ]
    linhas = []
    for epico, itens in por_epico.items():
        subtotal = sum(h for _, h in itens)
        nome = f"{epico} — {epicos.get(epico, '')}".strip(" —") if epico != "—" else "Sem épico"
        for hu, h in itens:
            linhas.append([nome, hu.id, hu.titulo[:70], formatar_horas(h) if h else "sem estimativa"])
        linhas.append([f"**Subtotal {epico}**", "", "", f"**{formatar_horas(subtotal)}**"])
    partes += [tabela_markdown(["Épico", "História", "Título", "Horas"], linhas), ""]
    resumo = [
        ["Horas estimadas", formatar_horas(base)],
        [f"Contingência ({contingencia}%)", formatar_horas(extra)],
        ["**Total de horas**", f"**{formatar_horas(total)}**"],
    ]
    if valor_hora:
        resumo.append(["**Valor total**", f"**{formatar_moeda(total * float(valor_hora), moeda)}**"])
    partes += ["## Total", "", tabela_markdown(["Item", "Valor"], resumo), ""]
    if opcionais:
        linhas_opc = [[hu.id, hu.titulo[:70], formatar_horas(h) if h else "sem estimativa",
                       formatar_moeda(h * (1 + float(contingencia) / 100) * float(valor_hora), moeda) if valor_hora and h else "—"]
                      for hu, h in opcionais]
        linhas_opc.append(["**Total dos opcionais**", "", f"**{formatar_horas(horas_opcionais)}**", ""])
        partes += ["## Opcionais (prioridade Could, fora do total)", "",
                   "O cliente escolhe quais entram. O valor de cada um já inclui a contingência.", "",
                   tabela_markdown(["História", "Título", "Horas", "Valor"], linhas_opc), ""]
    if fora:
        partes += ["## Fora desta entrega (Won't)", "", ", ".join(fora), ""]
    if sem_estimativa:
        partes += ["## Histórias sem estimativa", "", ", ".join(sem_estimativa), ""]
    destino = projeto.docs / "orcamento.md"
    from .i18n import traduzir
    gravar(destino, traduzir("\n".join(partes), projeto.idioma))  # no idioma do projeto
    return {
        "arquivo": projeto.rel(destino), "horas_base": base, "contingencia": contingencia, "horas_total": total,
        "valor_hora": valor_hora, "valor_total": total * float(valor_hora) if valor_hora else None,
        "moeda": moeda, "sem_estimativa": sem_estimativa, "historias": len(historias),
        "horas_opcionais": horas_opcionais, "opcionais": [hu.id for hu, _ in opcionais], "fora": fora,
    }


# ---------------------------------------------------------------- horas

def horas(projeto, de=None, ate=None, pausa_min=30, minimo_min=5):
    log = projeto.raiz / ".prumo" / "atividade.log"
    if not log.exists():
        raise ErroPrumo("Ainda não há registro de atividade (.prumo/atividade.log). "
                        "Ele é gravado pelos hooks do Claude Code a cada pedido e resposta.")
    eventos = []
    for linha in ler(log).splitlines():
        partes = linha.split("\t")
        try:
            momento = datetime.fromisoformat(partes[0])
        except (ValueError, IndexError):
            continue
        dia = momento.date().isoformat()
        if (de and dia < de) or (ate and dia > ate):
            continue
        eventos.append((momento, partes[1] if len(partes) > 1 else ""))
    eventos.sort()
    sessoes = []
    for momento, tipo in eventos:
        # Só um novo pedido depois de uma pausa longa abre outra sessão; o fim de uma resposta
        # sempre conta como trabalho (o Claude pode ter trabalhado sozinho por muito tempo).
        if sessoes and (tipo != "prompt" or momento - sessoes[-1][1] <= timedelta(minutes=pausa_min)):
            sessoes[-1][1] = momento
        else:
            sessoes.append([momento, momento])
    por_dia = OrderedDict()
    for inicio, fim in sessoes:
        duracao = max((fim - inicio).total_seconds() / 3600, minimo_min / 60)
        dia = inicio.date().isoformat()
        d = por_dia.setdefault(dia, {"sessoes": 0, "horas": 0.0})
        d["sessoes"] += 1
        d["horas"] += duracao
    return por_dia


# ---------------------------------------------------------------- exportação para outros agentes

ALVOS = {
    "gemini": ("GEMINI.md", ""),
    "copilot": (".github/copilot-instructions.md", ""),
    "cursor": (".cursor/rules/prumo.mdc", "---\ndescription: Instruções do projeto (geradas pelo Prumo a partir de AGENTS.md)\nalwaysApply: true\n---\n\n"),
}


def exportar_agentes(projeto, alvos=None):
    fonte = projeto.raiz / "AGENTS.md"
    if not fonte.exists():
        raise ErroPrumo("AGENTS.md não encontrado na raiz do projeto.")
    conteudo = ler(fonte)
    aviso = "<!-- Gerado por `prumo agentes exportar` a partir de AGENTS.md. Edite o AGENTS.md e exporte de novo. -->\n\n"
    escritos = []
    for alvo in alvos or ALVOS:
        if alvo not in ALVOS:
            raise ErroPrumo(f"Alvo desconhecido: {alvo}. Opções: {', '.join(ALVOS)}")
        caminho, cabecalho = ALVOS[alvo]
        from .i18n import traduzir
        gravar(projeto.raiz / caminho, traduzir(cabecalho + aviso, projeto.idioma) + conteudo)
        escritos.append(caminho)
    return escritos
