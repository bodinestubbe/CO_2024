import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from gurobipy import *
import readInstance
import instances
import os

def plot_tours(solution_x, instance):
    for i in range(len(solution_x)):
        for j in range(len(solution_x)):
            if solution_x[i, j] > 0:
                plt.plot([instance.Locations[i].X, instance.Locations[j].X], [instance.Locations[i].Y, instance.Locations[j].Y], 'b-')
    plt.plot([instance.Locations[0].X], [instance.Locations[0].Y], 'ro')  # Plot depot
    for i in range(1, len(instance.Locations)):  # Plot customers
        plt.plot([instance.Locations[i].X], [instance.Locations[i].Y], 'go')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('VRPTW Solution')
    plt.show()

def solve_vrptw(instance):
    # Constants
    truck_distance_cost = instance.truckDistanceCost
    truck_day_cost = instance.truckDayCost
    truck_cost=instance.truckCost

    # Vehicle capacity
    truck_capacity = instance.truckCapacity

    # Initialize model
    m = Model("VRPTW")

    # Decision variables
    x = {}
    for i in range(len(instance.Locations)):
        for j in range(len(instance.Locations)):
            x[i, j] = m.addVar(vtype=GRB.BINARY, name=f'x_{i}_{j}')  # Whether vehicle travels from i to j

    # Objective function: minimize total cost
    m.setObjective(
    quicksum(
        quicksum(
            (instance.distances[i][j] * truck_distance_cost + truck_cost) * x[i, j] for j in range(len(instance.Locations))
        ) for i in range(len(instance.Locations))
    ) + truck_day_cost * instance.days,
    GRB.MINIMIZE
)
    for j in range(1, len(instance.Locations)):
        m.addConstr(quicksum(x[i, j] for i in range(len(instance.Locations))) <= truck_capacity)

    # Each customer is departed from exactly once
    for i in range(1, len(instance.Locations)):
        m.addConstr(quicksum(x[i, j] for j in range(len(instance.Locations))) == 1)

    # No subtours
    for i in range(1, len(instance.Locations)):
        for j in range(1, len(instance.Locations)):
            if i != j:
                m.addConstr(quicksum(x[i, k] for k in range(len(instance.Locations))) -
                            quicksum(x[k, j] for k in range(len(instance.Locations))) <= 0)

    # Optimize model
    m.optimize()

    # Get solution
    solution_x = np.zeros((len(instance.Locations), len(instance.Locations)))
    for i in range(len(instance.Locations)):
        for j in range(len(instance.Locations)):
            solution_x[i, j] = x[i, j].X

    num_trucks_used = sum(x[i, j].X for i in range(len(instance.Locations)) for j in range(len(instance.Locations)))


    return solution_x, num_trucks_used


if __name__ == "__main__":
    # Read instance
    instance = readInstance.readInstance(readInstance.getInstancePath(20))


    # Solve VRPTW
    solution_x, num_trucks_used = solve_vrptw(instance)
    print("Number of trucks used:", num_trucks_used)


    # Plot tours
    plot_tours(solution_x, instance)
