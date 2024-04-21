from solution import *
from VRPtruckSavings2 import *
from technicianTourGRASP import *
from instances import *
from readInstance import *
from VRPtruckGurobi import *

#TODO

def get_solution_file_path(instance):
        path = os.path.join(os.getcwd(), "solutions") 

        file_name = instance.name.replace(" ", "_") +'.txt'
        
        return  os.path.join(path,file_name).replace("\\","/")

if __name__ == "__main__":

    instances = get_all_instances(20)
    
    # for instance in instances:
    # # for instance in instances[15]:
    instance = instances[16]
        
    #solution = return_final_solution(instance) # VRP savings solution

    # stored solution in 0421 solution folder
    solution = return_truck_gurobi_solution(instance) # VRP GRASP solution
    solution.write_to_file(get_solution_file_path(instance))