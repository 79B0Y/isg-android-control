#!/bin/bash

# Move/remove legacy backup copies that break Home Assistant imports
# by creating dotted package names like android_tv_box.backup.*

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; }

if [ $# -gt 1 ]; then
  err "Usage: $0 [HA_CONFIG_DIR]"
  exit 1
fi

HA_CONFIG_DIR="${1:-}"

if [ -z "$HA_CONFIG_DIR" ]; then
  # Try common locations
  if [ -d "/config" ]; then
    HA_CONFIG_DIR="/config"
  elif [ -d "$HOME/.homeassistant" ]; then
    HA_CONFIG_DIR="$HOME/.homeassistant"
  elif [ -d "/usr/share/hassio/homeassistant" ]; then
    HA_CONFIG_DIR="/usr/share/hassio/homeassistant"
  else
    err "Could not auto-detect Home Assistant config dir. Pass it explicitly."
    exit 1
  fi
fi

COMP_DIR="$HA_CONFIG_DIR/custom_components"

if [ ! -d "$COMP_DIR" ]; then
  err "custom_components not found at: $COMP_DIR"
  exit 1
fi

info "Scanning for legacy backups in $COMP_DIR"
mkdir -p "$COMP_DIR/_backups"

shopt -s nullglob
moved=0
for legacy in "$COMP_DIR"/android_tv_box.backup.*; do
  if [ -d "$legacy" ]; then
    warn "Moving $(basename "$legacy") to _backups/"
    mv "$legacy" "$COMP_DIR/_backups/"
    moved=$((moved+1))
  fi
done
shopt -u nullglob

if [ $moved -eq 0 ]; then
  info "No legacy dotted backups found."
else
  info "Moved $moved legacy backup folder(s)."
fi

info "Done. Restart Home Assistant to clear the import error."

