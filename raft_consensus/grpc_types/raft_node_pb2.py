# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: raft_node.proto
# Protobuf Python Version: 5.26.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0fraft_node.proto\x12\traft_node\"\xa3\x01\n\x14\x41ppendEntriesRequest\x12\x0c\n\x04term\x18\x01 \x01(\x05\x12\x11\n\tleader_id\x18\x02 \x01(\x05\x12\x16\n\x0eprev_log_index\x18\x03 \x01(\x05\x12\x15\n\rprev_log_term\x18\x04 \x01(\x05\x12$\n\x07\x65ntries\x18\x05 \x03(\x0b\x32\x13.raft_node.LogEntry\x12\x15\n\rleader_commit\x18\x06 \x01(\x05\"6\n\x15\x41ppendEntriesResponse\x12\x0c\n\x04term\x18\x01 \x01(\x05\x12\x0f\n\x07success\x18\x02 \x01(\x08\"g\n\x12RequestVoteRequest\x12\x0c\n\x04term\x18\x01 \x01(\x05\x12\x14\n\x0c\x63\x61ndidate_id\x18\x02 \x01(\x05\x12\x16\n\x0elast_log_index\x18\x03 \x01(\x05\x12\x15\n\rlast_log_term\x18\x04 \x01(\x05\"9\n\x13RequestVoteResponse\x12\x0c\n\x04term\x18\x01 \x01(\x05\x12\x14\n\x0cvote_granted\x18\x02 \x01(\x08\"8\n\x08LogEntry\x12\x0c\n\x04term\x18\x01 \x01(\x05\x12\r\n\x05index\x18\x02 \x01(\x05\x12\x0f\n\x07\x63ommand\x18\x03 \x01(\t2\xb0\x01\n\x08RaftNode\x12T\n\rAppendEntries\x12\x1f.raft_node.AppendEntriesRequest\x1a .raft_node.AppendEntriesResponse\"\x00\x12N\n\x0bRequestVote\x12\x1d.raft_node.RequestVoteRequest\x1a\x1e.raft_node.RequestVoteResponse\"\x00\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'raft_node_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_APPENDENTRIESREQUEST']._serialized_start=31
  _globals['_APPENDENTRIESREQUEST']._serialized_end=194
  _globals['_APPENDENTRIESRESPONSE']._serialized_start=196
  _globals['_APPENDENTRIESRESPONSE']._serialized_end=250
  _globals['_REQUESTVOTEREQUEST']._serialized_start=252
  _globals['_REQUESTVOTEREQUEST']._serialized_end=355
  _globals['_REQUESTVOTERESPONSE']._serialized_start=357
  _globals['_REQUESTVOTERESPONSE']._serialized_end=414
  _globals['_LOGENTRY']._serialized_start=416
  _globals['_LOGENTRY']._serialized_end=472
  _globals['_RAFTNODE']._serialized_start=475
  _globals['_RAFTNODE']._serialized_end=651
# @@protoc_insertion_point(module_scope)
