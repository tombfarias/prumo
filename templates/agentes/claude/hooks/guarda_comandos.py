"""PreToolUse (Bash/PowerShell): bloqueia comandos destrutivos e leitura de segredos."""

import re
import sys

from prumo_comum import bloquear, carregar_config, ler_entrada, raiz_projeto

I = re.IGNORECASE

REGRAS = [
    (r"\brm\s+(-\w*\s+)*-\w*[rR]\w*\s+(-\w+\s+)*(/|~|\*|\.|\$HOME)(\s|/?$)",
     "remoção recursiva da raiz, da pasta pessoal ou do projeto inteiro"),
    (r"\brm\s+(-\w*\s+)*-\w*[rR]\w*f?\w*\s+(-\w+\s+)*(\.git|docs)(/|\s|$)",
     "remoção da pasta .git ou da documentação"),
    (r"Remove-Item\b.*-Recurse\b.*\s(\\|/|~|\*|\.|C:\\|D:\\)\s*($|\s)", "remoção recursiva ampla no PowerShell"),
    (r"\bgit\s+push\b.*(\s--force(?!-with-lease)\b|\s-f\b)", "git push --force (use --force-with-lease, se realmente necessário)"),
    (r"\bgit\s+reset\s+--hard\b", "git reset --hard descarta trabalho não commitado"),
    (r"\bgit\s+clean\s+-\w*f", "git clean -f apaga arquivos não versionados"),
    (r"\bgit\s+checkout\s+--\s+\.", "git checkout -- . descarta alterações locais"),
    (r"\bgit\s+branch\s+-D\b", "exclusão forçada de branch"),
    (r"\bdrop\s+(database|schema|table)\b", "DROP de banco, schema ou tabela"),
    (r"\btruncate\s+(table\s+)?\w+", "TRUNCATE de tabela"),
    (r"\bprisma\s+migrate\s+reset\b|\bprisma\s+db\s+push\b.*--force-reset|--accept-data-loss",
     "reset de banco pelo Prisma"),
    (r"\b(manage\.py|artisan)\s+(flush|migrate:fresh|db:wipe)\b", "limpeza total do banco"),
    (r"\bmkfs(\.\w+)?\b|\bdd\s+if=|\bformat\s+[a-z]:", "formatação de disco"),
    (r"\bchmod\s+(-R\s+)?777\b", "permissão 777"),
    (r"(curl|wget|iwr|Invoke-WebRequest)\b[^|]*\|\s*(sudo\s+)?(ba|z)?sh\b|\|\s*iex\b",
     "execução de script baixado da internet sem revisão"),
    (r"\b(npm|pnpm|yarn)\s+publish\b", "publicação de pacote"),
    (r"\b(cat|type|more|less|head|tail|bat|nl|strings|xxd|Get-Content|gc)\b[^|;&\n]*?"
     r"(^|[\s/\\'\"])\.env(\.(?!example\b|sample\b|template\b)[\w.-]+)?(?=$|[\s'\"|;&])",
     "leitura de arquivo .env (segredos)"),
]


def main():
    entrada = ler_entrada()
    comando = (entrada.get("tool_input") or {}).get("command") or ""
    if not comando:
        sys.exit(0)
    config = carregar_config(raiz_projeto())
    permitidos = (config.get("hooks") or {}).get("comandos_permitidos") or []
    if any(re.search(p, comando, I) for p in permitidos):
        sys.exit(0)
    for padrao, motivo in REGRAS:
        if re.search(padrao, comando, I):
            bloquear(
                f"Comando bloqueado: {motivo}.\n"
                f"Comando: {comando}\n"
                "Se for realmente necessário, explique ao usuário e peça que ele rode o comando no terminal, "
                "ou que adicione uma exceção em projeto.prumo.json -> hooks.comandos_permitidos."
            )
    sys.exit(0)


if __name__ == "__main__":
    main()
