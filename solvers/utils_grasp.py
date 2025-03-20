from Instances.utils_instances import string_conversion
import numpy as np
import random
import math

random.seed(1000)
np.random.seed(1000)
       
def construct_feasible_solution(occupants, patients, operating_theaters, rooms, nurses, surgeons, D, dont_admit_nonMand = False):
   
   max_iter = 50
   iter = 1
   flag_stop = False
   bool5634 = False  
   bool127 = False

   while iter < max_iter and not flag_stop:
      # Choice for admission
      # data structure: binary vector 
      Adm_yes_or_no = np.random.randint(0,1, size=(len(patients),)) 

      # Date of admission for each patient from 0 to D ( X_t = D means that the patient is not admit, this is possible if the patient is not mandatory) 
      # data structure: vector of integer
      Adm_Date = np.random.randint(0,D-1, size=(len(patients),))     
      
      # Room id (col) for each patient (rows). It will be use the convention that if an element is -1  it means that the patient is not admit.
      # data structure: vector of integer
      roomXpatient = np.random.randint(0, len(rooms)-1, size=(len(patients),))  

      # OT id (col) for each patient (rows). It will be use the convention that if an element is -1 it means that the patient is not admit.
      # data structure: vector of integer

      otXpatient = np.random.randint(0, len(operating_theaters)-1, size=(len(patients),))

      # Nurse for each room (first dim) in each day (second dim) for each shift (third dim)
      # data structure: tridimensional matrix of integer
      nurseXroom = np.random.randint(0, len(nurses)-1, size=(len(rooms), D, 3))

      # Constraints:

      # 0) Each patient has only one room for all the stay: ensured by data structure
      # 0) Each room has only one nurse for each day and each shift: ensured by data structure

      # H5, H6 and H3 and H4) Force to admit every mandatory patient and be coherent with other structure (H5)
      # convention: if patient i is not admitted than otXpatient[i] = roomXpatient[i] = Adm_Date[i] = -1.
      # Each mandatory patient should be admitted between release day and due day 
      # and each non mandatory patient should be admitted after release day (H6)
      # Each surgeon should not work more than maximum surgery time (H3) and there is a maximum time for each OT (H4) 

      Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, bool5634 = admit_constr(Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, patients, D, surgeons, operating_theaters, len(rooms), dont_admit_nonMand)     
      
      if bool5634 == False: 
         iter = iter + 1
         flag_stop = False
         continue
 
      # H1, H2 and H7) limit of capacity of each room should not be overcome (H7) and in each room all people are the same gender (H1) 
      # Each patient should not be assigned to incompatible rooms (H2)

      roomXpatient, bool127 = room_constr(rooms, patients, occupants, roomXpatient, Adm_Date, Adm_yes_or_no, D)

      nurseXroom = follow_shift(nurses, nurseXroom, D)
      
      flag_stop = bool127 and bool5634
      iter = iter + 1

   print("Number of iter to find a feasible solution:")
   print(iter)

   x_feasible = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom]
   if not bool127:
      Warning("Problem in building a feasible solution due to room's constraints")
   if not bool5634:
      Warning("Problem in building a feasible solution due to date of admission or OTs, surgeons' constraints")
   return x_feasible, flag_stop


