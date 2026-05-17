#!/usr/bin/env bash
# lrc-tools uninstall — revierte lo instalado por setup.sh
set -euo pipefail

CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/lrc-tools"
PKG_DIR="$CONFIG_DIR/lrc_tools"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/lrc-tools"
BIN_DIR="${HOME}/.local/bin"

BINS=(lrc-fetch lrc-processor lrc-vis lrc-tools lt)

KEEP_DATA=0
KEEP_CONFIG=0
ASSUME_YES=0

usage() {
    cat <<'EOF'
Uso: uninstall.sh [opciones]

Elimina los binarios en ~/.local/bin, el paquete en ~/.config/lrc-tools/lrc_tools/
y, según elijas, la configuración y las letras descargadas.

Opciones:
  -y, --yes          Sin preguntas: borra bins, paquete, config y datos
  --keep-data        Solo bins + paquete; conserva config y ~/.local/share/lrc-tools
  --keep-config      Borra bins, paquete y datos; conserva ~/.config/lrc-tools
  -h, --help         Esta ayuda

No desinstala dependencias de sistema (pacman) ni paquetes pip globales.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -y|--yes) ASSUME_YES=1 ;;
        --keep-data) KEEP_DATA=1 ;;
        --keep-config) KEEP_CONFIG=1 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Opción desconocida: $1" >&2; usage >&2; exit 1 ;;
    esac
    shift
done

confirm() {
    local prompt="$1"
    if [[ "$ASSUME_YES" -eq 1 ]]; then
        return 0
    fi
    read -rp "$prompt [y/N] " ans
    [[ "${ans,,}" == "y" || "${ans,,}" == "yes" || "${ans,,}" == "s" || "${ans,,}" == "si" ]]
}

echo "=============================="
echo " lrc-tools uninstall"
echo "=============================="
echo "Package:  $PKG_DIR"
echo "Config:   $CONFIG_DIR"
echo "Data:     $DATA_DIR"
echo "Bins:     $BIN_DIR"
echo

removed_any=0

# --- Binarios ---
echo "[1/3] Binarios en $BIN_DIR"
for name in "${BINS[@]}"; do
    dest="$BIN_DIR/$name"
    if [[ -e "$dest" || -L "$dest" ]]; then
        rm -f "$dest"
        echo "  ✗ eliminado $name"
        removed_any=1
    else
        echo "  · $name (no estaba instalado)"
    fi
done

# --- Paquete Python instalado ---
echo
echo "[2/3] Paquete instalado"
if [[ -d "$PKG_DIR" ]]; then
    rm -rf "$PKG_DIR"
    echo "  ✗ eliminado $PKG_DIR"
    removed_any=1
else
    echo "  · $PKG_DIR no existe"
fi

# --- Config (opcional) ---
echo
echo "[3/3] Configuración y datos"
if [[ "$KEEP_CONFIG" -eq 0 ]]; then
    if [[ -d "$CONFIG_DIR" ]]; then
        if [[ "$ASSUME_YES" -eq 1 ]] || confirm "¿Borrar configuración en $CONFIG_DIR?"; then
            rm -rf "$CONFIG_DIR"
            echo "  ✗ eliminado $CONFIG_DIR"
            removed_any=1
        else
            echo "  · config conservada"
        fi
    else
        echo "  · $CONFIG_DIR no existe"
    fi
else
    echo "  · config conservada (--keep-config)"
fi

if [[ "$KEEP_DATA" -eq 0 ]]; then
    if [[ -d "$DATA_DIR" ]]; then
        if [[ "$ASSUME_YES" -eq 1 ]] || confirm "¿Borrar letras y datos en $DATA_DIR?"; then
            rm -rf "$DATA_DIR"
            echo "  ✗ eliminado $DATA_DIR"
            removed_any=1
        else
            echo "  · datos conservados"
        fi
    else
        echo "  · $DATA_DIR no existe"
    fi
else
    echo "  · datos conservados (--keep-data)"
fi

echo
echo "=============================="
if [[ "$removed_any" -eq 1 ]]; then
    echo " Desinstalación completada"
else
    echo " No había nada que eliminar (o todo se conservó)"
fi
echo "=============================="
echo
echo "Dependencias pip/sistema (textual, playerctl, etc.) no se tocaron."
echo "Para reinstalar: bash setup.sh desde el repositorio"
