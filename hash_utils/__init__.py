import json

from xxhash import xxh3_128_digest

# https://github.com/ifduyue/python-xxhash

def get_hash(data: str or dict) -> str:
    """
    Computes a hash for the given string or dictionary using xxh3_128_digest.

    Args:
        data (str or dict): The input data to compute the hash for. If a dictionary is provided, it will be serialized to JSON.

    Returns:
        str: The hash value as a hexadecimal string.
    """
    if isinstance(data, dict):
        return xxh3_128_digest(json.dumps(data).encode('utf-8')).hex()

    return xxh3_128_digest(data.encode('utf-8')).hex()

def check_hash(data: str or dict, hash_value: str) -> bool:
    """
    Verifies whether the given string or dictionary matches the specified hash value.

    Args:
        data (str or dict): The input data to verify. If a dictionary is provided, it will be serialized to JSON.
        hash_value (str): The expected hash value to compare against.

    Returns:
        bool: True if the hash of the input data matches the provided hash value, otherwise False.
    """

    return get_hash(data) == hash_value
