from solution import *
from VRPtruckSavings2 import *
from technicianTourGRASP import *
from instances import *
from readInstance import *

#TODO

def get_solution_file_path(instance):
        path = os.path.join(os.getcwd(), "solutions")

        file_name = instance.name.replace(" ", "_") +'.txt'
        
        return  os.path.join(path,file_name).replace("\\","/")

if __name__ == "__main__":

    instances = get_all_instances(20)
    
    for instance in instances:
        
        solution = return_final_solution(instance)
        solution.write_to_file(get_solution_file_path(instance))