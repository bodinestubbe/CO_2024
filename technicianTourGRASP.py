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

    # Calculate the inverse ratio of distance to max travel distance and normalize
    technician_weights = []
    for tech in candidates:
        distance = instance.distances[tech.locationID - 1][request.customerLocID - 1]
        adjusted_max_day_distance = max(tech.maxDayDistance, 0.01)  # Ensure non-zero denominator
        weight = 1.0 / ((distance+1e-4) / adjusted_max_day_distance)
        technician_weights.append(weight)

    total_weight = sum(technician_weights)
    normalized_weights = [w / total_weight for w in technician_weights]

    selected_technician = random.choices(candidates, weights=normalized_weights, k=1)[0]
    return selected_technician

def initial_technician_tours_GRASP2(instance, time_limit_seconds):
    start_time = time.time()
    possible_tours = {tech.ID: set() for tech in instance.Technicians}
    tour_distances = {tech.ID: {} for tech in instance.Technicians}  # Dictionary to store distances of tours

    while time.time() - start_time < time_limit_seconds:
        for request in range(1, len(instance.Requests)):
            max_number_of_requests = request + 1

            available_technicians = list(instance.Technicians)
            current_tours = {tech.ID: [] for tech in instance.Technicians}
            current_distances = {tech.ID: 0 for tech in instance.Technicians}
            last_locations = {tech.ID: tech.locationID for tech in instance.Technicians}

            # Shuffle requests for GRASP's randomization component
            shuffled_requests = list(instance.Requests)  # Make a copy if you need to preserve the original order
            random.shuffle(shuffled_requests)

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
                        if (len(current_tours[technician.ID]) >= max_number_of_requests or
                                len(current_tours[technician.ID]) >= technician.maxNrInstallations):
                            available_technicians.remove(technician)

            for tech_id, tour in current_tours.items():
                if tour:
                    tour_tuple = tuple(tour)
                    final_distance = current_distances[tech_id] + instance.distances[last_locations[tech_id] - 1][instance.Technicians[tech_id - 1].locationID - 1]
                    if tour_tuple not in possible_tours[tech_id]:
                        possible_tours[tech_id].add(tour_tuple)
                        tour_distances[tech_id][tour_tuple] = final_distance
        
        # Check if it's time to terminate
        if time.time() - start_time >= time_limit_seconds:
            break

    # Convert sets to lists for indexing
    final_tours = {tech_id: [list(tour) for tour in possible_tours[tech_id]] for tech_id in possible_tours}
    final_distances = {tech_id: [tour_distances[tech_id][tour_tuple] for tour_tuple in possible_tours[tech_id]] for tech_id in possible_tours}

    return final_tours, final_distances

def initial_technician_tours_GRASP(instance, iterations=50):
    possible_tours = {tech.ID: set() for tech in instance.Technicians}
    tour_distances = {tech.ID: {} for tech in instance.Technicians}  # Dictionary to store distances of tours

    for request in range(1, len(instance.Requests)):
        max_number_of_requests = request+1

        for _ in range(iterations):
            available_technicians = list(instance.Technicians)
            current_tours = {tech.ID: [] for tech in instance.Technicians}
            current_distances = {tech.ID: 0 for tech in instance.Technicians}
            last_locations = {tech.ID: tech.locationID for tech in instance.Technicians}

            random.shuffle(instance.Requests)
            
            for request in instance.Requests:
                technician = select_technician(instance, request, available_technicians, current_distances)
                if technician:
                    request_distance = instance.distances[last_locations[technician.ID] - 1][request.customerLocID - 1]
                    new_total_distance = current_distances[technician.ID] + request_distance
                    return_home_distance = instance.distances[request.customerLocID - 1][technician.locationID - 1]

                    if new_total_distance + return_home_distance <= technician.maxDayDistance:
                        current_tours[technician.ID].append(request.ID)
                        current_distances[technician.ID] = new_total_distance
                        last_locations[technician.ID] = request.customerLocID
                        if len(current_tours[technician.ID]) >= max_number_of_requests:
                            available_technicians.remove(technician)
                        elif len(current_tours[technician.ID]) >= technician.maxNrInstallations:
                            available_technicians.remove(technician)

            for tech_id, tour in current_tours.items():
                if tour:
                    tour_tuple = tuple(tour)
                    final_distance = current_distances[tech_id] + instance.distances[last_locations[tech_id] - 1][instance.Technicians[tech_id - 1].locationID - 1]
                    if tour_tuple not in possible_tours[tech_id]:
                        possible_tours[tech_id].add(tour_tuple)
                        tour_distances[tech_id][tour_tuple] = final_distance

    # Convert sets to lists for indexing
    final_tours = {}
    final_distances = {}
    for tech_id in possible_tours:
        final_tours[tech_id] = [list(tour) for tour in possible_tours[tech_id]]
        final_distances[tech_id] = [tour_distances[tech_id][tuple(tour)] for tour in final_tours[tech_id]]

    return final_tours, final_distances

