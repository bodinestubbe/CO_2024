from instances import Instance as Instance
import readInstance
from gurobipy import Model, GRB, quicksum, disposeDefaultEnv
import numpy as np
import itertools
class Truck:

    def __init__(self, capacity, max_km):
        self.capacity = capacity
        self.max_km = max_km
        self.route = [0, 0]
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

def canMerge(reqID1, truck1, reqID2, truck2, requests, savings):
    if truck1 == truck2:
        return False
    # do all requests in route have overlap in delivery time
    if hasOverlap(reqID1, reqID2):
        return False
    
    # is it in a route
    if len(truck2.route) > 3:
        return  False
    # is it still within capacity
    if truck1.current_load + requests[reqID2].amount > truck1.capacity:
        return False
    # has max km not been surpassed
    if truck1.current_km + truck2.current_km - savings[(reqID1, reqID2)] > truck1.max_km:
        return False

    return True


def hasOverlap(reqID1, reqID2):
    return reqID1.toDay >= reqID2.fromDay and reqID2.toDay >= reqID1.fromDay

### this one has to be fixed: take into account distance from and to depot
def calculate_truck_distance(truck, requests, distance_matrix):
    distance = 0
    for i in range(1, len(truck.route)):
        distance += distance_matrix[requests[truck.route[i-1]].customerLocID][requests[truck.route[i]].customerLocID]
    return distance #probably wrong

def calculate_truck_load(truck, requests):
    load = 0
    for reqID in truck.route:
        if reqID == 0:
            continue
        load += requests[reqID - 1].amount
    return load

def generate_feasible_truck_tour(instance):
    requests = instance.Requests
    planning_horizon = range(1, instance.days + 1)
    distance_matrix = instance.distances
    savings = generate_savings(instance.Requests, distance_matrix)
    print(savings)
    
    # make a dictionary with every request as key and the value is the assigned truck where you intitate each truck
    # with the max capacity and max distance
    assigned_trucks = {request.ID: Truck(instance.truckCapacity, instance.truckMaxDistance) for request in instance.Requests}
    for reqID, truck in assigned_trucks.items():
        truck.route.insert(len(truck.route)-1, reqID)
        truck.current_load = calculate_truck_load(truck, requests)
        truck.current_km = calculate_truck_distance(truck, requests, distance_matrix)

    # iterate over the savings dictionary and check if you can merge the requests
    for reqIDS, saving in savings.items():
        reqID1 = reqIDS[0]
        reqID2 = reqIDS[1]
        truck1 = assigned_trucks[reqID1]
        truck2 = assigned_trucks[reqID2]

        if canMerge(reqID1, truck1, reqID2, truck2, requests, savings):
            # update truck 1
            index = truck1.route.index(reqID1)
            truck1.route.insert(index + 1, reqID2)
            assigned_trucks[reqID2] = truck1
            truck1.current_load = calculate_truck_load(truck1, requests)
            truck1.current_km = calculate_truck_distance(truck1, requests, distance_matrix)
            
            # update truck 2
            truck2.route.remove(reqID2)
            truck2.current_load = calculate_truck_load(truck2, requests)
            truck2.current_km = calculate_truck_distance(truck2, requests, distance_matrix)
            # assigned_trucks.pop(reqID2) (could add this line to remove the truck from the dictionary)
