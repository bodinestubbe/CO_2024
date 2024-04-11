
import os
import instances


# def getInt():   
# def checkAssignment(string,  value):
     
     

# def getNextLine(f):
#     line = '\n'
#     while line and not line.strip():
#         line = f.readline()
#     return line

def readInstance(instance_path):
    
    try:
        f = open(instance_path,'r')
    except :
        print("error occured opening the file")
    

    print(f.readlines())


     
     

def getInstancePath(instance_number):
    path = os.path.join(os.getcwd(), "instances 2024")

    file_name = "CO_Case24"
    if instance_number < 10:
            file_name +='0'+ str(instance_number)+ '.txt'
    else:
            file_name += str(instance_number)+ '.txt'
    return  os.path.join(path,file_name).replace("\\","/")

if __name__ == "__main__":
    
    num_instances_to_test = 2

    
    for i in range(1,num_instances_to_test):
        instance_path = getInstancePath(i)
        print(instance_path)
        readInstance(instance_path)

        
