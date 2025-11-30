import typing as tp
import json

from decimal import Decimal

CUSTOM_KEY_TYPE = "__custom_key_type__"

CAST_TYPE: dict[str, tp.Callable[[str], tp.Any]] = {
    "int": int,
    "float": float,
    "decimal": Decimal,
}


def transform_typed_json(obj: tp.Any) -> tp.Any:
    if isinstance(obj, list):
        return list(map(transform_typed_json, obj))

    if isinstance(obj, dict):
        if CUSTOM_KEY_TYPE in obj:
            type_name = obj[CUSTOM_KEY_TYPE]
            if type_name not in CAST_TYPE:
                raise ValueError(f"Unsupported custom key type: {type_name}")

            cast = CAST_TYPE[type_name]
            new_dict = {}
            for key, value in obj.items():
                if key == CUSTOM_KEY_TYPE:
                    continue
                new_key = cast(key)
                new_dict[new_key] = transform_typed_json(value)

            return new_dict

        return {key: transform_typed_json(value) for key, value in obj.items()}

    return obj


def decode_typed_json(json_value: str) -> tp.Any:
    """
    Returns deserialized object from json string.
    Checks __custom_key_type__ in object's keys to choose appropriate type.

    :param json_value: serialized object in json format
    :return: deserialized object
    """
    parsed_json = json.loads(json_value)

    return transform_typed_json(parsed_json)
