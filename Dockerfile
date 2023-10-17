FROM ubuntu:latest
RUN apt-get update && apt-get install -y python3 python3 pip
RUN pip install grpcio==1.58.0 grpcio-tools==1.58.0
RUN pip3 install torch==2.0.1 --index-url https://download.pytorch.org/whl/cpu
RUN pip3 install numpy
COPY server.py .
COPY modelserver_pb2_grpc.py .
COPY modelserver_pb2.py .
CMD ["python3", "server.py"]

