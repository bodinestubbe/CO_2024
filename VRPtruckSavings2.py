from instances import Instance as Instance
from readInstance import *
# from gurobipy import Model, GRB, quicksum, disposeDefaultEnv
import numpy as np
import itertools
from technicianTourGRASP import *


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
        self.ID = 0


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
        truck.smallestToDate = requests[reqID-1].dayOfInstallation-1 #requests[reqID-1].toDay
        truck.largestFromDate = requests[reqID-1].fromDay 
    
    for reqID, truck in assigned_trucks.items():
        print(reqID, truck.largestFromDate, truck.smallestToDate)

       
   

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


    
    final_trucks = get_final_trucks(assigned_trucks)

    for truck in final_trucks:
        print(truck.route, truck.current_km, truck.current_load, truck.largestFromDate, truck.smallestToDate)
    
    return final_trucks
    

def get_final_trucks(assigned_trucks):
    final_trucks = []
    sorted_truck_routes = []
    for reqid, truck in assigned_trucks.items():
        # truck.route = truck.route[1:-1]
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

    #creates a dictionary with on each day which truck/route drives

    for truck in trucks:
        #choose delivery window:
        # check 1: only deliverable on 1 day - choose that day

        if truck.largestFromDate == truck.smallestToDate:
            delivery_day = truck.largestFromDate
            schedule[delivery_day].append(truck)
            truck.ID = len(schedule[delivery_day])
            update_delivery_day(delivery_day,truck, instance)

        else: #minimizing idling cost
            delivery_day = truck.smallestToDate
            schedule[delivery_day].append(truck)
            truck.ID = len(schedule[delivery_day])
            update_delivery_day(delivery_day,truck, instance)

        # T ODO: eliverable on mutiple days:
          # if day cost > truck cost:
                # put it all on same day
            # if day cost < truck cost:
                # spread it out
        #minimize idling cost

    
    #print
    return schedule

def update_delivery_day(delivery_day, truck, instance):
    for reqID in truck.route:
        if reqID != 0:
            instance.Requests[reqID-1].deliveryDay = truck.delivery_day = delivery_day



def calculate_costs(schedule, instance):
    #costs for distance
    distance_costs = total_distance(schedule)* instance.truckDistanceCost

    #costs for truck each day
    day_costs = num_truck_days(schedule)*instance.truckDayCost

    #costs using truck at all in time horizon (max trucks on any day)
    truck_cost = num_truck_used(schedule)*instance.truckCost

    idling_cost = 0
    for request in instance.Requests:
        idling_cost += (request.dayOfInstallation - request.deliveryDay -1)*request.amount*instance.Machines[request.machineID-1].idlePenalty
    
    return distance_costs + day_costs + truck_cost+ idling_cost



def add_schedule_solution(schedule, solution):
    
    for day, trucks in schedule.items():
        if len(trucks) != 0:
            for truck in trucks:
                
                        print("I am stuck")
                        
                        daily_schedule = solution.daily_schedules[day-1]
                        print(daily_schedule.day)
                        daily_schedule.add_truck_route(truck.ID, truck.route[1:-1])
                        print(truck.deliveryDay, truck.route)
                        solution.add_daily_schedule(daily_schedule)


def total_distance(schedule):
    return  sum([sum([truck.current_km for truck in trucks]) for day,trucks in schedule.items()])

def num_truck_used(schedule):
    return max([len(trucks) for days, trucks in schedule.items()])

def num_truck_days(schedule):
    return sum([len(trucks) for days, trucks in schedule.items()])

def return_final_solution(instance):
# instances = get_all_instances(20) #error still for 20
# instance_1 = instances[0]
    solution = return_solution(instance)
    routes = generate_feasible_truck_tour(instance)
    schedule = generate_schedule(routes, instance)


# store solution

    add_schedule_solution(schedule, solution)
    solution.num_truck_days = num_truck_days(schedule)
    solution.num_truck_used = num_truck_used(schedule)
    solution.truck_distance = total_distance(schedule)
    solution.truck_cost = calculate_costs(schedule, instance)

    return solution



# truck_days = get_truck_days(schedule)
# 
# distance = calculate_distance(routes, instance_1)
