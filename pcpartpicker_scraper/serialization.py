from dataclasses import is_dataclass, asdict
from moneyed import Money
from decimal import Decimal
from dacite import from_dict, Config


def dataclass_to_dict(dataclass) -> dict:
    if not is_dataclass(dataclass):
        raise RuntimeError
    fields = asdict(dataclass)
    result = {}
    for field, data in fields.items():
        if isinstance(data, Money):
            result.update({field: [str(data.amount), data.currency.code]})
        else:
            result.update({field: data})
    return result


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