def LocalSearch(x_feasible, f_best_sofar, patients, occupants, rooms, nurses, surgeons, D, operating_theaters, weights):
   
   # Choice: mix between first Improvement and best neighbour
   # (first improvements for perturbation of date of admission and room assigned, best improvements for nurse assignement)

   # PROBLEMA SE I PAZIENTI SONO TANTI E LENTISSIMO 
   # Possibili sol: prenderne solo un numero fissato limitato e li prendo casualmente?
   # per ora ho messo "int(math.sqrt(len(patient_id_shuffle)/2))" per prenderne solo una parte (già shufflelata)
   # radice quadrata così da smorzare ad alte dimensioni 
   
   print("activating local search")

   Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom = x_feasible

   list_accepted_p = []
   for p,patient in enumerate(patients):
      if patient.mandatory:
         list_accepted_p.append(p)
      else:
         if Adm_yes_or_no[p] == 1:
            list_accepted_p.append(p)


   perturbations = ["admission_forward", "admission_backward", "room_change", "nurse_swap"]
   random.shuffle(perturbations) 

   for perturbation in perturbations:
      ##########################################################################################
      if perturbation == "admission_forward":

         # First perturbation: date of admission 
         Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom = x_feasible

         patient_id_shuffle = list_accepted_p
         random.shuffle(patient_id_shuffle)

         for p in patient_id_shuffle[0:int(math.sqrt(len(patient_id_shuffle)/2))]:
            if Adm_Date[p] == D-1 or Adm_Date[p] == D-2 or Adm_Date[p] == -1:
               continue
            Adm_Date_change = random.choices([1, 2], weights=[0.5, 0.5], k=1)[0]
            Adm_Date[p] = Adm_Date[p] + Adm_Date_change

            x = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom]
            find = check_constraint(x, occupants, patients, rooms, nurses, surgeons, D, operating_theaters) # check if feasible

            if find == True:
               # Swap nurses (between rooms) if they work in the same day and same shift (it verify constraints)
               max_inner_iter = 30   # potrebbe dipendere dal numero di stanze (tipo = numero di permutazioni)
               iter_inner = 1
               f_best = f_best_sofar
               x_best = x_feasible
               flag_improve = False
               print("Perturbation 1.1")

               # CHANGE: visto che la assegnazione stanza nurse è senza vincolo, gratis possiamo velocizzare la ricerca locale assegnando già qui dentro il terzo tipo di pert
               # Prima senza era troppo lento e non si muoveva, non si spostava di tanto
               while iter_inner < max_inner_iter:
                  iter_inner = iter_inner + 1
                  for t in range(0,D):
                     for s in range(0,3):
                        np.random.shuffle(nurseXroom[:, t, s])
                        x = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom]
                        value_try = evaluate_obj_func(x, occupants, patients, rooms, nurses, surgeons, D, weights)
                        if value_try < f_best - 1:
                           print("migliora")
                           f_best = value_try
                           x_best = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom]
                           flag_improve = True
               if flag_improve == True:
                  print("f_best_sofar")
                  print(f_best_sofar)
                  print("f find now")
                  print(f_best)
                  print("b")
                  return x_best, True, f_best
            else:
               Adm_Date[p] = Adm_Date[p] - Adm_Date_change  # restore the perturbation CHANGE

      elif perturbation == "admission_backward":

         Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom = x_feasible
         patient_id_shuffle = list_accepted_p
         random.shuffle(patient_id_shuffle)

         for p in patient_id_shuffle[0:int(math.sqrt(len(patient_id_shuffle)/2))]:
            if Adm_Date[p] == 0 or Adm_Date[p] == 1 or Adm_Date[p] == -1 :
               continue
            Adm_Date_change = random.choices([1, 2], weights=[0.5, 0.5], k=1)[0]
            Adm_Date[p] = Adm_Date[p] - Adm_Date_change

            # Check if it's feasible
            x = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom]
            find = check_constraint(x, occupants, patients, rooms, nurses, surgeons, D, operating_theaters)

            if find == True:

               # Swap nurses (between rooms) if they work in the same day and same shift (it verify constraints)
               max_inner_iter = 30   # potrebbe dipendere dal numero di stanze (tipo = numero di permutazioni)
               iter_inner = 1
               f_best = f_best_sofar
               x_best = x_feasible
               flag_improve = False
               print("Perturbation 1.2")
               while iter_inner < max_inner_iter:
                  iter_inner = iter_inner + 1
                  for t in range(0,D):
                     for s in range(0,3):
                        np.random.shuffle(nurseXroom[:, t, s])
                        x = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom]
                        value_try = evaluate_obj_func(x, occupants, patients, rooms, nurses, surgeons, D, weights)
                        if value_try < f_best - 1:
                           f_best = value_try
                           x_best = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom]
                           flag_improve = True
               if flag_improve == True:
                  print("exit from localSearch, a sol found")
                  return x_best, True, f_best
            else:
               Adm_Date[p] = Adm_Date[p] + Adm_Date_change  # restore the perturbation

      elif perturbation == "room_change":
   
         # Second perturbation: 
         Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom = x_feasible

         patient_id_shuffle = list_accepted_p
         random.shuffle(patient_id_shuffle)
         
         for p in patient_id_shuffle[0:int(math.sqrt(len(patient_id_shuffle)/2))]:
            if Adm_yes_or_no[p] == 0:
               continue
            room_old = roomXpatient[p]
            roomXpatient[p] = random.choice(list(set(range(len(rooms))) - set(patients[p].incompatible_room_ids)))

            # Check if it's feasible
            x = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom]
            find = check_constraint(x, occupants, patients, rooms, nurses, surgeons, D, operating_theaters)

            if find == True:

               # Swap nurses (between rooms) if they work in the same day and same shift (it verify constraints)
               max_inner_iter = 30    # potrebbe dipendere dal numero di stanze (tipo = numero di permutazioni)
               iter_inner = 1
               f_best = f_best_sofar
               x_best = x_feasible
               flag_improve = False
               print("Perturbation 2")
               while iter_inner < max_inner_iter:
                  iter_inner = iter_inner + 1
                  for t in range(0,D):
                     for s in range(0,3):
                        np.random.shuffle(nurseXroom[:, t, s])
                        x = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom]
                        value_try = evaluate_obj_func(x, occupants, patients, rooms, nurses, surgeons, D, weights)
                        if value_try < f_best - 1:
                           f_best = value_try
                           x_best = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom]
                           flag_improve = True
               if flag_improve == True:
                  print("exit from localSearch, a sol found")
                  return x_best, True, f_best
            else:
               roomXpatient[p] = room_old  # restore the perturbation

      elif perturbation == "nurse_swap":

         # Third perturbation: swap nurse that work in the same shift
         Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom = x_feasible

         max_inner_iter = 30     # potrebbe dipendere dal numero di stanze (tipo = numero di permutazioni)
         iter_inner = 1
         f_best = f_best_sofar
         x_best = x_feasible
         flag_improve = False
         print("Perturbation 3")
         while iter_inner < max_inner_iter:
            iter_inner = iter_inner + 1
            for t in range(0,D):
               for s in range(0,3):
                  np.random.shuffle(nurseXroom[:, t, s])
                  x = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom]
                  value_try = evaluate_obj_func(x, occupants, patients, rooms, nurses, surgeons, D, weights)
                  if value_try < f_best - 1:
                     f_best = value_try
                     x_best = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom]
                     flag_improve = True
         if flag_improve == True:
            print("exit from localSearch, a sol found")
            return x_best, True, f_best

         print("no better neighbour")

   return [], False, 0

