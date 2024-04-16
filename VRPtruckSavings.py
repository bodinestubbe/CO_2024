from instances import Instance as Instance
import readInstance
from gurobipy import Model, GRB, quicksum, disposeDefaultEnv
import numpy as np

class Truck:

    def __init__(self, capacity, max_km, request):
        self.capacity = capacity
        self.max_km = max_km
        self.route = [1, request.customerLocID,1]
        self.current_load = 0
        self.current_km = 0
        self.day = 0


def generate_savings(distances):
    savings = []
    for i in range(len(distances)):
        for j in range(len(distances)):
            savings.append(((i,j),distances[i][0] + distances[0][j] - distances[i][j]))
    
    return sorted(savings, key = lambda x:x[1], reverse = True)

def canMerge():
    # do all requests in route have overlap in delivery time
    # is it still within capacity
    # has max km not been surpassed

    return None

def generate_feasible_truck_tour(instance):
    planning_horizon = range(1, instance.days + 1)
    distance_matrix = instance.distances
    savings = generate_savings(distance_matrix)

    trucks = [Truck(instance.truckCapacity, instance.truckMaxDistance, request) for request in instance.requests]
    
    for saving in savings:
        




Instance_1 = readInstance.readInstance(readInstance.getInstancePath(1))
generate_feasible_truck_tour(Instance_1)