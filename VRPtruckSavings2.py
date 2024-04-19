from instances import Instance as Instance
from readInstance import *
# from gurobipy import Model, GRB, quicksum, disposeDefaultEnv
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
    if hasOverlap(truck1, truck2) and withinCapacity(truck1, truck2) and withinDistance(truck1,truck2, savings, reqID1, reqID2):
        return True
    return False

def withinDistance(truck1,truck2, savings, reqID1, reqID2):
    return truck1.current_km + truck2.current_km - savings[(reqID1, reqID2)] <= truck1.max_km

def withinCapacity(truck1,truck2):
    return truck1.current_load + truck2.current_load <= truck1.capacity

def hasOverlap(truck1, truck2):
    return truck1.smallestToDate >= truck2.largestFromDate and truck2.smallestToDate >= truck1.largestFromDate



def calculate_truck_distance(truck, requests, distance_matrix):
    request_id = truck.route[1]
    custLoc = 0
    for request in requests:
        if request_id == request.ID:
            custLoc = request.customerLocID

    return distance_matrix[0][custLoc-1]*2


def calculate_truck_load(truck, requests, machines):
    load = 0
    for reqID in truck.route:
        if reqID == 0:
            continue        
        load += requests[reqID - 1].amount * machines[requests[reqID - 1].machineID-1].size
    return load

def updateDeliveryWindow(truck1, truck2):
    toDay = min(truck1.smallestToDate, truck2.smallestToDate)
    fromDay = max(truck1.largestFromDate, truck2.largestFromDate) #something check here

    return toDay, fromDay

def generate_feasible_truck_tour(instance):
    requests = instance.Requests
    machines = instance.Machines
    
    distance_matrix = instance.distances
    savings = generate_savings(instance.Requests, distance_matrix)
    print(savings)
    
    # make a dictionary with every request as key and the value is the assigned truck where you intitate each truck
    # with the max capacity and max distance
    assigned_trucks = {request.ID: Truck(instance.truckCapacity, instance.truckMaxDistance) for request in instance.Requests}
    
    
    for reqID, truck in assigned_trucks.items():
        #instantiate trucks and their routes
        truck.route.insert(len(truck.route)-1, reqID)
        truck.current_load = calculate_truck_load(truck, requests, machines)
        truck.current_km = calculate_truck_distance(truck, requests, distance_matrix)
        truck.smallestToDate = requests[reqID-1].toDay 
        truck.largestFromDate = requests[reqID-2].fromDay 
    
   

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
            # assigned_trucks[reqID2] = truck1 this?
            truck1.current_load = calculate_truck_load(truck1, requests, machines)
            truck1.current_km += truck2.current_km - savings[(reqID1, reqID2)]
            truck1.smallestToDate, truck1.largestFromDate = updateDeliveryWindow(truck1, truck2)
            assigned_trucks[reqID2] = truck1 

            if truck1.current_km > truck1.max_km:
                print("error, order of requests is wrong, update constraints in can merge")
            
            # update truck 2
            truck2.route.remove(reqID2)
            truck2.current_load = calculate_truck_load(truck2, requests, machines)
            truck2.current_km = calculate_truck_distance(truck2, requests, distance_matrix)


    # for reqid, truck in assigned_trucks.items():
    #     print(reqid)
    #     print(truck.route, truck.capacity, truck.current_km, truck.current_load, truck.largestFromDate, truck.smallestToDate)
        
    final_trucks = get_final_trucks(assigned_trucks)
    for truck in final_trucks:
        print(truck.route, truck.capacity, truck.current_km, truck.current_load, truck.largestFromDate, truck.smallestToDate)
    return final_trucks
    

   


def get_final_trucks(assigned_trucks):
    final_trucks = []
    sorted_truck_routes = []
    for reqid, truck in assigned_trucks.items():
        if sorted(truck.route) not in sorted_truck_routes:
                final_trucks.append(truck)
                sorted_truck_routes.append(sorted(truck.route))
    return final_trucks




def calculate_distance(trucks):
    distance = 0

    for truck in trucks:
        distance+= truck.current_km
    return distance

def generate_schedule(trucks, instance):
    planning_horizon = range(1, instance.days + 1)

    schedule = {day: [] for day in planning_horizon}
    
    #creates a dictionary with on each day which truck/route drives. For the trucks, the day is drive is chosen as
    # the From Date
    for truck in trucks:
        #change this - take into account when technician comes and if we do it on different days (spread) might be cheaper
        schedule[truck.largestFromDate].append(truck)

    # for day, trucks in schedule.items():
    #     print(f"Day :{day}")

    #     for truck in trucks:
    #         print(f"route: {truck.route}")
    return schedule

def get_truck_days(routes):
def calculate_costs(trucks, distance, instance):
    distance_costs = distance* instance.


    #TO DO:  idling costs
    return None

# def print_results(trucks, costs, distance):



instances = get_all_instances(20) #error still for 20
instance_1= instances[0]
routes = generate_feasible_truck_tour(instance_1)
schedule = generate_schedule(routes, instance_1)
distance = calculate_distance(routes)
truck_days = get_truck_days(schedule)
costs = calculate_costs(distance, schedule, instance_1)
# distance = calculate_distance(routes, instance_1)
