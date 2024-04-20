

class TruckRoute:
    def __init__(self, truck_id, locations):
        self.truck_id = truck_id
        self.route = locations  # List of location IDs the truck will visit

    def __repr__(self):
        return f"{self.truck_id} {' '.join(map(str, self.route))}"

class TechnicianTour:
    def __init__(self, technician_id, locations):
        self.technician_id = technician_id
        self.tour = locations  # List of tasks (location IDs and possibly other details)

    def __repr__(self):
        return f"{self.technician_id} {' '.join(map(str, self.tour))}"

class DailySchedule:
    def __init__(self, day):
        self.day = day
        self.truck_schedules = []  # List of TruckRoute objects
        self.technician_schedules = []  # List of TechnicianTour objects

    def add_truck_route(self, truck_id, locations):
        self.truck_schedules.append(TruckRoute(truck_id, locations))

    def add_technician_schedule(self, technician_id, locations):
        self.technician_schedules.append(TechnicianTour(technician_id, locations))

    def __repr__(self):
        truck_info = "\n".join(repr(truck) for truck in self.truck_schedules)
        tech_info = "\n".join(repr(tech) for tech in self.technician_schedules)
        return (f"DAY = {self.day}\n" +
                f"NUMBER_OF_TRUCKS = {len(self.truck_schedules)}\n" +
                f"{truck_info}\n" +
                f"NUMBER_OF_TECHNICIANS = {len(self.technician_schedules)}\n" +
                f"{tech_info}")

class Solution:
    def __init__(self, dataset, name, days):
        self.dataset = dataset
        self.name = name
        self.truck_distance = 0
        self.num_truck_days = 0
        self.num_trucks_used = 0
        self.technician_distance = 0
        self.num_technician_days = 0
        self.num_technicians_used = 0
        self.idle_machine_costs = 0
        self.technician_cost = 0
        self.truck_cost = 0
        self.total_cost = 0
        self.daily_schedules = [DailySchedule(day) for day in range(1,days+1)]


    def add_daily_schedule(self, daily_schedule):
        self.daily_schedules[daily_schedule.day-1] = daily_schedule

    
    def __repr__(self):
        sorted_schedules = sorted(self.daily_schedules, key=lambda x: x.day)
        return (f"DATASET = {self.dataset}\n" +
                f"NAME = {self.name}\n\n" +
                # f"TRUCK_DISTANCE = {self.truck_distance}\n" +
                # f"NUMBER_OF_TRUCK_DAYS = {self.num_truck_days}\n" +
                # f"NUMBER_OF_TRUCKS_USED = {self.num_trucks_used}\n" +
                # f"TECHNICIAN_DISTANCE = {self.technician_distance}\n" +
                # f"NUMBER_OF_TECHNICIAN_DAYS = {self.num_technician_days}\n" +
                # f"NUMBER_OF_TECHNICIANS_USED = {self.num_technicians_used}\n" +
                # f"IDLE_MACHINE_COSTS = {self.idle_machine_costs}\n" +
                # f"TOTAL_COST = {self.idle_machine_costs + self.technician_cost + self.truck_cost}\n\n" +
                "\n\n".join(repr(ds) for ds in sorted_schedules)
                )
    
    def write_to_file(self, file_path):
        with open(file_path, "w") as file: 
            file.write(self.__repr__())  # Use the string representation method to get the schedule info


