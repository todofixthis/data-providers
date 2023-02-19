import typing
from unittest import TestCase

from data_providers import BaseDataProvider, DataProvider, \
    MutableDataProviderMixin


class DataProviderTestCase(TestCase):
    """
    Shows how to use :py:class:`DataProvider`.
    """

    def test_example_usage(self):
        """
        Using `DataProvider` to bulk-load data from a backend such as a
        database.
        """

        # Example of a loader function that we'll wrap with a DataProvider.
        def get_users_by_id(
                user_ids: typing.Set[int]
        ) -> typing.Dict[int, dict]:
            # In order to keep the unit test self-contained, this function just
            # returns some hard-coded data, but in a real-world use case, it
            # would connect to a database and execute a complicated query (or
            # run a data model, make some API calls, etc.).
            return {
                1: {'id': 1, 'username': 'alice', 'role': 'admin'},
                2: {'id': 2, 'username': 'bob', 'role': 'boss'},
                3: {'id': 3, 'username': 'charlie', 'role': 'c-suite'},
            }

        # Wrap the function in a data provider.
        # Note that DataProvider is a generic, so we can also specify the type
        # for keys (``int``) and their corresponding values (``dict``).
        dp: DataProvider[int, dict] = DataProvider(get_users_by_id)

        # Before we can execute the query, we have to tell the data provider
        # which keys we'll be using to load the data.
        dp.register([1, 2, 3])

        # Now we can pull out individual rows from the bulk query.
        self.assertDictEqual(
            dp[1],
            {'id': 1, 'username': 'alice', 'role': 'admin'},
        )

        self.assertDictEqual(
            dp[2],
            {'id': 2, 'username': 'bob', 'role': 'boss'},
        )

        self.assertDictEqual(
            dp[3],
            {'id': 3, 'username': 'charlie', 'role': 'c-suite'},
        )


class CustomisedDataProviderTestCase(TestCase):
    """
    Tests various aspects of data provider implementations (effectively acts as
    a test case for :py:class:`BaseDataProvider`).
    """

    def test_computed_keys(self):
        """
        The data provider uses different keys for loading and caching.
        """

        class TestDataProvider(BaseDataProvider):
            def gen_load_key(self, key):
                # Use profession to load data from the backend.
                return key['profession']

            def gen_cache_key(self, key):
                # Cache results by last name.
                return key['lastName']

            def fetch_from_backend(self, load_keys):
                # This roughly simulates a scenario where we have to hit a
                # different backend depending on the load key.
                # For example, the load key could be the name of the R function
                # to invoke, the name of the database or collection to execute
                # the query against, etc.
                for lk in load_keys:
                    method = getattr(self, 'get_{job}s'.format(job=lk), None)
                    if method:
                        for key, data in method().items():
                            yield key, data

            def gen_empty_result(self):
                return {'firstName': '*unknown*'}

            @staticmethod
            def get_historians():
                return {
                    'Brody': {'firstName': 'Marcus'},
                    'Jones': {'firstName': 'Henry'},
                }

            @staticmethod
            def get_nazi_stooges():
                return {
                    'Belloq': {'firstName': 'René'},
                    'Donovan': {'firstName': 'Walter'},
                }

        users = [
            {'lastName': 'Jones', 'profession': 'historian'},
            {'lastName': 'Brody', 'profession': 'historian'},
            {'lastName': 'Belloq', 'profession': 'nazi_stooge'},
            {'lastName': 'Donovan', 'profession': 'nazi_stooge'},

            # The backend won't return any data for this user.
            {'lastName': 'Ravenwood', 'profession': 'adventurer'},
        ]

        data_provider = TestDataProvider()
        data_provider.register(users)

        for user_data in users:
            user_data.update(data_provider[user_data])

        self.assertDictEqual(
            users[0],

            {
                'firstName': 'Henry',
                'lastName': 'Jones',
                'profession': 'historian',
            },
        )

        self.assertDictEqual(
            users[1],

            {
                'firstName': 'Marcus',
                'lastName': 'Brody',
                'profession': 'historian',
            },
        )

        self.assertDictEqual(
            users[2],

            {
                'firstName': 'René',
                'lastName': 'Belloq',
                'profession': 'nazi_stooge',
            },
        )

        self.assertDictEqual(
            users[3],

            {
                'firstName': 'Walter',
                'lastName': 'Donovan',
                'profession': 'nazi_stooge',
            },
        )

        self.assertDictEqual(
            users[4],

            {
                # See :py:meth:`TestDataProvider.gen_empty_result` above.
                'firstName': '*unknown*',

                'lastName': 'Ravenwood',
                'profession': 'adventurer',
            },
        )

    def test_load_key_null(self):
        """
        A value has a null load key.
        """

        class TestDataProvider(BaseDataProvider):
            def gen_load_key(self, key):
                if key == 'bravo':
                    return None
                return key

            def fetch_from_backend(self, load_keys):
                return {
                    # Include data for ``bravo`` in the result, just to make
                    # sure that we aren't cheating.
                    'alpha': {'firstName': 'Henry'},
                    'bravo': {'firstName': 'Marcus'},
                }

            def gen_empty_result(self):
                return {}

        users = ['alpha', 'bravo']

        data_provider = TestDataProvider()
        data_provider.register(users)

        self.assertDictEqual(data_provider['alpha'], {'firstName': 'Henry'})

        # The load key for ``bravo`` is null, so the data provider does not
        # return any data for this key, even though technically the backend
        # did.
        self.assertDictEqual(data_provider['bravo'], {})

    def test_cache_key_null(self):
        """
        A value has a null cache key.
        """

        class TestDataProvider(BaseDataProvider):
            def gen_load_key(self, key):
                return key['lastName']

            def gen_cache_key(self, key):
                if key['profession'] == 'nazi_stooge':
                    return None

                return key['lastName']

            def gen_empty_result(self):
                return {}

            def fetch_from_backend(self, load_keys):
                return {
                    # Include data for Nazi stooges in the result, just to make
                    # sure that we aren't cheating.
                    'Jones': {'firstName': 'Henry'},
                    'Belloq': {'firstName': 'René'},
                }

        users = [
            # Control Group
            {'lastName': 'Jones', 'profession': 'historian'},
            {'lastName': 'Belloq', 'profession': 'archaeologist'},

            # Experimental Group
            {'lastName': 'Belloq', 'profession': 'nazi_stooge'},
        ]

        data_provider = TestDataProvider()
        data_provider.register(users)

        # The first two users generate a non-null cache key, so the data
        # provider returns data for them.
        self.assertDictEqual(data_provider[users[0]], {'firstName': 'Henry'})
        self.assertDictEqual(data_provider[users[1]], {'firstName': 'René'})

        # The third user has a non-null load key, so the data provider was able
        # to *load* data for it.  But, it has a null cache key, so the data
        # provider can't *return* any data for it.
        self.assertDictEqual(data_provider[users[2]], {})


