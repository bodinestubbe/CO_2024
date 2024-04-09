class LANG:
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

    def __repr__(self):
        return '{:>5} {:>5} {:>5} {:>5}  {:}'.format( self.ID,self.locationID,self.maxDayDistance,self.maxNrInstallations, ' '.join(str(x) for x in self.capabilities) )
#            return '%d %d %d %d %s' % (self.ID,self.locationID,self.maxDayDistance,self.maxNrInstallations, ' '.join(str(x) for x in self.capabilities))


     
class Instance:            
    def _init_(machines, requests, locations, technicians):
        self.Machines = machines
        self.Requests = requests
        self.Locations = locations
        self.Technicians = technicians
        self.ReadDistance = None
        self.calcDistance = None