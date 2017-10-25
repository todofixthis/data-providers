# coding=utf-8
from __future__ import absolute_import, division, print_function, \
    unicode_literals

from collections import defaultdict as default_dict
from typing import Any, Callable, Hashable, TypeVar

T = TypeVar('T')

class ParameterizedDefaultDict(default_dict):
    """
    A :py:class:`default_dict` that passes parameters to its
    :py:meth:`__missing__` method.
    """
    def __init__(self, default_factory=None, *args, **kwargs):
        # type: (Callable[..., T], *Any, **Any) -> None
        """
        :param default_factory:
            Factory method/class that will be used to create new
            items automatically.

            Must accept at least one argument (the key of the new
            value).

        :param args:
            Additional positional arguments that will be passed to the
            factory.

        :param kwargs:
            Additional keyword arguments that will be passed to the
            factory.
        """
        super(ParameterizedDefaultDict, self).__init__(default_factory)

        self._factory_args      = args
        self._factory_kwargs    = kwargs

    def __missing__(self, key):
        # type: (Hashable) -> T
        """
        Invoked when accessing a key that does not yet exist in the dict.
        """
        if not self.default_factory:
            raise KeyError(key)

        self[key] = value =\
            self.default_factory(
                key,
                *self._factory_args,
                **self._factory_kwargs
            )

        return value