class MutableDataProviderTestCase(TestCase):
    """
    Tests various aspects of mutable data provider implementation (effectively
    acts as a test case for :py:class:`MutableDataProviderMixin`).
    """

    def test_add_arbitrary_value(self):
        """
        Adding an arbitrary value to the data provider's cache.
        """

        class TestDataProvider(MutableDataProviderMixin, BaseDataProvider):
            def fetch_from_backend(self, load_keys):
                return {
                    'alpha': {'firstName': 'Henry'},
                    'bravo': {'firstName': 'Marcus'},
                }

        users = ['alpha', 'bravo']

        data_provider = TestDataProvider()
        data_provider.register(users)

        # If we try to get data for an unregistered value, we get an exception
        # as normal.
        with self.assertRaises(ValueError):
            # noinspection PyStatementEffect
            data_provider['charlie']

        # However, if we specify a cache value explicitly, then we can retrieve
        # it - even if we haven't loaded anything yet.
        data_provider['charlie'] = {'firstName': 'Sallah'}

        self.assertDictEqual(
            data_provider['charlie'],
            {'firstName': 'Sallah'},
        )

        # We can override this value any time we want to.
        data_provider['charlie'] = {'firstName': 'Marion'}

        self.assertDictEqual(
            data_provider['charlie'],
            {'firstName': 'Marion'},
        )

        # Other values continue to work as expected.
        self.assertDictEqual(
            data_provider['alpha'],
            {'firstName': 'Henry'},
        )

        with self.assertRaises(ValueError):
            # noinspection PyStatementEffect
            data_provider['delta']

    def test_override_backend_value(self):
        """
        Overriding data returned by the backend.
        """

        class TestDataProvider(MutableDataProviderMixin, BaseDataProvider):
            def fetch_from_backend(self, load_keys):
                return {
                    'alpha': {'firstName': 'Henry'},
                    'bravo': {'firstName': 'Marcus'},
                }

        users = ['alpha', 'bravo']

        data_provider = TestDataProvider()
        data_provider.register(users)

        # Specify an explicit cache value for ``bravo``.
        data_provider['bravo'] = {'firstName': 'Sallah'}

        # Explicitly invoke the data provider's backend.
        data_provider.warm_cache()

        # The backend cannot replace an overridden value.
        self.assertDictEqual(
            data_provider['bravo'],
            {'firstName': 'Sallah'},
        )

        # But we can override it any time we want.
        data_provider['bravo'] = {'firstName': 'Marion'}

        self.assertDictEqual(
            data_provider['bravo'],
            {'firstName': 'Marion'},
        )

        # Other values continue to work as expected.
        self.assertDictEqual(
            data_provider['alpha'],
            {'firstName': 'Henry'},
        )

        with self.assertRaises(ValueError):
            # noinspection PyStatementEffect
            data_provider['delta']
