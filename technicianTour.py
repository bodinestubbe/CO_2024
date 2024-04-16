from instances import Instance as Instance
import readInstance
from gurobipy import Model, GRB, quicksum, disposeDefaultEnv
import numpy as np

def generate_feasible_technician_tour(instance):
    planning_horizon = range(1, instance.days + 1)
    distance_matrix = instance.distances

    TECHNICIAN_DISTANCE = 0
    NUMBER_OF_TECHNICIAN_DAYS = 0
    technicians_used = set()

    feasible_tours = {
        tech.ID: {day: [] for day in planning_horizon}
        for tech in instance.Technicians
    }

    # Iterate over each day in the planning horizon
    for day in planning_horizon:
        for technician in instance.Technicians:
            if day in technician.DaysOff:
                continue  # Skip days off

            cumInstallation = 0
            cumDist = 0
            technician.currentLocationID = technician.locationID

            # Initialize remaining requests for the day
            remaining_requests = [
                req for req in instance.Requests
                if not req.isInstalled and day >= req.fromDay + 1
            ]

            while remaining_requests:
                # find the nearest request, sort requests based on the current location of the technician
                remaining_requests.sort(key=lambda req: distance_matrix[technician.currentLocationID - 1][req.customerLocID - 1])
                #print("finding...")

                # Attempt to find a feasible request to fulfill
                found_request = False
                for request in remaining_requests:
                    distance_to_request = distance_matrix[technician.currentLocationID - 1][request.customerLocID - 1]
                    return_distance = distance_matrix[request.customerLocID - 1][technician.locationID - 1]

                    if technician.capabilities[request.machineID - 1] and \
                       cumInstallation + request.amount <= technician.maxNrInstallations and \
                       cumDist + distance_to_request + return_distance <= technician.maxDayDistance:
                        
                        # Update tours, installation counts, and distances
                        feasible_tours[technician.ID][day].append(request.ID)
                        cumInstallation += request.amount
                        cumDist += distance_to_request
                        technician.currentLocationID = request.customerLocID
                        request.isInstalled = True
                        request.installationDay = day

                        # Debug information
                        #print(f"Tech {technician.ID} to Request {request.ID} (Location {technician.currentLocationID}) on Day {day}: Cumulative Distance = {cumDist}")

                        remaining_requests.remove(request)
                        found_request = True
                        break

                if not found_request:
                    # If no requests can be added, stop trying for this day
                    break

            # Calculate travel back home at the end of the day
            if feasible_tours[technician.ID][day]:
                cumDist += distance_matrix[technician.currentLocationID - 1][technician.locationID - 1]
                TECHNICIAN_DISTANCE += cumDist
                NUMBER_OF_TECHNICIAN_DAYS += 1
                technicians_used.add(technician.ID)
                technician.workedConsecutiveDays += 1
                
                if technician.workedConsecutiveDays == 5:
                    # Manage technician's days off after consecutive work
                    technician.DaysOff.extend([day + 1, day + 2])
                    #technician.DaysOff.extend([day + 1])
                    technician.workedConsecutiveDays = 0
            else:
                technician.workedConsecutiveDays = 0  # Reset if not worked that day

    print_results(TECHNICIAN_DISTANCE, NUMBER_OF_TECHNICIAN_DAYS, technicians_used, instance)

    return feasible_tours


def print_feasible_tours(feasible_tours, instance):
    for tech, days in feasible_tours.items():
        print("==============")
        print(f"Technician {tech}:")
        for day, request_ids in days.items():
            if request_ids: 
                locations = [instance.Requests[req_id - 1].customerLocID for req_id in request_ids]
                home_location = instance.Technicians[tech - 1].locationID
                route = f"Home ({home_location}) -> " + " -> ".join(
                    f"request {req_id} ({loc})" for req_id, loc in zip(request_ids, locations)
                ) + f" -> Home ({home_location})"
            else:
                route = "None"  # No requests
            print(f"Day {day}\n{route}")


def print_results(TECHNICIAN_DISTANCE, NUMBER_OF_TECHNICIAN_DAYS, technicians_used, instance):
    print(f"TECHNICIAN_DISTANCE = {TECHNICIAN_DISTANCE}")
    print(f"NUMBER_OF_TECHNICIAN_DAYS = {NUMBER_OF_TECHNICIAN_DAYS}")
    print(f"NUMBER_OF_TECHNICIANS_USED = {len(technicians_used)}")
    totalCost = (instance.technicianDistanceCost * TECHNICIAN_DISTANCE +
                 instance.technicianDayCost * NUMBER_OF_TECHNICIAN_DAYS +
                 instance.technicianCost * len(technicians_used))
    print("Total cost: ", totalCost)

    return totalCost

Instance_1 = readInstance.readInstance(readInstance.getInstancePath(20))

tour1 = generate_feasible_technician_tour(Instance_1)

# print_feasible_tours(tour1, Instance_1)
