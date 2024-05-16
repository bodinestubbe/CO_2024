from instances import Instance as Instance
import readInstance
from gurobipy import Model, GRB, quicksum
from solution import *
from technicianTourGRASP import *
from VRPtruckGurobi import *
from itertools import combinations


def truck_route_and_schedule_solver(instance, truck_routes, truck_distances, solution):
    model = Model("Truck Routing and Schedule")

    no_depot_routes = remove_depot_from_route(truck_routes)
    latest_delivery_days = update_latest_delivery_days(instance)

    # Parameters
    requests = range(1,len(instance.Requests)+1)
    days = range(1,instance.days+1)
    earliest_delivery_days = [instance.Requests[request-1].fromDay for request in requests]
    daily_idle_costs_by_request = [instance.Machines[instance.Requests[request-1].machineID-1].idlePenalty * instance.Requests[request-1].amount for request in requests]
    install_days = [instance.Requests[request-1].dayOfInstallation for request in requests]
    


    ## Decision variables
    # 1 if a truck route is chosen on a given day
    x = model.addVars(((r, d) for r in range(len(truck_routes)) for d in days), vtype=GRB.BINARY, name="truck_route_assignment")

    z = model.addVars(((d) for d in days), vtype=GRB.INTEGER, name="trucks_used_per_day")
    max_trucks_used = model.addVar(vtype=GRB.INTEGER, name="max_trucks_used")
    delivery_day = model.addVars(((m) for m in requests), vtype=GRB.INTEGER, name="request_delivery_day")


    # set max_trucks_used to the maximum of z[d]
    for d in days:
        model.addConstr(max_trucks_used >= z[d], f"MaxTrucksUsed_{d}")

    # Daily usage
    for d in days:
        model.addConstr(z[d] == quicksum(x[r, d] for r in range(len(truck_routes))), f"TrucksUsedDay_{d}")


    # Ensure each request is delivered and installed within its time window
    for m in requests:
        model.addConstr(quicksum(x[r, d] for r in range(len(truck_routes)) for d in days if m in truck_routes[r]) == 1, f"TruckCoverRequest_{m}")
        model.addConstr(delivery_day[m] >= earliest_delivery_days[m-1], f"EarliestDeliveryDay_{m}")
        model.addConstr(delivery_day[m] <= latest_delivery_days[m-1], f"LatestDeliveryDay_{m}")

    # Ensure requests in each truck route have the same delivery day
    for r, route in enumerate(no_depot_routes):
        for d in days:
            for request in route:  
                model.addConstr((x[r, d] == 1) >> (delivery_day[request] == d), f"DeliveryDayConsistency_{r}_{request}_{d}")

    for r in range(len(truck_routes)):
        model.addConstr(quicksum(x[r, d] for d in days) <= 1, f"OneDayPerTruckRoute_{r}")


    total_truck_cost = (quicksum(x[r, d] * truck_distances[r] * instance.truckDistanceCost for r in range(len(truck_routes)) for d in days) +
                        quicksum(x[r, d] * instance.truckDayCost for r in range(len(truck_routes)) for d in days) +
                        max_trucks_used * instance.truckCost)
    
    total_idle_cost = quicksum((install_days[m-1] - delivery_day[m] - 1) * daily_idle_costs_by_request[m-1] for m in requests)

    model.setObjective(total_truck_cost+total_idle_cost, GRB.MINIMIZE)

    # model.setParam(GRB.Param.TimeLimit, 600)  # 10 minutes limit
    model.setParam(GRB.Param.MIPFocus, 2)
    model.setParam('Heuristics', 0.2)  # Increase the use of heuristics
    # model.setParam('Presolve', 2) 
    model.setParam(GRB.Param.MIPGap, 0.01)
    model.optimize()


    if model.status == GRB.OPTIMAL:
        print('\033[95m' + "*" * 50+ ' Optimal solution found! '+ "*" * 50 + '\033[0m')        
        
        # for v in model.getVars():
        #     if v.X > 0:
        #         print(f"{v.varName} = {v.X}")


        for d in days:
            # print(f"Day {d}:")
            daily_schedule = solution.daily_schedules[d-1]
            
            # Process truck routes
            truck_id = 1
            for r in range(len(truck_routes)):
                if x[r, d].X > 0.5:  # This truck route is active on this day
                    daily_schedule.add_truck_route(truck_id, truck_routes[r])
                    #print(f"  Truck {truck_id} on Route {truck_routes[r]}")
                    solution.truck_distance += truck_distances[r]  # Update total truck distance
                    solution.num_truck_days += 1
                    truck_id += 1 

                    for m in truck_routes[r]:
                        if m > 0:
                            instance.Requests[m-1].deliveryDay = d # update delivery day
                            #print(f"    Request {m} delivered on Day {delivery_day[m].X}, [{earliest_delivery_days[m-1]}, {install_days[m-1]}]")
        
            solution.add_daily_schedule(daily_schedule)  # Add this daily schedule to the solution

        computed_truck_cost = sum(x[r, d].X * truck_distances[r] * instance.truckDistanceCost for r in range(len(truck_routes)) for d in days) + \
                          sum(x[r, d].X * instance.truckDayCost for r in range(len(truck_routes)) for d in days) + \
                          max_trucks_used.X * instance.truckCost

        computed_idle_cost = sum((install_days[m-1] - delivery_day[m].X - 1) * daily_idle_costs_by_request[m-1] for m in requests)


        solution.num_trucks_used = int(max_trucks_used.X)
        solution.total_cost = int(computed_idle_cost+computed_truck_cost)+ solution.technician_cost
        solution.idle_machine_costs = int(computed_idle_cost)
        solution.truck_cost = int(computed_truck_cost)

        return solution

    elif model.status == GRB.INFEASIBLE:
        print("Problem is infeasible.")

        return None


