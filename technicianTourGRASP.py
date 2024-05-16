from instances import Instance as Instance
import readInstance
from gurobipy import Model, GRB, quicksum
import random
from solution import DailySchedule, Solution
import time


def select_technician(instance, request, available_technicians, current_distances):
    # Filter candidates based on the request's machine type, technician's capabilities, and max distance
    candidates = [tech for tech in available_technicians if tech.capabilities[request.machineID - 1] == 1 and current_distances[tech.ID] + instance.distances[tech.locationID - 1][request.customerLocID - 1] <= tech.maxDayDistance]
    candidates = [available_technicians[tech] for tech in range(len(available_technicians)) 
                  if available_technicians[tech].capabilities[request.machineID - 1] == 1 
                  and current_distances[available_technicians[tech].ID] + instance.distances[available_technicians[tech].locationID - 1][request.customerLocID - 1] <= available_technicians[tech].maxDayDistance]

    if not candidates:
        return None

    selected_technician = random.choices(candidates)[0]
    return selected_technician

def initial_technician_tours_GRASP(instance, time_limit_seconds):
    start_time = time.time()
    tour_set = {}

    # Initialize the final tours and distances with empty lists for each technician
    final_tours = {tech.ID: [] for tech in instance.Technicians}
    final_distances = {tech.ID: [] for tech in instance.Technicians}

    while time.time() - start_time < time_limit_seconds:
        available_technicians = list(instance.Technicians)
        shuffled_requests = list(instance.Requests)
        random.shuffle(shuffled_requests)

        current_tours = {tech.ID: [] for tech in instance.Technicians}
        current_distances = {tech.ID: 0 for tech in instance.Technicians}
        last_locations = {tech.ID: tech.locationID for tech in instance.Technicians}

        for req in shuffled_requests:
            technician = select_technician(instance, req, available_technicians, current_distances)
            if technician:
                request_distance = instance.distances[last_locations[technician.ID] - 1][req.customerLocID - 1]
                new_total_distance = current_distances[technician.ID] + request_distance
                return_home_distance = instance.distances[req.customerLocID - 1][technician.locationID - 1]

                if new_total_distance + return_home_distance <= technician.maxDayDistance:
                    current_tours[technician.ID].append(req.ID)
                    current_distances[technician.ID] = new_total_distance
                    last_locations[technician.ID] = req.customerLocID

                    final_distance = current_distances[technician.ID] + instance.distances[last_locations[technician.ID] - 1][technician.locationID - 1]
                    tour_key = (frozenset(current_tours[technician.ID]), final_distance)
                    if tour_key not in tour_set:
                        tour_set[tour_key] = (technician.ID, current_tours[technician.ID].copy())

                    if len(current_tours[technician.ID]) >= technician.maxNrInstallations:
                        break

        # Prepare for a new iteration
        current_tours = {tech.ID: [] for tech in instance.Technicians}
        current_distances = {tech.ID: 0 for tech in instance.Technicians}
        last_locations = {tech.ID: tech.locationID for tech in instance.Technicians}

    # Add unique tours to the respective technician's list
    for key, (tech_id, tour) in tour_set.items():
        final_tours[tech_id].append(tour)
        final_distances[tech_id].append(key[1])

    return final_tours, final_distances

def find_all_capable_technicians(instance):
    capable_technicians = []
    for tech in instance.Technicians:
        # Check if the technician has the capability for every machine (simplified condition)
        if all(tech.capabilities):
            capable_technicians.append(tech)
    return capable_technicians

