import numpy as np
from solvers.grasp_solver import grasp_solver
from solvers.grasp_solver import grasp_solver_prova
from loader_data import load_data_1
from loader_data import load_data_2
from Instances.utils_instances import string_conversion
import time


if __name__ == "__main__":
    
   ## loading datasets
   json_file = "data/i07.json"
   occupants, patients, operating_theaters, rooms, nurses, surgeons, hospital = load_data_1(json_file)  
   D, num_skill_level, shift_types, age_groups, weights = load_data_2(json_file) 
   # i20 non troviamo una feasible neanche non accettando nessun non mandatory. Ma il problema è in Admit constr che non mi crea soluzione
   ## finding solution with GRASP method
   max_iter = 50
   f_best, solution, time_create_random, time_local_search = grasp_solver(D, weights, occupants, patients, operating_theaters, rooms, nurses, surgeons, max_iter)
   #f_best, solution = grasp_solver_prova(D, weights, occupants, patients, operating_theaters, rooms, nurses, surgeons, max_iter)
   print("final result:")
   print(f_best)
   print("Time for creating the initial random feasible point:")
   print(time_create_random)
   print("Time for searching a better solution in the neighborhood")
   print(time_local_search)

   # per file i20 che non va
   print(len(patients)/len(rooms))
   print(len(patients)/len(rooms))





    

    
        
    


       # distanza tra età?

    # creating model
    #model, X  = create_model(D,patient_list_id,patients)