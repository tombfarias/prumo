"""PreToolUse (Read/Edit/Write): protege segredos, documentos aprovados e arquivos gerados."""

import json
import re
import sys
from pathlib import PurePath

from prumo_comum import bloquear, carregar_config, ler_entrada, raiz_projeto, relativo

GERADOS = {
    "docs/rastreabilidade.md": "prumo rastreabilidade",
    "docs/orcamento.md": "prumo orcamento",
    "docs/00-mapa-do-codigo.md": "prumo mapear --atualizar",
}
EXEMPLOS_ENV = {".env.example", ".env.sample", ".env.template"}


def eh_segredo(caminho):
    nome = PurePath(caminho).name.lower()
    if nome in EXEMPLOS_ENV:
        return False
    if nome == ".env" or nome.startswith(".env."):
        return True
    if re.search(r"\.(pem|key|p12|pfx|keystore|jks)$", nome):
        return True
    if nome.startswith("id_rsa") or nome.startswith("id_ed25519"):
        return True
    return nome in {"credentials.json", "secrets.json", "service-account.json"} or nome.startswith("service-account")


def main():
    entrada = ler_entrada()
    ferramenta = entrada.get("tool_name") or ""
    dados = entrada.get("tool_input") or {}
    caminho = dados.get("file_path") or dados.get("notebook_path") or dados.get("path") or ""
    if not caminho:
        sys.exit(0)

    if eh_segredo(caminho):
        bloquear(
            f"Acesso bloqueado a '{PurePath(caminho).name}': arquivos de segredos não podem ser lidos nem editados por agentes. "
            "Documente variáveis em .env.example e peça ao usuário para preencher o .env."
        )

    if ferramenta == "Read":
        sys.exit(0)

    raiz = raiz_projeto()
    rel = relativo(raiz, caminho)
    if rel is None:
        sys.exit(0)
    config = carregar_config(raiz)
    aprovados = config.get("aprovados") or {}

    if rel in aprovados:
        info = aprovados[rel] or {}
        bloquear(
            f"'{rel}' foi aprovado pelo cliente em {info.get('data', '?')} e é somente leitura.\n"
            "Para alterar: registre um pedido com `prumo mudanca \"título\"`, faça a análise de impacto e, "
            "depois da aprovação do cliente, o usuário roda `prumo desaprovar " + rel + "`."
        )

    if rel in GERADOS:
        bloquear(f"'{rel}' é gerado automaticamente. Não edite: rode `{GERADOS[rel]}`.")

    if rel == "projeto.prumo.json":
        trechos = [str(dados.get(k, "")) for k in ("old_string", "new_string")]
        trechos += [str(e.get(k, "")) for e in dados.get("edits") or [] for k in ("old_string", "new_string")]
        if any('"aprovados"' in t or any(a in t for a in aprovados) for t in trechos):
            bloquear("A lista de documentos aprovados só pode ser alterada pelo usuário (prumo aprovar/desaprovar).")
        if ferramenta == "Write":
            try:
                novo = json.loads(dados.get("content") or "{}")
            except Exception:
                bloquear("Conteúdo inválido para projeto.prumo.json (JSON malformado).")
            if (novo.get("aprovados") or {}) != aprovados:
                bloquear("A lista de documentos aprovados só pode ser alterada pelo usuário (prumo aprovar/desaprovar).")

    sys.exit(0)


if __name__ == "__main__":
    main()
