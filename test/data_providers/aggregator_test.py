# coding=utf-8
from __future__ import absolute_import, division, print_function, \
    unicode_literals

from unittest import TestCase

from itertools import chain
from six import itervalues

from data_providers.aggregator import BaseDataProviderAggregator
from data_providers.testing import MockDataProvider

__all__ = [
    'DataProviderAggregatorTestCase',
]


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
    Trivial data provider aggregator implementation that assembles
    movie lines spoken by famous celebrities from a variety of sources.

    Used to test :py:class:`BaseDataProviderAggregator`.
    """
    def aggregate_data(self, value, data):
        return list(chain(*itervalues(data)))

    def create_data_providers(self):
        # Simulate a scenario where we are loading movie lines from
        # different sources depending on which movie they come from.
        # noinspection SpellCheckingInspection
        return {
            # Maybe we have all of the lines from Brazil stored in a
            # local database.
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

            # Perhaps we hit a 3rd-party web service to download lines
            # from Taxi Driver.
            'taxiDriver':
                MovieLineDataProvider({
                    'De Niro': [
                        "You're only as healthy as you feel.",
                    ],

                    'Keitel': [
                        "You're a funny guy - but looks aren't everything.",
                    ],
                })
        }

    def gen_routing_keys(self, value):
        # noinspection SpellCheckingInspection
        if value['lastName'] in {'De Niro', 'Pryce'}:
            yield 'brazil'

        # noinspection SpellCheckingInspection
        if value['lastName'] in {'De Niro', 'Keitel'}:
            yield 'taxiDriver'


class DataProviderAggregatorTestCase(TestCase):
    def test_happy_path(self):
        """
        Typical usage of a data provider aggregator.
        """
        jonathan = {'firstName': 'Jonathan', 'lastName': 'Pryce'}
        # noinspection SpellCheckingInspection
        harvey = {'firsName': 'Harvey', 'lastName': 'Keitel'}
        # noinspection SpellCheckingInspection
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