#def LocalSearch(x_feasible, f_best_sofar, patients, occupants, rooms, nurses, surgeons, D, operating_theaters, weights):
   
   # Choice: mix between first Improvement and best neighbour
   # (first improvements for perturbation of date of admission and room assigned, best improvements for nurse assignement)
   max_iter = 1
   iter = 0

        
   # PROBLEMA SE I PAZIENTI SONO TANTI E LENTISSIMO 
   # Possibili sol: prenderne solo un numero fissato limitato e li prendo casualmente?
   
   while iter <= max_iter:
      print("it (local search)")
      print(iter)
      iter += 1

      perturbations = ["admission_forward", "admission_backward", "room_change", "nurse_swap"]
      random.shuffle(perturbations) 

      for perturbation in perturbations:
         ##########################################################################################
         if perturbation == "admission_forward":
            # First perturbation: date of admission 
            Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom = x_feasible

            patient_id_shuffle = list(range(0,len(patients)))
            random.shuffle(patient_id_shuffle)
            for p in patient_id_shuffle:
               if Adm_Date[p] == D-1 or Adm_Date[p] == D-2 or Adm_Date[p] == -1:
                  continue
               Adm_Date_change = random.choices([1, 2], weights=[0.5, 0.5], k=1)[0]
               Adm_Date[p] = Adm_Date[p] + Adm_Date_change

               x = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom]
               find = check_constraint(x, occupants, patients, rooms, nurses, surgeons, D, operating_theaters) # check if feasible

               if find == True:
                  # Swap nurses (between rooms) if they work in the same day and same shift (it verify constraints)
                  max_inner_iter = 50   # potrebbe dipendere dal numero di stanze (tipo = numero di permutazioni)
                  iter_inner = 1
                  f_best = f_best_sofar
                  x_best = x_feasible
                  flag_improve = False
                  #print("Perturbation 1.1")

                  # CHANGE: visto che la assegnazione stanza nurse è senza vincolo, gratis possiamo velocizzare la ricerca locale assegnando già qui dentro il terzo tipo di pert
                  # Prima senza era troppo lento e non si muoveva, non si spostava di tanto
                  while iter_inner < max_inner_iter:
                     iter_inner = iter_inner + 1
                     for t in range(0,D):
                        for s in range(0,3):
                           np.random.shuffle(nurseXroom[:, t, s])
                           x = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom]
                           value_try = evaluate_obj_func(x, occupants, patients, rooms, nurses, surgeons, D, weights)
                           if value_try < f_best - 1:
                              print("migliora")
                              f_best = value_try
                              x_best = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom]
                              flag_improve = True
                  if flag_improve == True:
                     print("f_best_sofar")
                     print(f_best_sofar)
                     print("f find now")
                     print(f_best)
                     print("b")
                     return x_best, True, f_best
               else:
                  Adm_Date[p] = Adm_Date[p] - Adm_Date_change  # restore the perturbation CHANGE

         ##########################################################################################
         elif perturbation == "admission_backward":

            Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom = x_feasible

            patient_id_shuffle = list(range(0,len(patients)))
            random.shuffle(patient_id_shuffle)

            for p in patient_id_shuffle:
               if Adm_Date[p] == 0 or Adm_Date[p] == 1 or Adm_Date[p] == -1 :
                  continue
               Adm_Date_change = random.choices([1, 2], weights=[0.5, 0.5], k=1)[0]
               Adm_Date[p] = Adm_Date[p] - Adm_Date_change

               # Check if it's feasible
               x = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom]
               find = check_constraint(x, occupants, patients, rooms, nurses, surgeons, D, operating_theaters)

               if find == True:

                  # Swap nurses (between rooms) if they work in the same day and same shift (it verify constraints)
                  max_inner_iter = 50   # potrebbe dipendere dal numero di stanze (tipo = numero di permutazioni)
                  iter_inner = 1
                  f_best = f_best_sofar
                  x_best = x_feasible
                  flag_improve = False
                  #print("Perturbation 1.2")
                  while iter_inner < max_inner_iter:
                     iter_inner = iter_inner + 1
                     for t in range(0,D):
                        for s in range(0,3):
                           np.random.shuffle(nurseXroom[:, t, s])
                           x = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom]
                           value_try = evaluate_obj_func(x, occupants, patients, rooms, nurses, surgeons, D, weights)
                           if value_try < f_best - 1:
                              f_best = value_try
                              x_best = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom]
                              flag_improve = True
                  if flag_improve == True:
                     print("exit from localSearch, a sol found")
                     return x_best, True, f_best
               else:
                  Adm_Date[p] = Adm_Date[p] + Adm_Date_change  # restore the perturbation
         #########################################################################################
         elif perturbation == "room_change":

            # Second perturbation: 
            Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom = x_feasible

            patient_id_shuffle = list(range(0,len(patients)))
            random.shuffle(patient_id_shuffle)
            for p in patient_id_shuffle:
               if Adm_yes_or_no[p] == 0:
                  continue
               room_old = roomXpatient[p]
               roomXpatient[p] = random.choice(list(set(range(len(rooms))) - set(patients[p].incompatible_room_ids)))

               # Check if it's feasible
               x = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom]
               find = check_constraint(x, occupants, patients, rooms, nurses, surgeons, D, operating_theaters)

               if find == True:

                  # Swap nurses (between rooms) if they work in the same day and same shift (it verify constraints)
                  max_inner_iter = 50    # potrebbe dipendere dal numero di stanze (tipo = numero di permutazioni)
                  iter_inner = 1
                  f_best = f_best_sofar
                  x_best = x_feasible
                  flag_improve = False
                  #print("Perturbation 2")
                  while iter_inner < max_inner_iter:
                     iter_inner = iter_inner + 1
                     for t in range(0,D):
                        for s in range(0,3):
                           np.random.shuffle(nurseXroom[:, t, s])
                           x = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom]
                           value_try = evaluate_obj_func(x, occupants, patients, rooms, nurses, surgeons, D, weights)
                           if value_try < f_best - 1:
                              f_best = value_try
                              x_best = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom]
                              flag_improve = True
                  if flag_improve == True:
                     print("exit from localSearch, a sol found")
                     return x_best, True, f_best
               else:
                  roomXpatient[p] = room_old  # restore the perturbation
         #########################################################################################
         elif perturbation == "nurse_swap":

            # Third perturbation: swap nurse that work in the same shift
            Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom = x_feasible

            max_inner_iter = 50     # potrebbe dipendere dal numero di stanze (tipo = numero di permutazioni)
            iter_inner = 1
            f_best = f_best_sofar
            x_best = x_feasible
            flag_improve = False
            #print("Perturbation 3")
            while iter_inner < max_inner_iter:
               iter_inner = iter_inner + 1
               for t in range(0,D):
                  for s in range(0,3):
                     np.random.shuffle(nurseXroom[:, t, s])
                     x = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom]
                     value_try = evaluate_obj_func(x, occupants, patients, rooms, nurses, surgeons, D, weights)
                     if value_try < f_best - 1:
                        f_best = value_try
                        x_best = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom]
                        flag_improve = True
            if flag_improve == True:
               print("exit from localSearch, a sol found")
               return x_best, True, f_best
         #########################################################################################
         else:
            print("problema")

   print("no better neighbour")

   return [], False, 0                           

def check_constraint(x, occupants, patients, rooms, nurses, surgeons, D, operating_theaters):

   [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom] = x

   # Constraint H1, H7  
   bool_1_7_constraint = room_constr_bool(rooms, patients, occupants, roomXpatient, Adm_yes_or_no, Adm_Date, D)

   # Constraint H3, H4
   bool_3_4_constraint = OT_and_Surgeon_constr_bool(surgeons, patients, operating_theaters, Adm_Date, otXpatient, D)
   # prima era MaxTime_constr_bool
   
   # Constraint H5, H6
   bool_6_constraint = bool_period_of_admission_constr(Adm_yes_or_no, Adm_Date, patients)
   bool_5_constraint = bool_admit_mandatory_constr(Adm_yes_or_no, patients)

   # Constraint H2  
   bool_2_constraint = bool_incompatible_room_constr(patients, roomXpatient)

   # Scheduling of nurse are already respect because of the perturbation

   constraint_vector = [
   int(bool_1_7_constraint),   
   int(bool_2_constraint),
   int(bool_3_4_constraint),  
   int(bool_5_constraint),   
   int(bool_6_constraint)  
   ]

   return all([bool_1_7_constraint, bool_3_4_constraint, bool_6_constraint, bool_5_constraint, bool_2_constraint])


