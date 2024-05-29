import os
import sys
import logging
from concurrent import futures

import grpc
from grpc_reflection.v1alpha import reflection

from .grpc_types import raft_node_pb2, raft_node_pb2_grpc

from .raft_node_servicer import RaftNodeServicerImpl

from .db_client import RedisClient


def serve():
    """Serving gRPC Server"""

    port = os.getenv("GRPC_PORT")
    if port is None:
        sys.exit("GRPC_PORT environment variable is not set")

    max_workers = os.getenv("GRPC_MAX_WORKERS")
    if max_workers is None:
        logging.warning(
            "GRPC_MAX_WORKERS not found in environment variables. Using default value..."
        )
        max_workers = 10

    raft_nodes = os.getenv("RAFT_NODES")
    if raft_nodes is None:
        sys.exit("RAFT_NODES environment variable is not set")
    raft_nodes = [node for node in raft_nodes.split(",") if node != port]

    redis_client = RedisClient()
    raft_node_servicer = RaftNodeServicerImpl(port, raft_nodes, redis_client)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=int(max_workers)))
    raft_node_pb2_grpc.add_RaftNodeServicer_to_server(raft_node_servicer, server)
    SERVICE_NAMES = (
        raft_node_pb2.DESCRIPTOR.services_by_name["RaftNode"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)
    no = (int(port) % 50031) / 10
    no = int(no)
    server.add_insecure_port(f"raft-node-{no}:" + port)
    server.start()
    logging.info("Server Started, listening on port %s", port)
    raft_node_servicer.reset_election_timeout()
    server.wait_for_termination()
