import torch
from threading import Lock
import modelserver_pb2_grpc, modelserver_pb2
import grpc
from concurrent import futures
class PredictionCache:
    def __init__(self):
        self.coefs = None
        self.CAPACITY = 10
        self.cache = {}
        self.lock = Lock()

    def SetCoefs(self, coefs):
        with self.lock:
            self.cache = {} #reset cache
            coefs = torch.tensor(coefs)
            self.coefs = coefs

    def Predict(self, X):
        #round X first
        X = torch.round(X, decimals = 4)
        #flatten into tuple
        key = tuple(X.flatten().tolist())
        hit = False
        with self.lock:
            if key in self.cache: #hit occurs
                hit = True
                #update to most recently used, put at bottom by removing and adding
                y = X @ self.coefs
                self.cache.pop(key)
                self.cache[key] = y
            else: #no hit but must check size
                y = X @ self.coefs
                if len(self.cache) == self.CAPACITY:
                    #remove LRU from top of dict then add new item
                    del self.cache[next(iter(self.cache))]
                #add new item
                self.cache[key] = y
        return y, hit

class ModelServer(modelserver_pb2_grpc.ModelServerServicer):
    def __init__(self):
        self.cache = PredictionCache()

    def SetCoefs(self, request, context):
        try:
            coefs = torch.tensor(request.coefs)
            self.cache.SetCoefs(request.coefs)
            return modelserver_pb2.SetCoefsResponse(error='')
        except Exception as e:
            return modelserver_pb2.SetCoefsResponse(error=str(e))

    def Predict(self, request, context):
        try:
            X = torch.tensor(request.X)
            y, hit = self.cache.Predict(X)
            return modelserver_pb2.PredictResponse(y=y, hit=hit, error = '')
        except Exception as e:
            print("Error thrown: ", e)
            return modelserver_pb2.PredictResponse(y=0.0, hit=False, error = str(e))

def main():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers = 4), options=(('grpc.so_reuseport',0),))
    modelserver_pb2_grpc.add_ModelServerServicer_to_server(ModelServer(),server)
    server.add_insecure_port('[::]:5440')
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    main()

