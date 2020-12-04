import logging
import re
from typing import List, Tuple, Optional

import lxml.html
from moneyed import USD

from .mappings import currency_classes, currency_symbols, part_classes, \
    none_symbols
from .parse_utils import part_funcs
from .parts import *
from .utils import num_pattern

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARN)


class Parser:
    """Parser:

    This class is designed to parse raw html from PCPartPicker and to transform it into useful data objects.
    """

    currency_sign: str = "$"

    currency = USD

    region: str = "us"

    def __init__(self, region: str, part: str, manufacturers: List[str]) -> None:
        self.part = part
        self.region = region
        self.manufacturers = manufacturers
        self.currency_sign = currency_symbols[self.region]
        self.currency = currency_classes[self.region]

    def parse(self, parts: List[List[str]]):
        part_list = [self.parse_token(token) for token in parts]
        part_list.sort(key=lambda x: (x.brand, x.model if isinstance(x.model, str) else ""))
        return part_list

    def parse_token(self, data: list) -> object:
        """
        Hidden function that parses a list of data depending on the part type.

        :param part: str: The part type of the accompanying data.
        :param data: list: A list of the raw string data for the given part.
        :return: Object: Parsed data object.
        """

        brand, model = self.retrieve_brand_info(data[0])
        parsed_data = [brand, model]
        price = self.price(data[-1])
        tokens = data[1:-1]

        for x, token in enumerate(tokens):
            func = part_funcs[self.part][x]
            if func.__name__ == "hdd_data": # Handle special case of hdd_data input being None
                data = func(token)
                if data is None:
                    print(data)
                parsed_data.extend(data)
                continue
            elif func.__name__ == "price":  # Handle special case of price data being None
                parsed_data.append(self.price(token))
                continue
            else:
                if not token or token in none_symbols:
                    parsed_data.append(None)
                    continue

            try:
                result = func(token)
            except ValueError:
                result = func(token)
                result = None
            if isinstance(result, tuple):
                parsed_data.extend(result)
            else:
                parsed_data.append(result)

        parsed_data.append(price)

        _class = part_classes[self.part]
        try:
            return _class(*parsed_data)
        except (TypeError, ValueError) as _:
            logger.error(f"{parsed_data} is not valid input data for {_class}!")

    def price(self, price: str) -> Money:
        """
        Hidden function that retrieves the price from a raw string.

        :param price: str: Raw string containing currency amount and info.
        :return: Result: Money object extracted from the string.
        """

        if not price:
            return Money("0.00", self.currency)
        elif [x for x in self.currency_sign if x in price]:
            return Money(re.findall(num_pattern, price)[0], self.currency)

    def retrieve_brand_info(self, brand_information: str) -> Tuple[Optional[str], Optional[str]]:
        for x in range(len(brand_information) + 1):
            if brand_information[:x] in self.manufacturers:
                try:
                    next_char = brand_information[x]
                    if not next_char == " ":
                        continue
                    raise IndexError
                except IndexError:
                    brand = brand_information[:x].strip().lstrip()
                    model = brand_information[x:].strip().lstrip()
                    if not model:
                        return brand, None
                    else:
                        return brand, model


def find_products(html: str) -> list:
    html = lxml.html.fromstring(html)
    part_data = []
    elements = html.xpath('//*[@class="tr__product"]')
    for element in elements:
        element_data = element.xpath(
            './/*[@class="td__name"]/a/div[@class="td__nameWrapper"]/p | .//*[contains(@class, "td__spec")] | .//*[@class="td__price"]')
        part_data.append(parse_elements(element_data))
    return part_data


def parse_elements(elements: list) -> Tuple[Optional[str]]:
    text_elements: List[Optional[str]] = []
    for element in elements:
        text: str = element.xpath("text()")
        if not text:
            text_elements.append(None)
        elif len(text) == 1:
            text_elements.append(text[0])
        else:
            text_elements.append(" ".join(text))
    return tuple(text_elements)
