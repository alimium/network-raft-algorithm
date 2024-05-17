from .grpc_types.raft_node_pb2_grpc import RaftNodeServicer
from .grpc_types.raft_node_pb2 import (
    RequestVoteRequest,
    RequestVoteResponse,
    AppendEntriesRequest,
    AppendEntriesResponse,
)

from .db_client import RedisClient
from dataclasses import dataclass
from typing import List, Optional
import threading
import time
import random

#TODO: intergeate redis 

class RaftNodeServicerImpl(RaftNodeServicer):
    def __init__(self, redis_client: RedisClient) -> None:
        self._redis_client = redis_client

    def RequestVote(self, request: RequestVoteRequest, context) -> RequestVoteResponse:
        pass

    def AppendEntries(
        self, request: AppendEntriesRequest, context
    ) -> AppendEntriesResponse:
        pass

# Data class representing a log entry in the Raft algorithm
@dataclass
class LogEntry:
    term: int
    command: str

# Data class representing a RequestVote RPC request
@dataclass
class RequestVoteRequest:
    term: int
    candidate_id: int
    last_log_index: int
    last_log_term: int

# Data class representing a RequestVote RPC response
@dataclass
class RequestVoteResponse:
    term: int
    vote_granted: bool

# Data class representing an AppendEntries RPC request
@dataclass
class AppendEntriesRequest:
    term: int
    leader_id: int
    prev_log_index: int
    prev_log_term: int
    entries: List[LogEntry]
    leader_commit: int

# Data class representing an AppendEntries RPC response
@dataclass
class AppendEntriesResponse:
    term: int
    success: bool

class RaftNodeServicerImpl(RaftNodeServicer):
    def __init__(self, node_id: int, peers: List[int], db_client: RedisClient):
        self.node_id = node_id  # The ID of this node
        self.peers = peers  # List of peer node IDs
        self.current_term = 0  # Current term of the node
        self.db_client = db_client  # Redis client for log operations
        self.voted_for = None  # ID of the candidate this node voted for in the current term
        self.log = []  # The log entries for this node
        self.commit_index = 0  # Index of the highest log entry known to be committed
        self.last_applied = 0  # Index of the highest log entry applied to the state machine

        self.state = 'follower'  # The current state of the node (follower, candidate, or leader)
        self.votes_received = 0  # Number of votes received in the current term (used in candidate state)

        # Election timeout is randomized to avoid split votes
        self.election_timeout = random.uniform(1.0, 2.0)
        self.heartbeat_interval = 0.5  # Interval for sending heartbeats

        self.reset_election_timeout()  # Initialize the election timeout
        self.heartbeat_timer = None  # Timer for sending heartbeats

    def reset_election_timeout(self):
        # Reset the election timeout timer
        if hasattr(self, 'election_timer'):
            self.election_timer.cancel()
        self.election_timer = threading.Timer(self.election_timeout, self.start_election)
        self.election_timer.start()

    def start_election(self):
        # Transition to candidate state and start an election
        self.state = 'candidate'
        self.current_term += 1  # Increment the term
        self.voted_for = self.node_id  # Vote for self
        self.votes_received = 1  # Vote for self

        self.reset_election_timeout()  # Reset the election timeout

        # Send RequestVote RPCs to all peers
        for peer in self.peers:
            request = RequestVoteRequest(
                term=self.current_term,
                candidate_id=self.node_id,
                last_log_index=len(self.log) - 1,
                last_log_term=self.log[-1].term if self.log else 0
            )
            threading.Thread(target=self.send_request_vote, args=(peer, request)).start()

    def send_request_vote(self, peer, request: RequestVoteRequest):
        # Simulate network call to send the vote request
        response = peer.RequestVote(request, None)
        self.handle_vote_response(response)

    def handle_vote_response(self, response: RequestVoteResponse):
        # Handle the response to a vote request
        if response.term > self.current_term:
            # If the response term is higher, update term and revert to follower
            self.current_term = response.term
            self.state = 'follower'
            self.voted_for = None
            self.reset_election_timeout()
            return

        if response.vote_granted:
            # If the vote is granted, increment the count
            self.votes_received += 1
            if self.votes_received > len(self.peers) // 2:
                # If majority is reached, become the leader
                self.become_leader()

    def become_leader(self):
        # Transition to leader state and start sending heartbeats
        self.state = 'leader'
        self.heartbeat_timer = threading.Timer(self.heartbeat_interval, self.send_heartbeats)
        self.heartbeat_timer.start()

    def send_heartbeats(self):
        # Send heartbeats (empty AppendEntries RPCs) to all peers
        for peer in self.peers:
            request = AppendEntriesRequest(
                term=self.current_term,
                leader_id=self.node_id,
                prev_log_index=len(self.log) - 1,
                prev_log_term=self.log[-1].term if self.log else 0,
                entries=[],  # No new entries, just a heartbeat
                leader_commit=self.commit_index
            )
            threading.Thread(target=self.send_append_entries, args=(peer, request)).start()

    def send_append_entries(self, peer, request: AppendEntriesRequest):
        # Simulate network call to send the append entries request
        response = peer.AppendEntries(request, None)
        self.handle_append_entries_response(response)

    def handle_append_entries_response(self, response: AppendEntriesResponse):
        # Handle the response to an append entries request
        if response.term > self.current_term:
            # If the response term is higher, update term and revert to follower
            self.current_term = response.term
            self.state = 'follower'
            self.voted_for = None
            self.reset_election_timeout()
            if self.heartbeat_timer:
                self.heartbeat_timer.cancel()
            return

    def RequestVote(self, request: RequestVoteRequest, context) -> RequestVoteResponse:
        # Handle incoming RequestVote RPC
        if request.term < self.current_term:
            # If the request term is lower, reject the vote
            return RequestVoteResponse(term=self.current_term, vote_granted=False)

        if request.term > self.current_term:
            # If the request term is higher, update term and revert to follower
            self.current_term = request.term
            self.voted_for = None
            self.state = 'follower'

        if (self.voted_for is None or self.voted_for == request.candidate_id) and self.is_log_up_to_date(request):
            # If not voted yet or voted for the candidate, and candidate's log is up-to-date, grant vote
            self.voted_for = request.candidate_id
            self.reset_election_timeout()
            return RequestVoteResponse(term=self.current_term, vote_granted=True)

        return RequestVoteResponse(term=self.current_term, vote_granted=False)

    def is_log_up_to_date(self, request: RequestVoteRequest) -> bool:
        # Check if the candidate's log is up-to-date
        last_log_index = len(self.log) - 1
        last_log_term = self.log[-1].term if self.log else 0
        if request.last_log_term > last_log_term:
            return True
        if request.last_log_term == last_log_term and request.last_log_index >= last_log_index:
            return True
        return False

    def AppendEntries(self, request: AppendEntriesRequest, context) -> AppendEntriesResponse:
        # Handle incoming AppendEntries RPC
        if request.term < self.current_term:
            # If the request term is lower, reject the append entries
            return AppendEntriesResponse(term=self.current_term, success=False)

        if request.term > self.current_term:
            # If the request term is higher, update term and revert to follower
            self.current_term = request.term
            self.state = 'follower'
            self.voted_for = None

        self.reset_election_timeout()  # Reset election timeout

        # Validate the previous log index and term
        if request.prev_log_index >= 0 and (len(self.log) <= request.prev_log_index or self.log[request.prev_log_index].term != request.prev_log_term):
            return AppendEntriesResponse(term=self.current_term, success=False)

        # Append any new entries not already in the log
        for i, entry in enumerate(request.entries):
            if len(self.log) > request.prev_log_index + 1 + i:
                if self.log[request.prev_log_index + 1 + i].term != entry.term:
                    self.log = self.log[:request.prev_log_index + 1 + i]  # Delete conflicting entry
            self.log.append(entry)  # Append new entry

        # Update commit index if leader_commit is greater
        if request.leader_commit > self.commit_index:
            self.commit_index = min(request.leader_commit, len(self.log) - 1)

        return AppendEntriesResponse(term=self.current_term, success=True)
