from unittest import TestCase

from data_providers import MutableDataProviderMixin
from data_providers.delegate import BaseDataProviderDelegate, \
    MutableDataProviderDelegateMixin
from data_providers.testing import MockDataProvider


class ProfessionalDataProvider(MockDataProvider):
    """
    Template for :py:class:`TestDelegate`.
    """

    def gen_load_key(self, value):
        return value['lastName']

    def gen_empty_result(self):
        return {}


class TestDelegate(BaseDataProviderDelegate):
    """
    Data provider delegate used by :py:class:`DataProviderDelegateTestCase`.
    """

    def gen_delegate_key(self, value):
        return value['profession']

    def create_data_provider(self, profession):
        if profession == 'historian':
            return ProfessionalDataProvider({
                'Jones': {'firstName': 'Henry'},
                'Brody': {'firstName': 'Marcus'},
            })

        elif profession == 'nazi_stooge':
            return ProfessionalDataProvider({
                'Belloq': {'firstName': 'René'},
                'Donovan': {'firstName': 'Walter'},
            })

        raise ValueError(profession)


class MutableProfessionalDataProvider(
    # Mixin listed second so that it doesn't override MRO for subclass (it's
    # closer to the base class py:class:`BaseDataProvider` than
    # :py:class:`ProfessionalDataProvider` is).
    ProfessionalDataProvider,
    MutableDataProviderMixin,
):
    """
    Mutable version of :py:class:`ProfessionalDataProvider`.
    """
    pass


class TestMutableDelegate(
    # Mixin listed second so that it doesn't override MRO for subclass (it's
    # closer to the base class py:class:`BaseDataProvider` than
    # :py:class:`TestDelegate` is).
    TestDelegate,
    MutableDataProviderDelegateMixin,
):
    """
    Mutable version of :py:class:`TestDelegate`.
    """

    def create_data_provider(self, profession):
        if profession == 'historian':
            return MutableProfessionalDataProvider({
                'Jones': {'firstName': 'Henry'},
                'Brody': {'firstName': 'Marcus'},
            })

        elif profession == 'nazi_stooge':
            # Note that this data provider is not mutable.
            return ProfessionalDataProvider({
                'Belloq': {'firstName': 'René'},
                'Donovan': {'firstName': 'Walter'},
            })

        raise ValueError(profession)


class DataProviderDelegateTestCase(TestCase):
    """
    Tests various aspects of data provider delegate implementation (effectively
    acts as a test case for :py:class:`BaseDataProviderDelegate`).
    """

    def test_happy_path(self):
        """
        Typical usage of data provider delegate.
        """
        users = [
            {'lastName': 'Jones', 'profession': 'historian'},
            {'lastName': 'Brody', 'profession': 'historian'},
            {'lastName': 'Belloq', 'profession': 'nazi_stooge'},
            {'lastName': 'Donovan', 'profession': 'nazi_stooge'},
        ]

        # Delegates look and behave exactly like data providers.
        data_provider = TestDelegate()
        data_provider.register(users)

        for u in users:
            u.update(data_provider[u])

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

    def test_invalid_delegate_key(self):
        """
        A value cannot be matched with an appropriate data provider.
        """
        data_provider = TestDelegate()

        with self.assertRaises(ValueError):
            data_provider.register([
                # This value can't be registered because
                # :py:class:`TestDelegate` doesn't know which data provider to
                # use for the 'adventurer' profession.
                {'lastName': 'Ravenwood', 'profession': 'adventurer'},
            ])


class MutableDataProviderDelegateTestCase(TestCase):
    """
    Tests various aspects of mutable data provider delegate implementation
    (effectively acts as a test case for
    :py:class:`MutableDataProviderDelegateMixin`).
    """

    def test_add_arbitrary_values(self):
        """
        Adding arbitrary values to data provider caches.
        """
        users = [
            {'lastName': 'Brody', 'profession': 'historian'},
            {'lastName': 'Belloq', 'profession': 'nazi_stooge'},
        ]

        data_provider = TestMutableDelegate()
        data_provider.register(users)

        wild_card = {'lastName': 'Jones', 'profession': 'historian'}

        # If we try to get data for an unregistered value, we get an exception
        # as normal.
        with self.assertRaises(ValueError):
            # noinspection PyStatementEffect
            data_provider[wild_card]

        # However, if we specify a cache value explicitly, then we can retrieve
        # it - even if we haven't loaded anything yet.
        data_provider[wild_card] = {'firstName': 'Henry'}

        self.assertDictEqual(
            data_provider[wild_card],
            {'firstName': 'Henry'},
        )

        # We can override this value any time we want to.
        data_provider[wild_card] = {'firstName': 'Indiana'}

        self.assertDictEqual(
            data_provider[wild_card],
            {'firstName': 'Indiana'},
        )

        # Other values continue to work as expected.
        self.assertDictEqual(
            data_provider[users[0]],
            {'firstName': 'Marcus'},
        )

        with self.assertRaises(ValueError):
            # noinspection PyStatementEffect
            data_provider[{'lastName': 'Donovan', 'profession': 'nazi_stooge'}]

    def test_override_backend_values(self):
        """
        Overriding data returned by the backends.
        """
        users = [
            {'lastName': 'Jones', 'profession': 'historian'},
            {'lastName': 'Brody', 'profession': 'historian'},
        ]

        data_provider = TestMutableDelegate()
        data_provider.register(users)

        # I've got a lot of fond memories of that dog.
        data_provider[users[0]] = {'firstName': 'Indiana'}

        self.assertDictEqual(
            data_provider[users[0]],
            {'firstName': 'Indiana'},
        )

        # Other values continue to work as expected.
        self.assertDictEqual(
            data_provider[users[1]],
            {'firstName': 'Marcus'},
        )

        with self.assertRaises(ValueError):
            # noinspection PyStatementEffect
            data_provider[{'lastName': 'Donovan', 'profession': 'nazi_stooge'}]

    def test_immutable_data_provider(self):
        """
        Attempting to override a value for an immutable data provider.
        """
        data_provider = TestMutableDelegate()

        user = {'lastName': 'Belloq', 'profession': 'nazi_stooge'}

        # Note that :py:class:`TestMutableDelegate` uses an immutable data
        # provider for the "nazi_stooge" profession.
        with self.assertRaises(TypeError):
            data_provider[user] = {'firstName': 'René'}

    def test_invalid_delegate_key(self):
        """
        Attempting to override a value that cannot be matched with an
        appropriate data provider.
        """
        data_provider = TestMutableDelegate()

        # This value won't work because :py:class:`MutableTestDelegate` doesn't
        # know which data provider to use for the 'adventurer' profession.
        user = {'lastName': 'Ravenwood', 'profession': 'adventurer'}

        with self.assertRaises(ValueError):
            data_provider[user] = {'firstName': 'Marion'}
