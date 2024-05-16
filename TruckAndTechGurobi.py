from instances import Instance as Instance
import readInstance
from gurobipy import Model, GRB, quicksum
from solution import *
from technicianTourGRASP import *
from VRPtruckGurobi import *



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


def return_integrated_sol(instance):

    time_limit = 30 

    # instance 1,2,6,13,19,20
    if instance.technicianCost > 0 and instance.truckDistanceCost > 0 and instance.truckCost / instance.technicianCost >= 5 and instance.truckCost / instance.truckDistanceCost >= 10000:
        max_day_difference = 2 # try 2 or 3


    else:
        max_day_difference = round(instance.days * 0.6,0) # we can try other values if we have time
    
    
    print('max day difference:', max_day_difference)
        

    print('\033[92m' + "*" * 10 + " Truck GRASP...... " + "*" * 10 + '\033[0m')
    truck_routes = grasp_routes(instance, random_factor=50, time_limit=time_limit, max_day_difference=max_day_difference)
    truck_routes, truck_distances = split_routes_and_distances(truck_routes)
    truck_routes = remove_last_zero_from_routes(truck_routes)

    print('\033[92m' + "*" * 10 + " Tech GRASP...... " + "*" * 10 + '\033[0m')
    # tech: 60, 120, 600
    possible_tours, tour_distances = initial_technician_tours_GRASP_day_diff(instance, 60, max_day_difference)
    tech_solutions = mip_solver_all(instance, possible_tours, tour_distances) 


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
    instance_path = readInstance.getInstancePath(6)
    instance = readInstance.readInstance(instance_path)

    start_time = time.time() # Start timer

    best_solution = return_integrated_sol(instance)


    total_time = time.time() - start_time
    print(f"Total Time: {total_time:.2f} seconds")



















