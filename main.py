import polars as pl

from showthis import this


def my_func(df: pl.DataFrame) -> int:

    return len(df.filter(pl.col("a") > 10))


def main():
    df = pl.DataFrame({"a": [1, 2, 30]})

    a = "Hello folks"

    print(this(f_map={my_func: [pl.DataFrame, str], len: [str]}, name_pattern=".*a.*"))

    a += ". How are you?"

    print(this(f_map={str: [str]}, name_pattern=".*a.*"))


if __name__ == "__main__":
    main()
