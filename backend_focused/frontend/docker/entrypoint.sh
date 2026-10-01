#!/bin/sh
set -eu

stamp="node_modules/.install-stamp"
if [ ! -f "$stamp" ] || ! cmp -s package-lock.json "$stamp"; then
  npm ci
  cp package-lock.json "$stamp"
fi

exec "$@"