def neighborhood_search(instance, feasible_tours, time_limit_seconds):
    # get feasible neighbors  

    return possible_tours, tour_distances 

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

    time_limit = 300
    model.setParam('TimeLimit', time_limit)
    model.update()
    model.optimize()

    for v in model.getVars():
        if v.X > 0:
            print(f"{v.varName} = {v.X}")

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
        print("*" * 50+ ' Model is infeasible '+ "*" * 50)
    else:
        print('Optimization ended with status ' + str(model.status))

    return chosen_tours, total_distance, model.ObjVal, r.sum().getValue(), y.sum().getValue()

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

def schedule_onward(sorted_tour_keys, earliest_start_days, instance):
    current_day = 1
    scheduled_days = {}
    last_scheduled_day = {}

    # Determine whether to apply the day off rule
    apply_day_off_rule = instance.days > 10

    for key in sorted_tour_keys:
        tech_id, tour_id = key
        earliest_start = earliest_start_days[key]

        # Ensure the scheduling starts at least on the earliest allowable start day
        start_day = max(current_day, earliest_start, last_scheduled_day.get(tech_id, 0) + 1)

        # Skip rest days if the rule applies
        if apply_day_off_rule:
            while (start_day - 1) % 5 == 4:
                start_day += 1

        # Check if the start day exceeds the instance days
        if start_day > instance.days:
            continue  # If no other day is available, skip to the next tour

        # Assign the start day for the current tour
        scheduled_days[key] = start_day
        last_scheduled_day[tech_id] = start_day  # Track last scheduled day for each technician

        # Update current_day to the next day after the last scheduled day across all technicians
        if start_day == current_day:
            current_day = max(last_scheduled_day.values()) + 1
            if apply_day_off_rule and (current_day - 1) % 5 == 4:  # Skip rest day if the rule applies
                current_day += 1

    return scheduled_days
def schedule_backward(sorted_tour_keys, earliest_start_days, instance):
    scheduled_days = {}
    current_day = instance.days

    # Determine whether to apply the day off rule
    apply_day_off_rule = instance.days != 5

    for key in sorted(sorted_tour_keys, key=lambda x: earliest_start_days[x], reverse=True):
        tech_id, tour_id = key
        earliest_start = earliest_start_days[key]

        found_day = False
        while current_day >= earliest_start:
            if apply_day_off_rule and (current_day - 1) % 5 == 4:  # Skip rest day if the rule applies
                current_day -= 1
            else:
                scheduled_days[key] = current_day  # Schedule the tour
                found_day = True
                break  # Break the loop after scheduling

        if found_day:
            current_day = scheduled_days[key] - 1
        else:
            current_day -= 1  # Continue with the next lowest day

        if current_day < 1:  # Prevent current_day from going below 1
            break

    return scheduled_days

