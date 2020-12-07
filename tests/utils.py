import json
import re
from decimal import Decimal
from multiprocessing import Pool
from os import scandir, path
import os
from typing import Tuple, Dict

from dacite import from_dict, Config
from moneyed import Money

from pcpartpicker_scraper.mappings import part_classes


def dataclass_from_dict(datatype, dictionary: dict):
    result = {}
    for field, data in dictionary.items():
        if isinstance(data, list):
            if not len(data) == 2 or not isinstance(data[0], str) or not isinstance(data[1], str):
                raise RuntimeError
            money = Money(Decimal(data[0]), data[1])
            result.update({field: money})
        else:
            result.update({field: data})
    dataclass = from_dict(datatype, result, config=Config(check_types=False))
    return dataclass


def deserialize_part_data(part_data: Tuple[str, str]) -> list:
    body = re.findall('<body>(.*?)</body>', part_data[1], re.DOTALL)[0].strip().lstrip()
    deserialized_parts = json.loads(body)
    return [dataclass_from_dict(part_classes[part_data[0]], item) for item in deserialized_parts]


def get_part_data() -> Dict[str, Dict[str, str]]:
    region_data = {}
    docs_path = "docs"
    with scandir(path=docs_path) as curdir:
        for region in curdir:
            # jekyll theme filter
            if not os.path.isdir(region):
                continue
            part_data = {}
            with scandir(path=path.join(docs_path, region.name)) as regiondir:
                for part in regiondir:
                    with open(path.join(docs_path, region.name, part.name), "r+") as file:
                        file_contents = file.read()
                        filename, _ = path.splitext(path.join(docs_path, region.name, part.name))
                        part_data[path.basename(filename)] = file_contents
            region_data[region.name] = part_data
    return region_data


def parse(part_dict: Dict[str, str], multithreading: bool = True) -> Dict[str, list]:
    if multithreading:
        with Pool() as pool:
            results = pool.map(deserialize_part_data, (item for item in part_dict.items()))
    else:
        results = [deserialize_part_data(item) for item in part_dict.items()]
    return dict(zip(part_dict.keys(), results))


