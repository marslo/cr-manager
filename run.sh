#!/usr/bin/env bash
# shellcheck source=/dev/null
#=============================================================================
#     FileName : run.sh
#       Author : marslo
#      Created : 2026-04-16 19:20:20
#   LastChange : 2026-05-06 18:03:52
#=============================================================================

declare INIT=true
declare CLEAN=false
declare -r USAGE="
To setup/clean the Python virtual environment using Poetry

USAGE
  \$ source run.sh
  \033[0;2;3;37m# or\033[0m
  \$ bash run.sh [OPTIONS]

OPTIONS
  -i, --init       initialize the Python virtual environment using Poetry. ( default behavior )
  -c, --clean      clean up the Poetry cache and remove all virtual environments
  -s, --source     source the Poetry virtual environment ( without installing dependencies )
  -p, --print      print the command information and exit
  -h, --help       show this help message and exit
"

declare -r INFO="
\033[3;36m>> to run the application:\033[0m
  \033[0;32m\$ poetry run python -m cli.crm \033[0;3;35m--args\033[0m

\033[3;36m>> or execute with activating poetry virtual environment:\033[0m
  \033[0;32m\$ source \"\$(poetry env info --path)/bin/activate\"\033[0m
\033[2;3;37m  # and then run the application\033[0m
  \033[0;32m\$ python -m cli.crm \033[0;3;35m--args\033[0m
\033[2;3;37m  # or\033[0m
  \033[032m\$ cr-manager \033[0;3;35m--args\033[0m
"

function die() {
  local info="${1:?the info message is required}"
  local extra=''
  [[ 'true' = "${2:-}" ]] && extra=' Please check your Poetry installation.'
  echo "Failed to ${info}.${extra}" >&2
  out 1
}

function out() {
  local code="${1:-0}"
  [[ "${BASH_SOURCE[0]}" != "$0" ]] && return "${code}" || exit "${code}"
}

type -P poetry >/dev/null 2>&1 || die 'find Poetry in PATH, install Poetry first. Check https://python-poetry.org/docs/ for more details ..'

while [[ $# -gt 0 ]]; do
  case $1 in
    -c | --clean  ) INIT=false  ; CLEAN=true  ; shift    ;;
    -i | --init   ) INIT=true   ; CLEAN=false ; shift    ;;
    -p | --print  ) echo -e "${INFO}"  ; out 0           ;;
    -h | --help   ) echo -e "${USAGE}" ; out 0           ;;
    -s | --source ) source "$(poetry env info --path)/bin/activate"; out 0 ;;
    *             ) echo "Unknown option: $1" >&2; out 1 ;;
  esac
done

function init() {
  poetry install || die 'install dependencies using Poetry'
  # shellcheck disable=SC2015
  [[ "${BASH_SOURCE[0]}" = "$0" ]] && { echo -e "${INFO}"; exit 0; } || { source "$(poetry env info --path)/bin/activate"; return $?; }
}

function clean() {
  # poetry env remove "$(poetry env list --full-path | grep Activated | awk '{print $1}')" || true;
  poetry cache clear pypi --all || die 'clear Poetry cache' true
  poetry cache clear virtualenvs --all || die 'clear Poetry virtualenvs cache' true
  poetry env remove --all || die 'remove Poetry virtual environments' true

  # shellcheck disable=SC2015
  [[ "${BASH_SOURCE[0]}" = "$0" ]] && {
    echo -e "\033[2;3;37mNote: run \033[0;32m\`deactivate\`\033[2;3;37m in your shell if a virtualenv is still active.\033[0m" >&2
  } || { deactivate 2>/dev/null || true; }
  out 0
}

"${INIT}"  && init
"${CLEAN}" && clean

# vim:tabstop=2:softtabstop=2:shiftwidth=2:expandtab:filetype=sh:
