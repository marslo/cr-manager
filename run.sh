#!/usr/bin/env bash
# shellcheck source=/dev/null
#=============================================================================
#     FileName : run.sh
#       Author : marslo
#      Created : 2026-04-16 19:20:20
#   LastChange : 2026-05-06 19:12:35
#        USAGE : - init the environment  : $ source run.sh [--init] [--upgrade]
#                - clean the environment : $ source run.sh --clean
#
#                - setup poetry environment only: $ bash run.sh [--init]
#                - source poetry environment without installing dependencies: $ source run.sh --source [--upgrade]
#=============================================================================

# check if the script is being sourced or executed
#   - source run.sh : BASH_SOURCE[0] != $0, IS_EXEC=false
#   - bash run.sh   : BASH_SOURCE[0] == $0, IS_EXEC=true
# shellcheck disable=SC2015
[[ "${BASH_SOURCE[0]}" = "$0" ]] && declare IS_EXEC=true || declare IS_EXEC=false
declare INIT=true
declare CLEAN=false
declare SOURCE=false
declare UPGRADE=false
declare USAGE="
To setup/clean the Python virtual environment using Poetry

USAGE
  \$ source run.sh
  \033[0;2;3;37m# or\033[0m
  \$ bash run.sh [OPTIONS]

OPTIONS
  -i, --init       initialize the Python virtual environment using Poetry. ( default behavior )
  -u, --upgrade    upgrade pip and pynvim in the Poetry virtual environment ( only valid when used with '-i/--init' )
  -c, --clean      clean up the Poetry cache and remove all virtual environments
  -s, --source     source the Poetry virtual environment ( without installing dependencies )
  -p, --print      print the command information and exit
  -h, --help       show this help message and exit
"

declare INFO="
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
  local _extra=''
  [[ 'true' = "${2:-}" ]] && _extra=' Please check your Poetry installation ...'
  echo "Failed to ${info}.${_extra}" >&2
  out 1
}

function out() {
  local code="${1:-0}"
  "${IS_EXEC}" && exit "${code}" || return "${code}"
}

function spoetry() {
  source "$(poetry env info --path)/bin/activate" || { die 'source Poetry virtual environment'; return 1; }
  if "${UPGRADE}"; then
    python3 -m pip install --upgrade pip && python3 -m pip install --upgrade pynvim ||
    { echo "Failed to upgrade pip and pynvim in the Poetry virtual environment." >&2; return 0; }
  fi
}

type -P poetry >/dev/null 2>&1 || {
  echo -e 'Failed to find Poetry in PATH, install Poetry first. Check https://python-poetry.org/docs/ for more details ..' >&2;
  "${IS_EXEC}" && exit 0 || return 0 ;
}

while [[ $# -gt 0 ]]; do
  case $1 in
    -c | --clean   ) CLEAN=true ; shift ;;
    -i | --init    ) INIT=true    ; shift ;;
    -u | --upgrade ) UPGRADE=true ; shift ;;
    -s | --source  ) "${IS_EXEC}" && { echo "The option '-s/--source' is only valid when sourcing this script. Please use 'source run.sh -s' instead." >&2; exit 1; }
                     SOURCE=true  ; shift ;;
    -p | --print   ) echo -e "${INFO}"  ; "${IS_EXEC}" && exit 0 || return 0 ;;
    -h | --help    ) echo -e "${USAGE}" ; "${IS_EXEC}" && exit 0 || return 0 ;;
    *              ) echo "Unknown option: $1" >&2 ; out 1 ;;
  esac
done

function init() {
  poetry install || die 'install dependencies using Poetry'
  # shellcheck disable=SC2015
  "${IS_EXEC}" && { echo -e "${INFO}"; exit 0; } || { spoetry; return $?; }
}

function clean() {
  # poetry env remove "$(poetry env list --full-path | grep Activated | awk '{print $1}')" || true;
  poetry cache clear pypi --all || die 'clear Poetry cache' true
  poetry cache clear virtualenvs --all || die 'clear Poetry virtualenvs cache' true
  poetry env remove --all || die 'remove Poetry virtual environments' true

  # shellcheck disable=SC2015
  "${IS_EXEC}" && {
    echo -e "\033[2;3;37mNote: run \033[0;32m\`deactivate\`\033[2;3;37m in your shell if a virtualenv is still active.\033[0m" >&2
  } || { deactivate 2>/dev/null || true; }
  out 0
}

"${CLEAN}"  && { clean; "${IS_EXEC}" && exit 0 || return 0; }
"${SOURCE}" && { spoetry; _rc=$?; [[ 0 -ne "${_rc}" ]] && echo "Failed to source Poetry virtual environment." >&2; return "${_rc}"; }
"${INIT}"   && init

# vim:tabstop=2:softtabstop=2:shiftwidth=2:expandtab:filetype=sh:
