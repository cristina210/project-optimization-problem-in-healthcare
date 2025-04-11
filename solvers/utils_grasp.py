from Instances.utils_instances import string_conversion
import numpy as np
import random
import math
import copy

random.seed(42)
np.random.seed(42)
       
def construct_feasible_solution(occupants, patients, operating_theaters, rooms, nurses, surgeons, D, dont_admit_nonMand = False):
   
   max_iter = 200
   iter = 1
   flag_stop = False
   bool5634 = False  
   bool127 = False

   while iter < max_iter and not flag_stop:
      
      ##✅  Initializing decision variables
      
      # Choice for admission
      # data structure: binary vector 
      Adm_yes_or_no = np.random.randint(0,1, size=(len(patients),)) 

      # Date of admission for each patient 
      # data structure: vector of integer from 0 to D-1
      Adm_Date = np.random.randint(0,D-1, size=(len(patients),))     
      
      # Room id for each patient
      # data structure: vector of integer
      roomXpatient = np.random.randint(0, len(rooms)-1, size=(len(patients),))  

      # OT id for each patient 
      # data structure: vector of integer

      otXpatient = np.random.randint(0, len(operating_theaters)-1, size=(len(patients),))

      # Nurse id for each room (first dim) in each day (second dim) in each shift (third dim)
      # data structure: tridimensional matrix of integer
      nurseXroom = np.random.randint(0, len(nurses)-1, size=(len(rooms), D, 3))

      ##🚑 Constraints:

      # 0) Each patient has only one room for all the stay: ensured by data structure
      # 0) Each room has only one nurse for each day and each shift: ensured by data structure

      #🚑 Constraints: H5, H6, H3 and H4
      # Convention: if patient i is not admitted than otXpatient[i] = roomXpatient[i] = Adm_Date[i] = -1.
      # H5 --> Each mandatory patient should be admitted between release day and due day 
      # H6 --> Each non mandatory patient should be admitted after release day 
      # H3 --> Each surgeon should not work more than maximum surgery time 
      # H4 --> Each OT has a maximum time 

      Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, bool5634 = admit_constr(Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, patients, D, surgeons, operating_theaters, len(rooms), dont_admit_nonMand)     
      
      if bool5634 == False: 
         iter = iter + 1
         flag_stop = False
         continue
 
      #🚑 H1, H2 and H7) 
      # H7 --> Limit of capacity of each room should not be overcome 
      # H1 --> In each room all people have the same gender
      # H2 --> Each patient should not be assigned to incompatible rooms 

      roomXpatient, bool127 = room_constr(rooms, patients, occupants, roomXpatient, Adm_Date, Adm_yes_or_no, D)

      nurseXroom = follow_shift(nurses, nurseXroom, D)
      
      flag_stop = bool127 and bool5634
      iter = iter + 1

   print("Number of iter to find a feasible solution:")
   print(iter)

   x_feasible = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom]

   return x_feasible, flag_stop

def LocalSearch(x_feasible, f_best_sofar, patients, occupants, rooms, nurses, surgeons, D, operating_theaters, weights):

   Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom = x_feasible

   list_accepted_p = []
   for p,patient in enumerate(patients):
      if patient.mandatory:
         list_accepted_p.append(p)
      else:
         if Adm_yes_or_no[p] == 1:
            list_accepted_p.append(p)

   # type of perturbation
   perturbations = ["admission_forward", "admission_backward", "room_change", "nurse_swap"]
   random.shuffle(perturbations) 

   for perturbation in perturbations:
      # 🔁 Shifting admission date forward
      if perturbation == "admission_forward":
 
         Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom = x_feasible

         patient_id_shuffle = list_accepted_p
         random.shuffle(patient_id_shuffle)

         for p in patient_id_shuffle[0:int(math.sqrt(len(patient_id_shuffle)/2))]:
            if Adm_Date[p] == D-1 or Adm_Date[p] == D-2 or Adm_Date[p] == -1:
               continue
            Adm_Date_change = random.choices([1, 2], weights=[0.5, 0.5], k=1)[0]
            Adm_Date[p] = Adm_Date[p] + Adm_Date_change

            x = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom]
            find = check_constraint(x, occupants, patients, rooms, nurses, surgeons, D, operating_theaters) 

            if find == True:
               max_inner_iter = 30   
               iter_inner = 1
               f_best = f_best_sofar
               x_best = x_feasible
               flag_improve = False
               
               # Best improvement choice for nurses shift variable
               while iter_inner < max_inner_iter:
                  iter_inner = iter_inner + 1
                  for t in range(0,D):
                     for s in range(0,3):
                        np.random.shuffle(nurseXroom[:, t, s])
                        x = copy.deepcopy([Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom])
                        value_try = evaluate_obj_func(x, occupants, patients, rooms, nurses, surgeons, D, weights)
                        if value_try < f_best - 1:
                           f_best = value_try
                           x_best = copy.deepcopy([Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom])
                           flag_improve = True
               if flag_improve == True:
                  return x_best, True, f_best
               else: 
                  Adm_Date[p] = Adm_Date[p] - Adm_Date_change  # restore the perturbation
            else:
               Adm_Date[p] = Adm_Date[p] - Adm_Date_change  # restore the perturbation 

      # 🔁 Admission perturbation: shifting admission date backward
      elif perturbation == "admission_backward":

         Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom = x_feasible
         patient_id_shuffle = list_accepted_p
         random.shuffle(patient_id_shuffle)

         for p in patient_id_shuffle[0:int(math.sqrt(len(patient_id_shuffle)/2))]:
            if Adm_Date[p] == 0 or Adm_Date[p] == 1 or Adm_Date[p] == -1 :
               continue
            Adm_Date_change = random.choices([1, 2], weights=[0.5, 0.5], k=1)[0]
            Adm_Date[p] = Adm_Date[p] - Adm_Date_change

            x = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom]
            find = check_constraint(x, occupants, patients, rooms, nurses, surgeons, D, operating_theaters)

            if find == True:

               max_inner_iter = 30   
               iter_inner = 1
               f_best = f_best_sofar
               x_best = x_feasible
               flag_improve = False
               
               # Best improvement choice for nurses shift variable
               while iter_inner < max_inner_iter:
                  iter_inner = iter_inner + 1
                  for t in range(0,D):
                     for s in range(0,3):
                        np.random.shuffle(nurseXroom[:, t, s])
                        x = copy.deepcopy([Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom])
                        value_try = evaluate_obj_func(x, occupants, patients, rooms, nurses, surgeons, D, weights)
                        if value_try < f_best - 1:
                           f_best = value_try
                           x_best = copy.deepcopy([Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom])
                           flag_improve = True
               if flag_improve == True:
                  return x_best, True, f_best
               else:
                  Adm_Date[p] = Adm_Date[p] + Adm_Date_change   # restore the perturbation
            else:
               Adm_Date[p] = Adm_Date[p] + Adm_Date_change  # restore the perturbation

      # 🔁 Room perturbation: random choice
      elif perturbation == "room_change":

         Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom = x_feasible

         patient_id_shuffle = list_accepted_p
         random.shuffle(patient_id_shuffle)
         
         for p in patient_id_shuffle[0:int(math.sqrt(len(patient_id_shuffle)/2))]:
            if Adm_yes_or_no[p] == 0:
               continue
            room_old = roomXpatient[p]
            roomXpatient[p] = random.choice(list(set(range(len(rooms))) - set(patients[p].incompatible_room_ids)))

            x = copy.deepcopy([Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom])
            find = check_constraint(x, occupants, patients, rooms, nurses, surgeons, D, operating_theaters)

            if find == True:
               max_inner_iter = 30   
               iter_inner = 1
               f_best = f_best_sofar
               x_best = x_feasible
               flag_improve = False
               
               # Best improvement choice for nurses shift variable
               while iter_inner < max_inner_iter:
                  iter_inner = iter_inner + 1
                  for t in range(0,D):
                     for s in range(0,3):
                        np.random.shuffle(nurseXroom[:, t, s])
                        x = copy.deepcopy([Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom])
                        value_try = evaluate_obj_func(x, occupants, patients, rooms, nurses, surgeons, D, weights)
                        if value_try < f_best - 1:
                           f_best = value_try
                           x_best = copy.deepcopy([Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom])
                           flag_improve = True
               if flag_improve == True:
                  return x_best, True, f_best
               else:
                  roomXpatient[p] = room_old  # restore the perturbation
            else:
               roomXpatient[p] = room_old  # restore the perturbation

      # Nurse perturbation: shuffle rooms assigned to nurses that work in the same shift
      elif perturbation == "nurse_swap":

         Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom = x_feasible

         max_inner_iter = 70     
         iter_inner = 1
         f_best = f_best_sofar
         x_best = x_feasible
         flag_improve = False
         
         while iter_inner < max_inner_iter:
            iter_inner = iter_inner + 1
            for t in range(0,D):
               for s in range(0,3):
                  np.random.shuffle(nurseXroom[:, t, s])
                  x = copy.deepcopy([Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom])
                  value_try = evaluate_obj_func(x, occupants, patients, rooms, nurses, surgeons, D, weights)
                  if value_try < f_best - 1:
                     f_best = value_try
                     x_best = copy.deepcopy([Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom])
                     flag_improve = True
         if flag_improve == True:
            return x_best, True, f_best

   return [], False, 0

def check_constraint(x, occupants, patients, rooms, nurses, surgeons, D, operating_theaters):

   [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom] = x

   # Constraint H1, H7  
   bool_1_7_constraint = room_constr_bool(rooms, patients, occupants, roomXpatient, Adm_yes_or_no, Adm_Date, D)

   # Constraint H3, H4
   bool_3_4_constraint = OT_and_Surgeon_constr_bool(surgeons, patients, operating_theaters, Adm_Date, otXpatient, D)
   
   # Constraint H5, H6
   bool_6_constraint = bool_period_of_admission_constr(Adm_yes_or_no, Adm_Date, patients)
   bool_5_constraint = bool_admit_mandatory_constr(Adm_yes_or_no, patients)

   # Constraint H2  
   bool_2_constraint = bool_incompatible_room_constr(patients, roomXpatient)

   constraint_vector = [
   int(bool_1_7_constraint),   
   int(bool_2_constraint),
   int(bool_3_4_constraint),  
   int(bool_5_constraint),   
   int(bool_6_constraint)  
   ]

   return all([bool_1_7_constraint, bool_3_4_constraint, bool_6_constraint, bool_5_constraint, bool_2_constraint])

def evaluate_obj_func(x, occupants, patients, rooms, nurses, surgeons, D, weights, printing = False):
   Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom = x
   total_cost = 0
   
   # "list_day_patientAndoccupant" is a useful structure that will be exploited:
   # a list for each day (0 to D-1) containing the indices of all patients and occupants 
   # present in the hospital on that day. 
   
   list_day_patientAndoccupant = [[] for _ in range(D)]
   occupant_start_index = len(patients) 

   for p, patient in enumerate(patients):
      if Adm_yes_or_no[p] == 1:  
         start_stay = Adm_Date[p]
         end_stay = min(D, start_stay + patient.length_of_stay)  
         for t in range(start_stay, end_stay):
               list_day_patientAndoccupant[t].append(p)
   for o, occupant in enumerate(occupants):  
      start_stay = 0
      end_stay = min(D, start_stay + occupant.length_of_stay)  
      for t in range(start_stay, end_stay):
         list_day_patientAndoccupant[t].append(occupant_start_index+o)
   
   
   # S1) Cost deriving from soft constraint: Room age
   qnt1 = 0
   for t, list_people in enumerate(list_day_patientAndoccupant):
      list_of_set_age = [set() for _ in range(len(rooms))]
      for i in list_people:
         if i < len(patients) and Adm_yes_or_no[i] == 1:  
            room_id = roomXpatient[i]
            list_of_set_age[room_id].add(patients[i].age_group)
         elif i >= len(patients):     
            room_id = occupants[i-len(patients)].room_id 
            list_of_set_age[room_id].add(occupants[i-len(patients)].age_group)
      for set_age in list_of_set_age: 
         if len(set_age) != 0:
            qnt1 = qnt1 + (max(set_age)-min(set_age))
   qnt1 = qnt1 * weights['room_mixed_age']

   # S2) Cost deriving from soft constraint: skill level required
   # S3) Cost deriving from soft constraint: Continuity of care
   qnt2 = 0
   qnt3 = 0
   for p, patient in enumerate(patients):   
      set_nurse_p = set()
      roomXPat = roomXpatient[p]
      skill_level_req_list = patient.skill_level_required
      if Adm_yes_or_no[p] == 1:
         for t in range(Adm_Date[p], min(Adm_Date[p]+patient.length_of_stay, D)):
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
         qnt3 = qnt3 + (num_nurse_p )
      
   for o, occupant in enumerate(occupants):   
      set_nurse_p = set()
      room_id_o = occupant.room_id
      skill_level_req_list = occupant.skill_level_required
      for t in range(0, min(occupant.length_of_stay, D )):
         
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
      qnt3 = qnt3 + num_nurse_p

   qnt2 = qnt2 * weights['room_nurse_skill']
   qnt3 = qnt3 * weights['continuity_of_care']

   # S4) Cost deriving from soft constraint: maximum workload for nurse
   qnt4 = 0
   
   # Support data structure: 
   # matrix with dimension D x num_rooms x 3 in order to store workload total required in that room in that specific period
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
   
   # Calculate for each nurse the delta of workload
   for n, nurse in enumerate(nurses):   
      for i, diz in enumerate(nurse.working_shifts):   
         day = diz['day']
         shift = string_conversion(diz['shift'])
         max_work = diz['max_load']
         list_idRoom = np.where(nurseXroom[:,day,shift] == n)[0]
         qnt4 = qnt4 + max(0, sum(matrix[day,list_idRoom,shift]) - max_work) 
   qnt4 = qnt4 * weights['nurse_eccessive_workload']

   # S5) Cost deriving from soft constraint: number of OT with at least one patient (open) lead to a cost 
   qnt5 = 0
   for t in range(0,D):
      open_OT = set()
      for p,patient in enumerate(patients):
         if Adm_Date[p] == t:
            open_OT.add(otXpatient[p])
      num_open_OT = len(open_OT)
      qnt5 = qnt5 + num_open_OT
   qnt5 = qnt5 * weights['open_operating_theater']

   # S6) Cost deriving from soft constraint: surgeon transfer
   qnt6 = 0
   for t in range(0,D):
      list_surgeonXrooms_in_t = [set() for _ in range(len(surgeons))]
      for p,patient in enumerate(patients):
         if Adm_Date[p] == t:   
            list_surgeonXrooms_in_t[patient.surgeon_id].add(otXpatient[p]) 
      qnt6 = qnt6 + sum(max(0,len(s)-1) for s in list_surgeonXrooms_in_t)

   qnt6 = qnt6 * weights['surgeon_transfer']

   # S7) Cost deriving from soft constraint: admission delay
   qnt7 = 0
   for p,patient in enumerate(patients):
      if Adm_yes_or_no[p] == 0:
         continue
      qnt7 = qnt7 + (Adm_Date[p] - patient.surgery_release_day)
   qnt7 = qnt7 * weights['patient_delay']

   # S8) Cost deriving from soft constraint: unschedule non mandatory patients
   qnt8 = 0
   qnt8 = np.sum(Adm_yes_or_no == 0) * weights['unscheduled_optional']

   total_cost = qnt1 + qnt2 + qnt3 + qnt4 + qnt5 + qnt6 + qnt7 + qnt8 

   if printing == True:
     print('weights:', qnt1, qnt2, qnt3, qnt4, qnt5, qnt6, qnt7, qnt8)

   return  total_cost    

## Constructive function:

def admit_constr(Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, patients, D, surgeons, operating_theaters, num_rooms, dont_admit_nonMand):

   ## Decision if admit or not a patient
   prob = 1 # Probability with which we decide if admitting or not the non mandatory patient
   for p, patient in enumerate(patients):
      if patient.mandatory:   # admit all mandatory patient
         Adm_yes_or_no[p] = 1
      else:
         if dont_admit_nonMand == True:   # don't admit non mandatory because otherwise a feasible solution was not found
            Adm_yes_or_no[p] = 0
            Adm_Date[p] = - 1
            roomXpatient[p] = -1
            otXpatient[p] = -1
         else:    
            Adm_yes_or_no[p] = random.choices([0, 1], weights=[1 - prob, prob])[0]  
            if Adm_yes_or_no[p] == 0:
               Adm_yes_or_no[p] = 0
               Adm_Date[p] = - 1
               roomXpatient[p] = -1
               otXpatient[p] = -1
               
   
   # Useful structure for keeping track of remaining OT's and surgeon's availability
   surgeons_availability = []
   for s, surgeon in enumerate(surgeons):
      surgeons_availability.append(surgeon.list_max_surgery_time)
   list_timeXsurgeon = [[0] * D for _ in range(len(surgeons))]   
   list_timeXOT = [[0] * D for _ in range(len(operating_theaters))]  

   list_mandatory_p = []
   list_non_mandatory_p = []
   for p,patient in enumerate(patients):
      if patient.mandatory:
         list_mandatory_p.append(p)
      else:
         list_non_mandatory_p.append(p)

   # Adding randomness
   random.shuffle(list_mandatory_p)
   random.shuffle(list_non_mandatory_p)

   ## Process each mandatory patient giving each of them and admission date and an OT which is feasible
   # Iterate over all mandatory patients
   for p in list_mandatory_p:
      patient = patients[p]
      flag_find_configuration = False  # Set to True when a feasible scheduling is found for the patient
      id_surgeonXp = patient.surgeon_id

      # Get the availability of the surgeon and extract available days
      tot_day_availability = surgeons_availability[id_surgeonXp]
      day_available = np.nonzero(tot_day_availability)[0]
      day_available_set = set(day_available)

      # Randomly select an admission date within the patient’s release-due window and surgeon's availability
      Adm_Date[p] = random.choice(list(day_available_set.intersection(range(patient.surgery_release_day, patient.surgery_due_day + 1))))

      # Try to find a feasible operating theater (OT) and surgeon configuration for the selected admission day
      while not flag_find_configuration:
         available_OT = operating_theaters[otXpatient[p]].availability[Adm_Date[p]]
         already_used_OT = list_timeXOT[otXpatient[p]][Adm_Date[p]]
         requested_OT = patient.surgery_duration

         # Check if the selected OT has enough free time
         if (available_OT - already_used_OT) > requested_OT:
               available_surg = surgeons_availability[id_surgeonXp][Adm_Date[p]]
               already_used_surg = list_timeXsurgeon[id_surgeonXp][Adm_Date[p]]
               requested_surg = patient.surgery_duration

               # Check if the surgeon has enough available time on that day
               if (available_surg - already_used_surg) > requested_surg:
                  # Reserve time slots for both OT and surgeon
                  list_timeXOT[otXpatient[p]][Adm_Date[p]] += patient.surgery_duration
                  list_timeXsurgeon[id_surgeonXp][Adm_Date[p]] += patient.surgery_duration
                  flag_find_configuration = True  # Feasible scheduling found
               else:
                  # Remove this day from possible choices and retry with another day
                  day_available_set.discard(Adm_Date[p])
                  possible_day = list(day_available_set.intersection(range(patient.surgery_release_day, patient.surgery_due_day + 1)))
                  if not possible_day:
                     return [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, flag_find_configuration]
                  Adm_Date[p] = random.choice(possible_day)

         else:
               # No available time in the initially assigned OT, search for alternative feasible OTs
               list_available_Xp = [
                  i for i in range(len(list_timeXOT))
                  if (operating_theaters[i].availability[Adm_Date[p]] - (list_timeXOT[i][Adm_Date[p]] + patient.surgery_duration)) > 0
               ]

               # If no OTs available, change admission day
               if not list_available_Xp:
                  day_available_set.discard(Adm_Date[p])
                  possible_day = list(day_available_set.intersection(range(patient.surgery_release_day, patient.surgery_due_day + 1)))
                  if not possible_day:
                     return [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, flag_find_configuration]
                  Adm_Date[p] = random.choice(possible_day)
               else:
                  # At least one OT is feasible, randomly assign one and check surgeon constraint
                  otXpatient[p] = np.random.choice(list_available_Xp)
                  available_surg = surgeons_availability[id_surgeonXp][Adm_Date[p]]
                  already_used_surg = list_timeXsurgeon[id_surgeonXp][Adm_Date[p]]
                  requested_surg = patient.surgery_duration

                  if (available_surg - already_used_surg) > requested_surg:
                     # Reserve slots and mark configuration as feasible
                     list_timeXOT[otXpatient[p]][Adm_Date[p]] += patient.surgery_duration
                     list_timeXsurgeon[id_surgeonXp][Adm_Date[p]] += patient.surgery_duration
                     flag_find_configuration = True
                  else:
                     # Surgeon not available enough; retry with another day
                     day_available_set.discard(Adm_Date[p])
                     possible_day = list(day_available_set.intersection(range(patient.surgery_release_day, patient.surgery_due_day + 1)))
                     if not possible_day:
                           return [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, flag_find_configuration]
                     Adm_Date[p] = random.choice(possible_day)
   # DA QUA A COMMENTARE
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


