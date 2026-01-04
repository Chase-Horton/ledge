from functools import wraps
from typing import Any, Callable, TypeVar, overload

F = TypeVar("F", bound=Callable[..., Any])


# TODO:
class DocInherit:
    """Docstring inheriting method descriptor.

    The class itself is also used as a decorator.
    """

    mthd: Callable[..., Any]
    name: str

    def __init__(self, mthd: Callable[..., Any]) -> None:
        """Initialize the descriptor."""
        self.mthd = mthd
        self.name = mthd.__name__

    @overload
    def __get__(self, obj: None, cls: type[Any]) -> Callable[..., Any]: ...
    @overload
    def __get__(self, obj: object, cls: type[Any]) -> Callable[..., Any]: ...

    def __get__(self, obj: object | None, cls: type[Any]) -> Callable[..., Any]:
        """Retrieve the method, with docstring inherited from parent class."""
        if obj:
            return self._get_with_inst(obj, cls)
        else:
            return self._get_no_inst(cls)

    def _get_with_inst(self, obj: object, cls: type[Any]) -> Callable[..., Any]:
        overridden = getattr(super(cls, obj), self.name, None)

        @wraps(self.mthd, assigned=("__name__", "__module__"))
        def f(*args: Any, **kwargs: Any) -> Any:
            return self.mthd(obj, *args, **kwargs)

        return self._use_parent_doc(f, overridden)

    def _get_no_inst(self, cls: type[Any]) -> Callable[..., Any]:
        overridden: Callable[..., Any] | None = None
        for parent in cls.__mro__[1:]:
            overridden = getattr(parent, self.name, None)
            if overridden:
                break

        @wraps(self.mthd, assigned=("__name__", "__module__"))
        def f(*args: Any, **kwargs: Any) -> Any:
            return self.mthd(*args, **kwargs)

        return self._use_parent_doc(f, overridden)

    def _use_parent_doc(
        self, func: Callable[..., Any], source: Callable[..., Any] | None
    ) -> Callable[..., Any]:
        if source is None:
            raise NameError("Can't find '%s' in parents" % self.name)
        func.__doc__ = source.__doc__
        return func


doc_inherit = DocInherit
