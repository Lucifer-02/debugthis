# debugthis

`debugthis` is a simple Python way for inspecting variables at the call site. Just use `showthis.py` file to do that.

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

## API

```python
this(
    f_map=None,
    name_pattern=r".*",
    *,
    colors=True,
    truncate=50,
)
```

`f_map` maps probe functions to accepted types:

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

- `50`: default maximum result length.
- `False` or `None`: do not truncate.
- `True`: use the default truncation width.
- any integer: truncate to that many characters.

Probe exceptions are captured and displayed as `Err(...)` instead of being
raised.

## Development

Run the example:

```bash
uv run main.py
```

Run tests:

```bash
uv run pytest -q
```
## NOTE
THIS IS 80-20 PROJECT, THAT MEAN TO KEEP IT SIMPLE FOR MOST PEOPLE, MANY FEATURES WILL BE REJECT.