# def room_constr(rooms, patients, occupants, roomXpatient, Adm_Date, Adm_yes_or_no, D):

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

      for o, occupant in enumerate(occupants):
         id_room_oc = occupant.room_id
         start_stay = 0
         end_stay = occupant.length_of_stay
         availability_room_x_day[id_room_oc, start_stay:end_stay + 1] = availability_room_x_day[id_room_oc, start_stay:end_stay+1] -1
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

# def room_constr_bool(rooms, patients, occupants, roomXpatient, Adm_yes_or_no, Adm_Date, D):   
   
   gender_X_room = [set() for _ in range(len(rooms))]

   availability_room_x_day = np.zeros((len(rooms), D))
   for r, room in enumerate(rooms):
      availability_room_x_day[r,:] = room.capacity
      
   for o, occupant in enumerate(occupants):
         id_room_oc = occupant.room_id
         start_stay = 0
         end_stay = occupant.length_of_stay
         availability_room_x_day[id_room_oc, start_stay:end_stay + 1] = availability_room_x_day[id_room_oc, start_stay:end_stay+1] -1
         
   for p, patient in enumerate(patients):
      if Adm_yes_or_no[p] == 0:
         continue
      start_stay = Adm_Date[p]
      end_period_of_stay = min(D, start_stay + patient.length_of_stay + 2)  
      room_assigned = roomXpatient[p]
      availability_check = availability_room_x_day[room_assigned, Adm_Date[patient.id] : end_period_of_stay] - 1
      if not np.all(availability_check >= 0):  
         # Warning(f"🚨 Room {room_assigned} exceeds capacity on days {start_stay}-{end_period_of_stay}")
         print("Availability matrix:\n", availability_room_x_day)
         return False

      
      availability_room_x_day[room_assigned, start_stay : end_period_of_stay] = availability_room_x_day[room_assigned, start_stay : end_period_of_stay] - 1
      # print(availability_room_x_day)
      # Gender constraints
      gender_X_room[roomXpatient[p]].add(patient.gender)
   

   for r in range(0,len(rooms)):
      num_gender_r = len(gender_X_room[r])
      if num_gender_r >= 2:
         Warning("Room constraints failed: gender mix")
         return False

   return True