def evaluate_obj_func(x, occupants, patients, rooms, nurses, surgeons, D, weights):
   Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom = x
   
   # useful structure that will be exploited 
   list_day_patientAndoccupant = [[] for _ in range(D)]
   occupant_start_index = len(patients) 

   for p, patient in enumerate(patients):
      if Adm_yes_or_no[p] == 1:  
         start_stay = Adm_Date[p]
         end_stay = min(D, start_stay + patient.length_of_stay)  
         for t in range(start_stay, end_stay):
               list_day_patientAndoccupant[t].append(p)
   for o, occupant in enumerate(occupants):   # add occupants  
      start_stay = 0
      end_stay = min(D, start_stay + occupant.length_of_stay)  
      for t in range(start_stay, end_stay):
         list_day_patientAndoccupant[t].append(occupant_start_index+o)
   
   
   # S1) quantity derives from age difference in each room
   qnt1 = 0
   for t, list_people in enumerate(list_day_patientAndoccupant):
      # Create a data structure for each room list of patient (list of list) in room that day
      list_of_set_age = [set() for _ in range(len(rooms))]
      # fill the structure
      for i in list_people:
         if i < len(patients) and Adm_yes_or_no[i] == 1:   # i is an admitted patient
            room_id = roomXpatient[i]
            list_of_set_age[room_id].add(patients[i].age_group)
         elif i >= len(patients):     # i is an occupant
            room_id = occupants[i-len(patients)].room_id 
            list_of_set_age[room_id].add(occupants[i-len(patients)].age_group)
      for set_age in list_of_set_age: 
         if len(set_age) != 0:
            qnt1 = qnt1 + (max(set_age)-min(set_age))
   qnt1 = qnt1 * weights['room_mixed_age']

   # S2) The minimum skill level a nurse must have to provide the required care for a patient during each shift of their stay should be met
   # S3) Continuity of care
   qnt2 = 0
   qnt3 = 0
   for p, patient in enumerate(patients):   
      set_nurse_p = set()
      roomXPat = roomXpatient[p]
      skill_level_req_list = patient.skill_level_required
      if Adm_yes_or_no[p] == 1:
         for t in range(Adm_Date[p], min(Adm_Date[p]+patient.length_of_stay-1, D)):
            t_0 = t-Adm_Date[p]
            skill_level_req1 = skill_level_req_list[3*(t_0)]
            skill_level_req2 = skill_level_req_list[3*(t_0)+1]
            skill_level_req3 = skill_level_req_list[3*(t_0)+2]
            skill_given_shift1 = nurses[nurseXroom[roomXPat, t, 0]].skill_level
            skill_given_shift2 = nurses[nurseXroom[roomXPat, t, 1]].skill_level
            skill_given_shift3 = nurses[nurseXroom[roomXPat, t, 2]].skill_level
            qnt2 = qnt2 + max(0, skill_level_req1 - skill_given_shift1) + max(0, skill_level_req2 - skill_given_shift2) + max(0, skill_level_req3 - skill_given_shift3)
            set_nurse_p.add(nurseXroom[roomXPat, t, 0])
            set_nurse_p.add(nurseXroom[roomXPat, t, 1])
            set_nurse_p.add(nurseXroom[roomXPat, t, 2])
         num_nurse_p = len(set_nurse_p)
         qnt3 = qnt3 + (num_nurse_p - 3)
      
   for o, occupant in enumerate(occupants):   
      set_nurse_p = set()
      room_id_o = occupant.room_id
      skill_level_req_list = occupant.skill_level_required
      for t in range(0, min(occupant.length_of_stay - 1, D )):
         
         skill_level_req1 = skill_level_req_list[3*t]
         skill_level_req2 = skill_level_req_list[3*t+1]
         skill_level_req3 = skill_level_req_list[3*t+2]
         skill_given_shift1 = nurses[nurseXroom[room_id_o, t, 0]].skill_level
         skill_given_shift2 = nurses[nurseXroom[room_id_o, t, 1]].skill_level
         skill_given_shift3 = nurses[nurseXroom[room_id_o, t, 2]].skill_level
         qnt2 = qnt2 + max(0, skill_level_req1 - skill_given_shift1) + max(0, skill_level_req2 - skill_given_shift2) + max(0, skill_level_req3 - skill_given_shift3)
         set_nurse_p.add(nurseXroom[room_id_o, t, 0])
         set_nurse_p.add(nurseXroom[room_id_o, t, 1])
         set_nurse_p.add(nurseXroom[room_id_o, t, 2])
      num_nurse_p = len(set_nurse_p)
      qnt3 = qnt3 + (num_nurse_p - 3)

   qnt2 = qnt2 * weights['room_nurse_skill']
   qnt3 = qnt3 * weights['continuity_of_care']

   # S4) maximum workload for nurse
   qnt4 = 0
   
   # Support data structure: matrix with dimension D x num_rooms x 3 in order to store workload total required in that room in that specific period:
   matrix = np.zeros((D, len(rooms), 3))
 
   for o, occupant in enumerate(occupants): # fill the data structure with info of occupants
      for t in range(0, min(D, occupant.length_of_stay)):
         for s in range(0,3):
            matrix[t,occupant.room_id, s] = matrix[t,occupant.room_id, s] + occupant.workload_produced[3*t + s]

   for p, patient in enumerate(patients):   # fill the data structure with info of patients
      if Adm_yes_or_no[p] == 0:
         continue
      for t in range(Adm_Date[p], min(D,Adm_Date[p] + patient.length_of_stay)):
         for s in range(0,3):
            t_0 = t-Adm_Date[p]
            matrix[t,roomXpatient[p],s] = matrix[t,roomXpatient[p],s] + patient.workload_produced[3*t_0 + s]
   
   for n, nurse in enumerate(nurses):   # calculate for each nurse the delta of workload
      for i, diz in enumerate(nurse.working_shifts):   
         day = diz['day']
         shift = string_conversion(diz['shift'])
         max_work = diz['max_load']
         list_idRoom = np.where(nurseXroom[:,day,shift] == n)[0]
         qnt4 = qnt4 + max(0, sum(matrix[day,list_idRoom,shift]) - max_work) # potrebbe essere un problema
   qnt4 = qnt4 * weights['nurse_eccessive_workload']

   # S5) number of OT with at least one patient (open) lead to a cost 
   qnt5 = 0
   for t in range(0,D):
      open_OT = set()
      for p,patient in enumerate(patients):
         if Adm_Date[p] == t:
            open_OT.add(otXpatient[p])
      num_open_OT = len(open_OT)
      qnt5 = qnt5 + num_open_OT
   qnt5 = qnt5 * weights['open_operating_theater']

   # S6) The number of different OTs a surgeon is assigned to per working day should be minimized
   qnt6 = 0
   for t in range(0,D):
      list_surgeonXrooms_in_t = [set() for _ in range(len(surgeons))]
      for p,patient in enumerate(patients):
         if Adm_Date[p] == t:   # when occurs the surgery
            list_surgeonXrooms_in_t[patient.surgeon_id].add(roomXpatient[p])  # obiettivo: più stanze diverse più pago
      qnt6 = qnt6 + sum(max(0,len(s)-1) for s in list_surgeonXrooms_in_t)

   qnt6 = qnt6 * weights['surgeon_transfer']

   # S7) Admission delay: The number of days between a patient’s release date and their actual date of admission should be minimized
   qnt7 = 0
   for p,patient in enumerate(patients):
      if Adm_yes_or_no[p] == 0:
         continue
      qnt7 = qnt7 + (Adm_Date[p] - patient.surgery_release_day)
   qnt7 = qnt7 * weights['patient_delay']

   # S8) The number of optional patients who are not admitted in the current scheduling period should be minimized
   qnt8 = 0
   qnt8 = np.sum(Adm_yes_or_no == 0) * weights['unscheduled_optional']

   total_cost = qnt1 + qnt2 + qnt3 + qnt4 + qnt5 + qnt6 + qnt7 + qnt8 

   return  total_cost  
   

