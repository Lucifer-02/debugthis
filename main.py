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
