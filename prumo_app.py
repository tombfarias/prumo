"""Ponto de entrada da versão com janela (prumo-app.exe): abre a interface gráfica."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from prumo_cli.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["gui"]))
