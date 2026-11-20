"""UserPromptSubmit / Stop: registra a atividade em .prumo/atividade.log para `prumo horas`.

Não escreve nada na saída padrão (no UserPromptSubmit ela iria para o contexto do Claude).
Desligue com "hooks": {"registrar_horas": false} em projeto.prumo.json.
"""

import sys
from datetime import datetime

from prumo_comum import carregar_config, ler_entrada, raiz_projeto


def main():
    evento = sys.argv[1] if len(sys.argv) > 1 else "evento"
    entrada = ler_entrada()
    raiz = raiz_projeto()
    config = carregar_config(raiz)
    if not config or (config.get("hooks") or {}).get("registrar_horas") is False:
        sys.exit(0)
    try:
        pasta = raiz / ".prumo"
        pasta.mkdir(exist_ok=True)
        agora = datetime.now().astimezone().isoformat(timespec="seconds")
        sessao = entrada.get("session_id", "")
        with open(pasta / "atividade.log", "a", encoding="utf-8") as f:
            f.write(f"{agora}\t{evento}\t{sessao}\n")
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
