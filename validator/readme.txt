This folder contains a python script which can be used to validate your solutions. You need to put the three .py files included here in the same folder as your instance and solution.

This folder contains an example instance named student002, together with a valid solution for this instance. You can use these to test the validator.

To validate instance student002, execute the validator with arguments:
python Validate.py --instance student002.txt --solution student002sol.txt

It should give output like this:

File student002sol.txt is a valid solution
The given solution information is correct
        TruckDistance: 1551
        NrTruckDays: 6
        NrTrucksUsed 4
        TechnicianDistance: 1119
        NrTechnicianDays: 4
        NrTechniciansUsed: 2
        IdleMachineCost: 0
        Cost: 464205

Also try the validator with a wrong solution and see what happens!

Additional usage information of this script can be found by running:
python SolutionVerolog2019.py --help