def room_constr(rooms, patients, occupants, roomXpatient, Adm_Date, Adm_yes_or_no, D):
   
   flag = False
   max_iter = 500  
   iter  =  0
   while not flag and iter <= max_iter:

      # Adding randomness
      occupants_shuffled = occupants[:]  
      random.shuffle(occupants_shuffled) 

      rooms_shuffled = rooms[:]
      random.shuffle(rooms_shuffled)

      gender_room_x_day = np.full((len(rooms), D), 'N', dtype=object)

      availability_room_x_day = np.zeros((len(rooms), D))
      for r, room in enumerate(rooms):
         availability_room_x_day[r,:] = room.capacity
      
      # locate occupant in rooms already assigned
      
      for o, occupant in enumerate(occupants): 
         gender_occupant = occupant.gender
         o_room = occupant.room_id
         stay =  occupant.length_of_stay + 1
         gender_room_x_day[o_room, 0: stay] = gender_occupant

      for o, occupant in enumerate(occupants):
         id_room_oc = occupant.room_id
         start_stay = 0
         end_stay = occupant.length_of_stay
         availability_room_x_day[id_room_oc, start_stay:end_stay + 1] = availability_room_x_day[id_room_oc, start_stay:end_stay + 1]  - 1

      flag = True # if a feasible configuration is reached

      patients_shuffled = patients[:]  
      random.shuffle(patients_shuffled)  

      for _, patient in enumerate(patients_shuffled): 
         if Adm_yes_or_no[patient.id] == 0:
            continue
         gender_p = patient.gender
         start_period_of_day = Adm_Date[patient.id]
         end_period_of_stay = min(Adm_Date[patient.id] + patient.length_of_stay + 1, D) 
         # exctract compatible rooms respecting gender and incompatible rooms constraints
         compatible_rooms = set(list(range(len(rooms))))-set(patient.incompatible_room_ids)
         # create "room_gender_comp" which contains room which are feasible for the patient aka are empty or with the same gender
         room_gender_comp = []
         for _, room in enumerate(rooms_shuffled):
            id_room = room.id
            sub_list = gender_room_x_day[id_room, start_period_of_day : end_period_of_stay ]
            if np.all(np.isin(sub_list, ['N', gender_p])):
               room_gender_comp.append(id_room)
         compatible_rooms = compatible_rooms.intersection(room_gender_comp)
         if not compatible_rooms:
            flag = False # not a feasible configuration
            iter = iter + 1
            break
         compatible_final = list()
         for id_room in compatible_rooms:
            # check if the room is compatible regarding the room capacity (for all the stay)
            availability_check = availability_room_x_day[id_room, start_period_of_day : end_period_of_stay] - 1
            if np.all(availability_check >= 0):  
               compatible_final.append(id_room)
         # choose a room compatible for all the constraints and for every day
         if not compatible_final:  
            flag = False # not a feasible configuration
            iter = iter + 1
            break
         # update variables 
         rr_comp = random.choice(compatible_final)
         roomXpatient[patient.id] = rr_comp
         availability_room_x_day[rr_comp, start_period_of_day : end_period_of_stay] = availability_room_x_day[rr_comp, start_period_of_day : end_period_of_stay] - 1
         gender_room_x_day[rr_comp, start_period_of_day : end_period_of_stay] = np.full((end_period_of_stay - start_period_of_day,), gender_p)
         iter = iter + 1
   
   return roomXpatient, flag

