import json
import random
import time
from typing import List, Set

import lxml.html
from .part_data import PartData
from selenium import webdriver
from tqdm import tqdm
from .parser import find_products


class Scraper:
    supported_parts: Set[str] = {"cpu", "cpu-cooler", "motherboard", "memory", "internal-hard-drive",
                                 "video-card", "power-supply", "case", "case-fan", "fan-controller",
                                 "thermal-paste", "optical-drive", "sound-card", "wired-network-card",
                                 "wireless-network-card", "monitor", "external-hard-drive", "headphones",
                                 "keyboard", "mouse", "speakers", "ups"}

    supported_regions: Set[str] = {"au", "be", "ca", "de", "es", "fr", "se",
                                   "in", "ie", "it", "nz", "uk", "us"}
    current_region = None
    browser = None

    def __init__(self, executable_path: str):
        self.executable_path = executable_path

    def retrieve_all_html(self):
        all_data = {}
        for region in tqdm(self.supported_regions):
            self.current_region = region
            region_data = {}
            for part in tqdm(self.supported_parts):
                part_url = self.generate_part_url(part)
                part_data = self.get_part_data(part_url)
                region_data.update({region: part_data})
            all_data.update({region: region_data})
        with open("all_data.json", "wb") as file:
            json.dump(all_data, file, indent=4)

    def generate_part_url(self, part: str) -> str:
        return f"{self.base_url}{part}"

    def get_part_data(self, url: str) -> PartData:
        driver = self.get_driver()
        driver.get(url)
        products = []
        manufacturers = get_manufacturers(driver)
        while True:
            products.extend(find_products(driver.page_source))
            if not get_next_page(driver):
                break
        return PartData(manufacturers, products)

    @property
    def base_url(self):
        if not self.current_region == "us":
            return f"https://{self.current_region}.pcpartpicker.com/products/"
        return "https://pcpartpicker.com/products/"

    def get_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        return webdriver.Chrome(options=options, executable_path=self.executable_path)


def get_manufacturers(driver: webdriver.Chrome) -> List[str]:
    html = lxml.html.fromstring(driver.page_source)
    time.sleep(1)
    show_more = driver.execute_script("""return document.querySelector("#m_set > a.moreless.moreless-show")""")
    center_element(driver, show_more)
    time.sleep(1)
    click(driver, show_more)
    time.sleep(1)
    manufacturers = html.xpath('//*[@id="m_set"]/li[contains(@id, "li_")]/label/text()')
    return manufacturers


def center_element(driver, element) -> None:
    driver.execute_script("""arguments[0].scrollIntoView({
                behavior: 'auto',
                block: 'center',
                inline: 'center'
            });""", element)


def click(driver, element) -> None:
    driver.execute_script("""arguments[0].click();""", element)


def get_next_page(driver) -> bool:
    page_list = driver.execute_script("""return document.querySelector("#module-pagination > ul")""")
    time.sleep(1)
    center_element(driver, page_list)
    time.sleep(1)
    current_page_button = page_list.find_elements_by_xpath('//li/a[@class="pagination--current"]')[0]
    current_page = int(current_page_button.text)
    next_page_button = page_list.find_elements_by_xpath(f'//li/a[text()={current_page+1}]')
    if next_page_button:
        click(driver, next_page_button[0])
        time.sleep(3)
        return True
    else:
        return False