# CONSTRUCTIVE FUNCTIONS FOR CONSTRAINTS

def admit_constr(Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, patients, D, surgeons, operating_theaters, num_rooms, dont_admit_nonMand):

   rate = (num_rooms*0.5 + len(operating_theaters)*0.5)/len(patients)    # peso di più le stanze perchè le ot sono visitate da pazienti solo in un giorno 
   prob = 1 / (1 + math.exp(-rate))    # Probability to accept the non mandatory

   
   # We impose to admit all mandatory patients
   for p, patient in enumerate(patients):
      if patient.mandatory:
         Adm_yes_or_no[p] = 1
      # CHANGE Adm_yes_or_no[p] = random.uniform(0, 1)  Non mi sembra giusto: distribuzione uniforme non è categorica
      # Idea: più aumenta il "rate" (più ci sono stanze rispetto al numero di pazienti) più aumento la prob di accettare un non mandatory
      # parte seguente NECESSARIA: ALTRIMENTI ULTIMO VINCOLO SU ROOMS VENIVA SEMPRE NON FEASIBLE perchè ammettevo troppo 
      else:
         if dont_admit_nonMand == True:   # don't admit non mandatory
            Adm_yes_or_no[p] = 0
            Adm_Date[p] = - 1
            roomXpatient[p] = -1
            otXpatient[p] = -1
         else:    # admission of non mandatory depends on how many rooms and OT are there in the hospital problem
            Adm_yes_or_no[p] = random.choices([0, 1], weights=[1 - prob, prob])[0]
            if Adm_yes_or_no[p] == 0:
               Adm_yes_or_no[p] = 0
               Adm_Date[p] = - 1
               roomXpatient[p] = -1
               otXpatient[p] = -1



   surgeons_availability = []
   for s, surgeon in enumerate(surgeons):
      surgeons_availability.append(surgeon.list_max_surgery_time)
   
   list_timeXsurgeon = [[0] * D for _ in range(len(surgeons))]   # matrix len(surgeons) X D with total time for each surgeon in each day
   list_timeXOT = [[0] * D for _ in range(len(operating_theaters))]  # matrix len(operating_theaters) X D
   

   list_mandatory_p = []
   list_non_mandatory_p = []
   for p,patient in enumerate(patients):
      if patient.mandatory:
         list_mandatory_p.append(p)
      else:
         list_non_mandatory_p.append(p)

   # CHANGE: ho visto che è più facile rispettare i vincoli se prima soddisfiamo quelli per i mandatory (che sicuramente dobbiamo accettare), mentre i 
   # non mandatory possiamo anche rifiutarli. Quindi IDEA, ditemi se vi sembra sensata, prima inserisco i mandatory, poi cerco di inserire i non mandatory e mal che vada
   # li rifiuto (quindi non vado in ordine di id di paziente ma prima prendo tutti i mandatory poi tutti i non mandatory)
   # -> se facciamo così anche adm_yes_or_no viene costruita
   # -> oss per aggiungere variabilità se vediamo che la funzione ritorna sempre false possiamo anche scegliere casualmente l'ordine con cui inserisco i pazienti nelle OT/chirurgi. 
   # es: scelgo casualmente l'indice di inizio del for 

   # Adding randomness
   random.shuffle(list_mandatory_p)
   random.shuffle(list_non_mandatory_p)

   for p in list_mandatory_p:
      patient = patients[p]
      # Inizialization:
      flag_find_configuration = False # it's true when we find a feasible situation for the patient (adm date and OT which respect the constraint)
      id_surgeonXp = patient.surgeon_id 
      tot_day_availability = surgeons_availability[id_surgeonXp]
      day_available = np.nonzero(tot_day_availability)[0]
      day_available_set = set(day_available)
      # we take the intersection between day availability of the surgeon and interval time between surgery_release and surgery_due_day
      # Mettere un controllo eventualmente se a lista seguente è vuota
      Adm_Date[p] = random.choice(list(day_available_set.intersection(range(patient.surgery_release_day, patient.surgery_due_day + 1))))
      # CHANGE: condizione di blocco del ciclo
      # questa condizione porta il ciclo a fermarsi quando almeno una di queste due variabili diventa True ma noi vogliamo che si fermi quando entrambe lo sono
      while not flag_find_configuration:
         available_OT = operating_theaters[otXpatient[p]].availability[Adm_Date[p]]
         already_used_OT = list_timeXOT[otXpatient[p]][Adm_Date[p]]
         requested_OT = patient.surgery_duration
         if (available_OT - already_used_OT) > requested_OT:  # patient is in a feasible OT
            # CHANGE: quando si entra qui non si modifica mai più il flag_day perchè è nell'altro else, quindi ho aggiunto controllo su chirurghi:
            # Ho aggiunto questa parte sotto (copiata praticamente da quello che c'è sotto)
            # DA QUI
            available_surg = surgeons_availability[id_surgeonXp][Adm_Date[p]]
            already_used_surg = list_timeXsurgeon[id_surgeonXp][Adm_Date[p]]
            requested_surg = patient.surgery_duration
            if (available_surg - already_used_surg) > requested_surg:
               # update the local variables
               list_timeXOT[otXpatient[p]][Adm_Date[p]] += patient.surgery_duration   # the OT in which the patient is assigned has enough capacity
               list_timeXsurgeon[id_surgeonXp][Adm_Date[p]] += patient.surgery_duration
               flag_find_configuration = True
            else:   # change day of admission and restart the loop while
               # CHANGE: tolgo il giorno di ammissione che non soddisfa i vincoli (altrimenti rishio loop infinito)
               day_available_set.discard(Adm_Date[p])  # avoid to pick another time the admission date that lead to a configuration not feasible
               possible_day = list(day_available_set.intersection(range(patient.surgery_release_day, patient.surgery_due_day + 1)))
               if not possible_day: # not feasible admission day
                  return [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, flag_find_configuration]
               Adm_Date[p] = random.choice(possible_day)  
            # A QUI
         else:   # change OT for the patient 
               # CHANGE: non penso di aver capito perchè si usa la OT_availability che non tiene in considerazione dei pazienti già assegnati e invece
               # usare direttamente list_timeXOT. Es: una OT può avere availability alta ma se è già tutta occupata ne ha 0. 
               # Nell'ultimo blocco if (if + elif) mi sembra manchi 
               # di considerare il fatto che se sono nella situazione in cui flag_OT = true ma il chirurgo non ha disponibilità, non entro nè nell'if nè
               # nell'elif quindi quel flag_day non vedo dove si possa aggiornare. Questo si può aggiornare nel caso in cui cambio Adm_Date[p]
               # ovvero solo se entro nell'elif  (se non si aggiorna problema perchè in caso brutti potrei avere ciclo infinito, per ora non
               # l'abbiamo mai avuto perchè la condizione sul while era sbagliata). Ultimissima cosa, quando siamo sfortunati e non si soddisfa 
               # il constraint sul chirurgo andiamo a scegliere un'altra admission date (con random.choice), il problema secondo me è che se non 
               # togliamo la data di ammissione appena verificata essere non idonea rischio di entrare in un loop infinito. Es: in day_available ho tutti 
               # giorni che non vanno bene -> ciclo all'infinito perchè continuerò a pescare giorni non idonei. Soluzione: ogni volta tolgo il giorno
               # non idoneo e se arrivo a non avere più giorni disponibili la funzione complessiva ritorna un booleano e il processo riparte da capo (da create_random_point) sperando di
               # aver messo abbastanza variabilità in modo che difficilmente ricapiti. Quindi ho aggiunto una cosa con il metodo .discard che elimina elementi nei set.
               # In caso di non abbastanza variabilità possiamo aggiungere variabilità nell'ordine con cui assegniamo la adm date e le ot (per ora è in ordine deterministico di id)
               # Prima di aggiornare list_timeXOT devo aver assegnato sia l'admission date, sia la ot al paziente. Quindi questo lo faccio solo una volta che ho trovato una
               # configurazione feasible. Es: se assegno un ot al paziente e aggiorno list_timeXOT, poi controllo il chirurgo e non rispetto i vincoli dovrò cambiare il giorno di ammissione
               # e considerare una nuova configurazione
               # ALTERNATIVA:
               list_available_Xp = [      i for i in range(len(list_timeXOT))
                  if (operating_theaters[i].availability[Adm_Date[p]] - (list_timeXOT[i][Adm_Date[p]] + patient.surgery_duration)) > 0     ]   # list of feasible OT for the patient p in the day of admission
               if not list_available_Xp:  # not an OT available, so we need to change day of admission 
                  day_available_set.discard(Adm_Date[p])  # avoid to pick another time the admission date that lead to a configuration not feasible
                  possible_day = list(day_available_set.intersection(range(patient.surgery_release_day, patient.surgery_due_day + 1)))
                  if not possible_day: # not feasible admission day for the patient
                     return [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, flag_find_configuration]
                  Adm_Date[p] = random.choice(possible_day)
               else:    # there is at least one OT available for the patient
                  otXpatient[p] = np.random.choice(list_available_Xp)
                  # Check constraint regarding surgeon
                  available_surg = surgeons_availability[id_surgeonXp][Adm_Date[p]]
                  already_used_surg = list_timeXsurgeon[id_surgeonXp][Adm_Date[p]]
                  requested_surg = patient.surgery_duration
                  if (available_surg - already_used_surg) > requested_surg:
                     list_timeXOT[otXpatient[p]][Adm_Date[p]] += patient.surgery_duration
                     list_timeXsurgeon[id_surgeonXp][Adm_Date[p]] += patient.surgery_duration
                     flag_find_configuration = True
                  else: # the surgeon can't work so much, change day of admission  
                     day_available_set.discard(Adm_Date[p])  # avoid to pick another time the admission date that lead to a configuration not feasible
                     possible_day = list(day_available_set.intersection(range(patient.surgery_release_day, patient.surgery_due_day + 1)))
                     if not possible_day: # not feasible admission day
                        return [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, flag_find_configuration]
                     Adm_Date[p] = random.choice(possible_day) 
   for p in list_non_mandatory_p:
      if Adm_yes_or_no[p] == 0:
         continue
      patient = patients[p]
      id_surgeonXp = patient.surgeon_id 
      tot_day_availability = surgeons_availability[id_surgeonXp]
      day_available = np.nonzero(tot_day_availability)[0]
      day_available_set = set(day_available)
      flag_find_configuration = False # it's true when we find a feasible situation for the patient (adm date and OT which respect the constraint)
      # we take the intersection between day availability of the surgeon and interval time between surgery_release and D
      Adm_Date[p] = random.choice(list(day_available_set.intersection(range(patient.surgery_release_day, D))))
      while not flag_find_configuration:
         available_OT = operating_theaters[otXpatient[p]].availability[Adm_Date[p]]
         already_used_OT = list_timeXOT[otXpatient[p]][Adm_Date[p]]
         requested_OT = patient.surgery_duration
         if (available_OT - already_used_OT) > requested_OT:  # patient is in a feasible OT
                     if (surgeons_availability[id_surgeonXp][Adm_Date[p]] - list_timeXsurgeon[id_surgeonXp][Adm_Date[p]]) > patient.surgery_duration:
                        list_timeXsurgeon[id_surgeonXp][Adm_Date[p]] += patient.surgery_duration
                        list_timeXOT[otXpatient[p]][Adm_Date[p]] += patient.surgery_duration
                        flag_find_configuration = True
                     else:   
                        day_available_set.discard(Adm_Date[p]) 
                        possible_day = list(day_available_set.intersection(range(patient.surgery_release_day, D)))
                        if not possible_day: # not feasible admission day
                           # the patient is not accepted
                           Adm_yes_or_no[p] = 0
                           Adm_Date[p] = -1
                           roomXpatient[p] = -1
                           otXpatient[p] = -1
                           # move on to another patient
                           break    # refering to the while
                        Adm_Date[p] = random.choice(possible_day)
         else:
            req =  patient.surgery_duration
            adm_date = Adm_Date[p]
            list_available_Xp = [      i for i in range(len(list_timeXOT))
                  if (operating_theaters[i].availability[Adm_Date[p]] - (list_timeXOT[i][Adm_Date[p]] + patient.surgery_duration)) > 0     ]   
            if not list_available_Xp:   
               day_available_set.discard(Adm_Date[p])  # avoid to pick another time the admission date that lead to a configuration not feasible
               possible_day = list(day_available_set.intersection(range(patient.surgery_release_day, D)))
               if not possible_day: # not feasible admission day
                  # the patient is not accepted
                  Adm_yes_or_no[p] = 0
                  Adm_Date[p] = -1
                  roomXpatient[p] = -1
                  otXpatient[p] = -1
                  # move on to another patient
                  break
               Adm_Date[p] = random.choice(list(day_available_set.intersection(range(patient.surgery_release_day, D))))
            else:
               otXpatient[p] = np.random.choice(list_available_Xp)
               available_surg = surgeons_availability[id_surgeonXp][Adm_Date[p]]
               already_used_surg = list_timeXsurgeon[id_surgeonXp][Adm_Date[p]]
               requested_surg = patient.surgery_duration
               if  (( available_surg - already_used_surg) > requested_surg):
                  list_timeXOT[otXpatient[p]][Adm_Date[p]] += patient.surgery_duration
                  list_timeXsurgeon[id_surgeonXp][Adm_Date[p]] += patient.surgery_duration
                  flag_find_configuration = True
               else: # the surgeon can't work so much or the new OT's time is not enough, change the day of admission  
                  day_available_set.discard(Adm_Date[p])  # avoid to pick another time the admission date that lead to a configuration not feasible
                  possible_day = list(day_available_set.intersection(range(patient.surgery_release_day, D)))
                  if not possible_day: # not feasible admission day
                     # the patient is not accepted
                     Adm_yes_or_no[p] = 0
                     Adm_Date[p] = -1
                     roomXpatient[p] = -1
                     otXpatient[p] = -1
                     # move on to another patient
                     break
                  Adm_Date[p] = random.choice(possible_day)  
   return [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, flag_find_configuration] 

