from data_providers import BaseDataProvider

__all__ = [
    'MockDataProvider',
]


class MockDataProvider(BaseDataProvider):
    """
    A data provider that "loads" data from a dict stored in memory.

    This class is generally only used during unit tests.
    """

    def __init__(self, data):
        """
        :param data:
            Data used to seed the "backend".

            Usually, this is a list of dicts (simulates the result of a SQL
            query, data frame from an R function, etc.).
        """
        super(MockDataProvider, self).__init__()

        self._data = data

    def fetch_from_backend(self, load_keys):
        # If a load key does not appear in :py:attr:`_data`, do not return any
        # data for it.  This allows us to simulate that specific case during
        # unit tests.
        return (
            (lk, self._data[lk])
            for lk in load_keys
            if lk in self._data
        )

    def gen_empty_result(self):
        return {}