def return_full_solution(instance):
    print(f'\033[95m' + "*" * 10 + " Solving " + instance.name + "*" * 10 + '\033[0m')

    time_limit = 20
    max_day_difference = 6


    '''
    10
    Chosen Tours for Each Technician:
    Technician 4 assigned to Tour [7, 8, 15, 18, 9, 16, 13, 3, 19, 2]
    Technician 4 assigned to Tour [11, 4, 20, 17, 1, 6]
    Technician 4 assigned to Tour [10, 5, 12, 14]
    Total Distance: 2415
    Number of Technicians Used: 1.0
    Number of Tours: 3.0
    Total cost= 424150.0
    ({4: [[7, 8, 15, 18, 9, 16, 13, 3, 19, 2], [11, 4, 20, 17, 1, 6], [10, 5, 12, 14]]}, 2415, 424150, 1, 3)
    '''

    chosen_tours = {4: [[7, 8, 15, 18, 9, 16, 13, 3, 19, 2], [11, 4, 20, 17, 1, 6], [10, 5, 12, 14]]}
    total_distance = 2415
    total_cost = 424150
    num_technicians_used = 1
    num_tours = 3
    solution = generate_solution_from_chosen_tech_tours(instance, chosen_tours, total_distance, total_cost, num_technicians_used, num_tours)


    # solution = return_solution(instance)

    # tech_tours, tech_distances = initial_technician_tours_GRASP11(instance, time_limit)
    print('\033[91m' + "*" * 10 + " Tech GRASP...... " + "*" * 10 + '\033[0m')

    truck_routes = grasp_routes(instance, random_factor=50, time_limit=time_limit, max_day_difference=max_day_difference)
    truck_routes, truck_distances = split_routes_and_distances(truck_routes)
    truck_routes = remove_last_zero_from_routes(truck_routes)
    print('\033[92m' + "*" * 10 + " Truck GRASP...... " + "*" * 10 + '\033[0m')

    final_solution = truck_route_and_schedule_solver(instance, truck_routes, truck_distances, solution)


    # solution = Solution(instance.dataset, instance.name, instance.days)
    # final_solution = integrated_solver(instance, truck_routes, truck_distances, tech_tours, tech_distances, solution)
    # print('\033[95m' + "*" * 50 + " Final Solution " + "*" * 50 + '\033[0m')
    # print(final_solution)

    return final_solution

