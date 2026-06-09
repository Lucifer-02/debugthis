# debugthis

`debugthis` is a small Python helper for inspecting variables at the call site.
Call `this()` inside your code and it returns a formatted table showing matching
local and global variables, their types, the probe expression that was run, and
the probe result.

## Quick Start

```python
from showthis import this


def main():
    user = "Ada"
    scores = [10, 20, 30]

    print(this({len: [str, list]}, name_pattern=r"user|scores", colors=False))


if __name__ == "__main__":
    main()
```

Example output:

```text
This #1: main.py:8 | <module> -> main
---------------------------------------
local  scores  list  len(scores) = 3
local  user    str   len(user)   = 3
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
.venv/bin/pytest -q
```

Or, if you use `uv` to manage the environment:

```bash
uv run pytest -q
```
