import os
import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from pprint import pformat
from types import FrameType
from typing import Any, Callable, Dict, List, Optional, Pattern, Sequence, Type, Union


class Scope(Enum):
    LOCAL = 1
    GLOBAL = 2


@dataclass
class Result:
    """Rust-style tagged union representing the outcome of calling a probe function."""

    ok: bool
    value: Any = None
    error: Optional[Exception] = None

    @staticmethod
    def Ok(value: Any) -> "Result":  # noqa: N802
        """Wrap a successful function result."""
        return Result(ok=True, value=value)

    @staticmethod
    def Err(error: Exception) -> "Result":  # noqa: N802
        """Wrap a failed function call, capturing the raised exception."""
        return Result(ok=False, error=error)


@dataclass
class HereVar:
    var_name: str
    var_type: Type
    var_value: Any
    scope: Scope


@dataclass
class Combo:
    var: HereVar
    func: Callable[[Any], Any]
    result: Result


@dataclass
class ThisVars:
    lineno: int
    filename: Path
    call_stack: list[str]
    combos: list[Combo]


FuncMap = Dict[Callable[[Any], Any], Sequence[Type]]


def vars_from_scope(
    variables: dict[str, Any],
    *,
    scope: Scope,
) -> list[HereVar]:
    """Convert a raw name→value mapping into a list of :class:`HereVar` objects.

    Args:
        variables: A flat name→value dictionary, typically ``frame.f_locals``
            or ``frame.f_globals``.
        scope: The :class:`Scope` label to attach to every resulting variable.

    Returns:
        A list of :class:`HereVar` instances, one per entry in *variables*.
    """
    return [
        HereVar(
            var_name=name,
            var_type=type(value),
            var_value=value,
            scope=scope,
        )
        for name, value in variables.items()
    ]


def name_matches(pattern: Pattern[str], name: str) -> bool:
    return pattern.fullmatch(name) is not None


def type_matches(value: Any, accepted_types: Sequence[Type]) -> bool:
    return any(t is Any or isinstance(value, t) for t in accepted_types)


def collect_vars(frame: FrameType) -> list[HereVar]:
    return [
        *vars_from_scope(frame.f_locals, scope=Scope.LOCAL),
        *vars_from_scope(frame.f_globals, scope=Scope.GLOBAL),
    ]


def call_stack_from(frame: FrameType) -> list[str]:
    stack: list[str] = []
    current: Optional[FrameType] = frame

    while current is not None:
        stack.append(current.f_code.co_name)
        current = current.f_back

    return list(reversed(stack))


def _call(func: Callable[[Any], Any], value: Any) -> Result:
    try:
        return Result.Ok(func(value))
    except Exception as exc:
        return Result.Err(exc)


# ================================= API =================================
def inspect_this(
    frame: FrameType,
    f_map: Optional[FuncMap] = None,
    name_pattern: str = r".*",
) -> ThisVars:
    """Collect and probe variables from *frame*, applying the given function map.

    Variables are filtered first by *name_pattern* and then by the accepted
    types declared in *f_map*.  Each surviving (variable, function) pair
    becomes a :class:`Combo` whose ``result`` is the safe :class:`Result` of
    calling the function.

    Args:
        frame: The stack frame to inspect (typically obtained via
            ``sys._getframe(1)``).
        f_map: Mapping of probe functions to the types they should be applied
            to.  Defaults to ``{str: [Any]}`` (apply ``str()`` to everything).
        name_pattern: A regular-expression string; only variables whose names
            match are included.  Defaults to ``".*"`` (all variables).

    Returns:
        A :class:`ThisVars` containing the source location, call stack, and
        all (variable, function, result) combos.
    """
    pattern = re.compile(name_pattern)
    f_map = f_map or {str: [Any]}

    variables = [
        var for var in collect_vars(frame) if name_matches(pattern, var.var_name)
    ]

    return ThisVars(
        lineno=frame.f_lineno,
        filename=relative_filename(frame.f_code.co_filename),
        call_stack=call_stack_from(frame),
        combos=[
            Combo(
                var=var,
                func=func,
                result=_call(func, var.var_value),
            )
            for func, accepted_types in f_map.items()
            for var in variables
            if type_matches(var.var_value, accepted_types)
        ],
    )


# =================== IMPLEMENT =========================


RST = "\033[0m"
DIM = "\033[2m"
RULE = "\033[90m"
LOC = "\033[97m"
STACK = "\033[97m"
SCOPE = "\033[96m"
NAME = "\033[94m"
TYP = "\033[92m"
EXPR = "\033[95m"
VAL = "\033[93m"
ERR = "\033[91m"


def _c(text: object, color: str, *, colors: bool) -> str:
    """Wrap *text* in an ANSI escape sequence when *colors* is enabled.

    Args:
        text: Value to stringify and colour.
        color: An ANSI escape code (e.g. ``"\\033[94m"``).
        colors: When ``False`` the text is returned unmodified.
    """
    text = str(text)
    return f"{color}{text}{RST}" if colors else text


