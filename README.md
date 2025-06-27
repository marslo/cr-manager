# cr-manager

A tool to automatically **add**, **update**, or **delete** multi-format copyright headers in source files.

---

## Features

- **Add**: Insert copyright headers for multiple file types.
- **Update**: Force update or insert headers if missing.
- **Check**: Verify the presence and correctness of headers.
- **Delete**: Remove detected copyright headers from files.
- Supports recursive directory traversal and filetype auto-detection or override.

---

## Usage

```bash
$ cr-manager [--check | --delete | --update] [--copyright-file FILE]
             [--filetype TYPE] [--recursive] [--debug] [-v] [-h] [--version]
             [FILES ...]
```

### Action Modes (choose one, default is add)

| OPTION     | DESCRIPTION                                                                 |
| ---------- | --------------------------------------------------------------------------- |
| `--check`  | Check mode: Verifies file copyright status (match, mismatch, or not found). |
| `--delete` | Delete mode: Removes detected copyright headers from files.                 |
| `--update` | Update mode: Forces replacement of copyright or adds it if missing.         |

### OPTIONS

| OPTION                  | DESCRIPTION                                                                                                                          |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `--copyright-file FILE` | Specify the copyright template file path (default: `COPYRIGHT`).                                                                     |
| `--filetype TYPE`       | Force a filetype to override auto-detection (e.g., `python`, `java`). If provided alone, displays a formatted preview for that type. |
| `--recursive`, `-r`     | If FILES includes directories, process their contents recursively.                                                                   |
| `--debug`               | Debug mode: Preview the result of an action without modifying files.                                                                 |
| `-v`, `--verbose`       | Show a detailed processing summary.                                                                                                  |
| `-h`, `--help`          | Show help message and exit.                                                                                                          |
| `--version`             | Show program's version number and exit.                                                                                              |

## Examples

### add copyright headers
```bash
# to single file
$ python crm.py --copyright-file COPYRIGHT /path/to/file

# to filers in directory recursively
$ python crm.py --copyright-file COPYRIGHT /path/to/directory
```
