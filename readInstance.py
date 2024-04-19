
import os
import instances 


def getInt(line):
    parts = line.strip().split('=')
    return int(parts[1].strip())

def getValue(line):
    parts = line.strip().split('=')
    return parts[1].strip()
     

def getNextLine(f):
    line = '\n'
    while line and not line.strip():
        line = f.readline()
    return line

def getMachines(f):
    machines = []
    nrMachineTypes = getInt(getNextLine(f))
    for i in range(nrMachineTypes):
        elements = [int(element.strip()) for element in getNextLine(f).split()]
        machines.append(instances.Machine(elements[0], elements[1], elements[2]))

    return machines

def getLocations(f):
    locations = []
    nrLocations = getInt(getNextLine(f))
    for i in range(nrLocations):
        elements = [int(element.strip()) for element in getNextLine(f).split()]
        locations.append(instances.Location(elements[0], elements[1], elements[2]))

    return locations

def getRequests(f):
    requests = []
    nrRequests = getInt(getNextLine(f))
    for i in range(nrRequests):
        elements = [int(element.strip()) for element in getNextLine(f).split()]
        requests.append(instances.Request(elements[0], elements[1], elements[2], elements[3], elements[4], elements[5]))

    return requests

def getTechnicians(f):
    technicians = []
    nrTechnicians = getInt(getNextLine(f))
    for i in range(nrTechnicians):
        elements = [int(element.strip()) for element in getNextLine(f).split()]
        technicians.append(instances.Technician(elements[0], elements[1], elements[2], elements[3], elements[4:]))

    return technicians

     
def readInstance(instance_path):
    
    try:
        f = open(instance_path,'r')
    except :
        print("error occured opening the file")
    

    dataset = getValue(getNextLine(f))
    name = getValue(getNextLine(f))
    
    days = getInt(getNextLine(f))
    truckCapacity = getInt(getNextLine(f))
    truckMaxDistance = getInt(getNextLine(f))

    truckDistanceCost = getInt(getNextLine(f))
    truckDayCost = getInt(getNextLine(f))
    truckCost = getInt(getNextLine(f))

    technicianDistanceCost = getInt(getNextLine(f))
    technicianDayCost = getInt(getNextLine(f))
    technicianCost =getInt(getNextLine(f))

    machines = getMachines(f)
    locations = getLocations(f)
    requests = getRequests(f)
    technicians = getTechnicians(f)

    return instances.Instance(dataset, name, days,
                              truckCapacity, truckMaxDistance, 
                              truckDistanceCost, truckDayCost, truckCost,
                              technicianDistanceCost, technicianDayCost, technicianCost,
                              machines,  requests,locations, technicians)
    




          

def getInstancePath(instance_number):
    path = os.path.join(os.getcwd(), "instances 2024")

    file_name = "CO_Case24"
    if instance_number < 10:
            file_name +='0'+ str(instance_number)+ '.txt'
    else:
            file_name += str(instance_number)+ '.txt'
    return  os.path.join(path,file_name).replace("\\","/")


def getInstances(num_instances_to_test):
    setOfInstances = []
    
    for i in range(1,num_instances_to_test):
        instance_path = getInstancePath(i)
        setOfInstances.append(readInstance(instance_path))

    return setOfInstances

if __name__ == "__main__":
    
    num_instances_to_test = 3

    setOfInstances = []
    
    for i in range(1,num_instances_to_test):
        instance_path = getInstancePath(i)
        print(instance_path)
        setOfInstances.append(readInstance(instance_path))

    
    for i in setOfInstances:
         i.__repr__()

def get_all_instances(number_of_instances):
    set_of_instances = []
    
    for i in range(1,number_of_instances+1):
        instance_path = getInstancePath(i)
        print(instance_path)
        set_of_instances.append(readInstance(instance_path))

    return set_of_instances