# Parte per i non mandatory, stesse cose viste nella parte mandatory (vedi change) con la differenza che se per un paziente non abbiamo trovato una sistemazione lo rifiutiamo
# Perchè altrimenti anche qui si potrebbe generare un ciclo infinito (l'idea è che il codice è molto simile al mandatory, al posto del return false c'è un break + non ammissione)

def follow_shift(nurses, nurseXroom, D):  
  
  # Create useful data structure
  # id_nurse_working = 3xD matrix (rows -> shifts, columns -> days)
   
   id_nurse_working = np.empty((3, D), dtype=object)

   for s in range(3):
      for d in range(D):
         id_nurse_working[s][d] = []

   for n, nurse in enumerate(nurses):
      for s in range(3):
         for d in range(D):
               for shift_info in nurse.working_shifts:
                  if shift_info['day'] == d and s == string_conversion(shift_info["shift"]):
                     id_nurse_working[s][d].append(n)

  
   for s in range(0,3):
      for d in range(0,D):
         list_nurses_compatible = id_nurse_working[s][d]
         for r in range(0, nurseXroom.shape[0]):
            id_nurse_assigned = nurseXroom[r][d][s]
            if id_nurse_assigned not in list_nurses_compatible:
               nurseXroom[r][d][s] = random.choice(list_nurses_compatible)
   return nurseXroom