def _visible_len(text: str) -> int:
    """Return the visible (rendered) length of *text*, ignoring ANSI escape codes."""
    ansi_re = re.compile(r"\x1b\[[0-9;]*m")
    return len(ansi_re.sub("", text))


def _truncate_text(text: str, max_len: Optional[int]) -> str:
    """Shorten *text* to *max_len* characters, appending ``"..."`` when cut.

    Edge cases:

    * ``max_len`` is ``None`` — return *text* unchanged.
    * ``max_len <= 0``       — return an empty string.
    * ``max_len <= 3``       — return that many dots (no room for content).

    """
    if max_len is None:
        return text

    if max_len <= 0:
        return ""

    if len(text) <= max_len:
        return text

    if max_len <= 3:
        return "." * max_len

    return text[: max_len - 3] + "..."


def _pretty(
    value: object,
    *,
    truncate: Optional[int] = 100,
) -> str:
    """Format *value* as a compact single-line string, optionally truncated."""
    text = pformat(
        value,
        width=60,
        compact=True,
        sort_dicts=False,
    ).replace("\n", " ")

    if truncate is None:
        return text

    max_len = 100 if truncate is True else int(truncate)

    return _truncate_text(text, max_len)


def _func_name(func: object) -> str:
    """Return a human-readable name for *func*."""
    return getattr(func, "__name__", func.__class__.__name__)


def relative_filename(
    filename: Union[str, Path], base: Union[str, Path, None] = None
) -> Path:
    """Return *filename* expressed as a path relative to *base*."""
    path = Path(filename).resolve()
    base_path = Path(base or Path.cwd()).resolve()

    try:
        return path.relative_to(base_path)
    except ValueError:
        return Path(os.path.relpath(path, base_path))


_counter = 1


def this(
    f_map: Optional[FuncMap] = None,
    name_pattern: str = r".*",
    *,
    colors: bool = True,
    truncate: Optional[int] = 50,
) -> str:
    """Snapshot local/global variables at the call site and return a formatted table.

    Args:
        f_map: ``{function: [your_types,...]}``. Defaults to ``{str: [Any]}``.
        name_pattern: Regex filter on variable names. Defaults to ``".*"``.
        colors: ANSI colour output.
        truncate: Result cell width

    Examples::
        print(this({len: [list, str]}, name_pattern=r"^(x|label)$", colors=False))
    """
    global _counter

    this_frame = sys._getframe(1)

    t = inspect_this(
        frame=this_frame,
        f_map=f_map,
        name_pattern=name_pattern,
    )

    # format -----------------

    rows: List[Dict] = []

    for combo in t.combos:
        var = combo.var
        func_name = _func_name(combo.func)
        result = combo.result

        if result.ok:
            result_str = _pretty(result.value, truncate=truncate)
            is_err = False
        else:
            exc = result.error
            result_str = f"Err({type(exc).__name__}: {exc})"
            result_str = (
                _truncate_text(result_str, max_len=truncate)
                if truncate is not None
                else result_str
            )
            is_err = True

        rows.append(
            {
                "scope": var.scope.name.lower(),
                "name": var.var_name,
                "type": var.var_type.__name__,
                "expr": f"{func_name}({var.var_name})",
                "result": result_str,
                "is_err": is_err,
            }
        )

    rows.sort(
        key=lambda r: (
            0 if r["scope"] == "global" else 1,
            r["name"].lower(),
        )
    )

    title = f"This #{_counter}: {t.filename}:{t.lineno} | {' -> '.join(t.call_stack)}"

    lines: list[str] = [
        "",
        _c(title, LOC, colors=colors),
    ]

    if not rows:
        rule = "─" * len(title)
        lines.extend(
            [
                _c(rule, RULE, colors=colors),
                _c("(no variables)", DIM, colors=colors),
                _c(rule, RULE, colors=colors),
            ]
        )
        return "\n".join(lines)

    scope_w = max(len(r["scope"]) for r in rows)
    name_w = max(len(r["name"]) for r in rows)
    type_w = max(len(r["type"]) for r in rows)
    expr_w = max(len(r["expr"]) for r in rows)

    table_len = scope_w + 2 + name_w + 2 + type_w + 2 + expr_w + 3
    result_len = max(len(r["result"]) for r in rows)
    rule_len = max(len(title), table_len + result_len)

    rule = "─" * rule_len
    lines.append(_c(rule, RULE, colors=colors))

    for r in rows:
        scope = f"{r['scope']:<{scope_w}}"
        name = f"{r['name']:<{name_w}}"
        typ = f"{r['type']:<{type_w}}"
        expr = f"{r['expr']:<{expr_w}}"
        result = r["result"]
        result_color = ERR if r["is_err"] else VAL

        lines.append(
            f"{_c(scope, SCOPE, colors=colors)}  "
            f"{_c(name, NAME, colors=colors)}  "
            f"{_c(typ, TYP, colors=colors)}  "
            f"{_c(expr, EXPR, colors=colors)} "
            f"{_c('=', DIM, colors=colors)} "
            f"{_c(result, result_color, colors=colors)}"
        )

    lines.append(_c(rule, RULE, colors=colors))

    _counter += 1
    return "\n".join(lines)
