import grpc
from car_registration.grpc import car_service_pb2
from car_registration.grpc import car_service_pb2_grpc
import time
import logging
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CarSyncClient:

    def __init__(self, server_address=Config.GRPC_SERVER_ADDRESS):
        self.channel = grpc.insecure_channel(server_address)
        grpc.channel_ready_future(self.channel).result(timeout=10)
        self.stub = car_service_pb2_grpc.CarServiceStub(self.channel)
        logger.info(f"Connected to gRPC server at {server_address}")

    def sync_car_data(self):
        request_id = f"req_{int(time.time())}"
        request = car_service_pb2.SyncRequest(request_id=request_id)

        try:
            logger.info(f"Client sending sync request: {request_id}")
            response = self.stub.SyncCarData(request)

            logger.info(f"Client received response status: {response.status}")
            logger.info(f"Client received total cars: {response.total_count}")

            return response

        except grpc.RpcError as e:
            logger.error(f"Client gRPC error: {e}")
            return None
