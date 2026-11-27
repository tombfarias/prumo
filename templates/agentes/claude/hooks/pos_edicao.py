"""PostToolUse (Edit/Write): formata o arquivo e roda o lint configurado em projeto.prumo.json.

Configuração (projeto.prumo.json):
  "comandos": {"formatar": "npx prettier --write {arquivo}", "lint": "npx eslint {arquivo}"}
Formatação é silenciosa (melhor esforço). Erros de lint voltam para o Claude corrigir.
"""

import os
import shlex
import subprocess
import sys
from pathlib import Path

from datetime import datetime

from prumo_comum import (
    carregar_config, escrever_stderr, gravar_alteracoes, ler_alteracoes, ler_entrada, raiz_projeto, relativo,
)

IGNORAR = ("node_modules/", ".git/", "dist/", "build/", ".next/", ".venv/", "venv/", ".prumo/")
EXT_CODIGO = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue", ".svelte", ".astro",
    ".java", ".kt", ".cs", ".go", ".rb", ".php", ".rs", ".dart", ".swift", ".css", ".scss",
}


def citar(caminho):
    if os.name == "nt":
        return '"' + caminho.replace('"', "") + '"'
    return shlex.quote(caminho)


def linhas_alteradas(dados):
    if "content" in dados:
        return len(str(dados.get("content") or "").splitlines())
    edicoes = dados.get("edits") or [dados]
    return sum(max(len(str(e.get("old_string") or "").splitlines()), len(str(e.get("new_string") or "").splitlines()))
               for e in edicoes)


def registrar_alteracao(raiz, rel, dados):
    """Acumula as edições da sessão; o hook de parada decide se a mudança é significativa."""
    try:
        reg = ler_alteracoes(raiz)
        if not reg.get("desde"):
            reg["desde"] = datetime.now().astimezone().isoformat(timespec="seconds")
        arquivos = reg.setdefault("arquivos", {})
        arquivos[rel] = arquivos.get(rel, 0) + max(1, linhas_alteradas(dados))
        gravar_alteracoes(raiz, reg)
    except Exception:
        pass


def rodar(cmd, raiz):
    return subprocess.run(cmd, shell=True, cwd=str(raiz), capture_output=True, timeout=110)


def main():
    entrada = ler_entrada()
    dados = entrada.get("tool_input") or {}
    caminho = dados.get("file_path") or ""
    raiz = raiz_projeto()
    rel = relativo(raiz, caminho)
    if not rel or rel.startswith(IGNORAR) or not Path(caminho).exists():
        sys.exit(0)
    registrar_alteracao(raiz, rel, dados)
    config = carregar_config(raiz)
    comandos = config.get("comandos") or {}
    extras = {e.lower() for e in ((config.get("hooks") or {}).get("extensoes_lint") or []) if isinstance(e, str)}
    alvo = citar(str(Path(caminho)))

    formatar = (comandos.get("formatar") or "").strip()
    if formatar:
        try:
            rodar(formatar.replace("{arquivo}", alvo), raiz)
        except Exception:
            pass

    lint = (comandos.get("lint") or "").strip()
    if lint and Path(caminho).suffix.lower() in (EXT_CODIGO | extras):
        try:
            r = rodar(lint.replace("{arquivo}", alvo), raiz)
        except subprocess.TimeoutExpired:
            sys.exit(0)
        if r.returncode != 0:
            saida = (r.stdout + r.stderr).decode("utf-8", "replace").strip().splitlines()
            escrever_stderr(f"[Prumo] O lint encontrou problemas em {rel}:\n" + "\n".join(saida[-40:]))
            sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
