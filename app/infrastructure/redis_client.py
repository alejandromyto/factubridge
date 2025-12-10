from redis import Redis

# Instancia global reutilizable en toda la app
redis_client = Redis(host="redis", port=6379, db=0, decode_responses=True)
