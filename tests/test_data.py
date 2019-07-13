import pytest
from tests.utils import parse, get_part_data


def test_parse_data():
    data = get_part_data()
    for region in data:
        part_data = data[region]
        results = parse(part_data, multithreading=False)
        for result in results:
            assert result is not None
