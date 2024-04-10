from gurobipy import Model, GRB,quicksum

class VRPtruck:
    def __init__(self, instance):
        self.instance = instance
    def solve (self): 
        model= Model("VRPTrucks")

        requests=range(len(self.instance.requests))  
        locations= range(len(self.instance.locations))
        distance_matrix = self.instance.distance_matrix
        x= model.addVars(requests, locations, vtype=GRB.BINARY, name="x")
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

    if __name__ == "__main__":
        solve()
        
    
    

    

    # def solve (self):
    #      machine_request={}
    #      for request in self.requests: 
    #          machine_request[request.machineID].append(request)


