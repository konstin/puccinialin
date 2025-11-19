from __future__ import annotations

import os
import stat
import subprocess
import sys
import typing
from pathlib import Path
from subprocess import check_call

from filelock import FileLock

from puccinialin._target import Target, get_triple


def cache_dir(cache_program: str) -> Path:
    import platformdirs

    return Path(platformdirs.user_cache_dir(cache_program))


def download_rustup(
    url: str, output_file: Path, target: Target, file: typing.IO
) -> Path:
    """Download `rustup-init` for the correct target."""
    from secrets import token_hex

    import httpx
    from tqdm.auto import tqdm

    print(f"Downloading rustup-init from {url}", file=file)
    client = httpx.Client(timeout=60)
    response = client.head(url)
    total_size = int(response.headers.get("content-length", 0))
    # Transactional write
    tmp_download = output_file.parent.joinpath(f"tmp_{token_hex(16)}")
    with (
        # From the HTTP request ...
        client.stream("GET", url) as response,
        # ... through the progress bar ...
        tqdm(
            desc="Downloading rustup-init",
            total=total_size,
            unit="B",
            unit_scale=True,
        ) as progress_bar,
        # ... to the output file
        tmp_download.open("wb") as fp,
    ):
        response.raise_for_status()
        for chunk in response.iter_bytes(chunk_size=8192):
            size = fp.write(chunk)
            progress_bar.update(size)

        if not target.is_windows():
            tmp_download.chmod(tmp_download.stat().st_mode | stat.S_IEXEC)

    os.replace(tmp_download, output_file)

    return output_file


def install_rust(
    rustup_init: Path, rustup_home: Path, cargo_home: Path, file: typing.IO
):
    """Run rustup to install rust and cargo"""
    print(f"Installing rust to {rustup_home}", file=file)
    check_call(
        [
            rustup_init,
            "-y",
            "--no-modify-path",
            "--profile",
            "minimal",
        ],
        env={
            **os.environ,
            "RUST_HOME": str(rustup_home),
            "CARGO_HOME": str(cargo_home),
        },
        # Hide the "Rust is now installed" message.
        stdout=subprocess.DEVNULL,
        stderr=file,
    )


def setup_rust(
    installation_dir: str | Path | None = None,
    program: str | None = None,
    file: typing.IO = sys.stderr,
) -> dict[str, str]:
    """Install rust and return the modified environment variable to use it.

    If `installation_dir` is given, this directory is used. By default, the cache directory for `program` is used.

    All custom output is written to the file-like object `file`, which defaults to stderr. `file` must support
    `print(..., file=<file>)` and `subprocess.Popen(..., stderr=<file>)`."""
    # Step 1: Determine the target as a rustc target triple
    target = Target(file)
    target_triple = get_triple(file)
    # Installation paths
    if installation_dir:
        installation_dir = Path(os.getcwd()).joinpath(installation_dir)
    else:
        package_name = __name__.split(".")[0]
        installation_dir = cache_dir(program or package_name)
    print(f"Installation directory: {installation_dir}", file=file)
    rustup_init_dir = installation_dir.joinpath("rustup-init")
    rustup_init_dir.mkdir(parents=True, exist_ok=True)
    rustup_home = installation_dir.joinpath("rustup")
    rustup_home.mkdir(parents=True, exist_ok=True)
    cargo_home = installation_dir.joinpath("cargo")
    rustup_home.mkdir(parents=True, exist_ok=True)

    # Step 2: Download rustup
    rustup_init = rustup_init_dir.joinpath("rustup-init").with_suffix(
        target.exe_suffix()
    )
    url = f"https://static.rust-lang.org/rustup/dist/{target_triple}/rustup-init{target.exe_suffix()}"
    if rustup_init.is_file():
        print("Rustup already downloaded", file=file)
    else:
        rustup_init = download_rustup(url, rustup_init, target, file)
    # Step 3: Install rust and cargo

    # Only one rustup at a time, rustup isn't parallelism save.
    # https://github.com/rust-lang/rustup/issues/4607
    lock = FileLock(rustup_init.with_suffix(".lock"))
    with lock:
        install_rust(rustup_init, rustup_home, cargo_home, file)

    # Step 4: Construct and return a dict of changed environment variables to use this rust installation
    new_path = f"{cargo_home.joinpath('bin')}{target.env_path_separator()}{os.environ.get('PATH')}"
    extra_env: dict[str, str] = {
        "RUST_HOME": str(rustup_home),
        "CARGO_HOME": str(cargo_home),
        "PATH": new_path,
    }

    print("Checking if cargo is installed", file=file)
    check_call(["cargo", "--version"], env={**os.environ, **extra_env})
    return extra_env
