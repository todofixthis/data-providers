import typing
from abc import ABCMeta, abstractmethod as abstract_method
from collections import defaultdict as default_dict

from data_providers import BaseDataProvider, MutableDataProviderMixin
from data_providers.data_structures import ParameterisedDefaultDict
from data_providers.exceptions import with_context

__all__ = [
    'BaseDataProviderDelegate',
    'MutableDataProviderDelegateMixin',
]


class BaseDataProviderDelegate(metaclass=ABCMeta):
    """
    A data-provider-like object that delegates its responsibilities to other
    data providers.

    The delegate stores a collection of data providers internally, and it
    routes each incoming value to the appropriate data provider.
    """

    def __init__(self):
        super(BaseDataProviderDelegate, self).__init__()

        self._delegates: typing.Dict[
            typing.Hashable,
            BaseDataProvider,
        ] = ParameterisedDefaultDict(self.create_data_provider)

    def __getitem__(self, value: typing.Any) -> typing.Any:
        """
        Returns the data for the specified value, fetching it from the backend
        if necessary.
        """
        return self.get_data_provider(value)[value]

    @abstract_method
    def gen_delegate_key(self, value: typing.Any) -> typing.Hashable:
        """
        Generates a delegate key for a registered value.

        :param value:
            The value passed to `__getitem__`.
        """
        raise NotImplementedError(
            'Not implemented in {cls}.'.format(cls=type(self).__name__),
        )

    @abstract_method
    def create_data_provider(self,
            delegate_key: typing.Hashable,
    ) -> BaseDataProvider:
        """
        Creates the appropriate data provider for the specified delegate key.

        If ``delegate_key`` is invalid, this method must raise an exception.

        .. note::

           The resulting data provider instance is cached locally; this method
           is only invoked once per delegate key.
        """
        raise NotImplementedError(
            'Not implemented in {cls}.'.format(cls=type(self).__name__),
        )

    def register(self, values: typing.Iterable[typing.Any]) -> None:
        """
        Registers a set of values with the data provider.
        """
        grouped_values = self.group_by_delegate_key(values)

        for delegate_key, delegate_values in grouped_values.items():
            self._delegates[delegate_key].register(delegate_values)

    def get_data_provider(self, value: typing.Any) -> BaseDataProvider:
        """
        Returns the correct data provider to use for the specified value.
        """
        return self._delegates[self.gen_delegate_key(value)]

    def group_by_delegate_key(self,
            values: typing.Iterable[typing.Any],
    ) -> typing.Mapping[typing.Hashable, typing.Iterable[typing.Any]]:
        """
        Groups a collection of values by delegate key.

        This method may be overridden in subclasses if desired.
        """
        grouped = default_dict(list)

        for value in values:
            grouped[self.gen_delegate_key(value)].append(value)

        return grouped


class MutableDataProviderDelegateMixin(
    BaseDataProviderDelegate,
    metaclass=ABCMeta,
):
    """
    A mixin for data provider delegates that allow external code to modify the
    contents of the data providers' caches.
    """

    def __setitem__(self, value: typing.Any, cache_value: typing.Any):
        """
        Sets the cached value for the specified object.
        """
        delegate_key = self.gen_delegate_key(value)
        data_provider = self._delegates[delegate_key]

        if isinstance(data_provider, MutableDataProviderMixin):
            data_provider[value] = cache_value
        else:
            raise with_context(
                TypeError(
                    f'Cannot modify the contents of '
                    f'{type(data_provider).__name__}.'
                ),

                context={
                    'data_provider': data_provider,
                    'delegate_key': delegate_key,
                    'value': value,
                },
            )