def initial_technician_tours_GRASP_day_diff2(instance, time_limit_seconds, max_day_difference):
    start_time = time.time()
    tour_set = {}

    final_tours = {tech.ID: [] for tech in instance.Technicians}
    final_distances = {tech.ID: [] for tech in instance.Technicians}

    while time.time() - start_time < time_limit_seconds:
        available_technicians = find_all_capable_technicians(instance)
        shuffled_requests = list(instance.Requests)
        random.shuffle(shuffled_requests)

        current_tours = {tech.ID: [] for tech in instance.Technicians}
        current_distances = {tech.ID: 0 for tech in instance.Technicians}
        last_locations = {tech.ID: tech.locationID for tech in instance.Technicians}
        
        day_bounds = {tech.ID: [float('inf'), float('-inf')] for tech in instance.Technicians}  # [min_toDay, max_toDay]

        for req in shuffled_requests:
            technician = select_technician(instance, req, available_technicians, current_distances)
            if technician:
                request_distance = instance.distances[last_locations[technician.ID] - 1][req.customerLocID - 1]
                new_total_distance = current_distances[technician.ID] + request_distance
                return_home_distance = instance.distances[req.customerLocID - 1][technician.locationID - 1]

                # Update toDay bounds and check max day difference constraint
                new_min_toDay = min(day_bounds[technician.ID][0], req.toDay)
                new_max_toDay = max(day_bounds[technician.ID][1], req.toDay)
                if new_max_toDay - new_min_toDay > max_day_difference:
                    continue  # Skip adding this request if it violates the day difference constraint

                if new_total_distance + return_home_distance <= technician.maxDayDistance:
                    current_tours[technician.ID].append(req.ID)
                    current_distances[technician.ID] = new_total_distance
                    last_locations[technician.ID] = req.customerLocID
                    
                    day_bounds[technician.ID] = [new_min_toDay, new_max_toDay]  # Update day bounds


                    final_distance = current_distances[technician.ID] + instance.distances[last_locations[technician.ID] - 1][technician.locationID - 1]
                    tour_key = (frozenset(current_tours[technician.ID]), final_distance)
                    if tour_key not in tour_set:
                        tour_set[tour_key] = (technician.ID, current_tours[technician.ID].copy())

                    if len(current_tours[technician.ID]) >= technician.maxNrInstallations:
                        break

        # Prepare for a new iteration
        current_tours = {tech.ID: [] for tech in instance.Technicians}
        current_distances = {tech.ID: 0 for tech in instance.Technicians}
        last_locations = {tech.ID: tech.locationID for tech in instance.Technicians}

    # Add unique tours to the respective technician's list
    for key, (tech_id, tour) in tour_set.items():
        final_tours[tech_id].append(tour)
        final_distances[tech_id].append(key[1])

    return final_tours, final_distances


def initial_technician_tours_GRASP_day_diff(instance, time_limit_seconds, max_day_difference):
    start_time = time.time()
    tour_set = {}

    final_tours = {tech.ID: [] for tech in instance.Technicians}
    final_distances = {tech.ID: [] for tech in instance.Technicians}

    while time.time() - start_time < time_limit_seconds:
        available_technicians = list(instance.Technicians)
        shuffled_requests = list(instance.Requests)
        random.shuffle(shuffled_requests)

        current_tours = {tech.ID: [] for tech in instance.Technicians}
        current_distances = {tech.ID: 0 for tech in instance.Technicians}
        last_locations = {tech.ID: tech.locationID for tech in instance.Technicians}
        
        day_bounds = {tech.ID: [float('inf'), float('-inf')] for tech in instance.Technicians}  # [min_toDay, max_toDay]

        for req in shuffled_requests:
            technician = select_technician(instance, req, available_technicians, current_distances)
            if technician:
                request_distance = instance.distances[last_locations[technician.ID] - 1][req.customerLocID - 1]
                new_total_distance = current_distances[technician.ID] + request_distance
                return_home_distance = instance.distances[req.customerLocID - 1][technician.locationID - 1]

                # Update toDay bounds and check max day difference constraint
                new_min_toDay = min(day_bounds[technician.ID][0], req.toDay)
                new_max_toDay = max(day_bounds[technician.ID][1], req.toDay)
                if new_max_toDay - new_min_toDay > max_day_difference:
                    continue  # Skip adding this request if it violates the day difference constraint

                if new_total_distance + return_home_distance <= technician.maxDayDistance:
                    current_tours[technician.ID].append(req.ID)
                    current_distances[technician.ID] = new_total_distance
                    last_locations[technician.ID] = req.customerLocID
                    
                    day_bounds[technician.ID] = [new_min_toDay, new_max_toDay]  # Update day bounds


                    final_distance = current_distances[technician.ID] + instance.distances[last_locations[technician.ID] - 1][technician.locationID - 1]
                    tour_key = (frozenset(current_tours[technician.ID]), final_distance)
                    if tour_key not in tour_set:
                        tour_set[tour_key] = (technician.ID, current_tours[technician.ID].copy())

                    if len(current_tours[technician.ID]) >= technician.maxNrInstallations:
                        break

        # Prepare for a new iteration
        current_tours = {tech.ID: [] for tech in instance.Technicians}
        current_distances = {tech.ID: 0 for tech in instance.Technicians}
        last_locations = {tech.ID: tech.locationID for tech in instance.Technicians}

    # Add unique tours to the respective technician's list
    for key, (tech_id, tour) in tour_set.items():
        final_tours[tech_id].append(tour)
        final_distances[tech_id].append(key[1])

    return final_tours, final_distances

