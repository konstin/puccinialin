FROM ghcr.io/astral-sh/uv:python3.14-trixie

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

COPY src src
COPY README.md ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

ENV PATH="/app/.venv/bin:$PATH"
