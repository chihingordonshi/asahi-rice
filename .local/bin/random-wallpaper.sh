#!/usr/bin/env bash
set -euo pipefail

# Compatibility name for existing callers; never start a second renderer.
exec "$(dirname -- "${BASH_SOURCE[0]}")/random-wallpaper" "$@"