def return_feasible_solution(instance):
    print(f'\033[95m' + "*" * 10 + " Solving " + instance.name + "*" * 10 + '\033[0m')

    time_limit = 20

    if (instance.truckCost + instance.truckDayCost + instance.truckDistanceCost == 0) or instance.truckCost / instance.technicianCost < 5 and instance.truckCost / instance.truckDistanceCost < 10000:
        max_day_difference = round(instance.days * 0.7,0)  
    else:
        max_day_difference = 3 #3 is the best
    

    print('\033[91m' + "*" * 10 + " Tech GRASP...... " + "*" * 10 + '\033[0m')
    # solution = return_solution(instance) 
    all_solutions, all_temp_installation_days = return_all_tech_solutions(instance, max_day_difference)

    best_cost = math.inf
    best_solution = None

    for sol, temp_installation_days in zip(all_solutions, all_temp_installation_days):

        solution = sol

        # update installation days
        for request_ID, day in temp_installation_days.items():
            instance.Requests[request_ID - 1].dayOfInstallation = day

        # use grasp to generate initial routes for trucks
        truck_routes = grasp_routes(instance, random_factor=50, time_limit=time_limit, max_day_difference=max_day_difference)
        truck_routes, truck_distances = split_routes_and_distances(truck_routes)
        truck_routes = remove_last_zero_from_routes(truck_routes)

        print('\033[92m' + "*" * 10 + " Truck GRASP...... " + "*" * 10 + '\033[0m')
        final_solution = truck_route_and_schedule_solver(instance, truck_routes, truck_distances, solution)

        print('\033[95m' + "*" * 10 + " Final Solution " + "*" * 10 + '\033[0m')
        # print(final_solution)

        if final_solution.total_cost < best_cost:
            best_cost = final_solution.total_cost
            best_solution = final_solution

    return best_solution


