#!/usr/bin/env sh

set -eu

HOST_NAME="site.felipeleal.browserbridge"

TARGET="$HOME/.mozilla/native-messaging-hosts/$HOST_NAME.json"

echo ""
echo "Removendo BrowserBridge Native Host..."
echo ""

if [ -f "$TARGET" ]; then

    rm -f "$TARGET"

    echo "Manifest removido:"
    echo "$TARGET"

else

    echo "Manifest nao encontrado."

fi

echo ""
echo "BrowserBridge Native Host removido."
echo ""