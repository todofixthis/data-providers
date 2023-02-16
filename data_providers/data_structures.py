import typing
from collections import defaultdict as default_dict

T = typing.TypeVar('T')


class ParameterisedDefaultDict(default_dict):
    """
    A :py:class:`default_dict` that passes parameters to its
    :py:meth:`__missing__` method.
    """

    def __init__(self,
            default_factory: typing.Optional[typing.Callable[..., T]] = None,
            *args: typing.Any,
            **kwargs: typing.Any,
    ) -> None:
        """
        :param default_factory:
            Factory method/class that will be used to create new items
            automatically.

            Must accept at least one argument (the key of the new value).

        :param args:
            Additional positional arguments that will be passed to the factory
            after the key value.

        :param kwargs:
            Additional keyword arguments that will be passed to the factory.
        """
        super(ParameterisedDefaultDict, self).__init__(default_factory)

        self._factory_args = args
        self._factory_kwargs = kwargs

    def __missing__(self, key: typing.Hashable) -> T:
        """
        Invoked when accessing a key that does not yet exist in the dict.
        """
        if not self.default_factory:
            raise KeyError(key)

        # noinspection PyArgumentList
        self[key] = value = self.default_factory(
            key,
            *self._factory_args,
            **self._factory_kwargs
        )

        return value