def integrated_solver(instance, truck_routes, routes_distances, tech_tours, solution):
    model = Model("Integrated Model")

    no_depot_routes = remove_depot_from_route(truck_routes)

    # Parameters
    requests = range(1,len(instance.Requests)+1)
    days = range(1,instance.days+1)
    earliest_delivery_days = [instance.Requests[request-1].fromDay for request in requests]
    latest_delivery_days = [instance.Requests[request-1].toDay for request in requests]
    daily_idle_costs_by_request = [instance.Machines[instance.Requests[request-1].machineID-1].idlePenalty * instance.Requests[request-1].amount for request in requests]


    ## Decision variables
    # 1 if a truck route is chosen on a given day
    x = model.addVars(((r, d) for r in range(len(truck_routes)) for d in days), vtype=GRB.BINARY, name="truck_route_assignment")

    # 1 if a technician tour is chosen for technician p on a given day
    y = model.addVars(((p, t, d) for p in tech_tours for t in range(len(tech_tours[p])) for d in days), vtype=GRB.BINARY, name="technician_tour_assignment")
    
    z = model.addVars(((d) for d in days), vtype=GRB.INTEGER, name="trucks_used_per_day")
    max_trucks_used = model.addVar(vtype=GRB.INTEGER, name="max_trucks_used")
    delivery_day = model.addVars(((m) for m in requests), vtype=GRB.INTEGER, name="request_delivery_day")
    install_day = model.addVars(((m) for m in requests), vtype=GRB.INTEGER, name="request_install_day")


    # set max_trucks_used to the maximum of z[d]
    for d in days:
        model.addConstr(max_trucks_used >= z[d], f"MaxTrucksUsed_{d}")


    # Daily usage
    for d in days:
        model.addConstr(z[d] == quicksum(x[r, d] for r in range(len(truck_routes))), f"TrucksUsedDay_{d}")


    # Ensure each request is delivered and installed within its time window
    for m in requests:
        model.addConstr(quicksum(x[r, d] for r in range(len(truck_routes)) for d in days if m in truck_routes[r]) == 1, f"TruckCoverRequest_{m}")
        model.addConstr(quicksum(y[p, t, d] for p in tech_tours for t, tour in enumerate(tech_tours[p]) for d in days if m in tour) == 1, name=f"TechCoverRequest_{m}")
        model.addConstr(delivery_day[m] >= earliest_delivery_days[m-1], f"EarliestDeliveryDay_{m}")
        model.addConstr(delivery_day[m] <= latest_delivery_days[m-1], f"LatestDeliveryDay_{m}")
        model.addConstr(install_day[m] <= instance.days, f"LatestInstallDay_{m}")
        model.addConstr(install_day[m] - delivery_day[m] >= 1, name=f"install_after_delivery_strict_{m}")


    # Ensure requests in each truck route have the same delivery day
    for r, route in enumerate(no_depot_routes):
        for d in days:
            for request in route:  
                model.addConstr((x[r, d] == 1) >> (delivery_day[request] == d), f"DeliveryDayConsistency_{r}_{request}_{d}")

    # Ensure requests in each technician tour have the same install day
    for p in tech_tours:
        for t, tour in enumerate(tech_tours[p]):
            for d in days:
                for request in tour: 
                    model.addConstr((y[p, t, d] == 1) >> (install_day[request] == d), f"InstallDayConsistency_{p}_{t}_{request}_{d}")

    for r in range(len(truck_routes)):
        model.addConstr(quicksum(x[r, d] for d in days) <= 1, f"OneDayPerTruckRoute_{r}")

    for p, tours in tech_tours.items(): 
        for t, tour in enumerate(tours): 
            model.addConstr(quicksum(y[p, t, d] for d in days) <= 1, f"OneDayPerTechTour_{p}_{t}")

    # Ensure each technician is assigned to at most one tour per day
    for p in tech_tours:
        for d in days:
            model.addConstr(quicksum(y[p, t, d] for t in range(len(tech_tours[p])) ) <= 1, f"OneTourPerTechPerDay_{p}_{d}") 


    ## Objective Function

    total_truck_cost = (quicksum(x[r, d] * routes_distances[r] * instance.truckDistanceCost for r in range(len(truck_routes)) for d in days) +
                        quicksum(x[r, d] * instance.truckDayCost for r in range(len(truck_routes)) for d in days) +
                        max_trucks_used * instance.truckCost)


    total_cost = total_truck_cost + quicksum((install_day[m] - delivery_day[m] - 1) * daily_idle_costs_by_request[m-1] for m in requests)
    model.setObjective(total_cost, GRB.MINIMIZE)



    time_limit = 7200
    model.setParam('TimeLimit', time_limit)
    model.setParam(GRB.Param.MIPFocus, 0)
    # model.setParam(GRB.Param.MIPGap, 0.01)
    model.setParam('Method', 1)  # 1 is for dual simplex
    model.setParam('Sifting', 1)  # Enable sifting
    model.setParam('SiftMethod', 1)  # Use dual simplex for sifting sub-problems
    model.setParam('FeasibilityTol', 1e-6)
    model.setParam('OptimalityTol', 1e-6)
    # model.setParam('MIPFocus', 2)  # Balanced approach
    model.setParam('Heuristics', 0.05)  # Reduce the use of heuristics
    # model.setParam('Presolve', 2)  # Aggressive presolve
    model.optimize()

    if model.status == GRB.OPTIMAL:
        print('\033[95m' + "*" * 50+ ' Optimal solution found! '+ "*" * 50 + '\033[0m')        

        # # print decision variables
        # for var in model.getVars():
        #     print(f'{var.varName} = {var.Xn}')  # Xn gives the start value

        for d in days:
            daily_schedule = DailySchedule(d)
            print(f"Day {d}:")
            
            # Process truck routes
            truck_id = 1
            for r in range(len(truck_routes)):
                if x[r, d].X > 0.5:  # This truck route is active on this day
                    daily_schedule.add_truck_route(truck_id, truck_routes[r])
                    print(f"  Truck {truck_id} on Route {truck_routes[r]}")
                    solution.truck_distance += routes_distances[r]  # Update total truck distance
                    solution.num_truck_days += 1
                    truck_id += 1 

                    for m in truck_routes[r]:
                        if m > 0:
                            instance.Requests[m-1].deliveryDay = d # update delivery day
                            #print(f"    Request {m} delivered on Day {delivery_day[m].X}, [{earliest_delivery_days[m-1]}, {latest_delivery_days[m-1]}]")
        

            # Process technician tours
            for p in tech_tours:
                for t in range(len(tech_tours[p])):
                    if y[p, t, d].X > 0.5:  # This technician tour is active on this day
                        daily_schedule.add_technician_schedule(p, tech_tours[p][t])
                        print(f"  Technician {p} assigned to Tour {tech_tours[p][t]} on Day {d}")
      

                        for m in tech_tours[p][t]:
                            if m > 0:
                                instance.Requests[m-1].installDay = d # update install day
                                #print(f"    Request {m} installed on Day {install_day[m].X}")

            solution.add_daily_schedule(daily_schedule)  # Add this daily schedule to the solution

        computed_truck_cost = sum(x[r, d].X * routes_distances[r] * instance.truckDistanceCost for r in range(len(truck_routes)) for d in days) + \
                          sum(x[r, d].X * instance.truckDayCost for r in range(len(truck_routes)) for d in days) + \
                          max_trucks_used.X * instance.truckCost
        
        computed_idle_cost = sum((install_day[m].X - delivery_day[m].X - 1) * daily_idle_costs_by_request[m-1] for m in requests)


        solution.num_trucks_used = int(max_trucks_used.X)
        solution.idle_machine_costs = int(computed_idle_cost)
        solution.truck_cost = int(computed_truck_cost)
        solution.total_cost = solution.truck_cost + solution.technician_cost + solution.idle_machine_costs
        return solution

    elif model.status == GRB.INFEASIBLE:
        print("Problem is infeasible.")

        return None


