import typing
from abc import ABCMeta, abstractmethod as abstract_method
from collections import defaultdict as default_dict

from data_providers.exceptions import with_context

__all__ = [
    'BaseDataProvider',
    'MutableDataProviderMixin',
]


class BaseDataProvider(metaclass=ABCMeta):
    """
    Implementation of the flywheel pattern.  Bulk-loads data from a backend
    and parcels them out on an as-needed basis.
    """

    def __init__(self):
        super(BaseDataProvider, self).__init__()

        self._cache = self._create_cache()
        """
        Caches data loaded from the backend so that it can be accessed easily.
        """

        self._pending_load_keys: typing.Set[typing.Hashable] = set()
        """
        Stores lookup keys for values that haven't been loaded yet.

        Note: This value should be a set; if you find yourself wanting to use a
        dict here, :py:class:`BaseDataProviderDelegate` is probably a better
        fit for your use case.
        """

        self._pending_cache_keys: typing.Dict[
            typing.Hashable,
            typing.Set[typing.Hashable]
        ] = default_dict(set)
        """
        Stores cache keys for values that haven't been loaded yet.

        This is used to gracefully handle cases where the backend doesn't
        return data for one or more load keys.
        """

    def __getitem__(self, value: typing.Any) -> typing.Any:
        """
        Returns data for the specified value.

        :param value:
            The lookup key.

        :raise:
            - :py:class:`ValueError` if the value wasn't registered first.
        """
        # Determine the key we will use to look up the value in the cache.
        cache_key = self.gen_cache_key(value)
        if cache_key is None:
            return self.gen_empty_result()

        try:
            cached = self._get_from_cache(cache_key)
        except KeyError:
            # The value has not been cached yet.
            # Determine which data we need to load from the backend.
            load_key = self.gen_load_key(value)
            if load_key is None:
                cached = self.gen_empty_result()
            else:
                # If the key hasn't been registered, we cannot continue.
                # If we were to allow loading without registering, we would
                # undermine the whole point of using a flywheel in the first
                # place!
                if load_key not in self._pending_load_keys:
                    raise with_context(
                        ValueError(
                            f'Attempting to get data for '
                            'unregistered value {value!r}.',
                        ),

                        context={
                            'cacheKey': cache_key,
                            'loadKey': load_key,
                            'value': value,
                        },
                    )

                # Load data from the backend and populate/extend the cache.
                self._load_data(load_key)

                # Try loading from cache again, this time without a safety net.
                cached = self._get_from_cache(cache_key)

        return cached

    @abstract_method
    def fetch_from_backend(self, load_keys: typing.Set[typing.Hashable]) -> \
            typing.Union[
                typing.Mapping[typing.Hashable, typing.Any],
                typing.Generator[
                    typing.Tuple[typing.Hashable, typing.Any], None, None],
            ]:
        """
        Fetches data from the backend for the specified load keys.

        :return:
            A mapping, or a generator that yields (key, value) pairs.

            The keys in the resulting mapping should correspond to the data
            provider's cache keys (from :py:meth:`gen_cache_key`).
        """
        raise NotImplementedError(
            'Not implemented in {cls}.'.format(cls=type(self).__name__),
        )

    def gen_load_key(self,
            value: typing.Any,
    ) -> typing.Optional[typing.Hashable]:
        """
        Extracts the value that will be used by the backend to load
        data for the specified value.

        If this method returns ``None``, then the data provider will
        never attempt to return data for that value; if that value is
        passed to :py:meth:`__getitem__`, the data provider will return
        an empty result instead (see :py:meth:`gen_empty_result`).

        :param value:
            The value passed to :py:meth:`__getitem__`.
        """
        return value

    def gen_cache_key(self,
            value: typing.Any,
    ) -> typing.Optional[typing.Hashable]:
        """
        Generates a lookup key for the data provider's cached data.

        If this method returns ``None``, then the data provider will never
        attempt to return data for that value; if that value is passed to
        :py:meth:`__getitem__`, the data provider will return an empty result
        instead (see :py:meth:`gen_empty_result`).

        :param value:
            The key value passed to `__getitem__`.
        """
        return self.gen_load_key(value)

    def gen_empty_result(self) -> typing.Optional[typing.Any]:
        """
        Generates an empty result that is returned if the backend cannot (or
        will not) return data for a particular key.

        You may override this method in a subclass if desired.  This method may
        return any value, or even raise an exception, depending on the use
        case.
        """
        return None

    def register(self, values: typing.Iterable[typing.Any]) -> None:
        """
        Registers a set of values so that the data provider can plan out the
        bulk queries it needs to execute against the backend.
        """
        for v in values:
            self._add_to_key_registry(v)

    def warm_cache(self):
        """
        Warms the cache, fetching data for any keys that haven't been loaded
        yet.

        Note: the data provider will automatically load data from the backend
        as needed.  In general, you shouldn't have to invoke this method,
        though it can be useful in particular during debugging.
        """
        if self._pending_load_keys:
            self._load_batch(self._pending_load_keys)

    # noinspection PyMethodMayBeStatic
    def _create_cache(self) -> typing.MutableMapping[
        typing.Hashable,
        typing.Any,
    ]:
        """
        Initializes the cache that the data provider will use.

        You may override this method in a subclass if desired; the only
        restriction is that it must return some kind of mutable mapping.
        """
        return {}

    def _add_to_cache(self,
            cache_key: typing.Hashable,
            cache_value: typing.Any,
    ) -> None:
        """
        Adds a value to the cache.

        If there is an existing value with the same key, it is overwritten.

        You may override this method in a subclass if desired.
        """
        self._cache[cache_key] = cache_value

    def _get_from_cache(self, cache_key: typing.Hashable) -> typing.Any:
        """
        Attempts to retrieve the data from the cache for the specified key.

        You may override this method in a subclass if desired.

        :raise:
          - :py:class:`KeyError` in the event of a cache miss.
        """
        return self._cache[cache_key]

    def _add_to_key_registry(self, value: typing.Any) -> None:
        """
        Adds the specified value to the registry of unloaded keys.

        :param value:
            The value that was passed to :py:meth:`register`.
        """
        # If we can't load data for a value, then there's no point in
        # registering it.
        load_key = self.gen_load_key(value)
        if load_key is not None:
            # If we can't cache data for a value, then there would be no point
            # in loading data for it.
            # Also, we don't need to register a value if we already have cached
            # data for it.
            cache_key = self.gen_cache_key(value)
            if (cache_key is not None) and (cache_key not in self._cache):
                # Queue the load key for the next time we call
                # :py:meth:`_load_data`.
                self._pending_load_keys.add(load_key)

                # Queue the corresponding cache key so that we can ensure that
                # *some* kind of value is cached, even if the backend doesn't
                # return any data for it.
                self._pending_cache_keys[load_key].add(cache_key)

    # noinspection PyUnusedLocal
    def _get_keys_to_load(self, hint: typing.Hashable) -> typing.Set[
        typing.Hashable]:
        """
        Used by :py:meth:`_load_data` to decide which values to send to the
        backend.

        By default, this method returns all pending load keys, but you may
        override this method in a subclass if you want to use a more selective
        strategy.

        :param hint:
            The requested load key (based on the value passed to
            :py:meth:`__getitem__`).
        """
        return self._pending_load_keys

    def _load_data(self, hint: typing.Hashable) -> None:
        """
        Bulk-loads data from the backend in the event of a cache miss.

        :param hint:
            The requested load key (based on the value passed to
            :py:meth:`__getitem__`).
        """
        batched_load_keys = self._get_keys_to_load(hint)
        if batched_load_keys:
            self._load_batch(batched_load_keys)

    def _load_batch(self, load_keys: typing.Set[typing.Hashable]) -> None:
        """
        Bulk-loads data from the backend, only for the specified keys.
        """
        loaded = self.fetch_from_backend(load_keys)

        # :py:meth:`fetch_from_backend` is expected to return a mapping, or at
        # least a value that quacks like one.
        if isinstance(loaded, typing.Generator):
            iterator = loaded
        else:
            if not isinstance(loaded, typing.Mapping):
                loaded = dict(loaded)

            iterator = loaded.items()

        for cache_key, cache_value in iterator:
            # The backend can overwrite any existing cached values.
            # You may override :py:meth:`_add_to_cache` in a subclass if this
            # is not desirable behavior.
            self._add_to_cache(cache_key, cache_value)

        # Fill in any missing cache keys that weren't included in the result
        # from the backend.
        for lk in load_keys:
            for pck in self._pending_cache_keys[lk]:
                if pck not in self._cache:
                    self._add_to_cache(pck, self.gen_empty_result())
            self._pending_cache_keys.pop(lk, None)

        self._pending_load_keys -= load_keys


