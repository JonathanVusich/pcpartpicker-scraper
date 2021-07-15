import random
import time
from typing import List

import lxml.html
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait

from .parser import find_products


class Scraper:
    current_region = None
    browser = None

    def __init__(self, executable_path: str):
        self.executable_path = executable_path

    def get_part_data(self, region: str, part: str) -> tuple:
        try:
            base_url = generate_part_url(region, part)

            # For memory parts we want to add property that isn't readily available from the data-set: The type of
            # ECC support the memory module has For this purpose, we will query the memory URL 4 times, once per each
            # ECC option on the search page Every time we complete reading a result set, we will merge it to a
            # global/total list of memory modules, not before we populate a "fake" property indicating what ECC
            # support the module has:
            if part == "memory":
                urls = {
                    "Non-ECC / Unbuffered": base_url + "#E=0",
                    "Non-ECC / Registered": base_url + "#E=10",
                    "ECC / Unbuffered": base_url + "#E=1",
                    "ECC / Registered": base_url + "#E=11",
                }

                total_manufacturers_set = set()
                total_product_set = set()

                for ecc_type, url in urls.items():
                    # This will generate a result-set per ECC type
                    manufacturers, product_set = self.get_part_data_for_url(url)
                    # This will merge the manufacturer list from the per-ECC query back to the final
                    # list of manufacturers
                    total_manufacturers_set = total_manufacturers_set | set(manufacturers)
                    # Before we merge the per-ECC product list back with the global list,
                    # We have to add the ecc_type back to the tuple so that it would "appear" as if the scraped data
                    # had the ecc information embedded in it organically
                    product_set = set(map(lambda t: t[:-1] + (ecc_type,) + t[-1:], product_set))
                    # Merge the product list
                    total_product_set = total_product_set | set(product_set)

                # Finally, we return the memory manufacturer+product list as if they were 
                # all generated from a single scraping session
                return list(total_manufacturers_set), list(total_product_set)
            else:
                return self.get_part_data_for_url(base_url)
        except Exception:
            print(f"Failed to scrape {region}/{part}")
            raise

    def get_part_data_for_url(self, url: str) -> tuple:
        driver = self.get_driver()
        driver.get(url)
        manufacturers = get_manufacturers(driver)
        total_page_number = get_number_of_pages(driver)
        products = find_products(driver.page_source)

        if total_page_number == 1:
            driver.quit()
            return manufacturers, products
        else:
            page_numbers = set((x for x in range(2, total_page_number + 1)))
        previous_products = set(products)
        while len(page_numbers) > 0:
            new_page_num = random.sample(page_numbers, 1)[0]
            page_numbers.remove(new_page_num)
            new_url = generate_page_url_from_base(url, new_page_num)
            driver.get(new_url)
            start_refresh = time.perf_counter()
            while time.perf_counter() - start_refresh < 30:
                new_products = find_products(driver.page_source)
                if set(new_products) == previous_products:
                    time.sleep(3)
                else:
                    products.extend(new_products)
                    previous_products = set(new_products)
                    break
            else:
                raise TimeoutException
        driver.quit()
        product_set = list(set(products))
        return manufacturers, product_set

    def get_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--start-maximized")
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--incognito')
        driver = webdriver.Chrome(options=options, executable_path=self.executable_path)
        driver.set_script_timeout(300)
        driver.implicitly_wait(10)
        return driver


def get_manufacturers(driver: webdriver.Chrome) -> List[str]:
    html = lxml.html.fromstring(driver.page_source)
    try:
        show_more = WebDriverWait(driver, 10).until(lambda x: x.find_element_by_xpath('//*[@id="m_set"]/a[1]'))
        center_element(driver, show_more)
        click(driver, show_more)
    except TimeoutException:
        pass
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


def get_number_of_pages(driver) -> int:
    page_list = WebDriverWait(driver, 10).until(
        lambda x: x.find_elements_by_xpath('//*[@id="module-pagination"]/ul/li/a'))
    last_button = page_list[-1]
    return int(last_button.text)


def get_rand_float(amount: int) -> float:
    return random.uniform(amount, amount + 1)


def base_url(region: str):
    if not region == "us":
        return f"https://{region}.pcpartpicker.com/products"
    return "https://pcpartpicker.com/products"


def generate_part_url(region: str, part: str) -> str:
    return f"{base_url(region)}/{part}/"


def generate_page_url_from_base(url: str, page_number: int):
    if '#' in url:
        return f"{url}&page={page_number}"
    else:
        return f"{url}#page={page_number}"
