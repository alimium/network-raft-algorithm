from .grpc_types.raft_node_pb2_grpc import RaftNodeServicer
from .grpc_types.raft_node_pb2 import (
    RequestVoteRequest,
    RequestVoteResponse,
    AppendEntriesRequest,
    AppendEntriesResponse,
)

from .db_client import RedisClient


class RaftNodeServicerImpl(RaftNodeServicer):
    def __init__(self, redis_client: RedisClient) -> None:
        self._redis_client = redis_client

    def RequestVote(self, request: RequestVoteRequest, context) -> RequestVoteResponse:
        pass

    def AppendEntries(
        self, request: AppendEntriesRequest, context
    ) -> AppendEntriesResponse:
        pass