def room_constr_bool(rooms, patients, occupants, roomXpatient, Adm_yes_or_no, Adm_Date, D):   
   
   gender_room_x_day = np.full((len(rooms), D), 'N', dtype=object)

   for o, occupant in enumerate(occupants): 
      gender_occupant = occupant.gender
      o_room = occupant.room_id
      stay =  occupant.length_of_stay + 1
      gender_room_x_day[o_room, 0: stay] = gender_occupant

   availability_room_x_day = np.zeros((len(rooms), D))
   for r, room in enumerate(rooms):
      availability_room_x_day[r,:] = room.capacity

   for o, occupant in enumerate(occupants):
      id_room_oc = occupant.room_id
      start_stay = 0
      end_stay = occupant.length_of_stay
      availability_room_x_day[id_room_oc, start_stay:end_stay + 1] = availability_room_x_day[id_room_oc, start_stay:end_stay + 1]  - 1

   for p, patient in enumerate(patients):
      if Adm_yes_or_no[p] == 0:
         continue
      start_stay = Adm_Date[p]
      end_period_of_stay = min(D, start_stay + patient.length_of_stay + 1)  
      room_assigned = roomXpatient[p]
      availability_check = availability_room_x_day[room_assigned, start_stay : end_period_of_stay] - 1
      gender_p = patient.gender
      if not np.all(availability_check >= 0):  
         Warning("Room constraints failed: maximum capacity exceeded")
         return False
      sub_list = gender_room_x_day[roomXpatient[p], start_stay : end_period_of_stay ]
      if not np.all(np.isin(sub_list, ['N', gender_p])):
         Warning("Room constraints failed: gender mix")
         return False
      gender_room_x_day[roomXpatient[p], start_stay : end_period_of_stay ] = np.full((end_period_of_stay - start_stay,), gender_p)
      availability_room_x_day[room_assigned, start_stay : end_period_of_stay] = availability_room_x_day[room_assigned, start_stay : end_period_of_stay] - 1
      # Gender constraints   
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

