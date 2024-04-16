from instances import Instance as Instance
import readInstance
from gurobipy import Model, GRB, quicksum, disposeDefaultEnv
import numpy as np
import itertools
class Truck:

    def __init__(self, capacity, max_km):
        self.capacity = capacity
        self.max_km = max_km
        self.route = []
        self.current_load = 0
        self.current_km = 0
        self.largestFromDate = 0
        self.smallestToDate = 0
        self.deliveryDay = 0


def generate_savings(requests, distances):
    savings = {}
    
    for i in range(0,len(requests)):
        for j in range(0,len(requests)):
            if i != j:
                request_1 = requests[i].ID
                request_2 = requests[j].ID

                Loc1 = requests[i].customerLocID
                Loc2 = requests[j].customerLocID

                if (request_2, request_1) not in savings:
                    savings[request_1,request_2] = distances[Loc1-1][0] + distances[0][Loc2-1] - distances[Loc1-1][Loc2-1]
                
    
    return {k: v for k, v in sorted(savings.items(), key=lambda item: item[1], reverse = True)}

def canMerge(reqID1, truck1, reqID2, truck2):
    reqID1 = reqIDS[0]
    reqID2 = reqIDS[1]

    # do all requests in route have overlap in delivery time


    # is it in a route
    # is it still within capacity
    
    # has max km not been surpassed

    return None


def hasOverlap(reqID1, reqID2):
    return reqID1.toDay >= reqID2.fromDay and reqID2.toDay >= reqID1.fromDay

def generate_feasible_truck_tour(instance):
    planning_horizon = range(1, instance.days + 1)
    distance_matrix = instance.distances
    savings = generate_savings(instance.Requests, distance_matrix)
    print(savings)
    
    # make a dictionary with every request as key and the value is the assigned truck where you intitate each truck
    # with the max capacity and max distance
    assigned_trucks = {request.ID: Truck(instance.truckCapacity, instance.truckMaxDistance) for request in instance.Requests}
    print(assigned_trucks)

    # iterate over the savings dictionary and check if you can merge the requests
    






    for reqIDs, value in savings.items():
        
        for truck1, truck2 in itertools.product(trucks, repeat = 2):
            reqID1 = reqIDs[0]
            reqID2 = reqIDs[1]

            if reqID1 in truck1.route and reqID2 in truck2.route and truck1!= truck2:
                if canMerge(reqID1, truck1, reqID2, truck2):


            # check if all requests in route have overlap in delivery time
            #if hasOverlap(reqID1):


            # is it in a route
            # is it still within capacity
            
            # has max km not been surpassed






#Instance_1 = readInstance.readInstance(readInstance.getInstancePath(1))
#generate_feasible_truck_tour(Instance_1)

#trucks = [Truck(instance.maxCapacity, instance.maxDistance) for request in instance.Requests]