class MutableDataProviderMixin(BaseDataProvider, metaclass=ABCMeta):
    """
    A mixin for data provider classes that allow external code to modify the
    contents of the cache.

    Any values set this way will override values returned by the backend.
    """

    def __init__(self):
        super(MutableDataProviderMixin, self).__init__()

        self._override_cache_keys: typing.Set[typing.Hashable] = set()

    def __setitem__(self, value: typing.Any, cache_value: typing.Any) -> None:
        """
        Sets the cached value for the specified object.

        :param value:
            Same as :py:meth:`__getitem__`.

        :param cache_value:
            The value that should be put in the cache.
        """
        load_key = self.gen_load_key(value)
        if load_key is not None:

            cache_key = self.gen_cache_key(value)
            if cache_key is not None:

                # Since we are setting the cached value explicitly, we do not
                # need to backfill it when :py:meth:`_load_data` runs.
                pending_cache_keys = self._pending_cache_keys[load_key]
                pending_cache_keys.discard(cache_key)

                # If there are no [other] registered cache keys associated with
                # this load key, then we won't have to load any data for that
                # key (i.e., we can drop it).
                if not pending_cache_keys:
                    self._pending_load_keys.discard(load_key)

                # Allow :py:meth:`__setitem__` to override values more than
                # once.
                self._override_cache_keys.discard(cache_key)

                self._replace_cached_value(cache_key, cache_value)
                self._override_cache_keys.add(cache_key)

    def _replace_cached_value(self,
            cache_key: typing.Hashable,
            cache_value: typing.Any,
    ) -> None:
        """
        Replaces a value in the cache.

        You may override this method in a subclass if desired.

        Note: this method must *not* raise an exception.
        """
        self._add_to_cache(cache_key, cache_value)

    def _add_to_cache(self,
            cache_key: typing.Hashable,
            cache_value: typing.Any,
    ) -> None:
        """
        Adds a value to the cache, if it has not been overridden by
        :py:meth:`__setitem__`.
        """
        if cache_key not in self._override_cache_keys:
            super(MutableDataProviderMixin, self) \
                ._add_to_cache(cache_key, cache_value)
