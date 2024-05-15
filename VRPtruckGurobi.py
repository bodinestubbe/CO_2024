import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from gurobipy import *
import readInstance
from technicianTourGRASP import *
import random
from solution import *
import time
import math

class Truck:
    def __init__(self, capacity, max_km, first_toDay):
        self.capacity = capacity
        self.max_km = max_km
        self.route = []  # List to store sequence of serviced requests (using IDs or similar)
        self.current_load = 0
        self.current_km = 0
        self.current_location = 1 # depot location ID
        self.smallest_toDay = first_toDay

    def can_add_request(self, instance, request):
        return (self.current_load + request.amount * instance.Machines[request.machineID-1].size <= self.capacity and
                self.current_km + instance.distances[request.customerLocID-1][self.current_location-1] + instance.distances[request.customerLocID-1][0] <= self.max_km and 
                self.smallest_toDay >= request.fromDay and self.smallest_toDay <= request.toDay) 
   
    def add_request(self, instance, request):
        self.route.append(request.ID)
        self.current_load += request.amount * instance.Machines[request.machineID-1].size 
        self.current_km += instance.distances[request.customerLocID-1][self.current_location-1]
        self.current_location = request.customerLocID 
        self.smallest_toDay = min(self.smallest_toDay, request.toDay)

    def can_travel_but_full(self, instance, request):
        return (self.current_load + request.amount * instance.Machines[request.machineID-1].size  > self.capacity and 
                self.current_km + instance.distances[request.customerLocID-1][self.current_location-1] + instance.distances[request.customerLocID-1][0] <= self.max_km) 

    def back_to_depot(self, instance):
        self.current_km += instance.distances[self.current_location-1][0]
        self.route.append(0)  # Depot ID
        self.current_load = 0
        self.current_location = 1 # depot location ID

    def can_add_based_on_toDay(self, instance, request, max_day_difference):
        if not self.route:  # If no requests are in the truck yet
            return True
        
        # Calculate the toDay for the incoming request 
        new_request_to_day = instance.Requests[request.ID - 1].toDay  
        
        # Check if the new request's toDay is within the allowed range of existing requests' toDay
        existing_to_days = [instance.Requests[req - 1].toDay for req in self.route]  # Ensure this accesses the correct attribute
        return all(abs(new_request_to_day - to_day) <= max_day_difference for to_day in existing_to_days)

