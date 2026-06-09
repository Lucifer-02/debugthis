# Overview

A small Python helper for inspecting variables at the call site.

**Use `showthis.py` directly in the project you are debugging.**

## Quick Start

```python
import polars as pl

from showthis import this

def my_func(df: pl.DataFrame) -> int:
    return len(df.filter(pl.col("a") > 10))


def main():
    df = pl.DataFrame({"a": [1, 2, 30]})

    a1 = "Hello folks"

    print(
        this(
            f_map={my_func: [pl.DataFrame, str], str: [str]},
            name_pattern=r"[a-z]{2}",
            colors=False,
        )
    )

    a1 += ". How are you?"

    print(this(f_map={str: [str]}, name_pattern=r"\w{2}", colors=False))


if __name__ == "__main__":
    main()
```

Example output:

```text
This #1: main.py:16 | <module> -> main
──────────────────────────────────────
local  df  DataFrame  my_func(df) = 1
──────────────────────────────────────

This #2: main.py:25 | <module> -> main
─────────────────────────────────────────────────────
local  a1  str  str(a1) = 'Hello folks. How are you?'
─────────────────────────────────────────────────────
```

## Usage

`this()` returns a formatted table from the call site.

```python
print(this({len: [list, str]}, name_pattern=r"items|label", colors=False))
```

`f_map` maps probe functions to accepted types. If omitted, `str()` is applied
to every matching variable.

`name_pattern` uses full regex matching:

```python
this(name_pattern=r"sample_.*")  # matches sample_text
this(name_pattern=r"sample_")    # does not match sample_text
```

Use `colors=False` for logs or tests. Use `truncate=False` or `truncate=None`
to disable result truncation.

## API

Use `inspect_this()` for structured data instead of formatted text.

```python
import sys
from typing import Any

from showthis import inspect_this


result = inspect_this(
    frame=sys._getframe(),
    f_map={str: [Any]},
    name_pattern=r".*",
)
```

It returns `ThisVars`, which contains source location, call stack, and probe
results. Probe exceptions are captured in `Result.error`.

## Development

Run the example:

```bash
uv run main.py
```

Run tests:

```bash
uv run pytest -q
```

## Note

**THIS IS AN 80/20 PROJECT. TO KEEP IT SIMPLE FOR MOST PEOPLE, MANY FEATURE REQUESTS WILL BE REJECTED.**
