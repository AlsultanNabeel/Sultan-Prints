from functools import wraps
from flask import request, make_response
import redis
import json
from datetime import datetime, timedelta

redis_client = redis.Redis(host='localhost', port=6379, db=1)

def cache_page(timeout=3600):
    """
    Cache decorator for Flask views
    timeout: cache timeout in seconds (default: 1 hour)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip cache for logged-in users
            if 'user_id' in request.cookies:
                return f(*args, **kwargs)
            
            # Create cache key from request path and query string
            cache_key = f"page:{request.path}:{request.query_string.decode()}"
            
            # Try to get cached response
            cached = redis_client.get(cache_key)
            if cached:
                response = make_response(cached.decode())
                response.headers['X-Cache'] = 'HIT'
                return response
            
            # Get fresh response
            response = f(*args, **kwargs)
            
            # Cache only successful responses
            if response.status_code == 200:
                redis_client.setex(
                    cache_key,
                    timeout,
                    response.get_data()
                )
                response.headers['X-Cache'] = 'MISS'
            
            return response
        return decorated_function
    return decorator

def clear_cache(pattern="page:*"):
    """Clear cache entries matching pattern"""
    for key in redis_client.scan_iter(pattern):
        redis_client.delete(key)

def cache_data(key, data, timeout=3600):
    """Cache arbitrary data with timeout"""
    redis_client.setex(key, timeout, json.dumps(data))

def get_cached_data(key):
    """Retrieve cached data"""
    data = redis_client.get(key)
    return json.loads(data) if data else None

class QueryCache:
    """Cache for database queries"""
    
    @staticmethod
    def get_or_set(key, query_func, timeout=300):
        """Get cached query results or execute query and cache"""
        cached = redis_client.get(f"query:{key}")
        if cached:
            return json.loads(cached)
        
        # Execute query
        result = query_func()
        
        # Cache result
        redis_client.setex(
            f"query:{key}",
            timeout,
            json.dumps(result)
        )
        
        return result
    
    @staticmethod
    def invalidate(pattern="query:*"):
        """Invalidate query cache entries"""
        for key in redis_client.scan_iter(pattern):
            redis_client.delete(key) 