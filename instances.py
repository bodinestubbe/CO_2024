import math
class TXT:
    dataset = 'DATASET'
    distance = 'DISTANCE'
    name = 'NAME'
    days = 'DAYS'
    truckCapacity = 'TRUCK_CAPACITY'
    truckMaxDistance = 'TRUCK_MAX_DISTANCE'
    truckDistanceCost = 'TRUCK_DISTANCE_COST'
    truckDayCost = 'TRUCK_DAY_COST'
    truckCost = 'TRUCK_COST'
    technicianDistanceCost = 'TECHNICIAN_DISTANCE_COST'
    technicianDayCost = 'TECHNICIAN_DAY_COST'
    technicianCost = 'TECHNICIAN_COST'
    machines = 'MACHINES'
    locations = 'LOCATIONS'
    requests = 'REQUESTS'
    technicians = 'TECHNICIANS'
    
class Machine(object):
    def __init__(self,ID,size,idlePenalty):
        self.ID = ID
        self.size = size
        self.idlePenalty = idlePenalty

    def __repr__(self):
        return '{:>5} {:>5} {:>5}'.format(self.ID,self.size,self.idlePenalty)
#       return '%d %d %d' % (self.ID,self.size,self.idlePenalty)
    
class Request(object):
    def __init__(self,ID,customerLocID,fromDay,toDay,machineID,amount):
        self.ID = ID
        self.customerLocID = customerLocID
        self.fromDay = fromDay
        self.toDay = toDay
        self.machineID = machineID
        self.amount = amount
        self.isInstalled = False

    def __repr__(self):
        return '{:>5} {:>5} {:>5} {:>5} {:>5} {:>5}'.format(self.ID,self.customerLocID,self.fromDay,self.toDay,self.machineID,self.amount)
#            return '%d %d %d %d %d %d' % (self.ID,self.customerLocID,self.fromDay,self.toDay,self.machineID,self.amount)
    
class Location(object):
    def __init__(self,ID,X,Y):
        self.ID = ID
        self.X = X
        self.Y = Y

    def __repr__(self):
        return '{:>5} {:>5} {:>5}'.format(self.ID,self.X,self.Y)
#            return '%d %d %d' % (self.ID,self.X,self.Y)
          
class Technician(object):
    def __init__(self,ID,locationID,maxDayDistance, maxNrInstallations, capabilities):
        self.ID = ID
        self.locationID = locationID
        self.maxDayDistance = maxDayDistance
        self.maxNrInstallations = maxNrInstallations
        self.capabilities = capabilities
        self.DaysOff = []
        self.workedConsecutiveDays = 0
        self.currentLocationID = 0
    
    def __repr__(self):
        return '{:>5} {:>5} {:>5} {:>5}  {:}'.format( self.ID,self.locationID,self.maxDayDistance,self.maxNrInstallations, ' '.join(str(x) for x in self.capabilities) )
#            return '%d %d %d %d %s' % (self.ID,self.locationID,self.maxDayDistance,self.maxNrInstallations, ' '.join(str(x) for x in self.capabilities))




    
class Instance(object):            


    def __init__(self, dataset, name, days, 
               truckCapacity, truckMaxDistance, truckDistanceCost, truckDayCost,truckCost,
               technicianDistanceCost, technicianDayCost, technicianCost,
                machines, requests, locations, technicians):
        self.dataset = dataset
        self.name = name
        self.days = days
        self.truckCapacity = truckCapacity
        self.truckMaxDistance= truckMaxDistance
        self.truckDistanceCost= truckDistanceCost
        self.truckDayCost = truckDayCost
        self.truckCost  = truckCost
        self.technicianDistanceCost = technicianDistanceCost
        self.technicianDayCost = technicianDayCost
        self.technicianCost = technicianCost

        self.Machines = machines
        self.Requests = requests
        self.Locations = locations
        self.Technicians = technicians
        self.distances = None
        
        self.calculateDistances()

    def calculateDistances(self):
        numLocs = len(self.Locations)
        # print(numLocs)
        self.distances = [[0 for x in range(numLocs) ] for x in range(numLocs)]
        for i in range(numLocs):
            loc1 = self.Locations[i]
            for j in range(numLocs):
                loc2 = self.Locations[j]
                dist = math.ceil( math.sqrt( pow(loc1.X-loc2.X,2) + pow(loc1.Y-loc2.Y,2) ) )
                self.distances[i][j] = self.distances[j][i] = int(dist)
        
        
    
    def __repr__(self):
        print(f"{TXT.dataset} = { self.dataset}")
        print(f"{TXT.name} = { self.name}")
        print(f"{TXT.days} = {self.days}")

        print(f"{TXT.truckCapacity} = {self.truckCapacity}")
        print(f"{TXT.truckMaxDistance} = {self.truckMaxDistance}")

        print(f"{TXT.truckDistanceCost} = {self.truckDistanceCost}")
        print(f"{TXT.truckDayCost} = {self.truckDayCost}")
        print(f"{TXT.truckCost} = {self.truckCost}")

        print(f"{TXT.technicianDistanceCost} = {self.technicianDistanceCost}")
        print(f"{TXT.technicianDayCost} = {self.technicianDayCost}")
        print(f"{TXT.technicianCost} = {self.technicianCost}")

        print(f"Machines = {len(self.Machines)}")
        for i in range (len(self.Machines)):
            print(self.Machines[i])

        print(f"Locations = {len(self.Locations)}")
        for i in range (len(self.Locations)):
            print(self.Locations[i])

        print(f"Requests = {len(self.Requests)}")
        for i in range (len(self.Requests)):
            print(self.Requests[i])
        

        print(f"Technicians = {len(self.Technicians)}")
        for i in range (len(self.Technicians)):
            print(self.Technicians[i])
        
        print("Distances between locations")
        for i in range(len(self.Locations)):
            for j in range(len(self.Locations)):
                print(f"Location ({i+1}, {j+1}): {self.distances[i][j]}")
            print("\n")
        
        
    
        