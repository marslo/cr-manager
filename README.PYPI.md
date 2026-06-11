[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/marslo/cr-manager/main.svg)](https://results.pre-commit.ci/latest/github/marslo/cr-manager/main) [![publish to PyPI](https://github.com/marslo/cr-manager/actions/workflows/publish.yml/badge.svg)](https://github.com/marslo/cr-manager/actions/workflows/publish.yml) [![semantic-release](https://github.com/marslo/cr-manager/actions/workflows/semantic-release.yml/badge.svg?branch=main)](https://github.com/marslo/cr-manager/actions/workflows/semantic-release.yml)

---

# cr-manager -- the Copyright Header Manager

A tool to automatically **add**, **update**, or **delete** multi-format copyright headers in source files.

---

[![GitHub Release](https://img.shields.io/github/v/release/marslo/cr-manager?logo=github)](https://github.com/marslo/cr-manager/releases/latest)
[![GitHub Downloads](https://img.shields.io/github/downloads/marslo/cr-manager/total?logo=github)](https://github.com/marslo/cr-manager/releases/latest)
![Python](https://img.shields.io/badge/language-python-c7f484?logo=python&logoColor=white)
[![PyPI version](https://img.shields.io/pypi/v/cr-manager?logo=pypi)](https://pypi.org/project/cr-manager/)
[![Install with pipx](https://img.shields.io/badge/install%20with-pipx-4B8BBE?logo=python&logoColor=white)](https://pypi.org/project/cr-manager/)
[![Linux](https://img.shields.io/badge/Linux-FCC624?logo=linux&logoColor=black)](https://github.com/marslo/cr-manager/releases/latest)
[![macOS](https://img.shields.io/badge/macOS-000000?logo=apple&logoColor=white)](https://github.com/marslo/cr-manager/releases/latest)
[![Windows](https://img.shields.io/badge/Windows-0078D6?logo=data%3Aimage%2Fsvg%2Bxml%3Butf8%2C%253Csvg%2520xmlns%253D%2522http%253A%252F%252Fwww.w3.org%252F2000%252Fsvg%2522%2520viewBox%253D%25220%25200%252024%252024%2522%2520fill%253D%2522%2523ffffff%2522%253E%253Cpath%2520d%253D%2522M0%25200h11.377v11.372H0Zm12.623%25200H24v11.372H12.623ZM0%252012.628h11.377V24H0Zm12.623%25200H24V24H12.623Z%2522%252F%253E%253C%252Fsvg%253E)](https://github.com/marslo/cr-manager/releases/latest)
![License](https://github.com/marslo/cr-manager/raw/main/assets/license-marvell.svg)

---

- [Features](#features)
- [How to Contribute](#how-to-contribute)
- [Action Modes](#action-modes)
  - [Add New Copyright Headers](#add-new-copyright-headers)
  - [Update Existing Copyright Headers](#update-existing-copyright-headers)
  - [Delete Existing Copyright Headers](#delete-existing-copyright-headers)
  - [Debug Mode](#debug-mode)
  - [Supported File Types and Formats](#supported-file-types-and-formats)
  - [pre-commit hook](#pre-commit-hook)
- [Install](#install)
  - [Binary](#binary)
  - [bash completion](#bash-completion)
- [Help Message](#help-message)

---

# Features

- **Add**: Insert copyright headers for multiple file types.
- **Update**: Force update or insert headers if missing.
- **Check**: Verify the presence and correctness of headers.
- **Delete**: Remove detected copyright headers from files.
- Supports recursive directory traversal and filetype auto-detection or override.
- Supports combined author-info and copyright headers.

<table><thead>
  <tr>
    <th align="center"><b>FORMAT</b></th>
    <th align="center"><b>FILETYPE</b></th>
    <th align="center"><b>SUFFIXES</b></th>
  </tr></thead>
<tbody>
  <tr>
      <td valign="middle"><pre><code># ========================== #
# Copyright © 2026 Marslo    #
# Licensed under MIT         #
# ========================== #</code></pre></td>
      <td valign="middle"><code>python</code><br><code>shell</code><br><code>bash</code><br><code>sh</code><br><code>dockerfile</code></td>
      <td valign="middle"><code>.py</code><br><code>.sh</code><br><code>.dockerfile</code></td>
  </tr>
  <tr>
      <td valign="middle"><pre><code>/**
 *****************************
 * Copyright © 2026 Marslo   *
 * Licensed under MIT        *
 *****************************
**/</code></pre></td>
      <td valign="middle"><code>jenkinsfile</code><br><code>groovy</code><br><code>gradle</code><br><code>java</code></td>
      <td valign="middle"><code>.groovy</code><br><code>.java</code></td>
  </tr>
  <tr>
      <td valign="middle"><pre><code>/**
 * Copyright © 2026 Marslo
 * Licensed under MIT
 */</code></pre></td>
      <td valign="middle"><code>c</code><br><code>cpp</code><br><code>c++</code><br><code>cxx</code><br><code>h</code><br><code>hpp</code><br><code>hxx</code></td>
      <td valign="middle"><code>.c</code><br><code>.cpp</code><br><code>.cxx</code><br><code>.hpp</code><br><code>.hxx</code></td>
  </tr>
</tbody></table>

---

# [How to Contribute](https://github.com/marslo/cr-manager/blob/main/CONTRIBUTING.md)

---

# Action Modes

> without any action mode specified, the default action is to **add** copyright headers.

| OPTION     | DESCRIPTION                                                                 |
| ---------- | --------------------------------------------------------------------------- |
|            | Add mode: Automatically adds copyright headers to files (default).          |
| `--add`    | Add mode: Automatically adds copyright headers to files (default).          |
| `--check`  | Check mode: Verifies file copyright status (match, mismatch, or not found). |
| `--delete` | Delete mode: Removes detected copyright headers from files.                 |
| `--update` | Update mode: Forces replacement of copyright or adds it if missing.         |


## Add New Copyright Headers
```bash
# single file
$ cr-manager /path/to/file
# or
$ cr-manager --add /path/to/file

# files recursively in directories
$ cr-manager --recursive /path/to/directory
# or
$ cr-manager --add --recursive /path/to/directory

# add to non-supported suffixes with supplied filetype
# -- e.g. add to .txt files as python files --
$ cr-manager --filetype python /path/to/file.txt
# or
$ cr-manager --add --filetype python /path/to/file.txt
```

## Update Existing Copyright Headers

> `--filetype <TYPE>` can be used to force a specific filetype for the update action, overriding auto-detection.

```bash
# single file
$ cr-manager --update /path/to/file

# files recursively in directories
$ cr-manager --update --recursive /path/to/directory
```

## Delete Existing Copyright Headers

> `--filetype <TYPE>` can be used to force a specific filetype for the delete action, overriding auto-detection.

```bash
# single file
$ cr-manager --delete /path/to/file

# files recursively in directories
$ cr-manger --delete --recursive /path/to/directory
```

## Debug Mode

```bash
# *add* without modifying files
$ cr-manager --debug /path/to/file
# or
$ cr-manager --add --debug /path/to/file

# *update* without modifying files
$ cr-manager --update --debug /path/to/file

# *delete* without modifying files
$ cr-manager --delete --debug /path/to/file
```

## Supported File Types and Formats

> - check [Running as CLI tool](https://github.com/marslo/cr-manager?tab=readme-ov-file#running-as-cli-tool)

|                    FILETYPE                   |           SUFFIXES          |
|:---------------------------------------------:|:---------------------------:|
| `python`, `shell`, `bash`, `sh`, `dockerfile` | `.py`, `.sh`, `.dockerfile` |

```bash
# ============================================================================ #
# Copyright © 2026 marslo                                                      #
# Licensed under the MIT License, Version 2.0                                  #
# ============================================================================ #
```

![Python](https://github.com/marslo/cr-manager/raw/main/assets/ft-py.png)

---

|                  FILETYPE                 |      SUFFIXES      |
|:-----------------------------------------:|:------------------:|
| `jenkinsfile`, `groovy`, `gradle`, `java` | `.groovy`, `.java` |

```groovy
/**
 *******************************************************************************
 * Copyright © 2026 marslo                                                     *
 * Licensed under the MIT License, Version 2.0                                 *
 *******************************************************************************
**/
```

![java-groovy](https://github.com/marslo/cr-manager/raw/main/assets/ft-java-groovy.png)

---

|                   FILETYPE                  |                  SUFFIXES                  |
|:-------------------------------------------:|:------------------------------------------:|
| `c`, `cpp`, `c++`, `cxx`, `h`, `hpp`, `hxx` | `.c`, `.cpp`, `.cxx`, `.h`, `.hpp`, `.hxx` |

```c
/**
 * Copyright © 2026 marslo
 * Licensed under the MIT License, Version 2.0
 */
```

![c/cpp](https://github.com/marslo/cr-manager/raw/main/assets/ft-cpp.png)

---

## pre-commit hook

![cr-manager pre-commit hook](https://github.com/marslo/cr-manager/raw/main/assets/git-pre-commit-hook.png)

```yaml
# if `COPYRIGHT` file can be found in the root directory of this repository
---
repos:
  - repo: https://github.com/marslo/cr-manager
    rev: v4.0.0
    hooks:
      - id: cr-manager
        args: ["--update"]
```

```yaml
# specify the path to the COPYRIGHT file
---
repos:
  - repo: https://github.com/marslo/cr-manager
    rev: v4.0.0
    hooks:
      - id: cr-manager
        args: ["--update", "--copyright", "/path/to/COPYRIGHT"]
        files: ^(jenkinsfile/|.*\.(groovy|py|sh)$)
```

```yaml
# only check the copyright headers without modifying files after commit
---
repos:
  - repo: https://github.com/marslo/cr-manager
    rev: v4.0.0
    hooks:
      - id: cr-manager
        args: ["--check"]
        stages: [post-commit]
```

---

# Install
## Binary

> - pipx installation ( [how to install pipx](https://pipx.pypa.io/stable/how-to/install-pipx/) )
>   ```bash
>   $ python3 -m pip install pipx
>   $ python3 -m pipx ensurepath
>   ```
> - enable the ansicolor in Windows terminal for better output experience.
>   ```batch
>   > reg add HKCU\Console /v VirtualTerminalLevel /t REG_DWORD /d 1
>   ```

```bash
# via pipx
$ pipx install --force "git+https://github.com/marslo/cr-manager"
# via pip
$ python3 -m pip install cr-manager

# with binary
$ VERSION="$(curl -fsSL https://api.github.com/repos/marslo/cr-manager/releases/latest | jq -r .tag_name)"
# -- linux --
$ curl -fsSL -o cr-manager https://github.com/marslo/cr-manager/releases/download/${VERSION}/cr-manager-linux
# macos
$ curl -fsSL -o cr-manager https://github.com/marslo/cr-manager/releases/download/${VERSION}/cr-manager-macos
# Windows - running in cmd
> powershell -NoProfile -Command "$v=(Invoke-WebRequest -Uri 'https://api.github.com/repos/marslo/cr-manager/releases/latest' -UseBasicParsing | ConvertFrom-Json).tag_name; Invoke-WebRequest -Uri ('https://github.com/marslo/cr-manager/releases/download/'+$v+'/cr-manager.exe') -OutFile 'cr-manager.exe'; Write-Host ('Downloaded '+$v)"
```

## bash completion

> automatically detect the OS and install bash completion to the appropriate directory:
> - macos: `$(brew --prefix)/etc/bash_completion.d` → `$XDG_DATA_HOME/.local/share` →  `~/.bash_completion.d`
> - linux: `$XDG_DATA_HOME/.local/share` → `~/.bash_completion.d` → `/usr/share/bash-completion/completions` → `/etc/bash_completion.d`

```bash
# macos
$ cr-manager --install-completion
# or install manually
$ cr-manager --completion | tee "$(brew --prefix)/etc/bash_completion.d/cr-manager"
```

```bash
# linux user folder
$ cr-manager --install-completion
# or install manually
$ cr-manager --completion | tee ~/.bash_completion.d/cr-manager

# linux system folder (requires sudo)
$ sudo cr-manager --install-completion
# or install manually
$ cr-manager --completion | sudo tee /etc/bash_completion.d/cr-manager
```

```bash
# uninstall
test -f ~/.bash_completion.d/cr-manager && rm -rf ~/.bash_completion.d/cr-manager
test -f /etc/bash_completion.d/cr-manager && sudo rm -rf /etc/bash_completion.d/cr-manager
[[ 'Darwin' = "$(uname -s)" ]] && test -f "$(brew --prefix)/etc/bash_completion.d/cr-manager" && rm -rf "$(brew --prefix)/etc/bash_completion.d/cr-manager"
```

# Help Message

```bash
$ cr-manager --help
USAGE:
  cr-manager [--add | --check | --delete | --update] [--copyright FILE] [--filetype TYPE] [--recursive]
             [--debug] [--verbose] [--completion] [--install-completion] [--help] [--version]
             FILES ...

A tool to automatically add, update, or delete multi-format copyright headers.

POSITIONAL ARGUMENTS:
  FILES ...                 List of target files or directories to process.

ACTION MODES:
  -a, --add                 Add mode: Adds copyright header to files that are missing it (default).
  -c, --check               Check mode: Verifies file copyright status (match, mismatch, or not found).
  -d, --delete              Delete mode: Removes detected copyright headers from files.
  -u, --update              Update mode: Forces replacement of copyright or adds it if missing.

OPTIONS:
  --copyright FILE          Specify the copyright template file path (default: COPYRIGHT).
  -t, --filetype TYPE       Force override a filetype instead of auto-detection.
                            If provided, displays a formatted preview for that type. Supported: bash, c,
                            c++, cpp, cxx, dockerfile, gradle, groovy, h, hpp, hxx, java, jenkinsfile,
                            python, sh, shell
  -r, --recursive           If FILES includes directories, process their contents recursively.
  --debug                   Debug mode: Preview the result of an action without modifying files.
  --verbose                 Show a detailed processing summary.
  --completion              Print the bash completion script to stdout.
  --install-completion      Install bash completion to the OS-appropriate directory (auto-detected, no
                            root needed by default).
  -h, --help                Show this help message and exit.
  -v, --version             Show program's version number and exit.
```