def mip_solver(instance, possible_tours, tour_distances):
    model = Model("Person_SPP")
    theta = 0.8
    
    # Decision variables: 1 if tour t is chosen for technician p, 0 otherwise
    y = model.addVars(((p, t) for p in possible_tours for t in range(len(possible_tours[p]))), vtype=GRB.BINARY, name="tour_assignment")

    #  if a technician is used at all in planning_horizon
    r = model.addVars(((p) for p in possible_tours), vtype=GRB.BINARY, name="technician_is_used")

    # Objective
    model.setObjective(
        quicksum(instance.technicianDayCost * y[p, t] for p in possible_tours for t in range(len(possible_tours[p]))) +
        quicksum(instance.technicianDistanceCost * tour_distances[p][t] * y[p, t] for p in possible_tours for t in range(len(possible_tours[p]))) +
        quicksum(instance.technicianCost * r[p] for p in possible_tours), GRB.MINIMIZE)
    
    # Constraints
    # Each request must be covered exactly once
    for m in range(1,len(instance.Requests)+1):
        model.addConstr(quicksum(y[p, t] for p in possible_tours for t, tour in enumerate(possible_tours[p]) if m in tour) == 1,
                    name=f"Request_{m}")
    
    # Ensure working days are not too long for each technician
    for p in possible_tours:
        model.addConstr(quicksum(y[p, t] for t in range(len(possible_tours[p]))) <= theta * instance.days, name=f"max_working_tours_tech_{p}")


    # Activate r if a technician works 
    model.addConstrs((r[p] >= y[p, t] for p in possible_tours for t in range(len(possible_tours[p]))), "technician_usage")

    # Sum of r <= Sum of y
    model.addConstr(quicksum(r[p] for p in possible_tours) <= quicksum(y[p, t] for p in possible_tours for t in range(len(possible_tours[p]))))


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

    model.update()
    model.optimize()

        # Print status
    if model.status == GRB.OPTIMAL or model.status == GRB.TIME_LIMIT:
        print('\033[95m' + "*" * 50+ ' Optimal solution found! '+ "*" * 50 + '\033[0m')
        print()

        print("Chosen Tours for Each Technician:")
        chosen_tours = {}
        total_distance = 0

        for p in possible_tours:
            for t in range(len(possible_tours[p])):
                if y[p, t].X > 0.5:  # Check if the decision variable is set to 1
                    print(f"Technician {p} assigned to Tour {possible_tours[p][t]}")
                    if p not in chosen_tours:
                        chosen_tours[p] = []
                    chosen_tours[p].append(possible_tours[p][t])
                    total_distance += tour_distances[p][t]

        print(f"Total Distance: {total_distance}")
        print(f"Number of Technicians Used: {r.sum().getValue()}")
        print(f"Number of Tours: {y.sum().getValue()}")
        print("Total cost= {}".format(model.ObjVal))

    elif model.status == GRB.INFEASIBLE:
        print("*" * 50 + ' Model is infeasible ' + "*" * 50)
    else:
        print('Optimization ended with status ' + str(model.status))

    return chosen_tours, int(total_distance), int(model.ObjVal), int(r.sum().getValue()), int(y.sum().getValue())


