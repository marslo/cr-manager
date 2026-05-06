#!/usr/bin/env bash

declare INIT=true
declare CLEAN=false
declare -r USAGE="
To setup/clean the Python virtual environment using Poetry

USAGE
  \$ source run.sh [OPTIONS]

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
  poetry install
  if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    echo -e "\n\033[3;33m>> to run the application:\033[0m"
    echo -e '  $ poetry run python -m cli.crm --args'
    echo -e '\n\033[3;33m>> or execute with activating poetry virtual environment:\033[0m'
    echo -e "  \$ source \"\$(poetry env info --path)/bin/activate\""
    echo -e "\033[2;3;37m  # and then run the application using python\033[0m"
    echo -e '  $ python -m cli.crm --args'
    echo -e "\033[2;3;37m  # or\033[0m"
    echo -e '  $ cr-manager --args'
  else
    # shellcheck source=/dev/null
    source "$(poetry env info --path)/bin/activate";
  fi
}

"${CLEAN}" && {
  # poetry env remove "$(poetry env list --full-path | grep Activated | awk '{print $1}')" || true;
  poetry cache clear pypi --all
  poetry cache clear virtualenvs --all
  poetry env remove --all
  deactivate 2>/dev/null || true
}

# vim:tabstop=2:softtabstop=2:shiftwidth=2:expandtab:filetype=sh:
