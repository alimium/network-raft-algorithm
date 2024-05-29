import logging

import grpc

from .grpc_types.raft_node_pb2_grpc import RaftNodeStub


def connectoin_factory(nodes: list) -> dict[str, RaftNodeStub]:
    connections = {}
    for node in nodes:
        no = (int(node) % 50031) / 10
        no = int(no)
        stub = RaftNodeStub(
            grpc.insecure_channel(
                f"raft-node-{no}:" + node, options=(("grpc.enable_http_proxy", 0),)
            )
        )
        connections[node] = stub
    return connections
