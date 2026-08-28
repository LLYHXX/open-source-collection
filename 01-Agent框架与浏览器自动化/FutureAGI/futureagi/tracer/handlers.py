from opentelemetry.proto.collector.trace.v1 import trace_service_pb2_grpc

from tracer.services.grpc import ObservationSpanService


def grpc_handlers(server):
    servicer = ObservationSpanService.as_servicer()
    trace_service_pb2_grpc.add_TraceServiceServicer_to_server(servicer, server)
