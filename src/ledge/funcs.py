"""File for test functions."""


def bad(test: str) -> None:
    """Prints test string.

    Args:
        test (str): string to print
    """
    print(test)


def go(n: str) -> None:
    """Go.

    Args:
        n (str): num
    """
    bad("test")


def fib(n: int) -> int:
    """*2.

    Args:
        n (int): num

    Returns:
        int: num*2
    """
    return n * 2
