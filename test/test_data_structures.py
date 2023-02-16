from typing import Dict, List, Text
from unittest import TestCase, mock

from data_providers.data_structures import ParameterizedDefaultDict


class ParameterizedDefaultDictTestCase(TestCase):
    @staticmethod
    def test_no_params():
        """
        The factory only receives the missing key when it is invoked.
        """
        factory = mock.Mock(return_value=[])

        d = ParameterizedDefaultDict(factory)  # type: Dict[Text, List]

        d['foo'].append('bar')
        d['foo'].append('baz')
        d['foobie'].append('bletch')

        factory.assert_has_calls([
            mock.call('foo'),
            mock.call('foobie'),
        ])

    @staticmethod
    def test_with_params():
        """
        Specifying additional params to pass to the factory.
        """
        factory = mock.Mock(return_value=[])

        d = ParameterizedDefaultDict(
            factory,

            # Additional positional arguments.
            'alpha',
            'bravo',

            # Additional keyword arguments.
            charlie='delta',
            echo='foxtrot',
        )  # type: Dict[Text, List]

        d['foo'].append('bar')
        d['foo'].append('baz')
        d['foobie'].append('bletch')

        factory.assert_has_calls([
            mock.call('foo', 'alpha', 'bravo', charlie='delta',
                echo='foxtrot'),
            mock.call('foobie', 'alpha', 'bravo', charlie='delta',
                echo='foxtrot'),
        ])
