from pcpartpicker import parse_utils
from pcpartpicker.part_data import PartData

from tests.utils import get_part_data


def test_parse_data():
    data = get_part_data()
    for region in data.values():
        part_data = PartData()
        results = parse_utils.parse(region)
        for part, parts in results.items():
            part_data[part] = parts
        for part_type, parts in part_data.items():
            for part in parts:
                assert part.brand is not None
        assert part_data.to_json() is not None
