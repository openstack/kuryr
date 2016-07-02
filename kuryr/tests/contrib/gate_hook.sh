#!/usr/bin/env bash

set -ex

VENV=${1:-"debug-py27"}

GATE_DEST=$BASE/new
DEVSTACK_PATH=$GATE_DEST/devstack

$BASE/new/devstack-gate/devstack-vm-gate.sh
