[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/marslo/cr-manager/main.svg)](https://results.pre-commit.ci/latest/github/marslo/cr-manager/main)

---

# cr-manager -- the Copyright Header Manager

A tool to automatically **add**, **update**, or **delete** multi-format copyright headers in source files.

---

- [Features](#features)
- [Install](#install)
  - [Install as Binary](#install-as-binary)
  - [Install as pre-commit Hook](#install-as-pre-commit-hook)
  - [Install as Local Package](#install-as-local-package)
- [Action Modes](#action-modes)
  - [Supported File Types and Formats](#supported-file-types-and-formats)
- [Running as pre-commit Hooks](#running-as-pre-commit-hooks)
  - [Install pre-commit Hooks](#install-pre-commit-hooks)
  - [Running Manually](#running-manually)
  - [Running Automatcially](#running-automatcially)
  - [Unsupported Filetype](#unsupported-filetype)
- [Running as Binary](#running-as-binary)
  - [Add New Copyright Headers](#add-new-copyright-headers)
  - [Update Existing Copyright Headers](#update-existing-copyright-headers)
  - [Delete Existing Copyright Headers](#delete-existing-copyright-headers)
  - [Debug Mode](#debug-mode)
- [Running as CLI Tool](#running-as-cli-tool)
  - [Poetry Setup](#poetry-setup)
    - [Install Poetry](#install-poetry)
    - [Init Poetry Environment](#init-poetry-environment)
    - [Run as CLI](#run-as-cli)
- [Help Message](#help-message)

---

# Features

- **Add**: Insert copyright headers for multiple file types.
- **Update**: Force update or insert headers if missing.
- **Check**: Verify the presence and correctness of headers.
- **Delete**: Remove detected copyright headers from files.
- Supports recursive directory traversal and filetype auto-detection or override.
- Supports combined author-info and copyright headers.

---

# Install

> [!TIP]
> - enable the ansicolor in Windows terminal for better output experience.
>> ```batch
>> reg add HKCU\Console /v VirtualTerminalLevel /t REG_DWORD /d 1
>> ```

## Install as Binary

### via pipx

> [!TIP|label:pipx installation]
> ```bash
> $ python3 -m pip install pipx
> $ python3 -m pipx ensurepath
> ```

```bash
$ pipx install --force "git+https://github.com/marslo/cr-manager"

# upgrade
$ pipx upgrade cr-manager

# swith python version
$ pipx reinstall cr-manager --python /path/to/python3.x
```

```bash
# -- Linux/MacOS -- #
$ VERSION="$(curl -fsSL https://api.github.com/repos/marslo/cr-manager/releases/latest | jq -r .tag_name)"
# linux
$ curl -fsSL -o cr-manager https://github.com/marslo/cr-manager/releases/download/${VERSION}/cr-manager-linux
$ chmod +x cr-manager
# macos
$ curl -fsSL -o cr-manager https://github.com/marslo/cr-manager/releases/download/${VERSION}/cr-manager-macos
$ chmod +x cr-manager

# -- Windows - running in cmd -- #
> powershell -NoProfile -Command "$v=(Invoke-WebRequest -Uri 'https://api.github.com/repos/marslo/cr-manager/releases/latest' -UseBasicParsing | ConvertFrom-Json).tag_name; Invoke-WebRequest -Uri ('https://github.com/marslo/cr-manager/releases/download/'+$v+'/cr-manager.exe') -OutFile 'cr-manager.exe'; Write-Host ('Downloaded '+$v)"
```

## Install as pre-commit Hook
```yaml
# if `COPYRIGHT` file can be found in the root directory of this repository
---
repos:
  - repo: https://github.com/marslo/cr-manager
    rev: v3.0.1
    hooks:
      - id: cr-manager
        args: ["--update"]

# or specify the copyright file to use, and only check specific files/folders
---
repos:
  - repo: https://github.com/marslo/cr-manager
    rev: v3.0.1
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
    rev: v3.0.1
    hooks:
      - id: cr-manager
        args: ["--check"]
        stages: [post-commit]
```

## Install as Local Package

```bash
# clone the repo
$ git clone git@github.com:marslo/cr-manager.git

# install via pip
# - in global --
$ python3 -m pip install --upgrade --editable .
# - in local --
$ python3 -m pip install --upgrade --user --editable .

# or install via pipx
$ pipx install --editable [--force] .

# verify
$ cr-manager --help
$ cr-manager --version
```

---

# Action Modes

> [!TIP]
> without any action mode specified, the default action is to **add** copyright headers.

| OPTION     | DESCRIPTION                                                                 |
| ---------- | --------------------------------------------------------------------------- |
|            | Add mode: Automatically adds copyright headers to files.                    |
| `--check`  | Check mode: Verifies file copyright status (match, mismatch, or not found). |
| `--delete` | Delete mode: Removes detected copyright headers from files.                 |
| `--update` | Update mode: Forces replacement of copyright or adds it if missing.         |

---

## Supported File Types and Formats

> [!TIP]
> - check [Running as CLI tool](#running-as-cli-tool) first to install necessary dependencies via `poetry install`.

|                    FILETYPE                   |           SUFFIXES          |
|:---------------------------------------------:|:---------------------------:|
| `python`, `shell`, `bash`, `sh`, `dockerfile` | `.py`, `.sh`, `.dockerfile` |

```
# without venv
$ poetry run cr-manager --filetype python

# with venv
$ cr-manager --filetype python
```

result
```
#===============================================================================
# Copyright © 2025 marslo                                                      #
# Licensed under the MIT License, Version 2.0                                  #
#===============================================================================
```

![Python](./screenshots/ft-py.png)

---

|                  FILETYPE                 |      SUFFIXES      |
|:-----------------------------------------:|:------------------:|
| `jenkinsfile`, `groovy`, `gradle`, `java` | `.groovy`, `.java` |

```
# without venv
$ poetry run cr-manager --filetype java

# with venv
$ cr-manager --filetype groovy
```

result
```
/**
 *******************************************************************************
 * Copyright © 2025 marslo                                                     *
 * Licensed under the MIT License, Version 2.0                                 *
 *******************************************************************************
**/
```

![java-groovy](./screenshots/ft-java-groovy.png)

---

|                   FILETYPE                  |                  SUFFIXES                  |
|:-------------------------------------------:|:------------------------------------------:|
| `c`, `cpp`, `c++`, `cxx`, `h`, `hpp`, `hxx` | `.c`, `.cpp`, `.cxx`, `.h`, `.hpp`, `.hxx` |

```
# without venv
$ poetry run cr-manager --filetype c

# with venv
$ cr-manager --filetype cpp
```

result
```
/**
 * Copyright © 2025 marslo
 * Licensed under the MIT License, Version 2.0
 */
```

![c/cpp](./screenshots/ft-cpp.png)

---

# Running as pre-commit Hooks

## Install pre-commit Hooks
```bash
$ pre-commit install --install-hooks
```

## Running Manually

> [!TIP]
> without hook, you can run the cr-manager manually for all files in the repository.

```bash
$ pre-commit run cr-manager --all-files

# or particular file
$ pre-commit run cr-manager --files path/to/file
```

![run cr-manager --all-files](./screenshots/cr-manager-pre-commit.png)

## Running Automatcially
```bash
$ git commit -m "your commit message"
```

## Unsupported Filetype
```bash
$ python -m cli.crm [--update] --filetype python /path/to/file.txt
```

![un-supported filetype](./screenshots/handle-unsupported-filetype.png)

---

# Running as Binary

## Add New Copyright Headers
```bash
# single file
$ cr-manager /path/to/file

# files recursively in directories
$ cr-manager --recursive /path/to/directory

# add to non-supported suffixes with supplied filetype
# -- e.e. add to .txt files as python files --
$ cr-manager --filetype python /path/to/file.txt
```

## Update Existing Copyright Headers

> [!TIP]
> `--filetype <TYPE>` can be used to force a specific filetype for the update action, overriding auto-detection.

```bash
# single file
$ cr-manager --update /path/to/file

# files recursively in directories
$ cr-manager --update --recursive /path/to/directory
```

## Delete Existing Copyright Headers

> [!TIP]
> `--filetype <TYPE>` can be used to force a specific filetype for the update action, overriding auto-detection.

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

$ *update* without modifying files
$ cr-manager --update --debug /path/to/file

# *delete* without modifying files
$ cr-manager --delete --debug /path/to/file
```

# Running as CLI Tool

| COMMAND                                | DESCRIPTION                                                                                                                          |
|----------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------|
| `$ poetry run python -m cli.crm <cmd>` | requires `$ poetry install`                                                                                                          |
| `$ python -m cli.crm <cmd>`            | requires `$ poetry install && source "$(poetry env info --path)/bin/activate"`                                                       |
| `$ cr-manager <cmd>`                   | requires `$ poetry install && source "$(poetry env info --path)/bin/activate"`<br>or `pip install --user -e .`<br>or`pipx install .` |

## Poetry Setup

### Install Poetry

| ENVIRONMENT | COMMAND                                                                                       |
|-------------|-----------------------------------------------------------------------------------------------|
| linux       | `curl -sSL https://install.python-poetry.org \| python3 -`                                    |
| windows     | `(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content \| py -` |
| pip         | `pip install poetry`                                                                          |
| pipx        | `pipx install poetry`                                                                         |
| macOS       | `brew install poetry`                                                                         |

### Init Poetry Environment

> [!NOTE]
> it will:
> 1. create a virtual environment in the current directory
> 2. install the `cr-manager` package and its dependencies
> 3. to enable the pylint in pyproject.toml:
>> ```bash
>> $ poetry add --dev pylint
>> ```

```bash
$ poetry install
```

- clean up the poetry environment
  ```bash
  $ poetry env remove python
  # - or -
  $ poetry env remove --all

  # clear cache
  $ poetry cache clear pypi --all
  $ poetry cache clear virtualenvs --all
  ```

### Run as CLI

- run in the poetry environment

  ```bash
  $ poetry run python -m cli.crm --help
  ```

- run in the virtual environment

  > to show/check the current venv:
  >> ```bash
  >> $ echo "${VIRTUAL_ENV}"
  >> /Users/marslo/Library/Caches/pypoetry/virtualenvs/cr-manager-Uc1EBq6P-py3.13
  >> ```
  >
  > to show the package in current venv
  >> ```bash
  >> $ which -a cr-manager
  >> ~/Library/Caches/pypoetry/virtualenvs/cr-manager-Uc1EBq6P-py3.13/bin/cr-manager
  >> ```

  ```bash
  # to activate the virtual environment
  $ source "$(poetry env info --path)/bin/activate"

  # run as cli
  $ python -m cli.crm --help

  # run as package
  $ cr-manager --help
  ```

# Help Message

```bash
$ poetry run python3 -m cli.crm --help
USAGE
  python3 -m cli.crm [--check | --delete | --update] [--copyright FILE] [--filetype TYPE]
                     [-r|--recursive] [--debug] [--verbose] [-h|--help] [-v|--version]
                     FILES ...

A tool to automatically add, update, or delete multi-format copyright headers.

POSITIONAL ARGUMENTS:
  FILES ...                 List of target files or directories to process.

ACTION MODES (default is add):
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
  -h, --help                Show this help message and exit.
  -v, --version             Show program's version number and exit.
```