def mip_solver_all(instance, possible_tours, tour_distances):
    model = Model("Person_SPP")
    theta = 0.8
    
    # Decision variables: 1 if tour t is chosen for technician p, 0 otherwise
    y = model.addVars(((p, t) for p in possible_tours for t in range(len(possible_tours[p]))), vtype=GRB.BINARY, name="tour_assignment")

    #  if a technician is used at all in planning_horizon
    r = model.addVars(((p) for p in possible_tours), vtype=GRB.BINARY, name="technician_is_used")

    # Objective
    model.setObjective(
        quicksum(instance.technicianDayCost * y[p, t] for p in possible_tours for t in range(len(possible_tours[p]))) +
        quicksum(instance.technicianDistanceCost * tour_distances[p][t] * y[p, t] for p in possible_tours for t in range(len(possible_tours[p]))) +
        quicksum(instance.technicianCost * r[p] for p in possible_tours), GRB.MINIMIZE)
    
    # Constraints
    # Each request must be covered exactly once
    for m in range(1,len(instance.Requests)+1):
        model.addConstr(quicksum(y[p, t] for p in possible_tours for t, tour in enumerate(possible_tours[p]) if m in tour) == 1,
                    name=f"Request_{m}")
    
    # Ensure working days are not too long for each technician
    for p in possible_tours:
        model.addConstr(quicksum(y[p, t] for t in range(len(possible_tours[p]))) <= theta * instance.days, name=f"max_working_tours_tech_{p}")


    # Activate r if a technician works 
    model.addConstrs((r[p] >= y[p, t] for p in possible_tours for t in range(len(possible_tours[p]))), "technician_usage")

    # Sum of r <= Sum of y
    model.addConstr(quicksum(r[p] for p in possible_tours) <= quicksum(y[p, t] for p in possible_tours for t in range(len(possible_tours[p]))))


    time_limit = 7200 # can change this 
    model.setParam('TimeLimit', time_limit)
    model.setParam(GRB.Param.PoolSearchMode, 2)  # Enable solution pool
    model.setParam(GRB.Param.PoolSolutions, 500)  # Store up to 30 solutions
    model.setParam(GRB.Param.PoolGap, 0.2)  # Allow up to 20% gap from the optimal solution
    model.setParam('Method', 1)  # 1 is for dual simplex
    model.setParam('Sifting', 1)  # Enable sifting
    model.setParam('SiftMethod', 1)  # Use dual simplex for sifting sub-problems
    model.setParam('MIPFocus', 1) 
    model.setParam('Heuristics', 0.1)  # Reduce the use of heuristics
    # model.setParam('IterationLimit', float('inf'))  # Remove iteration limits if applicable
    # model.setParam('NodeLimit', float('inf'))  # Remove node limits for MIPs

    model.update()
    model.optimize()

    # Store results for each solution
    solutions = []
    if model.status == GRB.OPTIMAL or model.status == GRB.TIME_LIMIT:
        print('\033[95m' + "*" * 50+ ' Optimal solution found! '+ "*" * 50 + '\033[0m')
        print()

        number_of_solutions = model.SolCount
        for i in range(number_of_solutions):
            model.setParam(GRB.Param.SolutionNumber, i)
            chosen_tours = {}
            total_distance = 0

            print(f"Solution {i+1}:")
            for p in possible_tours:
                for t in range(len(possible_tours[p])):
                    if y[p, t].Xn > 0.5:  # Check if the decision variable is set to 1 in this solution
                        print(f"Technician {p} assigned to Tour {possible_tours[p][t]}")
                        if p not in chosen_tours:
                            chosen_tours[p] = []
                        chosen_tours[p].append(possible_tours[p][t])
                        total_distance += tour_distances[p][t]

            solution_details = {
                "solution_number": i + 1,
                "chosen_tours": chosen_tours,
                "total_distance": total_distance,
                "number_of_technicians_used": int(r.sum().getValue()),
                "number_of_tours": int(y.sum().getValue()),
                "total_cost": model.PoolObjVal
            }
            solutions.append(solution_details)

            print(f"Total Distance for Solution {i+1}: {total_distance}")
            print(f"Number of Technicians Used in Solution {i+1}: {int(r.sum().getValue())}")
            print(f"Number of Tours in Solution {i+1}: {int(y.sum().getValue())}")
            print("Total cost for Solution {0} = {1}".format(i+1, model.PoolObjVal))
            print()

    elif model.status == GRB.INFEASIBLE:
        print("*" * 50 + ' Model is infeasible ' + "*" * 50)
    else:
        print('Optimization ended with status ' + str(model.status))

    return solutions

