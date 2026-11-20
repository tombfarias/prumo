#!/bin/sh
# Gera o executável do Prumo para Linux/macOS (no Windows, use build.ps1).
set -e
cd "$(dirname "$0")"
python3 -m pip install --quiet pyinstaller
python3 -m PyInstaller --noconfirm --clean --onefile --name prumo \
  --add-data "templates:templates" --add-data "config/freelancer.exemplo.json:config" \
  --add-data "prumo_cli/gui:prumo_cli/gui" prumo.py
./dist/prumo --versao
