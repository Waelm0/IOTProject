#!/usr/bin/env bash
set -euo pipefail
export PATH=/d/omnetpp/omnetpp-6.2.0/bin:/d/omnetpp/inet4.6/src:$PATH
cd "$(dirname "$0")"
../src/smarthome.exe -u Cmdenv -n '.;../src;../../../inet4.6/src' -f experiment4.ini --cmdenv-interactive=false "$@"
