from typing import Dict, Set, Callable

from moneyed import USD, AUD, CAD, EUR, NZD, SEK, GBP, INR
from pcpartpicker.mappings import part_classes
from pcpartpicker.parts import Bytes, ClockSpeed

byte_classes: Dict[str, Callable] = {"GB": Bytes.from_gb, "TB": Bytes.from_tb, "MB": Bytes.from_mb,
                                     "KB": Bytes.from_kb, "PB": Bytes.from_pb}

currency_symbols: Dict[str, str] = {"us": "$", "au": "$", "ca": "$", "be": "€", "de": "€", "es": "€", "fr": "€",
                                    "ie": "€", "it": "€", "nl": "€", "nz": "$", "se": "kr", "uk": "£", "in": "₹"}

currency_classes: Dict[str, object] = {"us": USD, "au": AUD, "ca": CAD, "be": EUR, "de": EUR, "es": EUR, "fr": EUR,
                                       "ie": EUR, "it": EUR, "nl": EUR, "nz": NZD, "se": SEK, "uk": GBP, "in": INR}

clockspeeds: Dict[str, Callable] = {"GHz": ClockSpeed.from_ghz, "MHz": ClockSpeed.from_mhz}

none_symbols: Set[str] = {"-", "N/A", "None"}
