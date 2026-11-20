"""SessionStart: injeta no contexto do Claude um resumo do estado da especificação."""

import sys

from prumo_comum import carregar_config, contar_lacunas, documentos, escrever_stdout, raiz_projeto


def main():
    raiz = raiz_projeto()
    config = carregar_config(raiz)
    if not config:
        sys.exit(0)
    aprovados = config.get("aprovados") or {}
    pendentes, completos = [], 0
    for doc in documentos(raiz):
        rel = doc.relative_to(raiz).as_posix()
        if rel in aprovados:
            continue
        try:
            lacunas = contar_lacunas(doc.read_text(encoding="utf-8"))
        except Exception:
            continue
        if lacunas:
            pendentes.append(f"{rel[5:]}({lacunas})")
        else:
            completos += 1
    linhas = [
        f"[Prumo] {config.get('projeto', '?')} · cliente {config.get('cliente', '?')} · perfil {config.get('perfil', '?')}",
        f"Docs: {len(aprovados)} aprovado(s), {completos} completo(s), {len(pendentes)} com lacunas"
        + (": " + ", ".join(pendentes[:10]) + (" ..." if len(pendentes) > 10 else "") if pendentes else ""),
    ]
    if aprovados:
        linhas.append("Somente leitura (aprovados): " + ", ".join(a[5:] if a.startswith("docs/") else a for a in sorted(aprovados)))
    linhas.append("Regras: AGENTS.md. Use `prumo contexto <ID>` para carregar só a trilha necessária.")
    escrever_stdout("\n".join(linhas))
    sys.exit(0)


if __name__ == "__main__":
    main()
