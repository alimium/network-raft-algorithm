import logging

import grpc

from .grpc_types.raft_node_pb2_grpc import RaftNodeStub


def connectoin_factory(nodes: list):
    connections = {}
    for node in nodes:
        connections[node] = RaftNodeStub(grpc.insecure_channel("localhost:" + node))
    return connections
