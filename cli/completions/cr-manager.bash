#!/usr/bin/env bash
# bash completion for cr-manager                           -*- shell-script -*-
#
# AUTOMATIC INSTALL (after pip install / pipx install):
#   cr-manager --install-completion
#     macOS  → $(brew --prefix)/etc/bash_completion.d/cr-manager  (Homebrew preferred)
#     Linux  → $XDG_DATA_HOME/bash-completion/completions/cr-manager
#              or ~/.bash_completion.d/cr-manager
#              or /usr/share/bash-completion/completions/cr-manager (requires root)
#              or /etc/bash_completion.d/cr-manager (requires root)
#
# PRINT TO STDOUT (for manual piping):
#   cr-manager --completion | sudo tee /etc/bash_completion.d/cr-manager
#
# MANUAL INSTALL — pick one option:
#   # option A: user-level (no root needed, bash-completion >=2)
#   mkdir -p ~/.local/share/bash-completion/completions
#   cp cr-manager.bash ~/.local/share/bash-completion/completions/cr-manager
#
#   # option B: Homebrew (macOS)
#   cp cr-manager.bash "$(brew --prefix)/etc/bash_completion.d/cr-manager"
#
#   # option C: system-wide (Linux, requires root)
#   sudo cp cr-manager.bash /etc/bash_completion.d/cr-manager
#
#   # option D: source directly in ~/.bashrc / ~/.bash_profile
#   source /path/to/completions/cr-manager.bash

# shellcheck disable=SC2207

_cr_manager() {
  local cur prev words
  _init_completion || return

  local -r filetypes='bash c c++ cpp cxx dockerfile gradle groovy h hpp hxx java jenkinsfile python sh shell'

  local -r action_flags='--add --check --delete --update'
  local -r action_shorts='-a -c -d -u'

  local -r option_flags='--copyright --filetype --recursive --debug --verbose
                         --completion --install-completion
                         --help --version'
  local -r option_shorts='-t -r -h -v'

  # detect whether an action flag is already present
  local has_action=''
  local w
  for w in "${words[@]}"; do
    case "${w}" in
      --add|-a|--check|-c|--delete|-d|--update|-u) has_action="${w}" ;;
    esac
  done

  case "${prev}" in
    # --copyright expects a file path
    --copyright) _filedir; return ;;
    # --filetype / -t expects one of the known type tokens
    --filetype|-t) COMPREPLY=( $(compgen -W "${filetypes}" -- "${cur}") ); return ;;
  esac

  # complete flags
  if [[ "${cur}" == -* ]]; then
    local candidates="${option_flags} ${option_shorts}"

    # only offer action flags when none has been chosen yet
    if [[ -z "${has_action}" ]]; then
      candidates="${action_flags} ${action_shorts} ${candidates}"
    fi

    COMPREPLY=( $(compgen -W "${candidates}" -- "${cur}") )
    return
  fi

  # default: complete files / directories
  _filedir
}

complete -F _cr_manager cr-manager

# vim:tabstop=2:softtabstop=2:shiftwidth=2:expandtab:filetype=sh:
