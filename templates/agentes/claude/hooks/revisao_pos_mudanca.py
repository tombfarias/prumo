"""Stop: depois de uma mudança significativa, exige atualizar a documentação e revisar a segurança.

Conta as edições registradas por pos_edicao.py (e, se houver git, arquivos alterados por comandos).
É significativa quando passa de `limite_arquivos` arquivos de código, de `limite_linhas` linhas,
ou quando toca áreas sensíveis (autenticação, banco, rotas, dependências, infraestrutura...).
Configuração em projeto.prumo.json -> "hooks":
  "revisao_pos_mudanca": true, "limite_arquivos": 3, "limite_linhas": 80, "caminhos_sensiveis": []
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

from prumo_comum import (
    areas_sensiveis, carregar_config, documentos_sugeridos, eh_documentacao, escrever_stderr,
    gravar_alteracoes, ler_alteracoes, ler_entrada, raiz_projeto,
)


def arquivos_git(raiz, desde):
    """Arquivos alterados fora das ferramentas de edição (ex.: gerados por comandos) desde o início do registro."""
    if not desde or not (raiz / ".git").exists():
        return []
    try:
        limite = datetime.fromisoformat(desde).timestamp()
        r = subprocess.run(["git", "status", "--porcelain", "-uall"], cwd=str(raiz),
                           capture_output=True, timeout=10)
    except Exception:
        return []
    saida = []
    for linha in r.stdout.decode("utf-8", "replace").splitlines():
        caminho = linha[3:].split(" -> ")[-1].strip().strip('"')
        p = raiz / caminho
        try:
            if p.is_file() and p.stat().st_mtime >= limite:
                saida.append(caminho)
        except OSError:
            pass
    return saida


def arquivar(raiz, registro, motivo):
    try:
        with open(raiz / ".prumo" / "revisoes.log", "a", encoding="utf-8") as f:
            agora = datetime.now().astimezone().isoformat(timespec="seconds")
            f.write(f"{agora}\t{motivo}\t{','.join(sorted(registro.get('arquivos', {})))}\n")
    except Exception:
        pass
    gravar_alteracoes(raiz, {"desde": None, "arquivos": {}})


def main():
    entrada = ler_entrada()
    raiz = raiz_projeto()
    config = carregar_config(raiz)
    opcoes = config.get("hooks") or {}
    if not config or opcoes.get("revisao_pos_mudanca") is False:
        sys.exit(0)
    registro = ler_alteracoes(raiz)
    if entrada.get("stop_hook_active"):
        # O Claude está terminando a revisão pedida por este hook: as edições feitas nela não contam de novo.
        if registro.get("arquivos"):
            arquivar(raiz, registro, "edicoes-da-revisao")
        sys.exit(0)

    linhas_por_arquivo = dict(registro.get("arquivos") or {})
    for extra in arquivos_git(raiz, registro.get("desde")):
        linhas_por_arquivo.setdefault(extra, 0)
    codigo = {a: n for a, n in linhas_por_arquivo.items() if not eh_documentacao(a) and not a.startswith(".prumo/")}
    if not codigo:
        sys.exit(0)

    total_linhas = sum(codigo.values())
    sensiveis = areas_sensiveis(codigo, opcoes.get("caminhos_sensiveis") or [])
    significativa = (
        len(codigo) >= int(opcoes.get("limite_arquivos", 3))
        or total_linhas >= int(opcoes.get("limite_linhas", 80))
        or bool(sensiveis)
    )
    if not significativa:
        sys.exit(0)

    lista = sorted(codigo)
    mostrar = ", ".join(lista[:12]) + (f" (+{len(lista) - 12})" if len(lista) > 12 else "")
    docs = documentos_sugeridos(raiz, lista)
    detalhe_sensivel = f"; áreas sensíveis: {', '.join(sensiveis)}" if sensiveis else ""
    arquivar(raiz, registro, "revisao-solicitada")
    escrever_stderr(
        f"[Prumo] Mudança significativa nesta sessão: {len(lista)} arquivo(s) de código, ~{total_linhas} linha(s){detalhe_sensivel}.\n"
        f"Arquivos: {mostrar}\n"
        "Antes de encerrar, faça as duas verificações obrigatórias do projeto:\n"
        "1. Documentação: siga .claude/skills/atualizar-documentacao/SKILL.md. "
        f"Documentos provavelmente afetados: {', '.join(docs) or 'verifique a trilha da história'}. "
        "Documentos aprovados não podem ser editados: registre um pedido de mudança.\n"
        "2. Segurança: siga .claude/skills/revisar-seguranca/SKILL.md sobre esses arquivos e registre os achados em docs/12-seguranca.md.\n"
        "Depois, resuma ao usuário o que foi atualizado e os achados de segurança (ou que não houve achados)."
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
