
from diskcache import Cache
import os
import hashlib
import json

# Define cache directory
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".openbb_cache")

# Initialize Cache
# Size limit: 1GB
# Eviction policy: Least Recently Used (LRU) is default
cache = Cache(CACHE_DIR, size_limit=1024 * 1024 * 1024)

def _generate_key(func_name, **kwargs):
    """Generate a unique deterministic key for function calls."""
    # Sort keys to ensure consistent order
    key_str = f"{func_name}:" + json.dumps(kwargs, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()

def get_from_cache(func_name, **kwargs):
    """Retrieve result from cache if exists."""
    key = _generate_key(func_name, **kwargs)
    return cache.get(key)

def set_to_cache(value, func_name, expire=3600*24, **kwargs):
    """Save result to cache. Default expiry: 24 hours."""
    key = _generate_key(func_name, **kwargs)
    cache.set(key, value, expire=expire)

def clear_cache():
    """Clear the entire cache."""
    cache.clear()
