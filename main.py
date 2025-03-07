import numpy as np
from solvers.grasp_solver import grasp_solver
from loader_data import load_data_1
from loader_data import load_data_2
from Instances.utils_instances import string_conversion
import random

random.seed(1000)

if __name__ == "__main__":
    
   ## loading datasets
   json_file = "data/i01.json"
   occupants, patients, operating_theaters, rooms, nurses, surgeons, hospital = load_data_1(json_file)   # manca hospital
   D, num_skill_level, shift_types, age_groups, weights = load_data_2(json_file)
   
   print("Occupants:", occupants)
   print("Patients:", patients)
   print("Operating Theaters:", operating_theaters)
   print("Rooms:", rooms)
   print("Nurses:", nurses)
   print("Surgeons:", surgeons)
   
   ## Decision variables

   # Date of admission for each patient from 0 to D ( X_t = D means that the patient is not admit, this is possible if the patient is not mandatory)  
   # Room id (col) for each patient (rows). It will be use the convention that if a row is [0,0] it means that the patient is not admit.
   # OT id (col) for each patient (rows). It will be use the convention that if a row is [0,0] it means that the patient is not admit.
   # Nurse for each room (first dim) in each day (second dim) for each shift (third dim)
   # it will be exploited the fact that each row rapresent a specific patient for exctract patient id eventually (e.g. "p000" -> first col, "p009" -> tenth col)
   # and similarly room id r00 is rapresent with 0
   

   ## finding solution with GRASP method

   max_iteration = 5
   print("ciao1")

   '''
   PARTI AGGIUNTE: creaiamo questa struttura dati puù agevole per controllare successivamente che 
   la soluzione randomica rispetti i turni degli infermieri nel dataset (usata in follow_shift)
   id_nurse_working = matrice 3xD (riche -> shift, colonne -> giorni)
   OSS: la inseriamo come INPUT in grasp_solver
   '''
   id_nurse_working = np.empty((3, D), dtype = object)
   
   for n, nurse in enumerate(nurses):
      for s in range(0, 3):
         for d in range(0, D):
            if d == nurse.working_shifts["day"] and s == string_conversion(nurse.working_shifts["shift"]):
               id_nurse_working[s][d].append(n)
 
   f_best, solution = grasp_solver(D, weights, occupants, patients, operating_theaters, rooms, nurses, surgeons, max_iteration, id_nurse_working)
                  





    

    
        
    


       # distanza tra età?

    # creating model
    #model, X  = create_model(D,patient_list_id,patients)