def sort_tours_by_start_day(instance, possible_tours):
    earliest_start_days = {}
    for tech_id in possible_tours:
        for tour_id, tour in enumerate(possible_tours[tech_id]):
            max_earliest_day = 0
            for request in tour:
                request_start_day = instance.Requests[request-1].fromDay+1
                #print(request,": ",request_start_day)
                if request_start_day > max_earliest_day:
                    max_earliest_day = request_start_day
            earliest_start_days[(tech_id, tour_id)] = max_earliest_day
    #print(earliest_start_days)

    # Sorting the earliest_start_days dictionary by the values (start days), descending order
    sorted_tour_keys = sorted(
        earliest_start_days.keys(),
        key=lambda k: (earliest_start_days[k], len(possible_tours[k[0]][k[1]])),
        reverse=True
    )
    print('\033[95m' + "*" * 70 + '\033[0m')
    for key in sorted_tour_keys:
        tech_id, tour_id = key
        tour = possible_tours[tech_id][tour_id]
        print(f"Technician {tech_id}, Tour {tour_id}: Earliest Start Day = {earliest_start_days[key]}, Number of Requests = {len(tour)}")

    return sorted_tour_keys, earliest_start_days


def schedule_tours_from_last_day(sorted_tour_keys, earliest_start_days, days_in_horizon):
    schedule = {}
    last_working_day = {tech_id: days_in_horizon + 1 for tech_id, _ in sorted_tour_keys}
    working_streak = {tech_id: 0 for tech_id, _ in sorted_tour_keys}
    scheduled_days = {tech_id: [] for tech_id, _ in sorted_tour_keys}  # Track all scheduled days for each tech
    day_occupancy = {day: 0 for day in range(1, days_in_horizon + 1)}
    all_successfully_scheduled = True

    # Start scheduling from the last day backwards
    for tech_id, tour_id in sorted_tour_keys:
        earliest_start_day = earliest_start_days[(tech_id, tour_id)]
        day_to_schedule = min(last_working_day[tech_id] - 1, days_in_horizon)

        successfully_scheduled = False
        while day_to_schedule >= earliest_start_day:
            if working_streak[tech_id] == 4:  # Check for required rest day
                working_streak[tech_id] = 0
                last_working_day[tech_id] -= 1  # Enforce the rest day
                day_to_schedule -= 1
                continue  # Skip this loop iteration to enforce rest day

            if day_to_schedule < earliest_start_day:
                break

            if working_streak[tech_id] < 4 and day_to_schedule not in scheduled_days[tech_id] and day_occupancy[day_to_schedule] == 0:
                # Schedule the tour on this day
                schedule[(tech_id, tour_id)] = day_to_schedule
                working_streak[tech_id] += 1
                last_working_day[tech_id] = day_to_schedule
                scheduled_days[tech_id].append(day_to_schedule)
                day_occupancy[day_to_schedule] += 1
                successfully_scheduled = True
                break

            day_to_schedule -= 1

        # Backtracking: Try the earliest start day and move forward if not scheduled
        if not successfully_scheduled:
            # Check 4 days onward from the attempt_day for availability
            attempt_day = earliest_start_day
            while attempt_day <= days_in_horizon:
                print(f"Backtracking Tour {tour_id} for Technician {tech_id} on Day {attempt_day}")

                if working_streak[tech_id] == 4:
                    working_streak[tech_id] = 0
                    attempt_day += 1  # Skip for rest day
                    continue

                if attempt_day not in scheduled_days[tech_id] and can_schedule_tech(tech_id, attempt_day, working_streak, scheduled_days, days_in_horizon):
                    schedule[(tech_id, tour_id)] = attempt_day
                    update_scheduling(tech_id, attempt_day, working_streak, scheduled_days)
                    successfully_scheduled = True
                    break
                attempt_day += 1

        if not successfully_scheduled:
            all_successfully_scheduled = False
            print(f"Failed to schedule Tour {tour_id} for Technician {tech_id}.")

    return schedule, all_successfully_scheduled

