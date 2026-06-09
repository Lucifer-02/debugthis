import re
import sys
from typing import Any

import pytest

import showthis

TEST_GLOBAL_VALUE = "global-value"


@pytest.fixture(autouse=True)
def reset_counter() -> None:
    showthis._counter = 1


def test_inspect_this_filters_names_and_types() -> None:
    def capture() -> showthis.ThisVars:
        sample_text = "abc"
        sample_items = [1, 2, 3]
        sample_count = 7
        ignored = "not included"
        assert ignored == "not included"

        return showthis.inspect_this(
            sys._getframe(),
            f_map={len: [str, list], str: [int]},
            name_pattern=r"sample_.*",
        )

    result = capture()

    combos = {
        (combo.func, combo.var.var_name): combo.result.value for combo in result.combos
    }
    assert combos[(len, "sample_text")] == 3
    assert combos[(len, "sample_items")] == 3
    assert combos[(str, "sample_count")] == "7"
    assert len(result.combos) == 3
    assert "capture" in result.call_stack


@pytest.mark.parametrize(
    ("pattern", "name", "expected"),
    [
        (r"sample_.*", "sample_text", True),
        (r"sample_", "sample_text", False),
        (r".*_text", "sample_text", True),
        (r"text", "sample_text", False),
    ],
)
def test_name_matches_requires_the_pattern_to_match_the_full_name(
    pattern: str, name: str, expected: bool
) -> None:
    assert showthis.name_matches(re.compile(pattern), name) is expected


def test_inspect_this_can_include_matching_globals() -> None:
    def capture() -> showthis.ThisVars:
        local_value = "local"
        assert local_value == "local"
        return showthis.inspect_this(
            sys._getframe(),
            f_map={str: [Any]},
            name_pattern=r"^(TEST_GLOBAL_VALUE|local_value)$",
        )

    result = capture()

    values_by_name = {
        combo.var.var_name: (combo.var.scope, combo.result.value)
        for combo in result.combos
    }
    assert values_by_name["TEST_GLOBAL_VALUE"] == (
        showthis.Scope.GLOBAL,
        "global-value",
    )
    assert values_by_name["local_value"] == (showthis.Scope.LOCAL, "local")


def test_call_captures_exceptions_as_error_results() -> None:
    def explode(value: object) -> object:
        raise ValueError(f"bad value: {value}")

    result = showthis._call(explode, "input")

    assert not result.ok
    assert isinstance(result.error, ValueError)
    assert str(result.error) == "bad value: input"


@pytest.mark.parametrize(
    ("max_len", "expected"),
    [
        (None, "abcdef"),
        (0, ""),
        (2, ".."),
        (3, "..."),
        (4, "a..."),
        (6, "abcdef"),
    ],
)
def test_truncate_text_edge_cases(max_len: int | None, expected: str) -> None:
    assert showthis._truncate_text("abcdef", max_len) == expected


def test_this_formats_matching_local_variable_without_ansi_codes() -> None:
    def capture() -> str:
        username = "Ada"
        return showthis.this(
            {str: [str]},
            name_pattern=r"^username$",
            colors=False,
            truncate=False,
        )

    output = capture()

    assert not re.search(r"\x1b\[[0-9;]*m", output)
    assert "This #1:" in output
    assert "capture" in output
    assert "local" in output
    assert "username" in output
    assert "str(username)" in output
    assert "'Ada'" in output


def test_this_reports_no_variables_when_pattern_matches_nothing() -> None:
    def capture() -> str:
        visible = "present but filtered out"
        assert visible == "present but filtered out"
        return showthis.this(
            name_pattern=r"^does_not_exist$",
            colors=False,
        )

    output = capture()

    assert "(no variables)" in output
    assert "visible" not in output


def test_this_formats_probe_errors() -> None:
    def fail(value: object) -> object:
        raise RuntimeError(f"cannot inspect {value}")

    def capture() -> str:
        target = "x"
        return showthis.this(
            {fail: [str]},
            name_pattern=r"^target$",
            colors=False,
            truncate=False,
        )

    output = capture()

    assert "fail(target)" in output
    assert "Err(RuntimeError: cannot inspect x)" in output