def grasp_routes(instance, random_factor, time_limit, max_day_difference):
    start_time = time.time()
    routes_set = set()
    routes_with_distance = []

    while time.time() - start_time < time_limit:
        trucks = []
        shuffled_requests = instance.Requests[:]  # Copy to avoid altering the original
        random.shuffle(shuffled_requests)

        for request in shuffled_requests:
            possible_trucks = [truck for truck in trucks if truck.can_add_request(instance, request) and truck.can_add_based_on_toDay(instance, request, max_day_difference)]
            back_to_depot_trucks = [truck for truck in trucks if truck.can_travel_but_full(instance, request)]

            if possible_trucks:
                selected_truck = random.choice(possible_trucks[:max(1, len(possible_trucks) * random_factor // 100)])
                selected_truck.add_request(instance, request)
            elif back_to_depot_trucks:
                for truck in back_to_depot_trucks:
                    truck.back_to_depot(instance)
                    if truck.can_add_request(instance, request) and truck.can_add_based_on_toDay(instance, request, max_day_difference):
                        truck.add_request(instance, request)
            else:
                new_truck = Truck(instance.truckCapacity, instance.truckMaxDistance, request.toDay)
                if new_truck.can_add_based_on_toDay(instance, request, max_day_difference):
                    new_truck.add_request(instance, request)
                    trucks.append(new_truck)

        # Ensure all trucks return to depot after last request
        for truck in trucks:
            if truck.current_location != 1:
                truck.back_to_depot(instance)
            route_tuple = tuple(truck.route)
            distance = truck.current_km
            if route_tuple not in routes_set:
                routes_set.add(route_tuple)
                routes_with_distance.append((list(route_tuple), distance))

    return routes_with_distance


def split_routes_and_distances(all_routes):
    routes = []
    distances = []

    for route_distance_pair in all_routes:
        if len(route_distance_pair) == 2:  # Check if each entry has two elements: the route and the distance
            route, distance = route_distance_pair
            routes.append(route)
            distances.append(distance)

    return routes, distances

def truck_route_solver(instance, routes, routes_distances):
    model = Model("Truck_SPP")
    
    # Decision variables: 1 if route is chosen 
    x = model.addVars(((r) for r in range(len(routes))), vtype=GRB.BINARY, name="route_assignment")

    # Objective
    model.setObjective(
        quicksum(instance.truckDayCost * x[r] for r in range(len(routes))) +
        quicksum(instance.truckDistanceCost * routes_distances[r] * x[r] for r in range(len(routes))),
        GRB.MINIMIZE)
    
    # Constraints
    # Each request must be covered exactly once
    for m in range(1, len(instance.Requests)+1):
        model.addConstr(quicksum(x[r] for r, route in enumerate(routes) if m in route) == 1,
                    name=f"Request_{m}")
        
    # distance of route <= max_distance
    for r in range(len(routes)):
        model.addConstr(routes_distances[r] * x[r] <= instance.truckMaxDistance, name="max_distance")

    time_limit = 180
    model.setParam('TimeLimit', time_limit)
    model.update()
    model.optimize()

    # for v in model.getVars():
    #     if v.X > 0:
    #         print(f"{v.varName} = {v.X}")

    # Print status
    if model.status == GRB.OPTIMAL or model.status == GRB.TIME_LIMIT:
        print('\033[95m' + "*" * 50+ ' Truck Route Optimal solution found! '+ "*" * 50 + '\033[0m')
        print()

        print("Chosen Tours for Each truck:")
        chosen_tours = []
        total_distance = 0


        for r in range(len(routes)):
            if x[r].X > 0.5:  # Check if the decision variable is set to 1
                print(f"Route is chosen: {routes[r]}")
                chosen_tours.append(routes[r])
                total_distance += routes_distances[r]

        print(f"Total Truck Distance: {total_distance}")
        print(f"Number of Truck Routes: {x.sum().getValue()}")
        print("Total Truck Cost= {}".format(model.ObjVal))

        return chosen_tours, total_distance, model.ObjVal, x.sum().getValue()

    elif model.status == GRB.INFEASIBLE:
        print("*" * 50+ ' Model is infeasible '+ "*" * 50)
        return None, None, None, None
    else:
        print('Optimization ended with status ' + str(model.status))
        return None, None, None, None

def update_latest_delivery_days(instance):
    latest_delivery_days = []
    print(list(instance.Requests[i].toDay for i in range(len(instance.Requests))))

    for i in range(len(instance.Requests)):
        delivery_day_before_install = instance.Requests[i].dayOfInstallation-1
        #print(f"Request ID: {i+1}, Delivery Day Before Install: {delivery_day_before_install}, Must Deliver On: {instance.Requests[i].toDay}")
        # Initialize latest_delivery_day with a default value
        if delivery_day_before_install > instance.Requests[i].toDay:
            latest_delivery_day = instance.Requests[i].toDay
        else:
            # Assign the delivery_day_before_install if it does not exceed toDay
            latest_delivery_day = delivery_day_before_install

        latest_delivery_days.append(latest_delivery_day)
    return latest_delivery_days

def smallest_latest_delivery_days(instance, chosen_routes, latest_delivery_days):
    latest_delivery_days_route = [float('inf')] * len(instance.Requests)

    # Iterate over each route
    for route in chosen_routes:
        if not route: 
            continue

        print(f"Route: {route}")
        
        non_depot_requests = [req for req in route if req != 0]

        print(f"   Non-Depot Requests: {non_depot_requests}")

        # Find the smallest latest delivery day among all requests in the route
        if non_depot_requests:  
            min_latest_day = min(latest_delivery_days[req-1] for req in non_depot_requests)
            print(f"      Min Latest Day: {min_latest_day}")
            
            # Update all requests in this route to have the same, smallest latest day
            for request_ID in non_depot_requests:
                latest_delivery_days_route[request_ID-1] = min(latest_delivery_days_route[request_ID-1], min_latest_day)

    return latest_delivery_days_route

def remove_depot_from_route(routes):
    return [[node for node in route if node != 0] for route in routes]

def remove_last_zero_from_routes(routes):
    updated_routes = []
    for route in routes:
        if route and route[-1] == 0:  # Check if the last element is 0
            updated_routes.append(route[:-1])  # Exclude the last element

    return updated_routes

def assign_truck(instance, chosen_routes, latest_delivery_days):

    requests = range(1, len(instance.Requests) + 1)
    earliest_delivery_days = [instance.Requests[request-1].fromDay for request in requests]
    install_days = [instance.Requests[request-1].dayOfInstallation for request in requests]
    daily_idle_costs_by_request = [instance.Machines[instance.Requests[request-1].machineID-1].idlePenalty * instance.Requests[request-1].amount for request in requests]
    latest_delivery_days_route = smallest_latest_delivery_days(instance, chosen_routes, latest_delivery_days)
    print("Earliest Delivery Days: ", earliest_delivery_days)
    print("Latest Delivery Days: ", latest_delivery_days)
    print("Latest Delivery Days Route: ", latest_delivery_days_route)
    print("Install Days: ", install_days)


    NUM_DAYS = range(1, instance.days + 1)
    updated_routes = remove_depot_from_route(chosen_routes)

    # Model
    m = Model("vehicle_routing_schedule")

    # Variables
    x = m.addVars(((i, d) for i in range(len(updated_routes)) for d in NUM_DAYS), vtype=GRB.BINARY, name="route_day")
    y = m.addVars(((r, d) for r in requests for d in NUM_DAYS), vtype=GRB.BINARY, name="request_day")
    z = m.addVars(((i) for i in range(len(updated_routes))), vtype=GRB.BINARY, name="use_truck")

    # Objective: Minimize the total cost of idle days and trucks used
    idle_cost = quicksum(y[r, d] * (install_days[r-1] - d - 1) * daily_idle_costs_by_request[r-1]
                        for r in requests for d in NUM_DAYS 
                        if d < install_days[r-1]-1)
    truck_cost = quicksum(z[i] * instance.truckCost for i in range(len(updated_routes)))
    m.setObjective(idle_cost + truck_cost, GRB.MINIMIZE)

    # Constraints

    # Each request must be fulfilled within its time window on exactly one day
    for r in requests:
        m.addConstr(quicksum(y[r, d] for d in range(earliest_delivery_days[r-1], latest_delivery_days_route[r-1] + 1)) == 1, f"fulfill_{r}")

    # Link the request day to the route day - each request on a route must be on the same day that the route runs
    for i, route in enumerate(updated_routes):
        for r in route:
            for d in NUM_DAYS:
                if earliest_delivery_days[r-1] <= d <= latest_delivery_days_route[r-1]:  # Ensure d is within the valid delivery window for request r
                    m.addConstr(y[r, d] <= x[i, d], f"link_request_{r}_to_route_{i}_day_{d}")

    # # Activate z if a truck is used on any day
    for d in NUM_DAYS:
        m.addConstr(quicksum(x[i, d] for i in range(len(updated_routes))) <= quicksum(z[i] for i in range(len(updated_routes))), f"truck_use_{d}")

    # Only one day can be selected for each route
    for i in range(len(updated_routes)):
        m.addConstr(quicksum(x[i, d] for d in NUM_DAYS) == 1, f"one_day_per_route_{i}")


    # Solve
    m.optimize()

    # for v in m.getVars():
    #     if v.X > 0:
    #         print(f"{v.varName} = {v.X}")


    # Dictionary to store the schedule
    schedule = {}
    total_idle_cost = 0
            
    # Output the schedule
    if m.status == GRB.OPTIMAL:
        print('\033[95m' + "*" * 50+ ' Truck Schedule Optimal solution found! '+ "*" * 50 + '\033[0m')

        # Initialize the schedule dictionary for each day
        for d in NUM_DAYS:
            schedule[d] = {}
            truck_id = 1  # Start truck IDs from 1 each day

        for i in range(len(updated_routes)):
            for d in NUM_DAYS:
                if x[i, d].x > 0.5:  # Check if route i is scheduled on day d
                    # Assign route to truck, starting from 1 and incrementing as needed
                    if truck_id not in schedule[d]:
                        schedule[d][truck_id] = chosen_routes[i]  # Directly set the route for the truck
                        print(f"Route {chosen_routes[i]} on Truck {truck_id} on Day {d}")

                        # Iterate over requests in the route
                        for r in updated_routes[i]:
                            if y[r, d].x > 0.5:  # Check if request r is delivered on day d
                                print(f"  Request {r} delivered on Day {d}, Latest Delivery Day: {latest_delivery_days_route[r-1]}, Installed on Day {install_days[r-1]}")
                                # Calculate idle days and cost
                                idle_days = max(0, install_days[r-1] - d - 1)
                                idle_cost = idle_days * daily_idle_costs_by_request[r-1]
                                total_idle_cost += idle_cost
                                print(f"    Idle days: {idle_days}, Idle cost: {idle_cost}")

                    truck_id += 1  # Increment truck ID for next possible assignment on this day
        
        # Printing the schedule dictionary to visualize the complete schedule
        print("Complete truck schedule:")
        for day, trucks in schedule.items():
            print(f"Day {day}:")
            for truck, route in trucks.items():
                print(f"  Truck {truck} runs route: {route}")

        return m.ObjVal, total_idle_cost, z.sum().getValue(), schedule

    else:
        print("No feasible solution found.")
        return None, None, None, None

def add_schedule_solution(schedule, solution):
    
    for day, trucks in schedule.items():
        if len(trucks) != 0:
            for truck_id, route in trucks.items():             
                daily_schedule = solution.daily_schedules[day-1]
                daily_schedule.add_truck_route(truck_id, route)
                solution.add_daily_schedule(daily_schedule)

def search(instance, latest_delivery_days, iterations=4):
    best_number_routes = 0
    best_distance_and_route_costs = 0
    best_truck_and_idle_costs = 0
    best_idle_cost = 0
    best_used_truck = 0
    best_schedule = {}
    best_cost = math.inf
    best_distance = 0

    max_day_difference = 0

    for i in range(iterations):
        print(f"Starting iteration {i+1} with max_day_difference = {max_day_difference}")
        routes_by_request = grasp_routes(instance, random_factor=50, time_limit=10, max_day_difference=max_day_difference)
        possible_routes, routes_distances = split_routes_and_distances(routes_by_request)

        chosen_routes, total_distance, distance_and_route_costs, total_routes = truck_route_solver(instance, possible_routes, routes_distances)
        if chosen_routes is not None:
            chosen_routes = remove_last_zero_from_routes(chosen_routes)
            truck_and_idle_costs, idle_cost, used_truck, schedule = assign_truck(instance, chosen_routes, latest_delivery_days)
            if truck_and_idle_costs is None:
                print("No valid truck and idle costs found, breaking the loop.")
                break  # Exit the loop if no valid truck and idle costs calculation is possible

            total_cost = distance_and_route_costs + truck_and_idle_costs

            if total_cost < best_cost:
                best_cost = total_cost
                best_number_routes = total_routes
                best_distance = total_distance
                best_distance_and_route_costs = distance_and_route_costs
                best_truck_and_idle_costs = truck_and_idle_costs
                best_idle_cost = idle_cost
                best_used_truck = used_truck
                best_schedule = schedule
        
        if instance.days > max_day_difference:
            max_day_difference += 1 
        
    return int(best_number_routes), int(best_distance), int(best_distance_and_route_costs), int(best_truck_and_idle_costs), int(best_idle_cost), int(best_used_truck), best_schedule

def naive_assign_truck(instance, latest_delivery_days):
    schedule = {}
    truck_id_counters = {}
    total_idle_cost = 0

    # Precompute installation days and idle costs for each request
    install_days = [instance.Requests[i].dayOfInstallation for i in range(len(instance.Requests))]
    daily_idle_costs_by_request = [
        instance.Machines[instance.Requests[i].machineID - 1].idlePenalty * instance.Requests[i].amount 
        for i in range(len(instance.Requests))
    ]

    # Iterate over each request in the instance
    for i in range(len(instance.Requests)):
        request = instance.Requests[i]
        exact_delivery_day = latest_delivery_days[request.ID - 1] 

        # Initialize the day in the schedule if not already present
        if exact_delivery_day not in schedule:
            schedule[exact_delivery_day] = {}
            truck_id_counters[exact_delivery_day] = 1  

        truck_id = truck_id_counters[exact_delivery_day]
        truck_id_counters[exact_delivery_day] += 1

        if truck_id not in schedule[exact_delivery_day]:
            schedule[exact_delivery_day][truck_id] = []

        schedule[exact_delivery_day][truck_id].append(request.ID)
        
        idle_days = max(0, install_days[i] - exact_delivery_day - 1)  
        total_idle_cost += daily_idle_costs_by_request[i] * idle_days

    number_of_routes = sum(len(trucks) for trucks in schedule.values())

    return schedule, number_of_routes, total_idle_cost

def return_truck_gurobi_solution(instance):

    solution = return_solution(instance) 
    latest_delivery_days = update_latest_delivery_days(instance)

    # instance 5
    if instance.truckCost + instance.truckDayCost + instance.truckDistanceCost == 0:
        print('\033[95m' + "*" * 50+ ' Truck Cost is 0, Assigning Trucks Naively '+ "*" * 50 + '\033[0m')

        schedule = naive_assign_truck(instance, latest_delivery_days)
        print("Naive Truck Schedule: ", schedule)
        add_schedule_solution(schedule, solution)

    else:
        best_number_routes, best_distance, best_distance_and_route_costs, best_truck_and_idle_costs, best_idle_cost, best_used_truck, best_schedule = search(instance, latest_delivery_days)

        # store solution
        add_schedule_solution(best_schedule, solution)
        solution.num_truck_days = best_number_routes
        solution.num_trucks_used = best_used_truck
        solution.truck_distance = best_distance
        solution.truck_cost = best_distance_and_route_costs + best_truck_and_idle_costs - best_idle_cost
        solution.idle_machine_costs = best_idle_cost

        print(solution)

    return solution



if __name__ == "__main__":
    # Read instance
    instance = readInstance.readInstance(readInstance.getInstancePath(6))


    print('\033[95m' + "*" * 50 + " Solving Truck...... " + "*" * 50 + '\033[0m')

    solution = return_truck_gurobi_solution(instance)
    print(solution)

    # Still not optimal in some cases. can be improved later