def schedule_tours_from_earliest_day(sorted_tour_keys, earliest_start_days, days_in_horizon):
    schedule = {}
    working_streak = {tech_id: 0 for tech_id, _ in sorted_tour_keys}
    scheduled_days = {tech_id: [] for tech_id, _ in sorted_tour_keys}
    all_successfully_scheduled = True

    # Iterate over each tour to schedule it as early as possible
    for tech_id, tour_id in sorted_tour_keys:
        earliest_start_day = earliest_start_days[(tech_id, tour_id)]
        successfully_scheduled = False

        for attempt_day in range(earliest_start_day, days_in_horizon + 1):
            if working_streak[tech_id] == 4:  # Ensure mandatory rest after 4 days of work
                working_streak[tech_id] = 0  # Reset working streak
                continue  # Skip the rest day

            # Check if the tour can be scheduled on this day
            if attempt_day not in scheduled_days[tech_id]:
                # Schedule the tour on this day
                schedule[(tech_id, tour_id)] = attempt_day
                working_streak[tech_id] += 1  # Increment the working streak
                scheduled_days[tech_id].append(attempt_day)
                successfully_scheduled = True
                break

        # If the tour could not be scheduled within the allowed days, mark the scheduling as unsuccessful
        if not successfully_scheduled:
            all_successfully_scheduled = False
            print(f"Failed to schedule Tour {tour_id} for Technician {tech_id}. No suitable days found.")

    return schedule, all_successfully_scheduled

def sort_tours_by_start_day_penalty(instance, possible_tours):
    '''
    Starting at the earliest day, an eligible tour with maximum penalty is scheduled. 
    We then continue with the next day or day after that, 
    depending on whether tours have been scheduled on four consecutive days and 
    schedule another eligible tour with maximum penalty and so on.
    '''
    earliest_start_days = {}
    tour_penalty = {}

    for tech_id in possible_tours:
        for tour_id, tour in enumerate(possible_tours[tech_id]):
            max_earliest_day = 0
            idle_cost = 0
            for request in tour:
                request_start_day = instance.Requests[request-1].fromDay+1
                idle_cost += instance.Machines[instance.Requests[request-1].machineID-1].idlePenalty * instance.Requests[request-1].amount
                #print(request,": ",request_start_day)
                if request_start_day > max_earliest_day:
                    max_earliest_day = request_start_day
            earliest_start_days[(tech_id, tour_id)] = max_earliest_day
            tour_penalty[(tech_id, tour_id)] = idle_cost
    #print(earliest_start_days)

    # Sorting the tours based on the earliest start day, and in case of ties, by the descending penalty value.
    sorted_tour_keys = sorted(
        earliest_start_days.keys(),
        key=lambda k: (earliest_start_days[k], -tour_penalty[k])
    )


    # print('\033[95m' + "*" * 70 + '\033[0m')
    # for key in sorted_tour_keys:
    #     tech_id, tour_id = key
    #     tour = possible_tours[tech_id][tour_id]
    #     print(f"Technician {tech_id}, Tour {tour_id}: Earliest Start Day = {earliest_start_days[key]}, Number of Requests = {len(tour)}, idle penalty = {tour_penalty[key]}")

    return sorted_tour_keys, earliest_start_days


def can_schedule_tech(tech_id, day, working_streak, scheduled_days, horizon):
    # Check if scheduling on this day would violate the 4-day work rule
    if day + 3 > horizon:
        # Not enough days left in the horizon to check four days onward
        return True  # Allow scheduling if within the horizon limits
    
    # Check the next three days plus the current one
    for i in range(4):
        if (day + i) in scheduled_days[tech_id] or (working_streak[tech_id] + i + 1) > 4:
            return False
    return True

