import time
import json
import pickle
import bz2
import sys

from diskcache import Cache
from tqdm import tqdm

from pcpartpicker_scraper import Parser
from pcpartpicker_scraper import Scraper
from pcpartpicker_scraper.serialization import dataclass_to_dict, dataclass_from_dict
from pcpartpicker_scraper.parse_utils import tokenize
from pcpartpicker_scraper.mappings import part_classes


def scrape_part_data():
    supported_parts = {"cpu", "cpu-cooler", "motherboard", "memory", "internal-hard-drive",
                       "video-card", "power-supply", "case", "case-fan", "fan-controller",
                       "thermal-paste", "optical-drive", "sound-card", "wired-network-card",
                       "wireless-network-card", "monitor", "external-hard-drive", "headphones",
                       "keyboard", "mouse", "speakers", "ups"}

    supported_regions = {"au", "be", "ca", "de", "es", "fr", "se",
                         "in", "ie", "it", "nz", "uk", "us"}

    scraper = Scraper("/usr/lib/chromium-browser/chromedriver")
    cache = Cache("/tmp/")
    cache.clear()
    regions_to_scrape = set()
    for region in supported_regions:
        if region in cache:
            region_data = cache[region]
            for part in supported_parts:
                if part not in region_data:
                    regions_to_scrape.add(region)
    for region in tqdm(regions_to_scrape):
        if region not in cache:
            cache[region] = {}
        for part in supported_parts:
            if part not in cache[region]:
                part_data = scraper.get_part_data(region, part)
                stored_parts = cache[region]
                stored_parts.update({part: part_data})
                cache[region] = stored_parts


def parse_part_data():
    cache = Cache("/tmp/")
    parsed_part_data = {}
    for region in tqdm(cache):
        parsed_parts = {}
        part_data = cache[region]
        for part, part_data in part_data.items():
            manufacturers, parts = part_data
            parser = Parser(region, part, manufacturers)
            pparts = parser.parse(parts)
            parsed_parts[part] = pparts
        parsed_part_data[region] = parsed_parts
    parsed_cache = Cache("/parsed/")
    parsed_cache["current"] = parsed_part_data


def create_json():
    all_data = {}
    cache = Cache("/parsed/")
    region_data = cache["current"]
    for region in tqdm(region_data):
        part_data = region_data[region]
        dict_data = {}
        for part, data in part_data.items():
            data_to_dict = [dataclass_to_dict(item) for item in data]
            dict_data.update({part: data_to_dict})
        all_data.update({region: dict_data})
    json_string = json.dumps(all_data).encode()
    compressed_string = bz2.compress(json_string, compresslevel=9)
    compressed_cache = Cache("/json/")
    compressed_cache["current"] = compressed_string


def deserialize_json():
    cache = Cache("/json/")
    compressed_json = cache["current"]
    json_string = bz2.decompress(compressed_json)
    data = json.loads(json_string.decode(encoding="utf8"))
    all_data = {}
    for region, region_data in tqdm(data.items()):
        deserialized_region_data = {}
        for part, data in region_data.items():
            deserialized_data = [dataclass_from_dict(part_classes[part], item) for item in data]
            deserialized_region_data.update({part: deserialized_data})
        all_data.update({region: deserialized_region_data})
    unserialized_cache = Cache("/deserialized_json/")
    unserialized_cache["current"] = all_data


def update_cache_format():
    cache = Cache("/tmp/")
    for region in cache:
        part_data = cache[region]
        for part in part_data:
            manufacturers, data = part_data[part]
            parts = [token for p in data for token in p]
            part_data[part] = manufacturers, parts
        cache[region] = part_data

    for region in cache:
        part_data = cache[region]
        for part in part_data:
            manufacturers, data = part_data[part]
            parts = list(tokenize(part, data))
            part_data[part] = manufacturers, parts
        cache[region] = part_data


def get_size():
    cache = Cache("/json/")
    data = cache["current"]
    return sys.getsizeof(data)


if __name__ == "__main__":
    deserialize_json()