def scheduling(instance, possible_tours):
    sorted_tour_keys, earliest_start_days = sort_tours_by_start_day(instance, possible_tours)

    if instance.truckCost < 100000:
        scheduled_days = schedule_onward(sorted_tour_keys, earliest_start_days, instance)
    else:
        scheduled_days = schedule_backward(sorted_tour_keys, earliest_start_days, instance)

    all_tours = {}  # Redefine all_tours as a nested dictionary

    # Populate all_tours with structured data
    for key in sorted_tour_keys:
        tech_id, tour_id = key
        if key in scheduled_days:
            scheduled_day = scheduled_days[key]
            tour_requests = possible_tours[tech_id][tour_id]
            if scheduled_day not in all_tours:
                all_tours[scheduled_day] = {}
            if tech_id not in all_tours[scheduled_day]:
                all_tours[scheduled_day][tech_id] = {}
            all_tours[scheduled_day][tech_id][tour_id] = tour_requests

            # Update day of installation for requests
            for request_ID in tour_requests:
                instance.Requests[request_ID - 1].dayOfInstallation = scheduled_day

    # Print the schedule in the desired structured format
    print('\033[95m' + "*" * 70 + '\033[0m')
    for day, techs in all_tours.items():
        print(f"Day {day}")
        for tech_id, tours in techs.items():
            print(f"  Technician {tech_id}:")
            for tour_id, requests in tours.items():
                print(f"    Tour {tour_id}: {requests}")

    return all_tours

def add_schedule_solution(schedule, solution):

    for day, techs in schedule.items():
      daily_schedule = DailySchedule(day)
      for tech_id, tours in techs.items():
          for tour_id, tour_requests in tours.items():
              daily_schedule.add_technician_schedule(tech_id, tour_requests)
      solution.add_daily_schedule(daily_schedule)

def return_solution(instance):

    print(f'\033[95m' + "*" * 30 + " Solving " + instance.name + "*" * 30 + '\033[0m')


    possible_tours, tour_distances = initial_technician_tours_GRASP2(instance, 10)

    # # Run the MIP solver to assign tours to technicians
    chosen_tours, total_distance, total_cost, num_technicians_used, num_tours = mip_solver(instance, possible_tours, tour_distances)

    # Schedule the tours based on the start days and working days rule
    schedule = scheduling(instance, chosen_tours)

    # store solution
    solution = Solution(instance.dataset, instance.name, instance.days)
    add_schedule_solution(schedule, solution)
    solution.num_technician_days = num_tours
    solution.num_technicians_used = num_technicians_used
    solution.technician_distance = total_distance
    solution.technician_cost = total_cost

    #print('\033[95m' + "*" * 50 + " Final Solution " + "*" * 50 + '\033[0m')

    #print(solution)
    return solution

if __name__ == "__main__":
    instance_path = readInstance.getInstancePath(6)
    instance = readInstance.readInstance(instance_path)

    print('\033[95m' + "*" * 50 + " Solving...... " + "*" * 50 + '\033[0m')

    possible_tours, tour_distances = initial_technician_tours_GRASP2(instance, 10)

    # # Run the MIP solver to assign tours to technicians
    chosen_tours, total_distance, total_cost, num_technicians_used, num_tours = mip_solver(instance, possible_tours, tour_distances)

    # Schedule the tours based on the start days and working days rule
    schedule = scheduling(instance, chosen_tours)

    # Create a Solution object to store the final schedule
    solution = Solution(instance.dataset, instance.name, instance.days)
    add_schedule_solution(schedule, solution)
    solution.num_technician_days = num_tours
    solution.num_technicians_used = num_technicians_used
    solution.technician_distance = total_distance
    solution.technician_cost = total_cost

    print('\033[95m' + "*" * 50 + " Final Solution " + "*" * 50 + '\033[0m')

    print(solution)

    # for request in range(1, len(instance.Requests)+1):
    #     print("Request {} installation day: ".format(request),instance.Requests[request-1].dayOfInstallation)


    '''
    instance 4 only has distance cost for trucks
    instance 5 only has distance cost for technicians
    11, 16, 17, 18: higher distance cost 
    20: 30 sec is fine, took a long time to run
    13: 60 sec is better
    11, 12 different time limit return the same solution
    13, 20: 1 technician is better
    14, 15: 20 sec is better
    '''



