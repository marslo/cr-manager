# Contributing to `cr-manager`

Thanks for your interest in contributing to **cr-manager**! 🙌

This document explains how to set up your environment, propose changes, and open pull requests.

---

- [What is `cr-manager`?](#what-is-cr-manager)
- [Code of Conduct](#code-of-conduct)
- [Coding Style](#coding-style)
- [Checklist](#checklist)
- [How to Contribute](#how-to-contribute)
  - [1. Fork & Clone](#1-fork--clone)
  - [2. Set Up Feature Branch](#2-set-up-feature-branch)
  - [3. Setup Your Environment](#3-setup-your-environment)
  - [4. Keep Your Branch Up to Date](#4-keep-your-branch-up-to-date)
  - [5. Open a Pull Request](#5-open-a-pull-request)

---

# What is `cr-manager`?

`cr-manager` is a command-line tool to automatically add, update, or delete multi-format copyright headers in source files.
- GitHub: <https://github.com/marslo/cr-manager>
- PyPI: <https://pypi.org/project/cr-manager/>

Contributions are welcome for:

- New features
- Bug fixes
- Better documentation
- Support for more languages / filetypes
- Performance or maintainability improvements

---

# Code of Conduct

By participating in this project, you agree to maintain a respectful and constructive environment.
Please be kind and professional in issues, discussions, and reviews.

---

# Coding Style

Please try to keep the code:

- Simple and readable
- Consistent with existing style
- Python ≥ 3.10 compatible

We use `pylint` as a linting tool. Please ensure your code passes `pylint` checks before submitting a PR. Basic guidelines:

- Use `4 spaces` for indentation
- Prefer clear naming over very short names
- Avoid unnecessary complexity

---

# Checklist

Please check all that apply:

- [ ] I have read the CONTRIBUTING.md guide.
- [ ] My changes are focused and easy to review.
- [ ] I did not bump the version in pyproject.toml.
- [ ] I updated documentation / README where necessary.
- [ ] My commit message is following [Conventional Commits specification](https://www.conventionalcommits.org/en/v1.0.0/)

---

# How to Contribute

## 1. Fork & Clone

1. Click **Fork** on GitHub to create your copy of the repo.
2. Clone your fork:

   ```bash
   $ git clone git@github.com:<your-username>/cr-manager.git
   $ cd cr-manager
   ```

3. Set the original repo as upstream:

   ```bash
   $ git remote add upstream https://github.com/marslo/cr-manager.git
   $ git fetch upstream
   ```

## 2. Set Up Feature Branch

```bash
$ git checkout -b feature/<short-description>
```

## 3. Setup Your Environment

> [!TIP]
> We use [Poetry](https://python-poetry.org/) for dependency management.

| COMMAND                                | DESCRIPTION                                                                                                                           |
|----------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| `$ poetry run python -m cli.crm <cmd>` | `$ poetry install`                                                                                                           |
| `$ python -m cli.crm <cmd>`            | `$ poetry install && source "$(poetry env info --path)/bin/activate"`                                                        |
| `$ cr-manager <cmd>`                   | **choose any :**<ul><li>`$ poetry install && source "$(poetry env info --path)/bin/activate"`</li><li>`$ pip install --user -e .`</li><li>`$ pipx install .`</li></ul> |


1. install Poetry if necessary:
   <details>
   <summary>click for details ...</summary>

   | ENVIRONMENT | COMMAND                                                                                       |
   |-------------|-----------------------------------------------------------------------------------------------|
   | linux       | `curl -sSL https://install.python-poetry.org \| python3 -`                                    |
   | windows     | `(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content \| py -` |
   | pip         | `pip install poetry`                                                                          |
   | pipx        | `pipx install poetry`                                                                         |
   | macOS       | `brew install poetry`                                                                         |

   ```bash
   $ curl -sSL https://install.python-poetry.org | python3 -

   # or
   $ pipx install poetry

   # or
   $ python -m pip install --user poetry
   ```
   </details>


2. Install dependencies:

   > it will:
   > 1. create a virtual environment in the current directory
   > 2. install the `cr-manager` package and its dependencies

   ```bash
   $ poetry install
   ```

   <details>
   <summary><b>how to clean up the poetry environment</b></summary>

   ```bash
   $ poetry env remove python
   # - or -
   $ poetry env remove --all

   # clear cache
   $ poetry cache clear pypi --all
   $ poetry cache clear virtualenvs --all
   ```
   </details>


3. Activate the virtual environment:

   ```bash
   $ source "$(poetry env info --path)/bin/activate"
   ```

   - run in the poetry environment

     ```bash
     $ poetry run python -m cli.crm --help
     ```

   - run in the virtual environment

     <details>
     <summary>about <code>${VIRTUAL_ENV}</code></summary>

     ```bash
     # to show/check the current venv:
     $ echo "${VIRTUAL_ENV}"
     ~/Library/Caches/pypoetry/virtualenvs/cr-manager-Uc1EBq6P-py3.13

     # to show the package in current venv
     $ which -a cr-manager
     ~/Library/Caches/pypoetry/virtualenvs/cr-manager-Uc1EBq6P-py3.13/bin/cr-manager
     ```
     </details>

     ```bash
     # to activate the virtual environment
     $ source "$(poetry env info --path)/bin/activate"

     # run as cli
     $ python -m cli.crm --help

     # run as package
     $ cr-manager --help
     ```

## 4. Keep Your Branch Up to Date

Before opening a PR, sync your branch with the latest main:
```bash
$ git fetch upstream
$ git checkout main
$ git merge upstream/main
$ git checkout feature/<your-branch>
$ git rebase main
```

## 5. Open a Pull Request
1. Push your branch to your fork:

   ```bash
   $ git push origin feature/<your-branch>
   ```

2. Go to the original repo on GitHub, you should see a prompt to open a PR from your branch, or using GH CLI:

   ```bash
   # with gh cli
   $ gh pr create --base main \
                  --head feature/<your-branch> \
                  --title "<title>" \
                  --body "<description>" \
   ```
