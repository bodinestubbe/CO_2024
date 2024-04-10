from instances import instance as instance

from gurobipy import Model, GRB, quicksum



def technician_tour(instance.technicians, instance.requests, instance.machines):
    for tech in instance.technicians:
        # get the location of the technician
        technician_location = instance.technicians[tech].locationID
        cumInstallation = 0
        cumDist = 0
        technician_tour = []

        if tech.workedDays > 3:
            break
        else:

            for request in instance.requests:
                worked = False
                # get the location of the request
                request_location = instance.requests[tech].customerLocID

                # check if the technician has the capability to install the machine
                if tech.capabilities[request.machineID - 1] == 1: 

                    # check if the technician has the capacity to install the machine
                    if cumInstallation + request.amount <= tech.maxNrInstallations:

                        # get from the distance matrix
                        distance = distance_matrix[technician_location-1][request_location-1] 

                        # check if the technician can travel the distance
                        if cumDist + distance <= tech.maxDayDistance:
                            cumDist += distance
                            cumInstallation += request.amount
                            worked = True
                            technician_tour.append(request.ID)
                if worked == True:
                    tech.workedDays += 1




