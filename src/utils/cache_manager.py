import redis
import json
import pickle
from typing import Any, Optional
from datetime import timedelta
from src.config.settings import settings
from src.utils.logger import logger

class CacheManager:
    """Redis cache manager for storing temporary data"""
    
    def __init__(self):
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=False
            )
            self.redis_client.ping()
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using in-memory cache.")
            self.redis_client = None
            self._memory_cache = {}
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: int = None
    ) -> bool:
        """
        Set a value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        
        Returns:
            Success status
        """
        if ttl is None:
            ttl = settings.CACHE_TTL
        
        try:
            if self.redis_client:
                serialized = pickle.dumps(value)
                self.redis_client.setex(key, ttl, serialized)
            else:
                self._memory_cache[key] = value
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None
        """
        try:
            if self.redis_client:
                data = self.redis_client.get(key)
                if data:
                    return pickle.loads(data)
            else:
                return self._memory_cache.get(key)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache"""
        try:
            if self.redis_client:
                self.redis_client.delete(key)
            else:
                self._memory_cache.pop(key, None)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            if self.redis_client:
                return self.redis_client.exists(key) > 0
            else:
                return key in self._memory_cache
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        try:
            if self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
            else:
                count = 0
                keys_to_delete = [k for k in self._memory_cache.keys() if pattern in k]
                for key in keys_to_delete:
                    self._memory_cache.pop(key, None)
                    count += 1
                return count
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")
            return 0
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter"""
        try:
            if self.redis_client:
                return self.redis_client.incrby(key, amount)
            else:
                current = self._memory_cache.get(key, 0)
                self._memory_cache[key] = current + amount
                return self._memory_cache[key]
        except Exception as e:
            logger.error(f"Cache increment error: {e}")
            return None
    
    def set_hash(self, key: str, mapping: dict, ttl: int = None) -> bool:
        """Set a hash in cache"""
        try:
            if self.redis_client:
                self.redis_client.hset(key, mapping=mapping)
                if ttl:
                    self.redis_client.expire(key, ttl)
            else:
                self._memory_cache[key] = mapping
            return True
        except Exception as e:
            logger.error(f"Cache set hash error: {e}")
            return False
    
    def get_hash(self, key: str) -> Optional[dict]:
        """Get a hash from cache"""
        try:
            if self.redis_client:
                return self.redis_client.hgetall(key)
            else:
                return self._memory_cache.get(key)
        except Exception as e:
            logger.error(f"Cache get hash error: {e}")
            return None

# Global cache instance
cache = CacheManager()
