#!/usr/bin/env bash

type -P poetry >/dev/null 2>&1 || {
  echo "Poetry is not installed. Please install Poetry first." >&2
  exit 1
}

poetry install
# shellcheck disable=SC1091
source "$(poetry env info --path)/bin/activate"

# vim:tabstop=2:softtabstop=2:shiftwidth=2:expandtab:filetype=sh:
