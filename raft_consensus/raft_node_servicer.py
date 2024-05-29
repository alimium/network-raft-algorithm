import logging

import grpc._channel
from .grpc_types.raft_node_pb2_grpc import RaftNodeServicer, RaftNodeStub
from .grpc_types.raft_node_pb2 import (
    RequestVoteRequest,
    RequestVoteResponse,
    AppendEntriesRequest,
    AppendEntriesResponse,
)
from .raft_node_client_factory import connectoin_factory
from .db_client import RedisClient
from dataclasses import dataclass
from typing import List, Optional
import threading
import time
import grpc
import random
from concurrent.futures import ThreadPoolExecutor


class RaftNodeServicerImpl(RaftNodeServicer):
    def __init__(self, node_id: str, peers: List[str], db_client: RedisClient):
        self.node_id = node_id  # The ID of this node
        self.peers = peers  # List of peer node IDs
        self.peer_stubs = connectoin_factory(self.peers)  # gRPC stubs for peers
        self.current_term = -1  # Current term of the node
        self.current_leader = None  # ID of the current leader
        self.db_client = db_client  # Redis client for log operations
        self.voted_for = (
            None  # ID of the candidate this node voted for in the current term
        )
        self.commit_index = 0  # Index of the highest log entry known to be committed
        self.last_applied = (
            0  # Index of the highest log entry applied to the state machine
        )

        self.state = (
            "follower"  # The current state of the node (follower, candidate, or leader)
        )
        self.votes_received = (
            0  # Number of votes received in the current term (used in candidate state)
        )

        # Election timeout is randomized to avoid split votes
        self.election_timeout = random.uniform(20.0, 30.0)
        self.heartbeat_interval = 1  # Interval for sending heartbeats

        self.heartbeat_timer = None
        # self.heartbeat_timer = threading.Timer(
        #     interval=self.heartbeat_interval, function=self.send_heartbeats
        # )  # Timer for sending heartbeats
        # self.election_timer = threading.Timer(
        #     interval=self.election_timeout, function=self.start_election
        # )  # Timer for starting an election
        self.election_timer = None

        logging.info(str(self))
        logging.info(f"Raft Node {self.node_id} Initialized.")

    def __str__(self) -> str:
        config = "=============================\n"
        config += f'{"Node No.:":<20}{self.node_id}\n'
        config += f'{"Election Timeout:":<20}{self.election_timeout}\n'
        config += f'{"Heartbeat Interval:":<20}{self.heartbeat_interval}\n'
        config += f'{"Peers:":<20}{", ".join(list(self.peer_stubs.keys()))}\n'
        config += "======================================="
        return config

    def reset_election_timeout(self):
        # Reset the election timeout timer
        if self.election_timer:
            self.election_timer = self.election_timer.cancel()
            logging.info("Election timer stopped.")
        if self.state != "leader":
            self.election_timer = threading.Timer(
                interval=self.election_timeout, function=self.start_election
            )  # Timer for starting an election
            self.election_timer.start()
            logging.info("Election timer started.")

    def start_election(self):
        # Wait for all nodes to come to life in initialization phase
        if self.current_term == -1:
            all_ready = 0
            request = AppendEntriesRequest(term=self.current_term)
            while all_ready < len(self.peers):
                all_ready = 0
                for peer in self.peers:
                    try:
                        response = self.peer_stubs[peer].AppendEntries(request)
                        if response.success:
                            all_ready += 1
                    except grpc._channel._InactiveRpcError as e:
                        logging.warning(
                            f"Node {peer} is not ready. ({e.__class__.__name__})"
                        )
                        break
                time.sleep(2)
            self.current_term = 0

        # Transition to candidate state and start an election
        self.current_term += 1
        self.state = "candidate"
        self.voted_for = self.node_id  # Vote for self
        self.votes_received = 1  # Vote for self
        self.reset_election_timeout()

        last_log = self.db_client.get_log(self.node_id)
        last_log_index = last_log.index if last_log else -1
        last_log_term = last_log.term if last_log else 0

        # Send RequestVote RPCs to all peers
        for peer in self.peers:
            request = RequestVoteRequest(
                term=self.current_term,
                candidate_id=int(self.node_id),
                last_log_index=last_log_index,
                last_log_term=last_log_term,
            )
            # threading.Thread(
            #     target=self.send_request_vote, args=(peer, request)
            # ).start()
            self.send_request_vote(peer, request)

    def send_request_vote(self, peer, request: RequestVoteRequest):
        # Simulate network call to send the vote request
        logging.info(f"Sending RequestVote to {peer}")
        response = self.peer_stubs[peer].RequestVote(request)
        self.handle_vote_response(response)

    def handle_vote_response(self, response: RequestVoteResponse):
        # Handle the response to a vote request
        if response.term > self.current_term:
            # If the response term is higher, update term and revert to follower
            self.current_term = response.term
            self.state = "follower"
            self.voted_for = None
            self.reset_election_timeout()

        elif response.vote_granted:
            # If the vote is granted, increment the count
            self.votes_received += 1
            if self.votes_received > len(self.peers) // 2:
                # If majority is reached, become the leader
                self.become_leader()

    def become_leader(self):
        # Transition to leader state and start sending heartbeats
        self.state = "leader"
        self.current_leader = self.node_id
        self.reset_election_timeout()
        self.ping()

    def ping(self):
        self.send_heartbeats()
        self.heartbeat_timer = threading.Timer(
            interval=self.heartbeat_interval, function=self.pong
        )  # Timer for sending heartbeats
        self.heartbeat_timer.start()

    def pong(self):
        self.send_heartbeats()
        self.heartbeat_timer = threading.Timer(
            interval=self.heartbeat_interval, function=self.ping
        )  # Timer for sending heartbeats
        self.heartbeat_timer.start()

    def send_heartbeats(self):
        # Send heartbeats (empty AppendEntries RPCs) to all peers
        logging.info(
            f"Node is the leader. Term: {self.current_term}. Sending heartbeats..."
        )
        for peer in self.peers:
            prev_log = self.db_client.get_log(self.node_id)
            request = AppendEntriesRequest(
                term=self.current_term,
                leader_id=int(self.node_id),
                prev_log_index=prev_log.index if prev_log else -1,
                prev_log_term=prev_log.term if prev_log else 0,
                entries=[],  # No new entries, just a heartbeat
                leader_commit=self.commit_index,
            )
            # threading.Thread(
            # target=self.send_append_entries, args=(peer, request)
            # ).start()
            self.send_append_entries(peer, request)

    def send_append_entries(self, peer, request: AppendEntriesRequest):
        # Simulate network call to send the append entries request

        response = self.peer_stubs[peer].AppendEntries(request, None)
        self.handle_append_entries_response(response)

    def handle_append_entries_response(self, response: AppendEntriesResponse):
        # Handle the response to an append entries request
        if response.term > self.current_term:
            # If the response term is higher, update term and revert to follower
            self.current_term = response.term
            self.state = "follower"
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
            self.state = "follower"
            self.reset_election_timeout()  # Reset election timeout

        if (
            self.voted_for is None or self.voted_for == request.candidate_id
        ) and self.is_log_up_to_date(request):
            # If not voted yet or voted for the candidate, and candidate's log is up-to-date, grant vote
            self.voted_for = request.candidate_id
            self.reset_election_timeout()
            return RequestVoteResponse(term=self.current_term, vote_granted=True)

        return RequestVoteResponse(term=self.current_term, vote_granted=False)

    def is_log_up_to_date(self, request: RequestVoteRequest) -> bool:
        # Check if the candidate's log is up-to-date
        last_log = self.db_client.get_log(self.node_id)
        last_log_index = last_log.index if last_log else -1
        last_log_term = last_log.term if last_log else 0
        if request.last_log_term > last_log_term:
            return True
        if (
            request.last_log_term == last_log_term
            and request.last_log_index >= last_log_index
        ):
            return True
        return False

    def AppendEntries(
        self, request: AppendEntriesRequest, context
    ) -> AppendEntriesResponse:
        # Handle incoming AppendEntries RPC
        if request.term == -1:
            # If the nodes are in initialization phase, return success
            return AppendEntriesResponse(term=self.current_term, success=True)
        if request.term < self.current_term:
            # If the request term is lower, reject the append entries
            return AppendEntriesResponse(term=self.current_term, success=False)

        if request.term > self.current_term:
            # If the request term is higher, update term and revert to follower
            self.current_term = request.term
            self.state = "follower"
            self.current_leader = request.leader_id
            self.voted_for = None
            self.reset_election_timeout()  # Reset election timeout

        # Validate the previous log index and term
        last_log = self.db_client.get_log(self.node_id)
        if request.prev_log_index >= 0 and (
            last_log is None
            or last_log.index < request.prev_log_index
            or last_log.term != request.prev_log_term
        ):
            return AppendEntriesResponse(term=self.current_term, success=False)

        # Append any new entries not already in the log
        for i, entry in enumerate(request.entries):
            existing_entry = self.db_client.get_log(self.node_id)
            if (
                existing_entry
                and existing_entry.index == request.prev_log_index + 1 + i
                and existing_entry.term != entry.term
            ):
                self.db_client.get_connection().ltrim(
                    f"raft:logs:{self.node_id}", 0, request.prev_log_index + i
                )
            self.db_client.append_log(
                self.node_id, entry.term, request.prev_log_index + 1 + i, entry.command
            )

        # Update commit index if leader_commit is greater
        if request.leader_commit > self.commit_index:
            self.commit_index = min(
                request.leader_commit, self.db_client.get_log(self.node_id).index
            )

        return AppendEntriesResponse(term=self.current_term, success=True)
