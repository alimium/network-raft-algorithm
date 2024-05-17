import redis
import redis_om as rom


class LogEntry(rom.HashModel):
    term: int
    index: int
    command: str

    class Meta:
        global_key_prefix = "raft"
        model_key_prefix: str = "logs"
        index_name = "log_entry"


class RedisClient:
    def __init__(self) -> None:
        self.client = redis.StrictRedis(host="localhost", port=6379, db=0)

    def append_log(self, node: int, term: int, index: int, command: str):
        entry = LogEntry(term=term, index=index, command=command)
        entry.save()
        self.client.lpush(f"raft:logs:{node}", entry.pk)
        self.client.save()

    def get_log(self, node: int):
        entry_pk = self.client.lindex(f"raft:logs:{node}", 0)
        return LogEntry.get(entry_pk)