def update_scheduling(tech_id, day, working_streak, scheduled_days):
    # Update the scheduling status for the technician
    working_streak[tech_id] += 1
    scheduled_days[tech_id].append(day)
    if working_streak[tech_id] == 4:
        working_streak[tech_id] = 0  # Reset after 4 days of work

      
def scheduling(instance, possible_tours, schedule):
    organized_schedule = {}

    for (tech_id, tour_id), day in schedule.items():
        requests = possible_tours[tech_id][tour_id]

        for request_ID in requests:
            instance.Requests[request_ID - 1].dayOfInstallation = day
            # print("Request {} installation day: ".format(request_ID),instance.Requests[request_ID-1].dayOfInstallation)

        if day not in organized_schedule:
            organized_schedule[day] = {}
        if tech_id not in organized_schedule[day]:
            organized_schedule[day][tech_id] = {}

        # Store requests associated with the tour for this technician on this day
        requests = possible_tours[tech_id][tour_id]
        organized_schedule[day][tech_id][tour_id] = requests

    return organized_schedule

def scheduling_all(instance, possible_tours, schedule):
    organized_schedule = {}
    temp_installation_days = {}  # Temporary store for installation days

    for (tech_id, tour_id), day in schedule.items():
        requests = possible_tours[tech_id][tour_id]

        for request_ID in requests:
            # Instead of modifying instance data directly:
            temp_installation_days[request_ID] = day
            # print("Request {} installation day: ".format(request_ID), day)

        if day not in organized_schedule:
            organized_schedule[day] = {}
        if tech_id not in organized_schedule[day]:
            organized_schedule[day][tech_id] = {}

        # Store requests associated with the tour for this technician on this day
        organized_schedule[day][tech_id][tour_id] = requests

    return organized_schedule, temp_installation_days


def add_schedule_solution(schedule, solution):

    for day, techs in schedule.items():
      daily_schedule = DailySchedule(day)
      for tech_id, tours in techs.items():
          for tour_id, tour_requests in tours.items():
              daily_schedule.add_technician_schedule(tech_id, tour_requests)
      solution.add_daily_schedule(daily_schedule)

def return_solution(instance):

    print(f'\033[95m' + "*" * 30 + " Solving " + instance.name + "*" * 30 + '\033[0m')

    if instance.truckCost / instance.technicianCost >= 5 and instance.truckCost / instance.truckDistanceCost >= 10000:
        max_day_difference = 3  #3 is the best
    else:
        max_day_difference = round(instance.days * 0.6,0)

    possible_tours, tour_distances = initial_technician_tours_GRASP_day_diff(instance, 60, max_day_difference)


    # # Run the MIP solver to assign tours to technicians
    chosen_tours, total_distance, total_cost, num_technicians_used, num_tours = mip_solver(instance, possible_tours, tour_distances)
 
    if (instance.truckCost + instance.truckDayCost + instance.truckDistanceCost == 0) or (instance.truckCost / instance.technicianCost < 5 and instance.truckCost / instance.truckDistanceCost < 10000):
        sorted_tour_keys, earliest_start_days = sort_tours_by_start_day(instance, chosen_tours)
        schedule, successfully_scheduled = schedule_tours_from_last_day(sorted_tour_keys, earliest_start_days, instance.days)
        print(successfully_scheduled)

    elif instance.truckCost / instance.technicianCost >= 5 and instance.truckCost / instance.truckDistanceCost >= 10000:
        sorted_tour_keys, earliest_start_days = sort_tours_by_start_day_penalty(instance, chosen_tours)
        schedule, successfully_scheduled = schedule_tours_from_earliest_day(sorted_tour_keys, earliest_start_days, instance.days)
        print(schedule)



    # Schedule the tours based on the start days and working days rule
    final_schedule = scheduling(instance, chosen_tours, schedule)

    # store solution
    solution = Solution(instance.dataset, instance.name, instance.days)
    add_schedule_solution(final_schedule, solution)
    solution.num_technician_days = num_tours
    solution.num_technicians_used = num_technicians_used
    solution.technician_distance = total_distance
    solution.technician_cost = total_cost

    print('\033[95m' + "*" * 50 + " Final Solution " + "*" * 50 + '\033[0m')

    print(solution)
    return solution


