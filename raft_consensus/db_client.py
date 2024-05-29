import time
import logging
import redis
import redis_om as rom


class LogEntry(rom.HashModel):
    term: int
    index: int  # Added index field
    command: str

    class Meta:
        global_key_prefix = "raft"
        model_key_prefix: str = "logs"
        index_name = "log_entry"


class RedisClient:
    def __init__(self) -> None:
        self.pool = redis.BlockingConnectionPool(
            timeout=None,
            host="log-database",
            port=6379,
            username="",
            password="",
        )

    def get_connection(self):
        r = redis.StrictRedis(connection_pool=self.pool)
        retry = 0
        if not r.ping() and retry < 10:
            logging.error(
                f"Redis Server is not running. Attempting to reconnect {retry+1}..."
            )
            retry += 1
            time.sleep(1)
            r = redis.StrictRedis(connection_pool=self.pool)
        if retry == 10:
            raise redis.exceptions.ConnectionError("Redis Server is not running.")

        return r

    def append_log(self, node: str, term: int, index: int, command: str):
        r = self.get_connection()
        entry = LogEntry(term=term, index=index, command=command)
        entry._meta.database = r
        entry.save()
        r.lpush(f"raft:logs:{node}", entry.pk)
        r.save()

    def get_log(self, node: str):
        r = self.get_connection()
        entry_pk = r.lindex(f"raft:logs:{node}", 0)
        if entry_pk is None:
            return None
        return LogEntry.get(entry_pk)
