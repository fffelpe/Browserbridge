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


target = sys.argv[1]
launcher = sys.argv[2]
host_name = sys.argv[3]
extension_id = sys.argv[4]


payload = {
    "name": host_name,
    "description": "BrowserBridge Native Messaging Host",
    "path": launcher,
    "type": "stdio",
    "allowed_extensions": [
        extension_id
    ],
}


Path(target).write_text(
    json.dumps(
        payload,
        indent=2
    ),
    encoding="utf-8"
)

PY

echo ""
echo "======================================"
echo " BrowserBridge Native Host instalado"
echo "======================================"
echo ""

echo "Manifest:"
echo "$TARGET"

echo ""

echo "Extensao autorizada:"
echo "$EXTENSION_ID"

echo ""

echo "Agora carregue a extensao no Firefox:"
echo "about:debugging#/runtime/this-firefox"

echo ""