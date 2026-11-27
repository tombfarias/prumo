"""Stop: se ligado, roda os testes antes de o Claude encerrar a resposta.

Ligue com "hooks": {"testes_ao_parar": true} e "comandos": {"testar": "npm test"} em projeto.prumo.json.
Se os testes falharem, o Claude recebe a saída e continua trabalhando (uma vez; não entra em loop).
"""

import subprocess
import sys

from prumo_comum import carregar_config, escrever_stderr, ferramenta_ausente, ler_entrada, raiz_projeto


def main():
    entrada = ler_entrada()
    if entrada.get("stop_hook_active"):
        sys.exit(0)
    raiz = raiz_projeto()
    config = carregar_config(raiz)
    if not (config.get("hooks") or {}).get("testes_ao_parar"):
        sys.exit(0)
    testar = ((config.get("comandos") or {}).get("testar") or "").strip()
    if not testar:
        sys.exit(0)
    try:
        r = subprocess.run(testar, shell=True, cwd=str(raiz), capture_output=True, timeout=580)
    except subprocess.TimeoutExpired:
        escrever_stderr("[Prumo] Os testes passaram do tempo limite. Informe o usuário.")
        sys.exit(2)
    if ferramenta_ausente(r):
        escrever_stderr(
            f"[Prumo] Não foi possível rodar os testes (`{testar}`): o programa não está instalado ou não está no PATH. "
            "Não instale nada globalmente por conta própria: avise o usuário qual ferramenta falta."
        )
        sys.exit(2)
    if r.returncode != 0:
        saida = (r.stdout + r.stderr).decode("utf-8", "replace").strip().splitlines()
        escrever_stderr(
            f"[Prumo] Os testes falharam (`{testar}`). Corrija antes de encerrar ou explique ao usuário "
            "por que não foi possível:\n" + "\n".join(saida[-60:])
        )
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