def room_constr(rooms, patients, occupants, roomXpatient, Adm_Date, Adm_yes_or_no, D):

   # per modifiche sul vincolo di GENERE: consideriamo gli occupanti (che sono attribuiti a una stanza ciascuno)
   # estraiamo per ogni stanza il genere del primo occupante (sono per forza TUTTI uguali perchè il vincolo di genere è FORTE)
   
   
   flag = False
   max_iter = 500  # non dà problemi con 1 e mettendo nel bool i vincoli sul genere
   iter  =  0
   while not flag and iter <= max_iter:

      genderXroom = dict()    # diz with key = id room and value = gender of the room (CON ALTERNATIVA NON SERVE)
      gathering_room_byGender = {
      "A": [],
      "B": [],
      }

      # Adding randomness
      occupants_shuffled = occupants[:]  
      random.shuffle(occupants_shuffled)  
      
      for o, occupant in enumerate(occupants_shuffled): 
         gender_occupant = occupant.gender
         o_room = occupant.room_id
         # Stampa per verificare il valore di gender_room
         # update the dicts
         gathering_room_byGender[gender_occupant].append(o_room)
         if o_room not in genderXroom:
            genderXroom[o_room] = gender_occupant
      
      missing_rooms = list(set(range(len(rooms))) - set(genderXroom.keys()))  # no occupants in these rooms
      # estraiamo da roomXpatient gli id dei pazienti che stanno nelle missing_rooms, tra quelli che stanno nella stessa, selezioniamo
      # quello con data di ammissione più piccola e prendiamo il suo genere
      # IMPORTANTE: ASSUNZIONE CHE STIAMO FACENDO -> supponiamo che il primo paziente/occpuante nella stanza determini anche in futuro
      # il genere perchè sennò bisognerebbe trovare pazienti/occupanti che liberano tutti insieme la stanza nello stesso momento
      # e da lì in avanti far ripartire il genere, una sorta di discontinuità (caso molto particolare, quindi lo escludiamo), per questo NON consideriamo list_of_set_gender
      # domanda: questione anche di realismo? cioè in generale gli ospedali fissano le stanze per femmine e quelli per maschi e non cambiano giusto?
      # MA creiamo genderXroom
      # Anche se nei dataset con pochi pazienti rispetto alle stanze questo potrebbe impattare (eventualmente confrontare le funzioni obiettivo, la nostra e quella che minimizza)
      #
      # CHANGE: idea, admission date è fissata.
      # Quindi la proposta è: scelgo il gender della stanza con una probabilità che dipende dalla proporzione di gender durante tutta la stay (nota perchè è fissata sia la adm date)
      # c'è nessuno allora il secondo ecc). Infatti come ne parlavamo con ceci, perchè partire dal primo e non dall'ultimo giorno per esempio? Non c'è una vera e propria priorità sulle giornate.
      # Caso peggiore: il primo giorno ammetto solo A, e gli altri solo B. La scelta è subottima. Una soluzione più robusta mi sembra quella di considerare tutta la stay
      # Per gli occupanti sì perchè loro fissano il gender. 
      # ALTERNATIVA
      
      proportion_A = 0
      proportion_B = 0

      for p, patient in enumerate(patients):
         if Adm_yes_or_no[patient.id] == 0:
            continue
         # counting how many days the patient stay in the hospital and update proportion_A
         if patient.gender == "A":
            if Adm_Date[patient.id] + patient.length_of_stay < D:
               proportion_A = proportion_A + patient.length_of_stay
            else:
               proportion_A = proportion_A + (D - Adm_Date[patient.id])
         else:
            if Adm_Date[patient.id] + patient.length_of_stay < D:
               proportion_B = proportion_B + patient.length_of_stay  
            else:
               proportion_B = proportion_B + (D - Adm_Date[patient.id])
      proportion_norm_A = proportion_A/(proportion_A + proportion_B)
      prob = proportion_norm_A

   
      for id_room in missing_rooms:
         sample = np.random.binomial(1, prob, 1)
         if sample == 1:
            genderXroom[id_room] = "A"
            gathering_room_byGender["A"].append(id_room) 
         else:
            genderXroom[id_room] = "B"
            gathering_room_byGender["B"].append(id_room) 

      # Check for gender and room constraints (capacity and compatibility)

      # CHANGE: problema nel primo ciclo for (sulle rooms), stiamo ciclando sulle stanze ma non cè un ciclo fuori sul paziente quindi patient chi è? forse l'indentature è sbagliata o forse il ciclo è scambiato con quello sotto (let me know)
      # PROBLEMA GENERALE: mi è venuto in mente che può succedere la seguente cosa e la nostra funzione non lo evita:
      # un paziente al tempo 0 può stare solo nella stanza 1,2,3. Randomicamente prendo la 1
      # Passo al tempo successivo e il paziente può stare nella stanza 2,3. Randomicamente prendo la 3
      # il problema è che per ogni tempo posso riassegnare la stanza per le esigenze di quel giorno ma trascuro tutto quello che viene prima )=
      # Quindi, fatemi sapere se sbaglio, bisogna cambiare.L'idea può essere partire da 0 diciamo e NON cambio mai la stanza ma la assegno una volta e fine. Se non raggiungo qualcosa di feasible rifaccio da capo (da construct feasible)

      # ALTERNATIVA:
      
      availability_room_x_day = np.zeros((len(rooms), D))
      for r, room in enumerate(rooms):
         availability_room_x_day[r,:] = room.capacity


      flag = True # if a feasible configuration is reached

      patients_shuffled = patients[:]  
      random.shuffle(patients_shuffled)  

      for p, patient in enumerate(patients_shuffled): 
         if Adm_yes_or_no[patient.id] == 0:
            continue
         gender_p = patient.gender
         end_period_of_stay = min(Adm_Date[patient.id] + patient.length_of_stay + 1, D) 
         # exctract compatible rooms respecting gender and incompatible rooms constraints
         compatible_rooms = set(list(range(len(rooms))))-set(patient.incompatible_room_ids)
         compatible_rooms = compatible_rooms.intersection(set(gathering_room_byGender[gender_p]))
         if not compatible_rooms:
            flag = False # not a feasible configuration
            iter = iter + 1
            break
         compatible_final = list()
         for id_room in compatible_rooms:
            # check if the room is compatible regarding the room capacity (for all the stay)
            availability_check = availability_room_x_day[id_room, Adm_Date[patient.id] : end_period_of_stay] - 1
            if np.all(availability_check >= 0):  
               compatible_final.append(id_room)
         # choose a room compatible for all the constraints and for every day
         if not compatible_final:  
            flag = False # not a feasible configuration
            iter = iter + 1
            break
         rr_comp = random.choice(compatible_final)
         roomXpatient[patient.id] = rr_comp
         availability_room_x_day[rr_comp, Adm_Date[patient.id] : end_period_of_stay] = availability_room_x_day[rr_comp, Adm_Date[patient.id] : end_period_of_stay] - 1
         iter = iter + 1
   
   return roomXpatient, flag


