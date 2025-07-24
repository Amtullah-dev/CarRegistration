import grpc
from concurrent import futures
import logging

from car_registration.grpc import car_service_pb2
from car_registration.grpc import car_service_pb2_grpc
from car_registration.tasks.car_tasks.sync_car_data_task import sync_car_data_task

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CarServicer(car_service_pb2_grpc.CarServiceServicer):
    def SyncCarData(self, request, context):
        logger.info(f"Received sync request: {request.request_id}")

        task = sync_car_data_task.delay()

        logger.info(f"Task {task.id} dispatched to Celery")

        return car_service_pb2.SyncResponse(
            status="queued",
            cars=[],
            total_count=0
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    car_service_pb2_grpc.add_CarServiceServicer_to_server(CarServicer(), server)
    listen_addr = '[::]:50051'
    server.add_insecure_port(listen_addr)

    logger.info(f"Starting gRPC server on {listen_addr}")
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