def truck_route_solver_all(instance, routes, routes_distances):
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
    model.setParam('PoolSolutions', 20)  # Set the number of solutions to be stored
    model.setParam('PoolSearchMode', 2)  # Set to conduct a more thorough search for diverse solutions
    model.setParam(GRB.Param.PoolGap, 0.3)  
    model.setParam(GRB.Param.MIPFocus, 2)
    
    model.update()
    model.optimize()

    # for v in model.getVars():
    #     if v.X > 0:
    #         print(f"{v.varName} = {v.X}")

    # Print status
    if model.status == GRB.OPTIMAL or model.status == GRB.TIME_LIMIT:
        print('\033[95m' + "*" * 50+ ' Truck Route Optimal solution found! '+ "*" * 50 + '\033[0m')
        print()

        all_solutions = []

        for k in range(model.SolCount):
            model.setParam(GRB.Param.SolutionNumber, k)
            chosen_tours = []
            total_distance = 0

            print(f"Solution {k+1}:")
            for r in range(len(routes)):
                if x[r].Xn > 0.5:  # Check if the decision variable is set to 1 in the k-th solution
                    print(f"Route is chosen: {routes[r]}")
                    chosen_tours.append(routes[r])
                    total_distance += routes_distances[r]

            solution_obj_val = model.PoolObjVal
            num_routes = sum(1 for r in range(len(routes)) if x[r].Xn > 0.5)

            print(f"Total Truck Distance: {total_distance}")
            print(f"Number of Truck Routes: {num_routes}")
            print(f"Total Truck Cost= {solution_obj_val}")

            all_solutions.append((chosen_tours, total_distance, solution_obj_val, num_routes))
            print()

        return all_solutions

    elif model.status == GRB.INFEASIBLE:
        print("*" * 50+ ' Model is infeasible '+ "*" * 50)
        return None, None, None, None
    else:
        print('Optimization ended with status ' + str(model.status))
        return None, None, None, None


def return_integrated_sol(instance):


    time_limit = 30 
    if instance.truckCost / instance.technicianCost >= 5 and instance.truckCost / instance.truckDistanceCost >= 10000:
        max_day_difference = 2 # try 2 or 3

    else:
        max_day_difference = round(instance.days * 0.6,0)
    
    print('max day difference:', max_day_difference)
        

    print('\033[92m' + "*" * 10 + " Truck GRASP...... " + "*" * 10 + '\033[0m')
    truck_routes = grasp_routes(instance, random_factor=50, time_limit=time_limit, max_day_difference=max_day_difference)
    truck_routes, truck_distances = split_routes_and_distances(truck_routes)
    truck_routes = remove_last_zero_from_routes(truck_routes)

    print('\033[92m' + "*" * 10 + " Tech GRASP...... " + "*" * 10 + '\033[0m')
    # tech: 60, 120, 600
    possible_tours, tour_distances = initial_technician_tours_GRASP_day_diff(instance, 600, max_day_difference)
    tech_solutions = mip_solver_all(instance, possible_tours, tour_distances)  # expecting a list of solution details


    best_cost = math.inf
    best_solution = None

    for sol in tech_solutions:
        chosen_tours = sol["chosen_tours"]

        solution = Solution(instance.dataset, instance.name, instance.days)
        solution.num_technician_days = sol["number_of_tours"]
        solution.num_technicians_used = sol["number_of_technicians_used"]
        solution.technician_distance = sol["total_distance"]
        solution.technician_cost = sol["total_cost"]

        print('\033[92m' + "*" * 10 + " Final ...... " + "*" * 10 + '\033[0m')

        final_solution = integrated_solver(instance, truck_routes, truck_distances, chosen_tours, solution)

        if final_solution.total_cost < best_cost:
            best_cost = final_solution.total_cost
            best_solution = final_solution

    print('\033[92m' + "*" * 10 + " Best Solution " + "*" * 10 + '\033[0m')
    print(best_solution)
    return best_solution

if __name__ == "__main__":
    instance_path = readInstance.getInstancePath(16)
    instance = readInstance.readInstance(instance_path)

    best_solution = return_integrated_sol(instance)

    '''
    use neighborhood search -> swap, remove, insert -> improve schedule -> min cost 
    add working day constraint 
    '''
    




















