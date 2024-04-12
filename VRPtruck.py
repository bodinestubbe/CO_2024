from gurobipy import Model, GRB,quicksum
from instances import Instance as Instance
import readInstance

class VRPtruck:
    def __init__(self, instance):
        self.instance = instance

    def solve (self): 
        model= Model("VRPTrucks")

        requests = self.instance.Requests
        locations = self.instance.Location
        distance_matrix = self.instance.distances
        
        x = model.addVars(requests, locations, vtype=GRB.BINARY, name="x")
        
        
        
        
        model.setObjective(quicksum(distance_matrix[0][j] * x[i, j] for i in requests for j in locations), GRB.MINIMIZE)
        model.addConstrs((quicksum(x[i, j] for j in locations) == 1 for i in requests))
        model.optimize()
        if model.status == GRB.OPTIMAL:
            for i in requests:
                for j in locations:
                    if x[i, j].x > 0.99:  # Check if variable value is close to 1 (assigned)
                        print(f"Request {i+1} assigned to Location {j+1}")
        else:
            print("Solution not found")


    
    Instance_1 = readInstance.readInstance(readInstance.getInstancePath(20))
    print(range(len(Instance_1.Requests)))
    



