import instances
import readInstance
import numpy as np

def generate_feasible_truck_tour(instance):

    routes=[]
    depot_id=1

    for request in instances.Requests: 
        current_route = [depot_id, request.customerLocID, depot_id]
        routes.append(current_route)

    return routes

instance_path="/Users/myriam/Desktop/University /Year 3 BA /CO/Case/CO_2024/instances 2024/CO_Case2401.txt"
instance= readInstance.readInstance(instance_path)
routes = generate_feasible_truck_tour(instance)
print("Feasible Truck Routes:")
for i, route in enumerate(routes):
    print(f"Route {i+1}: {route}")
    