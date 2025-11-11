#!/usr/bin/env bash

declare INIT=true
declare CLEAN=false
declare -r USAGE="
To setup/clean the Python virtual environment using Poetry

USAGE
  \$ run.sh [OPTIONS]

OPTIONS
  -i, --init       initialize the Python virtual environment using Poetry. ( This is the default behavior )
  -c, --clean      clean up the Poetry cache and remove all virtual environments
  -h, --help       show this help message and exit
"

while [[ $# -gt 0 ]]; do
  case $1 in
    -c | --clean ) INIT=false ; CLEAN=true  ; shift      ;;
    -i | --init  ) INIT=true  ; CLEAN=false ; shift      ;;
    -h | --help  ) echo -e "${USAGE}"; exit 0            ;;
    *            ) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

type -P poetry >/dev/null 2>&1 || {
  echo "Poetry is not installed. Please install Poetry first." >&2
  exit 1
}

"${INIT}" && {
  poetry install;
  # shellcheck disable=SC1091
  source "$(poetry env info --path)/bin/activate";
}

"${CLEAN}" && {
  # poetry env remove "$(poetry env list --full-path | grep Activated | awk '{print $1}')" || true;
  poetry cache clear pypi --all
  poetry cache clear virtualenvs --all
  poetry env remove --all
}

# vim:tabstop=2:softtabstop=2:shiftwidth=2:expandtab:filetype=sh:
