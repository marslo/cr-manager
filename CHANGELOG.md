## [4.1.1](https://github.com/marslo/cr-manager/compare/v4.1.0...v4.1.1) (2026-11-25)

### CI/CD

* **release**, **workflow**: support semantic-release 26 ([5cd5def](https://github.com/marslo/cr-manager/commit/5cd5def9b7d60fe0de02286176e65d99b05c75c0))
  - add a function `template` for `conventional-changelog-writer` 9 that renders the same markdown as the Handlebars templates
  - keep the Handlebars strings for writer 8 ( semantic-release <= 25 )
  - fix `headerPartial is not a function` on semantic-release 26
  - run the release workflow on node 26 so npm no longer falls back to semantic-release 25
  - pin plugin majors and drop the unused standalone `@semantic-release/release-notes-generator`

## [4.1.0](https://github.com/marslo/cr-manager/compare/v4.0.2...v4.1.0) (2026-11-25)

### Features

* **formats**: add css/js and html copyright header formats ([08136d9](https://github.com/marslo/cr-manager/commit/08136d9d111990af9618c821704dacfbe9d68ffb))
  - css_js_comment: `/*! ... */` bordered block for .css / .js / .mjs / .cjs
  - html_comment: `<!-- ... -->` bordered block for .html / .htm / .xhtml, inserted below a leading `<?xml ...?>` / `<!DOCTYPE ...>`
  - formats.toml: optional `insert_after` regex list for leading lines kept above the header ( default: shebang, then encoding )
  - strip ljust padding on bordered content lines without a right delimiter
  - pre-commit hook: match css / js / html, exclude *.min.css / *.min.js
  - docs, bash completion and samples
* **formats**: add rust copyright header format ([3703b4a](https://github.com/marslo/cr-manager/commit/3703b4abf45cdee160a9656366ac74a55eaefa9d))
  - rust_comment: `// ===` bordered line comments for .rs; plain `//` only, as `///` `//!` `/**` `/*!` are rustdoc comments
  - keep a cargo-script shebang on top; an inner attribute `#![...]` is not skipped
  - fix(manager): use the adjacent border pair that encloses the copyright, so an existing `# ===` / `// ===` banner in the same comment block is no longer replaced or deleted
  - docs, bash completion and sample
* **formats**: detect Dockerfile / Containerfile by file name ([a59263c](https://github.com/marslo/cr-manager/commit/a59263c1b1706a83445d87f1fbee3c8fe37d2fce))
  - formats.toml: optional `filenames` regex list, checked before `suffixes`
  - hash_comment: match Dockerfile / Containerfile as a dot-separated name part, case-insensitive ( Dockerfile, Dockerfile.dev, app.Dockerfile, build.dockerfile ); add containerfile filetype and .containerfile suffix
  - pre-commit: add `cr-manager-dockerfile` hook ( case-insensitive `files`, `--filetype dockerfile` ); drop Dockerfile from the main hook
  - docs and bash completion

### Documentation

* **readme**: update readme for 3 new filetype screenshots ([ad393a5](https://github.com/marslo/cr-manager/commit/ad393a5d28ed0e31538cfdd0bee8c79c3208a4a8))

### CI/CD

* **release**: use function templates for changelog notes ([10ff986](https://github.com/marslo/cr-manager/commit/10ff986ebbd6f7ae4dcf8270612ea00dc6c9d825))
  - replace Handlebars `mainTemplate` / `headerPartial` / `commitPartial` strings with function versions
  - add `template`, `preamblePartial` and `footerPartial` for `conventional-changelog-writer` 9
  - fix `headerPartial is not a function` on `semantic-release` 26
* **workflow**: add branch tip revision to sync summary (#43)

## [4.0.2](https://github.com/marslo/cr-manager/compare/v4.0.1...v4.0.2) (2026-07-29)

### Others

* chore(sync,pyproject): rebrand on forks and set PyPI license to Marvell Semiconductor

## [4.0.1](https://github.com/marslo/cr-manager/compare/v4.0.0...v4.0.1) (2026-07-29)

### Bug Fixes

* fix(pre-commit): run cr-manager serially in pre-commit and documents update (#39)

### Documentation

* docs: update readme
* docs(readme): add local repo + pypi solution for pre-commit hook install

### CI/CD

* ci(workflow): restrict release workflows to the source repository and add a fork sync workflow (#40)

### build

* build(release): migrate semantic-release config from JSON to JS with custom Handlebars templates (#41)

## [4.0.0](https://github.com/marslo/cr-manager/compare/v3.3.4...v4.0.0) (2026-05-26)

### ⚠ BREAKING CHANGES

* update the license type

Signed-off-by: marslo <marslo.jiao@gmail.com>

### Documentation

* update the license type ([376ff05](https://github.com/marslo/cr-manager/commit/376ff05b12713318bd9772d082379e9332a80e9f))

## [3.3.4](https://github.com/marslo/cr-manager/compare/v3.3.3...v3.3.4) (2026-05-20)

### Documentation

* add `Format Configuration` in readme; update screenshots ([696d8bd](https://github.com/marslo/cr-manager/commit/696d8bdd899915ea0cefe9f7e50a43f6a28b307d))

## [3.3.3](https://github.com/marslo/cr-manager/compare/v3.3.2...v3.3.3) (2026-05-20)

### Bug Fixes

* **check:** fix false mismatch for bordered copyright formats and skip redundant updates ([ed20238](https://github.com/marslo/cr-manager/commit/ed2023818accc0c5992fe5906ec9fe6ad48e5390)), closes [#36](https://github.com/marslo/cr-manager/issues/36)

### CI/CD

* disable precommit automatic upgrade via PR ([f5eb3cc](https://github.com/marslo/cr-manager/commit/f5eb3ccbf22f53feb3048a849ca986e5e2a34d93))
* **workflow:** using pre-commit workflow instead of pre-commit application - to disable PR auto creation ([df5eaa9](https://github.com/marslo/cr-manager/commit/df5eaa9c8362717b2528fb6134031c61284021c9))

## [3.3.2](https://github.com/marslo/cr-manager/compare/v3.3.1...v3.3.2) (2026-05-07)

### Code Refactoring

* isolate source code and configuration, and store configuration files separately in a toml file ([#34](https://github.com/marslo/cr-manager/issues/34)) ([824677b](https://github.com/marslo/cr-manager/commit/824677b502c2d263b0a1cac34a5eb4cc871283c3))

## [3.3.1](https://github.com/marslo/cr-manager/compare/v3.3.0...v3.3.1) (2026-05-07)


### Code Refactoring

* **output,format:** refactor output format to fixed-width format ( similar to output of pre-commit hook ) ([#33](https://github.com/marslo/cr-manager/issues/33)) ([5d27c73](https://github.com/marslo/cr-manager/commit/5d27c737884ebf980c8cda18a162e06c95773404))

# [3.3.0](https://github.com/marslo/cr-manager/compare/v3.2.1...v3.3.0) (2026-05-07)


### Code Refactoring

* **manager.py:** refactor the `FILE_TYPE_MAP` map in manager module, for unified management of the left and right sides of the box ( when `simple_format=False` ) ([#32](https://github.com/marslo/cr-manager/issues/32)) ([d61ed98](https://github.com/marslo/cr-manager/commit/d61ed98d4a0402f5ab309fca9cab608a12430165))
  * `comment`       : core line marker for detection & content stripping (e.g. `#`, `*`)
  * `content_left`  : left delimiter of each content line
  * `content_right` : right delimiter of each content line
  * `box_left`      : left side of border line (`simple_format=False` only)
  * `box_right`     : right side of border line (`simple_format=False` only)
  * `box_char`      : repeated character forming the border run

## [3.2.1](https://github.com/marslo/cr-manager/compare/v3.2.0...v3.2.1) (2026-05-07)


### Bug Fixes

* resolve the combined header issue for shell script ([#31](https://github.com/marslo/cr-manager/issues/31)) ([85f9740](https://github.com/marslo/cr-manager/commit/85f974090bf1f63ca49055b9051a12aae473b427)), closes [#30](https://github.com/marslo/cr-manager/issues/30)
* **run.sh:** fix the `run.sh` to handle if the script is sourced or executed, and handle exit/return properly. ([#29](https://github.com/marslo/cr-manager/issues/29)) ([73c58fc](https://github.com/marslo/cr-manager/commit/73c58fce4b168cb3a2244fc14dcb939100376d2d))


### CI/CD

* **workflow:** prompt the runner to `@v6` to prevent the warning `Node.js 20 actions are deprecated` ([#28](https://github.com/marslo/cr-manager/issues/28)) ([ce287dc](https://github.com/marslo/cr-manager/commit/ce287dc4a0402f5ab309fca9cab608a12430165))

# [3.2.0](https://github.com/marslo/cr-manager/compare/v3.1.0...v3.2.0) (2026-05-07)


### Features

* **bash_completion:** add bash completion for cr-manager ([#27](https://github.com/marslo/cr-manager/issues/27)) ([cbeaa18](https://github.com/marslo/cr-manager/commit/cbeaa180a31d6a6d56a5e364411e4f97e431fb0b))


### Documentation

* **readme:** update README file, and upgraded the typo pre-commit hook version to `v1.43.3` ([cbe3e18](https://github.com/marslo/cr-manager/commit/cbe3e18f))
* add badges in readme ([0f9f970](https://github.com/marslo/cr-manager/commit/0f9f9703))


### CI/CD

* pre-commit update ([872930b](https://github.com/marslo/cr-manager/commit/872930be))

# [3.1.0](https://github.com/marslo/cr-manager/compare/v3.0.5...v3.1.0) (2026-02-07)


### Features

* enhance hash-style border and fix delete artifacts ([f39003f](https://github.com/marslo/cr-manager/commit/f39003f6c9e3d46461fcb1ece3dd1b7dac478df4))

## [3.0.5](https://github.com/marslo/cr-manager/compare/v3.0.4...v3.0.5) (2025-11-15)

### Docs

* update readme for pypi

## [3.0.4](https://github.com/marslo/cr-manager/compare/v3.0.3...v3.0.4) (2025-11-15)

### Docs

* create readme for PyPI

### CI

* add workflow for publish to pypi repository

## [3.0.3](https://github.com/marslo/cr-manager/compare/v3.0.2...v3.0.3) (2025-11-15)

### publish to official pypi repository [cr-manager](https://pypi.org/project/cr-manager)
### CI

* add workflow for semantic-release

## [3.0.2](https://github.com/marslo/cr-manager/compare/v3.0.1...v3.0.2) (2025-11-14)


### Bug Fixes

* **compatibility:** for lower python version compatibility, and fix/bypass the pylint warning ([#15](https://github.com/marslo/cr-manager/issues/15)) ([a1fa458](https://github.com/marslo/cr-manager/commit/a1fa45859dce935f2fa145e4b5230d485e05b2b7)), closes [#14](https://github.com/marslo/cr-manager/issues/14)

## [3.0.1](https://github.com/marslo/cr-manager/compare/v3.0.0...v3.0.1) (2025-11-12)

# [3.0.0](https://github.com/marslo/cr-manager/compare/v2.0.8...v3.0.0) (2025-11-11)


* feat(python3.14,color)!: improve regex handling in helper.py for better terminal formatting ([24ff244](https://github.com/marslo/cr-manager/commit/24ff24487c9eed6cdd2250cfbf46208bf8d3df1d))


### BREAKING CHANGES

* update python version requirement to >=3.10; and support python3.14

Signed-off-by: marslo <marslo.jiao@gmail.com>

## [2.0.8](https://github.com/marslo/cr-manager/compare/v2.0.7...v2.0.8) (2025-08-27)


### Bug Fixes

* **python:** fix the insert position base on shebang/coding if filetype is python ([#10](https://github.com/marslo/cr-manager/issues/10)) ([ef837e5](https://github.com/marslo/cr-manager/commit/ef837e55c36dce53ab66b480e217ef48c7348f65))

## [2.0.7](https://github.com/marslo/cr-manager/compare/v2.0.6...v2.0.7) (2025-08-26)


### Bug Fixes

* fix the issue for remove shebang and coding in python type with `--delete` ([#9](https://github.com/marslo/cr-manager/issues/9)) ([e491840](https://github.com/marslo/cr-manager/commit/e49184004db2656caafbba63a9dfd016eed88edb))

## [2.0.6](https://github.com/marslo/cr-manager/compare/v2.0.5...v2.0.6) (2025-08-26)


### Bug Fixes

* fix the issue for misjudgment the shebang and coding line ([#8](https://github.com/marslo/cr-manager/issues/8)) ([9e37e78](https://github.com/marslo/cr-manager/commit/9e37e78150cee1e6798fbd2a71d56615b88b3f20))

## [2.0.5](https://github.com/marslo/cr-manager/compare/v2.0.4...v2.0.5) (2025-08-26)


### Bug Fixes

* **ignore:** add files/folders ignore list for recursive mode ([4875fec](https://github.com/marslo/cr-manager/commit/4875fece185cd7dccf59e5477be46a08bd33322b))

## [2.0.4](https://github.com/marslo/cr-manager/compare/v2.0.3...v2.0.4) (2025-06-28)


### Bug Fixes

* **pyinstaller:** init the main.py for pyinstaller ([33e983e](https://github.com/marslo/cr-manager/commit/33e983e48b8239aff55f65f718303730655c7cc0))
* **workflow,deploy:** to fix for issue `ERROR: Failed to import from 'libs' package, ... Details: No module named 'wcwidth'` ([85dd1a2](https://github.com/marslo/cr-manager/commit/85dd1a2ca12bde6d8fdc7dc4a6e7634cda5de6a2))

## [2.0.3](https://github.com/marslo/cr-manager/compare/v2.0.2...v2.0.3) (2025-06-28)


### Bug Fixes

* **help:** enhancement the help message ([b12595e](https://github.com/marslo/cr-manager/commit/b12595eb8288d673abfea76418c04b0b99a4b7d1))
* **releaserc:** remove `--no-update` from for semantic-release config ([74c8208](https://github.com/marslo/cr-manager/commit/74c8208cb4e7908c3a5b30731dc1b40141265d6b))
* remote the redundant message for verbose ([b36dda9](https://github.com/marslo/cr-manager/commit/b36dda9ecf40f8441c82ac26efa5724d3c494015))

## [2.0.2](https://github.com/marslo/cr-manager/compare/v2.0.1...v2.0.2) (2025-06-27)


### Bug Fixes

* **update:** fix the `--update` logic for combined copyright comment block; enhance the `--delete --debug` output ([3936a2d](https://github.com/marslo/cr-manager/commit/3936a2db66f163759ba5daf82d93632e0873cee8)), closes [#1](https://github.com/marslo/cr-manager/issues/1) [#2](https://github.com/marslo/cr-manager/issues/2)

## [2.0.1](https://github.com/marslo/cr-manager/compare/v2.0.0...v2.0.1) (2025-06-27)


### Bug Fixes

* **exit_code,check:** set exit_code to 0 for check mode; and update readme ([5bb5368](https://github.com/marslo/cr-manager/commit/5bb5368d90a48d1fbf6bd7170819c67585e37d10))

# [2.0.0](https://github.com/marslo/cr-manager/compare/v1.1.0...v2.0.0) (2025-06-27)


* feat!: restructure the folder, and using `cli.crm:main`; fix the --check for python and --debug for groovy; enhance the help message with filetypes ([13e19e6](https://github.com/marslo/cr-manager/commit/13e19e6a34c01e9e2a64b556944f614bd8bd96df))


### Features

* add ansicolor for output, reformat the code, add README and screenshots ([dcc20e2](https://github.com/marslo/cr-manager/commit/dcc20e21ab4686ccd6c1bd629ae32432c76e7341))


### BREAKING CHANGES

* v2.0.0

Signed-off-by: marslo <marslo.jiao@gmail.com>
