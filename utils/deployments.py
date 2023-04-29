import json
from pathlib import Path

import app.constants as constants


def load(network: str) -> dict:
    json_path = get_deployed_contracts_json_path(network)
    with open(json_path, "r") as f:
        return json.load(f)


def save(data: dict, network: str):
    json_path = get_deployed_contracts_json_path(network)
    if not json_path.parent.exists():
        json_path.parent.mkdir()

    with open(json_path, "w") as f:
        json.dump(data, f)


def get_deployed_contracts_json_path(network: str) -> Path:
    return Path(constants.DEPLOYED_CONTRACTS_JSON_DIR) / Path(
        network
    ).with_suffix(".json")


def camel_to_snake(camel_str):
    snake_str = ""
    for i, char in enumerate(camel_str):
        if char.isupper():
            if i > 0 and camel_str[i - 1].islower():
                snake_str += "_"
            if i < len(camel_str) - 1 and camel_str[i + 1].islower():
                snake_str += char.lower()
            else:
                snake_str += char
        else:
            snake_str += char
    return snake_str.lower()
