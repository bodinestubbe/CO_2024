from instances import Instance as Instance
import readInstance
from gurobipy import Model, GRB, quicksum
import random

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

def initial_technician_tours_GRASP(instance, iterations=50):
    possible_tours = {tech.ID: set() for tech in instance.Technicians}
    tour_distances = {tech.ID: {} for tech in instance.Technicians}  # Dictionary to store distances of tours

    for request in range(1, len(instance.Requests)+1):
        max_number_of_requests = request

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

    model.update()
    model.optimize()

    for v in model.getVars():
        if v.X > 0:
            print(f"{v.varName} = {v.X}")

    # Print status
    if model.status == GRB.OPTIMAL:
        print("*" * 50+ ' Optimal solution found! '+ "*" * 50)
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
        print("Total cost= {}".format(model.ObjVal))

    elif model.status == GRB.INFEASIBLE:
        print("*" * 50+ ' Model is infeasible '+ "*" * 50)
    else:
        print('Optimization ended with status ' + str(model.status))

    return chosen_tours

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

    for key in sorted_tour_keys:
        tech_id, tour_id = key
        tour = possible_tours[tech_id][tour_id]
        print()
        print(f"Technician {tech_id}, Tour {tour_id}: Earliest Start Day = {earliest_start_days[key]}, Number of Requests = {len(tour)}")

    return sorted_tour_keys, earliest_start_days

def working_days_rule(sorted_tour_keys, earliest_start_days):

    # Initialize the starting day for scheduling
    current_day = 1
    scheduled_days = {}

    # Iterate through each tour based on the sorted order
    for key in sorted_tour_keys:
        tech_id, tour_id = key
        # Retrieve the earliest start day for the current tour
        earliest_start = earliest_start_days[key]
        
        # Ensure the scheduling starts at least on the earliest allowable start day
        if current_day < earliest_start:
            current_day = earliest_start
        
        # Find the next valid start day according to the 4 days on, 1 day off pattern
        # Adjust current_day if it falls on a rest day
        if (current_day - 1) % 5 == 4:  # Check if the current day is a rest day
            current_day += 1  # Skip the rest day

        # Assign the start day for the current tour
        scheduled_days[key] = current_day
        
        # Increment the day for the next possible scheduling
        current_day += 1
        
        # Automatically adjust for the next cycle's rest day if needed
        if (current_day - 1) % 5 == 4:  # If the next day is a rest day, skip it
            current_day += 1

    return scheduled_days
def scheduling(instance, possible_tours):

    sorted_tour_keys, earliest_start_days = sort_tours_by_start_day(instance, possible_tours)
    scheduled_days = working_days_rule(sorted_tour_keys, earliest_start_days)
 
    # Create a dictionary to store schedules by technician
    technician_schedules = {}

    # Populate the technician schedules from the scheduled days information
    for key in sorted_tour_keys:
        tech_id, tour_id = key
        scheduled_day = scheduled_days[key]
        if tech_id not in technician_schedules:
            technician_schedules[tech_id] = []
        # Retrieve the actual tour (list of requests) from possible_tours
        tour_requests = possible_tours[tech_id][tour_id]
        technician_schedules[tech_id].append((tour_requests, scheduled_day))

    # Print the schedule for each technician with full tour details
    print("Schedule for Each Technician:")
    for tech_id, schedules in technician_schedules.items():
        print(f"Technician {tech_id}:")
        for tour_requests, day in sorted(schedules, key=lambda x: x[1]):  # Sort by day for better readability
            print(f"  Day {day}: {tour_requests}")


if __name__ == "__main__":
    instance_path = readInstance.getInstancePath(20)
    instance = readInstance.readInstance(instance_path)

    possible_tours, tour_distances  = initial_technician_tours_GRASP(instance, iterations=100)

    chosen_tour = mip_solver(instance, possible_tours, tour_distances)

    schedule = scheduling(instance, chosen_tour)

