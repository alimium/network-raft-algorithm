import redis
import redis_om as rom

@dataclass
class LogEntry(rom.HashModel):
    term: int
    index: int  # Added index field
    command: str
    pk: Optional[str] = None

    class Meta:
        global_key_prefix = "raft"
        model_key_prefix: str = "logs"
        index_name = "log_entry"

    def save(self):
        if not self.pk:
            self.pk = f"{self.term}:{self.index}"
        client = redis.StrictRedis(host="localhost", port=6379, db=0)
        client.hset(self.pk, mapping={"term": self.term, "index": self.index, "command": self.command})
        client.save()

    @classmethod
    def get(cls, pk: str):
        client = redis.StrictRedis(host="localhost", port=6379, db=0)
        data = client.hgetall(pk)
        if not data:
            return None
        return cls(term=int(data[b'term']), index=int(data[b'index']), command=data[b'command'].decode('utf-8'), pk=pk)
    

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