# BOOL FUNCTIONS FOR CONSTRAINTS

def room_constr_bool(rooms, patients, occupants, roomXpatient, Adm_yes_or_no, Adm_Date, D):   
   
   gender_X_room = [set() for _ in range(len(rooms))]

   availability_room_x_day = np.zeros((len(rooms), D))
   for r, room in enumerate(rooms):
      availability_room_x_day[r,:] = room.capacity

   for p, patient in enumerate(patients):
      if Adm_yes_or_no[p] == 0:
         continue
      start_stay = Adm_Date[p]
      end_period_of_stay = min(D, start_stay + patient.length_of_stay + 1)  
      room_assigned = roomXpatient[p]
      availability_check = availability_room_x_day[room_assigned, Adm_Date[patient.id] : end_period_of_stay] - 1
      if not np.all(availability_check >= 0):  
         Warning("Room constraints failed: maximum capacity exceeded")
         return False
      availability_room_x_day[room_assigned, start_stay : end_period_of_stay] = availability_room_x_day[room_assigned, start_stay : end_period_of_stay] - 1
      # Gender constraints
      gender_X_room[roomXpatient[p]].add(patient.gender)
   

   for r in range(0,len(rooms)):
      num_gender_r = len(gender_X_room[r])
      if num_gender_r >= 2:
         Warning("Room constraints failed: gender mix")
         return False

   return True


def bool_period_of_admission_constr(Adm_yes_or_no, Adm_Date, patients):
   for p, patient in enumerate(patients):
        amm = Adm_yes_or_no[p]
        if Adm_yes_or_no[p] == 0:
            continue  
        surgery_release = patient.surgery_release_day
        if patient.mandatory:
            if not (surgery_release <= Adm_Date[p] <= patient.surgery_due_day):
               Warning("Period of admission constraint failed")
               return False  # at least one admission date is wrong
        elif Adm_Date[p] < surgery_release:   # for non mandatory
            Warning("Period of admission constraint failed")            
            return False  # at least one admission date is wrong
   return True


def bool_admit_mandatory_constr(Adm_yes_or_no, patients):
   for p, current_patient in enumerate(patients):  
    if current_patient.mandatory and Adm_yes_or_no[p] == 0 :   
       Warning("Mandatory patient is not admitted")
       return False
   return True


def bool_incompatible_room_constr(patients, roomXpatient):
   for p, patient in enumerate(patients):
      if roomXpatient[p] in patient.incompatible_room_ids:  
         Warning("Room constraints failed: incompatible room")
         return False
   return True


def OT_and_Surgeon_constr_bool(surgeons, patients, operating_theaters, Adm_Date, otXpatient, D):
   for t in range(0,D):
      list_timeXsurgeon = np.zeros(len(surgeons))
      list_timeXOT = np.zeros(len(operating_theaters))
      # extract only patient admitted in t  
      patient_in_t = [i for i in range(len(patients)) if Adm_Date[i] == t]  # List containing index i if the date of admission is t (contain patient)
      info_patient_in_t = [patients[i] for i in patient_in_t]     
      for p, pat in enumerate(info_patient_in_t):
         list_timeXsurgeon[pat.surgeon_id] += pat.surgery_duration
         list_timeXOT[otXpatient[pat.id]] += pat.surgery_duration  
      # Check if the total amount of time for the surgeon is feasible   
      for s, surgeon in enumerate(surgeons):
         if list_timeXsurgeon[s] > surgeon.list_max_surgery_time[t]:
            Warning("Surgeon's constraint violeted: maximum time exceeded")
            return False
      # Check if the total amount of time for the OT is feasible
      for ot, OT_theater in enumerate(operating_theaters):
         if list_timeXOT[ot] > OT_theater.availability[t]:
            Warning("OT's constraint violeted: maximum time exceeded")
            return False
   return True


