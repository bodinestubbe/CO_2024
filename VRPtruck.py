from instances import Instance as Instance
import readInstance
import numpy as np

def generate_feasible_truck_tour(instance):

    routes=[]
    depot_id=1

    for request in instance.Requests:
        current_route = [depot_id, request.customerLocID, depot_id]
        routes.append(current_route)

    return routes

instance= readInstance.readInstance(readInstance.getInstancePath(20))
routes = generate_feasible_truck_tour(instance)
print("Feasible Truck Routes:")
for i, route in enumerate(routes):
    print(f"Route {i+1}: {route}")
    