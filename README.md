# yapm-contrib
contribution repo for yapm.

## Package format

A `.yapm` package is a **tar.zst** archive (zstd-compressed tarball) containing a `yapm.data` file at its root (or in a subdirectory).

```
mypackage.yapm (tar.zst)
├── yapm.data
├── ...
```

## yapm.data format

A plain-text key-value file. Lines starting with `//` are comments.

```
name = my-package
version = 1.0.0
description = A short description
author = Your Name
license = MIT
```

**Required fields:** `name`, `version`, `description`, `author`, `license`

## Validation workflow

A GitHub Actions workflow (`.github/workflows/validate.yml`) runs on every pull request that touches `.yapm` files. It:

1. Finds changed `.yapm` files by diffing against the PR base branch.
2. For each file, checks that:
   - It is a valid tar.zst archive.
   - It contains a `yapm.data` file.
   - `yapm.data` has all required fields.

If any check fails the workflow fails and the PR cannot be merged.
