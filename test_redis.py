import redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    print("Attempting to ping Redis...")
    response = r.ping()
    print(f"Redis ping response: {response}")
except Exception as e:
    print(f"Error connecting to Redis: {e}")
