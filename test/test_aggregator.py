from itertools import chain
from unittest import TestCase

from data_providers.aggregator import BaseDataProviderAggregator
from data_providers.testing import MockDataProvider


class MovieLineDataProvider(MockDataProvider):
    """
    Data provider that will be used to test
    :py:class:`BaseDataProviderAggregator`.
    """

    def gen_load_key(self, value):
        return value['lastName']

    def gen_empty_result(self):
        return []


class MovieLineAggregator(BaseDataProviderAggregator):
    """
    Trivial data provider aggregator implementation that assembles movie lines
    spoken by celebrities from a variety of sources.

    Used to test :py:class:`BaseDataProviderAggregator`.
    """

    def aggregate_data(self, value, data):
        return list(chain(*data.values()))

    def create_data_providers(self):
        # Simulate a scenario where we are loading movie lines from different
        # sources depending on which movie they come from.
        return {
            # Maybe we have all the lines from Brazil stored in a local
            # database; I'm sure somebody does, anyway.
            'brazil':
                MovieLineDataProvider({
                    'Pryce': [
                        'Triplets? My how time flies.',
                        "It's my lunch hour. Besides, it's not my department.",
                    ],

                    'De Niro': [
                        "Listen, kid, we're all in it together.",
                        'My good friends call me Harry.',
                    ],
                }),

            # Perhaps we hit a 3rd-party web service to download lines from
            # Taxi Driver.
            'taxiDriver':
                MovieLineDataProvider({
                    'De Niro': [
                        "You're only as healthy as you feel.",
                    ],

                    'Keitel': [
                        "You're a funny guy - but looks aren't everything.",
                    ],
                }),
        }

    def gen_routing_keys(self, value):
        if value['lastName'] in {'De Niro', 'Pryce'}:
            yield 'brazil'

        if value['lastName'] in {'De Niro', 'Keitel'}:
            yield 'taxiDriver'


class DataProviderAggregatorTestCase(TestCase):
    def test_happy_path(self):
        """
        Typical usage of a data provider aggregator.
        """
        jonathan = {'firstName': 'Jonathan', 'lastName': 'Pryce'}
        harvey = {'firsName': 'Harvey', 'lastName': 'Keitel'}
        robert = {'firstName': 'Robert', 'lastName': 'De Niro'}

        aggregator = MovieLineAggregator()
        aggregator.register([jonathan, harvey, robert])

        self.assertEqual(
            aggregator[jonathan],

            [
                'Triplets? My how time flies.',
                "It's my lunch hour. Besides, it's not my department.",
            ],
        )

        self.assertEqual(
            aggregator[harvey],

            [
                "You're a funny guy - but looks aren't everything.",
            ],
        )

        self.assertEqual(
            aggregator[robert],

            # Results from multiple data providers are aggregated.
            [
                "Listen, kid, we're all in it together.",
                'My good friends call me Harry.',
                "You're only as healthy as you feel.",
            ],
        )
