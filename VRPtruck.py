import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from gurobipy import *
import readInstance
import instances
import os
#new version
def solve_vrptw(instance):
    # Constants
    truck_distance_cost = instance.truckDistanceCost
    truck_day_cost = instance.truckDayCost
    truck_cost = instance.truckCost
    truck_capacity = instance.truckCapacity
    T = instance.days
    N = len(instance.Locations)

    # Initialize model
    m = Model("VRPTW")

    # Decision variables
    x = {}
    mk = {}
    vtk = {}

    for i in range(N):
        for j in range(N):
            for t in range(T):
                x[i, j, t] = m.addVar(vtype=GRB.BINARY, name=f'x_{i}_{j}_{t}')  # Whether vehicle travels from i to j on day t

    for k in range(len(instance.Technicians)):
        mk[k] = m.addVar(vtype=GRB.BINARY, name=f'm_{k}')  # Whether vehicle k is used during the planning horizon

    for k in range(len(instance.Technicians)):
        for t in range(T):
            vtk[k, t] = m.addVar(vtype=GRB.BINARY, name=f'v_{k}_{t}')  # Whether vehicle k is used during day t

    # Objective function
    m.setObjective(
        quicksum(
            quicksum(
                quicksum((instance.distances[i][j] * truck_distance_cost + truck_cost) * x[i, j, t] for t in range(T))
                for j in range(N))
            for i in range(N)
        ) + truck_day_cost * T,
        GRB.MINIMIZE
    )

    # Each request must be served by exactly one truck
    for j in range(1, N):
        m.addConstr(quicksum(x[i, j, t] for i in range(N) for t in range(T)) == 1)

    # Capacity constraint
    for t in range(T):
        for i in range(N):
            m.addConstr(quicksum(instance.Requests[j].amount * x[i, j, t] for j in range(N)) <= truck_capacity)

    # Truck must start and end at the depot
    for t in range(T):
        m.addConstr(quicksum(x[0, j, t] for j in range(N)) == quicksum(x[i, 0, t] for i in range(N)))

    # No self-loops for trucks
    for i in range(N):
        for t in range(T):
            m.addConstr(x[i, i, t] == 0)

    # Binary variable constraint
    for i in range(N):
        for j in range(N):
            for t in range(T):
                x[i, j, t].vtype = GRB.BINARY

    # Optimize model
    m.optimize()

    # Get solution
    solution_x = np.zeros((N, N, T))
    for i in range(N):
        for j in range(N):
            for t in range(T):
                solution_x[i, j, t] = x[i, j, t].X

    num_trucks_used = sum(sum(sum(x[i, j, t].X for t in range(T)) for j in range(N)) for i in range(N))

    return solution_x, num_trucks_used

if __name__ == "__main__":
    # Read instance
    instance = readInstance.readInstance(readInstance.getInstancePath(20))

    # Solve VRPTW
    solution_x, num_trucks_used = solve_vrptw(instance)
    print("Number of trucks used:", num_trucks_used)

    # Plot tours
    def plot_tours(solution_x, instance):
        for t in range(instance.days):
            plt.figure()
            plt.title(f'VRPTW Solution for Day {t+1}')
            for i in range(len(solution_x)):
                for j in range(len(solution_x)):
                    if solution_x[i, j, t] > 0:
                        plt.plot([instance.Locations[i].X, instance.Locations[j].X], [instance.Locations[i].Y, instance.Locations[j].Y], 'b-')
            plt.plot([instance.Locations[0].X], [instance.Locations[0].Y], 'ro')  # Plot depot
            for i in range(1, len(instance.Locations)):  # Plot customers
                plt.plot([instance.Locations[i].X], [instance.Locations[i].Y], 'go')
            plt.xlabel('X')
            plt.ylabel('Y')
            plt.show()

    plot_tours(solution_x, instance)


