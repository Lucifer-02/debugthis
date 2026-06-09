# debugthis

`debugthis` is a small Python helper for inspecting variables at the call site.
Use `showthis.py` directly in the project you are debugging.

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

## Display Helper

```python
this(
    f_map=None,
    name_pattern=r".*",
    *,
    colors=True,
    truncate=50,
)
```

The `f_map` argument maps probe functions to accepted types:

```python
print(this({len: [list, str], str: [object]}))
```

If `f_map` is omitted, `str()` is applied to every matching variable.

`name_pattern` is a regular expression matched against the full variable name.
For prefix matches, include `.*` yourself:

```python
this(name_pattern=r"sample_.*")  # matches sample_text
this(name_pattern=r"sample_")    # does not match sample_text
```

`colors=False` disables ANSI color codes, which is useful for logs and tests.

`truncate` controls result width:

- `50`: default maximum result length
- `False` or `None`: do not truncate
- `True`: use the default truncation width
- any integer: truncate to that many characters

Probe exceptions are captured and displayed as `Err(...)` instead of being
raised.

## API

Use `inspect_this()` when you want structured data instead of a formatted string.
It takes an explicit Python frame and returns a `ThisVars` object.

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

Signature:

```python
inspect_this(
    frame,
    f_map=None,
    name_pattern=r".*",
)
```

Arguments:

- `frame`: the frame to inspect, usually from `sys._getframe()`
- `f_map`: a mapping of `{probe_function: [accepted_types]}`
- `name_pattern`: a regular expression matched against the full variable name

If `f_map` is omitted, `inspect_this()` uses `{str: [Any]}`.

Return value:

```python
ThisVars(
    lineno=int,
    filename=Path,
    call_stack=list[str],
    combos=list[Combo],
)
```

Each `Combo` contains:

- `var`: a `HereVar` with `var_name`, `var_type`, `var_value`, and `scope`
- `func`: the probe function that was called
- `result`: a `Result` object

`Result` is a small success/error wrapper:

- `Result.ok == True`: read the probe output from `Result.value`
- `Result.ok == False`: read the captured exception from `Result.error`

Scopes are represented by `Scope.LOCAL` and `Scope.GLOBAL`.

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

This is an 80/20 project. To keep it simple for most people, many feature
requests will be rejected.
