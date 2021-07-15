import argparse
import itertools
import sqlite3
from datetime import datetime
from functools import partial
from multiprocessing import Pool
from typing import Tuple, Set

from diskcache import Cache
from tqdm import tqdm

from pcpartpicker_scraper.mappings import part_classes
from pcpartpicker_scraper.parser import Parser
from pcpartpicker_scraper.scraper import Scraper
from pcpartpicker_scraper.serialization import dataclass_to_dict, dataclass_from_dict


def scrape_part_region_combo(chromedriver: str, html_cache: str, parts: Tuple[str, str]):
    part = parts[0]
    region = parts[1]
    scraper = Scraper(chromedriver)
    cache = Cache(html_cache)

    part_data = scraper.get_part_data(region, part)
    stored_parts = cache[region]
    stored_parts.update({part: part_data})
    cache[region] = stored_parts
    print(f"finished with {region}/{part}")


def scrape_part_data(parse_args):
    supported_parts: Set[str] = {"cpu", "cpu-cooler", "motherboard", "memory", "internal-hard-drive",
                                 "video-card", "power-supply", "case", "case-fan", "fan-controller",
                                 "thermal-paste", "optical-drive", "sound-card", "wired-network-card",
                                 "wireless-network-card", "monitor", "external-hard-drive", "headphones",
                                 "keyboard", "mouse", "speakers", "ups"}

    supported_regions: Set[str] = {"au", "be", "ca", "de", "es", "fr", "se",
                                   "in", "ie", "it", "nz", "uk", "us"}

    cache = Cache(parse_args.html_cache)

    if "timestamp" in cache:
        timestamp = cache["timestamp"]
        if datetime.now().month > timestamp.month:
            cache.clear()
            cache["timestamp"] = datetime.now()
            print("Clearing cache...")
    else:
        cache.clear()
        cache["timestamp"] = datetime.now()
        print("Clearing cache...")

    for region in supported_regions:
        if region not in cache:
            cache[region] = {}

    products_to_scrape = list(itertools.product(supported_parts, supported_regions))
    total_to_scrape = len(products_to_scrape)
    products_to_scrape = list(filter(lambda x: x[0] not in cache[x[1]], products_to_scrape))
    pool = Pool(parse_args.parallel)

    print(
        f"About to scrape {len(products_to_scrape)}/{total_to_scrape} part+region combos that are not cached using {parse_args.parallel} "
        f"concurrent requests")

    map_func = partial(scrape_part_region_combo, parse_args.chromedriver, parse_args.html_cache)

    pool.map(map_func, products_to_scrape)


def parse_part_data(parse_args):
    db_connection = sqlite3.connect(parse_args.database)
    cache = Cache(parse_args.html_cache)

    for region in tqdm(cache):
        if region == "timestamp":
            continue
        part_data = cache[region]
        for part, part_data in part_data.items():
            manufacturers, parts = part_data
            parser = Parser(region, part, manufacturers)
            pparts = parser.parse(parts)

            data_to_dict = [dataclass_to_dict(item) for item in pparts]

            # Verify that the dataclasses are legit
            dataclass_data = [dataclass_from_dict(part_classes[part], item) for item in data_to_dict]

            formatted_part_name = part.replace("-", "_")

            db_connection.execute(f"drop table if exists {region}_{formatted_part_name};")
            db_connection.execute(f"create table if not exists {region}_{formatted_part_name} (part text);")
            db_connection.executemany(f"insert into {region}_{formatted_part_name} values(?);", data_to_dict)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape pcpartpicker.com')
    parser.add_argument('--database', type=str, help="Determine the database to serialize the data to.")
    parser.add_argument('--chromedriver', type=str)
    parser.add_argument('--html_cache', type=str)
    parser.add_argument('--parallel', '-P', default=1, type=int, metavar='N', help="Scrape up to N pages concurrently")

    args = parser.parse_args()
    scrape_part_data(args)
    parse_part_data(args)
