import argparse
import itertools
import json
import os
import sqlite3
from multiprocessing import Pool
from pathlib import Path

from datetime import datetime

from diskcache import Cache
from tqdm import tqdm

from pcpartpicker_scraper.mappings import part_classes
from pcpartpicker_scraper.parser import Parser
from pcpartpicker_scraper.scraper import Scraper
from pcpartpicker_scraper.serialization import dataclass_to_dict, dataclass_from_dict


def scrape_part_region_combo(p):
    part = p[0]
    region = p[1]
    scraper = Scraper("/usr/lib/chromium-browser/chromedriver")
    cache = Cache("/tmp/pcpartpicker-cache/")

    part_data = scraper.get_part_data(region, part)
    stored_parts = cache[region]
    stored_parts.update({part: part_data})
    cache[region] = stored_parts
    print(f"finished with {region}/{part}")


def scrape_part_data(pool_size):
    supported_parts = {"cpu", "cpu-cooler", "motherboard", "memory", "internal-hard-drive",
                       "video-card", "power-supply", "case", "case-fan", "fan-controller",
                       "thermal-paste", "optical-drive", "sound-card", "wired-network-card",
                       "wireless-network-card", "monitor", "external-hard-drive", "headphones",
                       "keyboard", "mouse", "speakers", "ups"}

    supported_regions = {"au", "be", "ca", "de", "es", "fr", "se",
                         "in", "ie", "it", "nz", "uk", "us"}

    cache = Cache("/tmp/pcpartpicker-cache/")
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

    to_scrape = list(itertools.product(supported_parts, supported_regions))
    total_to_scrape = len(to_scrape)
    to_scrape = list(filter(lambda x: x[0] not in cache[x[1]], to_scrape))
    pool = Pool(pool_size)
    print(
        f"About to scrape {len(to_scrape)}/{total_to_scrape} part+region combos that are not cached using {pool_size} "
        f"concurrent requests")
    pool.map(scrape_part_region_combo, to_scrape)


def parse_part_data():
    cache = Cache("/tmp/pcpartpicker-cache/")

    parsed_part_data = {}
    for region in tqdm(cache):
        if region == "timestamp":
            continue
        parsed_parts = {}
        part_data = cache[region]
        for part, part_data in part_data.items():
            manufacturers, parts = part_data
            parser = Parser(region, part, manufacturers)
            pparts = parser.parse(parts)
            parsed_parts[part] = pparts
        parsed_part_data[region] = parsed_parts
    parsed_cache = Cache("/tmp/pcpartpicker-parsed/")
    parsed_cache["current"] = parsed_part_data


def write_to_database(database: str):
    db_connection = sqlite3.connect(database)
    cache = Cache("/tmp/pcpartpicker-parsed/")
    region_data = cache["current"]
    for region in tqdm(region_data):
        part_data = region_data[region]
        for part, data in part_data.items():
            data_to_dict = [dataclass_to_dict(item) for item in data]

            # Verify that the dataclasses are legit
            dataclass_data = [dataclass_from_dict(part_classes[part], item) for item in data_to_dict]

            formatted_part_name = part.replace("-", "_")

            db_connection.execute(f"create table if not exists {region}_{formatted_part_name} (part text);")
            db_connection.executemany(f"insert into {region}_{formatted_part_name} values(?);", data_to_dict)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape pcpartpicker.com')
    parser.add_argument('--database', type=str, help="Determine the database to serialize the data to.")
    parser.add_argument('--parallel', '-P', default=2, type=int, metavar='N', help="Scrape up to N pages concurrently")

    args = parser.parse_args()
    scrape_part_data(args.parallel)
    parse_part_data()
    write_to_database(args.database)
