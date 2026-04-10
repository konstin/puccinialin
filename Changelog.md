# Changelog

## 0.1.10

- Fix `RUST_HOME` -> `RUSTUP_HOME` (rustup ignores `RUST_HOME`)
- Fix Windows ARM64 support ([#33](https://github.com/konstin/puccinialin/pull/33))

## 0.1.9

- Fix creation of cargo home

## 0.1.8

- Fixed the release process, no code changes

## 0.1.7

- Switch to flit to avoid bootstrapping loop
- Fix Windows by using an absolute target path when checking for cargo

## 0.1.6

- Fix parallel runs with a file lock (see https://github.com/rust-lang/rustup/issues/4607)

## 0.1.5

- Add license declaration and files.

## 0.1.4

- Add support for GraalPy.
