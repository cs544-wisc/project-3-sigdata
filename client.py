import grpc
import modelserver_pb2
import modelserver_pb2_grpc
import sys
import csv
import threading

#grab args
port = int(sys.argv[1])
coefs = sys.argv[2]
csvs = sys.argv[3:]
coefs = [float(x) for x in coefs.split(",")]
#connect to channel
channel = grpc.insecure_channel(f"127.0.0.1:{port}")
stub = modelserver_pb2_grpc.ModelServerStub(channel)
stub.SetCoefs(modelserver_pb2.SetCoefsRequest(coefs=coefs))

lock = threading.Lock()
hit = total = 0
def worker(csv_file):
    global hit
    global total
    with open(csv_file, 'r') as file:
        for line in file:
            x = [float(z) for z in line.split(",")]
            response = stub.Predict(modelserver_pb2.PredictRequest(X=x))
            with lock:
                #check if hit or not
                total += 1
                if response.error != '':
                    continue
                else:
                    if response.hit:
                        hit += 1

#create threads using worker func as target
threads = [threading.Thread(target=worker, args=[file]) for file in csvs]
for thread in threads:
    thread.start()

#join
for thread in threads:
    thread.join()

print(hit/total)
