## [3.0.5](https://github.com/marslo/cr-manager/compare/v3.0.4...v3.0.5) (2025-11-15)

## [3.0.4](https://github.com/marslo/cr-manager/compare/v3.0.3...v3.0.4) (2025-11-15)

## [3.0.3](https://github.com/marslo/cr-manager/compare/v3.0.2...v3.0.3) (2025-11-15)

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
