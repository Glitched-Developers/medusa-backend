"""
Hash Utilities Module

This module provides fast hashing functionality for the Medusa Backend application
using xxHash algorithm for efficient change detection and data integrity verification.

Key Features:
- Fast xxHash3 128-bit hashing for performance
- Support for both string and dictionary inputs
- JSON serialization for consistent dictionary hashing
- Change detection for schedule updates
- Data integrity verification

The xxHash algorithm is chosen for its speed and collision resistance,
making it ideal for detecting changes in schedule data.
"""

import json
from typing import Union

from xxhash import xxh3_128_digest

# Reference: https://github.com/ifduyue/python-xxhash


def get_hash(data: Union[str, dict]) -> str:
    """
    Compute xxHash3 128-bit hash for input data.
    
    This function generates a fast, collision-resistant hash for change detection
    and data integrity verification. Dictionaries are serialized to JSON for
    consistent hashing across different object instances.
    
    Args:
        data (Union[str, dict]): Input data to hash. Dictionaries are automatically
                                serialized to JSON before hashing.
    
    Returns:
        str: Hexadecimal hash string (32 characters)
        
    Examples:
        >>> get_hash("test string")
        'a1b2c3d4e5f6...'
        >>> get_hash({"key": "value"})
        'f6e5d4c3b2a1...'
        
    Note:
        Dictionary serialization uses json.dumps() which may not preserve
        key order in older Python versions. For consistent results across
        versions, consider using sorted keys in input dictionaries.
    """
    if isinstance(data, dict):
        # Serialize dictionary to JSON for consistent hashing
        json_data = json.dumps(data, sort_keys=True)
        return xxh3_128_digest(json_data.encode('utf-8')).hex()

    # Hash string data directly
    return xxh3_128_digest(data.encode('utf-8')).hex()


def check_hash(data: Union[str, dict], hash_value: str) -> bool:
    """
    Verify if data matches the provided hash value.
    
    This function is used for change detection - comparing current data
    against a previously stored hash to determine if content has changed.
    Essential for efficient schedule update detection.
    
    Args:
        data (Union[str, dict]): Data to verify against hash.
                               Dictionaries are serialized to JSON.
        hash_value (str): Expected hash value in hexadecimal format.
    
    Returns:
        bool: True if data hash matches provided hash_value, False otherwise.
        
    Examples:
        >>> original_hash = get_hash("test data")
        >>> check_hash("test data", original_hash)
        True
        >>> check_hash("different data", original_hash)
        False
        
    Use Cases:
        - Schedule change detection
        - Cache validation
        - Data integrity verification
        - Avoiding unnecessary database updates
    """
    return get_hash(data) == hash_value