def return_all_tech_solutions(instance, max_day_difference):

    possible_tours, tour_distances = initial_technician_tours_GRASP_day_diff(instance, 1800, max_day_difference)

    # Run the MIP solver to assign tours to technicians
    solutions = mip_solver_all(instance, possible_tours, tour_distances)  # expecting a list of solution details

    all_solutions = []  # to store the processed solutions
    all_temp_installation_days = []

    for sol in solutions:
        chosen_tours = sol["chosen_tours"]
        total_distance = sol["total_distance"]
        total_cost = sol["total_cost"]
        num_technicians_used = sol["number_of_technicians_used"]
        num_tours = sol["number_of_tours"]

        # if (instance.truckCost + instance.truckDayCost + instance.truckDistanceCost == 0) or instance.truckCost / instance.technicianCost >= 5 and instance.truckCost / instance.truckDistanceCost >= 10000:
        if instance.truckCost / (instance.technicianCost + instance.technicianDayCost + instance.technicianDistanceCost) > 4:
            # instance 1,2,6,13,18,19,20
            sorted_tour_keys, earliest_start_days = sort_tours_by_start_day_penalty(instance, chosen_tours)
            schedule, successfully_scheduled = schedule_tours_from_earliest_day(sorted_tour_keys, earliest_start_days, instance.days)
            # print(schedule)

        elif (instance.technicianCost + instance.technicianDayCost) / (instance.truckCost + instance.truckDayCost) >= 1:
            # instance 7,8,9,10,14,16
            sorted_tour_keys, earliest_start_days = sort_tours_by_start_day_penalty(instance, chosen_tours)
            schedule, successfully_scheduled = schedule_tours_from_earliest_day(sorted_tour_keys, earliest_start_days, instance.days)
            print(schedule)

        else:
            sorted_tour_keys, earliest_start_days = sort_tours_by_start_day(instance, chosen_tours)
            schedule, successfully_scheduled = schedule_tours_from_last_day(sorted_tour_keys, earliest_start_days, instance.days)
            # print(successfully_scheduled)


        # Schedule the tours based on the start days and working days rule
        final_schedule, temp_installation_days = scheduling_all(instance, chosen_tours, schedule)
        all_temp_installation_days.append(temp_installation_days)

        # store solution for this iteration
        solution = Solution(instance.dataset, instance.name, instance.days)
        add_schedule_solution(final_schedule, solution)
        solution.num_technician_days = num_tours
        solution.num_technicians_used = num_technicians_used
        solution.technician_distance = total_distance
        solution.technician_cost = total_cost

        all_solutions.append(solution)

    return all_solutions, all_temp_installation_days

def generate_solution_from_chosen_tech_tours(instance, chosen_tours, total_distance, total_cost, num_technicians_used, num_tours):

    sorted_tour_keys, earliest_start_days = sort_tours_by_start_day_penalty(instance, chosen_tours)
    schedule, successfully_scheduled = schedule_tours_from_earliest_day(sorted_tour_keys, earliest_start_days, instance.days)
    print(schedule)

    # Schedule the tours based on the start days and working days rule
    final_schedule = scheduling(instance, chosen_tours, schedule)

    # store solution
    solution = Solution(instance.dataset, instance.name, instance.days)
    add_schedule_solution(final_schedule, solution)
    solution.num_technician_days = num_tours
    solution.num_technicians_used = num_technicians_used
    solution.technician_distance = total_distance
    solution.technician_cost = total_cost

    print('\033[95m' + "*" * 50 + " Final Solution " + "*" * 50 + '\033[0m')

    print(solution)
    return solution



if __name__ == "__main__":
    instance_path = readInstance.getInstancePath(6)
    instance = readInstance.readInstance(instance_path)

    possible_tours, tour_distances = initial_technician_tours_GRASP_day_diff(instance, 36, 3)
    for i in possible_tours:
        print(len(possible_tours[i]))
