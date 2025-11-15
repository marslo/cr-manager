[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/marslo/cr-manager/main.svg)](https://results.pre-commit.ci/latest/github/marslo/cr-manager/main)

---

# cr-manager -- the Copyright Header Manager

A tool to automatically **add**, **update**, or **delete** multi-format copyright headers in source files.

---

# Features

- **Add**: Insert copyright headers for multiple file types.
- **Update**: Force update or insert headers if missing.
- **Check**: Verify the presence and correctness of headers.
- **Delete**: Remove detected copyright headers from files.
- Supports recursive directory traversal and filetype auto-detection or override.
- Supports combined author-info and copyright headers.

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


## Supported File Types and Formats

> [!TIP]
> - check [Running as CLI tool](https://github.com/marslo/cr-manager?tab=readme-ov-file#running-as-cli-tool)

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

![Python](https://github.com/marslo/cr-manager/raw/main/screenshots/ft-py.png)

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

![java-groovy](https://github.com/marslo/cr-manager/raw/main/screenshots/ft-java-groovy.png)

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

![c/cpp](https://github.com/marslo/cr-manager/raw/main/screenshots/ft-cpp.png)

---

# Install

> [!TIP]
> - enable the ansicolor in Windows terminal for better output experience.
>> ```batch
>> reg add HKCU\Console /v VirtualTerminalLevel /t REG_DWORD /d 1
>> ```

## Binary
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

## pre-commit hook

```yaml
---
repos:
  - repo: https://github.com/marslo/cr-manager
    rev: v3.0.3
    hooks:
      - id: cr-manager
        args: ["--update", "--copyright", "/path/to/COPYRIGHT"]
        files: ^(jenkinsfile/|.*\.(groovy|py|sh)$)
```

only check the copyright headers without modifying files after commit
```yaml
---
repos:
  - repo: https://github.com/marslo/cr-manager
    rev: v3.0.3
    hooks:
      - id: cr-manager
        args: ["--check"]
        stages: [post-commit]
```
