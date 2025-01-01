# puccinialin

Install rust into a temporary directory to support rust-based builds. cargo and rustc are installed into a cache
directory, to avoid modifying the host's environment, and activated using a set of environment variables.

The difficult is mapping one of the various sources python platform information (`sys`, `platform`, `sysconfig`, etc.)
to a rustc target triple (https://doc.rust-lang.org/nightly/rustc/platform-support.html). Currently, this project uses
`SOABI`, which contains the file extensions of native modules.

## Contributing

The platform specific logic is in `src/puccinialin/_target.py`, specifically `get_triple`.

## Usage: Python

There is a single `setup_rust` function that takes the installation directory, or uses the user cache directory by
default. It returns a dict of environment variables to be used when calling rust.

```python
import os
from subprocess import check_call

from puccinialin import setup_rust

extra_env = setup_rust("path/to/installation/dir")
check_call(["cargo", "build"], env={**os.environ, **extra_env})
```

With setuptools-rust:

```python
import os
import shutil

from setuptools import setup
from setuptools_rust import RustBin

if not shutil.which("cargo"):
    from puccinialin import setup_rust

    print("Rust not found, installing into a temporary directory")
    extra_env = setup_rust()
    env = {**os.environ, **extra_env}
else:
    env = None

setup(
    ...,
    rust_extensions=[RustBin(..., env=env)],
)
```

You can use it as custom build backend to avoid the dependency when not needed, as e.g. in maturin:

```python
"""Support installing rust before compiling maturin.

Installing a package that uses maturin as build backend on a platform without maturin
binaries, we install rust in a cache directory if the user doesn't have a rust
installation already. Since this bootstrapping requires more dependencies but is only
required if rust is missing, we check if cargo is present before requesting those
dependencies.

https://setuptools.pypa.io/en/stable/build_meta.html#dynamic-build-dependencies-and-other-build-meta-tweaks
"""

from __future__ import annotations

import os
import shutil
from typing import Any

# noinspection PyUnresolvedReferences
from setuptools.build_meta import *


def get_requires_for_build_wheel(_config_settings: dict[str, Any] = None) -> list[str]:
    if not os.environ.get("MATURIN_NO_INSTALL_RUST") and not shutil.which("cargo"):
        return ["puccinialin"]
    return []


def get_requires_for_build_sdist(_config_settings: dict[str, Any] = None) -> list[str]:
    if not os.environ.get("MATURIN_NO_INSTALL_RUST") and not shutil.which("cargo"):
        return ["puccinialin"]
    return []
```

## Usage: CLI

```console
$ python -m puccinialin --help
usage: __main__.py [-h] [--location LOCATION] [--program PROGRAM] [--info-json INFO_JSON]

options:
  -h, --help            show this help message and exit
  --location LOCATION   The directory for installing rust to
  --program PROGRAM     The name of the installation directory in the cache, if `--location` was not used. Defaults to 'puccinialin'.
  --info-json INFO_JSON
                        Write the new environment variables as JSON to this file
```

## Implementation

Setting up rust consists of 4 steps:

- Determine the platform in terms of a rust target triple
- Download `rustup-init` for this target triple
- Use rustup to install rust and cargo for this target
- Report the environment variables to use this rust installation
