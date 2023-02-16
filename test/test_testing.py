from unittest import TestCase

from data_providers.testing import MockDataProvider


class MockDataProviderTestCase(TestCase):
    def test_happy_path(self):
        """
        Typical usage of :py:class:`MockDataProvider`.
        """
        users = {
            'alpha': {},
            'bravo': {},
            'charlie': {},
            'delta': {},
        }

        data_provider = MockDataProvider({
            # Note that the backend will not return any data for ``delta``.
            'alpha': {'firstName': 'Henry'},
            'bravo': {'firstName': 'Henry'},
            'charlie': {'firstName': 'Marcus'},
        })

        # You can't get any data until you've registered the corresponding
        # values.
        with self.assertRaises(ValueError):
            # noinspection PyStatementEffect
            data_provider['alpha']

        data_provider.register(users.keys())

        for username, user_data in users.items():
            user_data.update(data_provider[username])

        self.assertDictEqual(users['alpha'], {'firstName': 'Henry'})
        self.assertDictEqual(users['bravo'], {'firstName': 'Henry'})
        self.assertDictEqual(users['charlie'], {'firstName': 'Marcus'})

        # The backend didn't return any data for ``delta``.
        self.assertDictEqual(users['delta'], {})
