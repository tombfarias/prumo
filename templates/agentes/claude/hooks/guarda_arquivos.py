"""PreToolUse (Read/Edit/Write): protege segredos, documentos aprovados e arquivos gerados."""

import json
import re
import sys
from pathlib import PurePath

from prumo_comum import (
    aprovados_do, bloquear, carregar_config, chave, dados_pessoais, ler_entrada, raiz_projeto, relativo, segredos,
)

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
    return nome in {"credentials.json", "secrets.json", "service-account.json", "wp-config.php"} or nome.startswith("service-account")


def texto_novo(dados):
    partes = [str(dados.get("content") or ""), str(dados.get("new_string") or "")]
    partes += [str(e.get("new_string") or "") for e in dados.get("edits") or [] if isinstance(e, dict)]
    return "\n".join(partes)


def verificar_dados_sensiveis(rel, dados, config):
    """Segredos nunca vão para arquivos do projeto; dados pessoais reais de clientes não vão para docs/."""
    if (config.get("hooks") or {}).get("bloquear_dados_sensiveis") is False:
        return
    texto = texto_novo(dados)
    if not texto.strip():
        return
    achados = segredos(texto)
    if chave(rel).startswith("docs/"):
        achados += dados_pessoais(texto)
    if achados:
        bloquear(
            f"O conteúdo para '{rel}' parece conter {', '.join(achados)}. Segredos ficam só no .env (documente o nome "
            "da variável em .env.example) e a documentação usa dados fictícios, nunca dados reais de clientes. "
            "Se for um falso positivo, peça ao usuário para desligar a verificação (hooks.bloquear_dados_sensiveis: false)."
        )


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
    aprovados = aprovados_do(config)
    aprovado = next((a for a in aprovados if chave(a) == chave(rel)), None)

    if aprovado is not None:
        rel = aprovado
        info = aprovados[rel] if isinstance(aprovados[rel], dict) else {}
        bloquear(
            f"'{rel}' foi aprovado pelo cliente em {info.get('data', '?')} e é somente leitura.\n"
            "Para alterar: registre um pedido com `prumo mudanca \"título\"`, faça a análise de impacto e, "
            "depois da aprovação do cliente, o usuário roda `prumo desaprovar " + rel + "`."
        )

    gerado = next((g for g in GERADOS if chave(g) == chave(rel)), None)
    if gerado:
        rel = gerado
        bloquear(f"'{rel}' é gerado automaticamente. Não edite: rode `{GERADOS[rel]}`.")

    verificar_dados_sensiveis(rel, dados, config)

    if chave(rel) == "projeto.prumo.json":
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
