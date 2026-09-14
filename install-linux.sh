#!/usr/bin/env sh
set -eu

HOST_NAME="site.felipeleal.browserbridge"
EXTENSION_ID="browserbridge@felipeleal.site"
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
LAUNCHER="$SCRIPT_DIR/browserbridge-host"

chmod +x "$LAUNCHER"
chmod +x "$SCRIPT_DIR/bridge.py"

TARGET_DIR="$HOME/.mozilla/native-messaging-hosts"
TARGET="$TARGET_DIR/$HOST_NAME.json"

mkdir -p "$TARGET_DIR"

python3 - "$TARGET" "$LAUNCHER" "$HOST_NAME" "$EXTENSION_ID" <<'PY'
import json
import sys
from pathlib import Path

target, launcher, host_name, extension_id = sys.argv[1:]
payload = {
    "name": host_name,
    "description": "BrowserBridge Native Messaging Host",
    "path": launcher,
    "type": "stdio",
    "allowed_extensions": [extension_id],
}
Path(target).write_text(json.dumps(payload, indent=2), encoding="utf-8")
PY

echo
echo "BrowserBridge instalado para o usuário atual."
echo "Manifest: $TARGET"
echo "Agora carregue a extensão no Firefox em about:debugging."
