from Instances.utils_instances import string_conversion
import numpy as np
import random
import math
import copy

random.seed(42)
np.random.seed(42)
       
def construct_feasible_solution(occupants, patients, operating_theaters, rooms, nurses, surgeons, D, dont_admit_nonMand = False):

   """
   Constructs a feasible initial solution for the hospital admission and scheduling problem.

   This function generates a random yet feasible solution to initialize the GRASP's exploration in each iteration.
   This function initializes decision variables related to patient admissions, room assignments, 
   operating theater allocations, and nurse schedules. It iteratively generates random solutions 
   and checks if they respect all hard constraints in order to ensure feasibility.

   Parameters:
      occupants (list): List of current occupants in each room.
      patients (list): List of patients to be considered for admission.
      operating_theaters (list): Available operating theaters.
      rooms (list): Available rooms in the hospital.
      nurses (list): Available nurses.
      surgeons (list): Available surgeons.
      D (int): Number of scheduling days.
      dont_admit_nonMand (bool): If True, non-mandatory patients are excluded from admission.

   Returns:
      x_feasible (list): A list containing feasible values for the decision variables:
                        [adm_yes_or_no, adm_date, room_x_patient, ot_x_patient, nurse_x_room].
      flag_stop (bool): True if a feasible solution satisfying all constraints was found,
                        False otherwise (after max iterations).
   """
   
   max_iter = 200
   iter = 1
   flag_stop = False
   bool5634 = False  
   bool127 = False

   while iter < max_iter and not flag_stop:
      
      ##  Initializing decision variables
      
      # Choice for admission
      # data structure: binary vector 
      adm_yes_or_no = np.random.randint(0,1, size=(len(patients),)) 

      # Date of admission for each patient 
      # data structure: vector of integer from 0 to D-1
      adm_date = np.random.randint(0,D-1, size=(len(patients),))     
      
      # Room id for each patient
      # data structure: vector of integer
      room_x_patient = np.random.randint(0, len(rooms)-1, size=(len(patients),))  

      # OT id for each patient 
      # data structure: vector of integer
      ot_x_patient = np.random.randint(0, len(operating_theaters)-1, size=(len(patients),))

      # Nurse id for each room (first dim) in each day (second dim) in each shift (third dim)
      # data structure: tridimensional matrix of integer
      nurse_x_room = np.random.randint(0, len(nurses)-1, size=(len(rooms), D, 3))

      ## Constraints:

      # 0) Each patient has only one room for all the stay: ensured by data structure
      # 0) Each room has only one nurse for each day and each shift: ensured by data structure

      # Constraints: H5, H6, H3 and H4
      # Convention: if patient i is not admitted than ot_x_patient[i] = room_x_patient[i] = adm_date[i] = -1.
      # H5 --> Each mandatory patient should be admitted between release day and due day 
      # H6 --> Each non mandatory patient should be admitted after release day 
      # H3 --> Each surgeon should not work more than maximum surgery time 
      # H4 --> Each OT has a maximum time 

      adm_yes_or_no, adm_date, room_x_patient, ot_x_patient, bool5634 = admit_constr(adm_yes_or_no, adm_date, room_x_patient, ot_x_patient, patients, D, surgeons, operating_theaters, len(rooms), dont_admit_nonMand)     
      
      if bool5634 == False: 
         iter = iter + 1
         flag_stop = False
         continue
 
      # H1, H2 and H7) 
      # H7 --> Limit of capacity of each room should not be overcome 
      # H1 --> In each room all people have the same gender
      # H2 --> Each patient should not be assigned to incompatible rooms 

      room_x_patient, bool127 = room_constr(rooms, patients, occupants, room_x_patient, adm_date, adm_yes_or_no, D)

      # Each nurse has a roster
      nurse_x_room = follow_shift(nurses, nurse_x_room, D)
      
      flag_stop = bool127 and bool5634
      iter = iter + 1

   x_feasible = [adm_yes_or_no, adm_date, room_x_patient, ot_x_patient, nurse_x_room]

   return x_feasible, flag_stop

def local_search(x_feasible, f_best_sofar, patients, occupants, rooms, nurses, surgeons, D, operating_theaters, weights):

   """
   Performs a local search to explore the solution space and potentially improve the current feasible solution.

   The function attempts various perturbations (such as shifting admission dates or changing room assignments) 
   on the input solution and evaluates whether these changes lead to a feasible solution with a better objective 
   function value. The perturbations applied are: 
   1. Admission date forward shift
   2. Admission date backward shift
   3. Room reassignment
   4. Nurse shift swap
   
   If an improvement is found, the function returns the improved solution and the updated objective function value.
   Therefore this function implementes a "first improvements" strategy in GRASP.

   Parameters:
      x_feasible (list): The current feasible solution, including admission status, admission dates, 
                           room assignments, operating theater allocations, and nurse schedules.
      f_best_sofar (float): The best objective function value found so far.
      patients (list): List of patients.
      occupants (list): List of current room occupants.
      rooms (list): Available rooms in the hospital.
      nurses (list): Available nurses in the hospital.
      surgeons (list): Available surgeons in the hospital.
      D (int): The number of days in the scheduling period.
      operating_theaters (list): Available operating theaters.
      weights (list): Weights for different penalties in the objective function.

   Returns:
      - x_best (list): The best feasible solution found after applying perturbations and improvements.
      - flag_improve (bool): A flag indicating if an improvement was found (True if improved, False otherwise).
      - f_best (float): The best objective function value after the local search.
   """

   adm_yes_or_no, adm_date, room_x_patient, ot_x_patient, nurse_x_room = x_feasible

   list_accepted_p = get_accepted_patients(patients, adm_yes_or_no)

   # type of perturbation
   perturbations = ["admission_forward", "admission_backward", "room_change", "nurse_swap"]
   random.shuffle(perturbations) 

   for perturbation in perturbations:

      ## Attempt to perturb the solution by shifting the admission dates of some patients forward
      if perturbation == "admission_forward":
 
         adm_yes_or_no, adm_date, room_x_patient, ot_x_patient, nurse_x_room = x_feasible

         # Randomize the list of currently accepted patients
         patient_id_shuffle = list_accepted_p
         random.shuffle(patient_id_shuffle)

         # Apply perturbation to a subset of patients
         for p in patient_id_shuffle[0:int(math.sqrt(len(patient_id_shuffle)/2))]:

            # Skip if patient admission is too close to the planning horizon or not admitted
            if adm_date[p] == D-1 or adm_date[p] == D-2 or adm_date[p] == -1:
               continue

            # Choose a forward shift of 1 or 2 days with equal probability
            Adm_Date_change = random.choices([1, 2], weights=[0.5, 0.5], k=1)[0]
            adm_date[p] = adm_date[p] + Adm_Date_change

            # Check the feasibility of the new solution after the perturbation
            x = [adm_yes_or_no, adm_date, room_x_patient, ot_x_patient, nurse_x_room]
            find = check_constraint(x, occupants, patients, rooms, nurses, surgeons, D, operating_theaters) 

            if find == True:

               # Attempt to improve the solution via nurse shift reallocation (this perturbation breaks no hard constraints)
               x_best, flag_improve, f_best = nurse_shift_shuffle(adm_yes_or_no, adm_date, room_x_patient, ot_x_patient, nurse_x_room, f_best_sofar, occupants, patients, rooms, nurses, surgeons, D, weights)
               
               # Return immediately if an improved feasible solution is found (first improvements)
               if flag_improve == True:
                  return x_best, True, f_best
               else: 
                  adm_date[p] = adm_date[p] - Adm_Date_change  # restore the perturbation
            else:
               adm_date[p] = adm_date[p] - Adm_Date_change  # restore the perturbation 

      ## Attempt to perturb the solution by shifting the admission dates of some patients backward
      elif perturbation == "admission_backward":

         adm_yes_or_no, adm_date, room_x_patient, ot_x_patient, nurse_x_room = x_feasible

         # Randomize the list of currently accepted patients
         patient_id_shuffle = list_accepted_p
         random.shuffle(patient_id_shuffle)

         # Apply perturbation to a subset of patients
         for p in patient_id_shuffle[0:int(math.sqrt(len(patient_id_shuffle)/2))]:

            # Skip if patient admission is too close to the planning horizon or not admitted
            if adm_date[p] == 0 or adm_date[p] == 1 or adm_date[p] == -1 :
               continue

            # Choose a backward shift of 1 or 2 days with equal probability
            Adm_Date_change = random.choices([1, 2], weights=[0.5, 0.5], k=1)[0]
            adm_date[p] = adm_date[p] - Adm_Date_change

            # Check the feasibility of the new solution after the perturbation
            x = [adm_yes_or_no, adm_date, room_x_patient, ot_x_patient, nurse_x_room]
            find = check_constraint(x, occupants, patients, rooms, nurses, surgeons, D, operating_theaters)

            if find == True:

               # Attempt to improve the solution via nurse shift reallocation (this perturbation breaks no hard constraints)
               x_best, flag_improve, f_best = nurse_shift_shuffle(adm_yes_or_no, adm_date, room_x_patient, ot_x_patient, nurse_x_room, f_best_sofar, occupants, patients, rooms, nurses, surgeons, D, weights)
               
               # Return immediately if an improved feasible solution is found (first improvements)
               if flag_improve == True:
                  return x_best, True, f_best
               else:
                  adm_date[p] = adm_date[p] + Adm_Date_change   # restore the perturbation
            else:
               adm_date[p] = adm_date[p] + Adm_Date_change  # restore the perturbation

      ## Attempt to perturb the solution by changing the room assignment of some patients
      elif perturbation == "room_change":

         adm_yes_or_no, adm_date, room_x_patient, ot_x_patient, nurse_x_room = x_feasible

         # Randomize the list of currently accepted patients
         patient_id_shuffle = list_accepted_p
         random.shuffle(patient_id_shuffle)
         
         # Apply perturbation to a subset of patients
         for p in patient_id_shuffle[0:int(math.sqrt(len(patient_id_shuffle)/2))]:
            if adm_yes_or_no[p] == 0:
               continue
            room_old = room_x_patient[p]

            # Assign a new room randomly, ensuring it's not in the patient's list of incompatible rooms
            room_x_patient[p] = random.choice(list(set(range(len(rooms))) - set(patients[p].incompatible_room_ids)))

            # Check the feasibility of the new solution after the perturbation
            x = copy.deepcopy([adm_yes_or_no, adm_date, room_x_patient, ot_x_patient, nurse_x_room])
            find = check_constraint(x, occupants, patients, rooms, nurses, surgeons, D, operating_theaters)

            # Return immediately if an improved feasible solution is found (first improvements)
            if find == True:
               
               # Attempt to improve the solution via nurse shift reallocation (this perturbation breaks no hard constraints)
               x_best, flag_improve, f_best = nurse_shift_shuffle(adm_yes_or_no, adm_date, room_x_patient, ot_x_patient, nurse_x_room, f_best_sofar, occupants, patients, rooms, nurses, surgeons, D, weights)
               
               if flag_improve == True:
                  return x_best, True, f_best
               else:
                  room_x_patient[p] = room_old  # restore the perturbation
            else:
               room_x_patient[p] = room_old  # restore the perturbation

      ## Nurse perturbation: shuffle rooms assigned to nurses that work in the same shift
      elif perturbation == "nurse_swap":

         adm_yes_or_no, adm_date, room_x_patient, ot_x_patient, nurse_x_room = x_feasible

         x_best, flag_improve, f_best = nurse_shift_shuffle(adm_yes_or_no, adm_date, room_x_patient, ot_x_patient, nurse_x_room, f_best_sofar, occupants, patients, rooms, nurses, surgeons, D, weights)
         if flag_improve == True:
            return x_best, True, f_best

   return [], False, 0

def nurse_shift_shuffle(adm_yes_or_no, adm_date, room_x_patient, ot_x_patient, nurse_x_room,
                                  f_best_sofar, occupants, patients, rooms, nurses, surgeons, D, weights):
   
   """

   This function performs an optimization procedure by randomly shuffling nurse assignments to improve the solution.

   This function iteratively shuffles the nurse assignments for each shift and day: room's nurse is changed. 
   After each shuffle, it evaluates the new solution using the objective function and checks whether the 
   new solution improves upon the best-known solution so far. If an improvement is found, the new solution 
   becomes the current best solution.

   """

   max_inner_iter = 30
   iter_inner = 1
   f_best = f_best_sofar
   x_best = [adm_yes_or_no, adm_date, room_x_patient, ot_x_patient, nurse_x_room]
   flag_improve = False    # Flag to track if any improvement occurs

   # Start the inner optimization loop
   while iter_inner < max_inner_iter:
      iter_inner += 1
      for t in range(0, D):   # Iterate over days
         for s in range(0, 3):   # Iterate over shifts
               np.random.shuffle(nurse_x_room[:, t, s])   # Randomly shuffle nurse assignment
               x = copy.deepcopy([adm_yes_or_no, adm_date, room_x_patient, ot_x_patient, nurse_x_room])
               value_try = evaluate_obj_func(x, occupants, patients, rooms, nurses, surgeons, D, weights)
                # Check if the new solution is better
               if value_try < f_best - 1:
                  f_best = value_try
                  x_best = copy.deepcopy(x)
                  flag_improve = True
   return x_best, flag_improve, f_best

def get_accepted_patients(patients, adm_yes_or_no):
    list_accepted_p = []
    for p, patient in enumerate(patients):
        if patient.mandatory or adm_yes_or_no[p] == 1:
            list_accepted_p.append(p)
    return list_accepted_p

def check_constraint(x, occupants, patients, rooms, nurses, surgeons, D, operating_theaters):

   """
   Checks whether the given solution satisfies all the hard constraints.

   This function evaluates a set of constraints related to room assignments, operating theater usage, 
   surgeon availability, patient admission schedules, and other hospital-specific constraints. It 
   returns True if all hard constraints are satisfied, and False otherwise.

   """

   [adm_yes_or_no, adm_date, room_x_patient, ot_x_patient, nurse_x_room] = x

   # Constraint H1, H7  
   bool_1_7_constraint = room_constr_bool(rooms, patients, occupants, room_x_patient, adm_yes_or_no, adm_date, D)

   # Constraint H3, H4
   bool_3_4_constraint = OT_and_Surgeon_constr_bool(surgeons, patients, operating_theaters, adm_date, ot_x_patient, D)
   
   # Constraint H5, H6
   bool_6_constraint = bool_period_of_admission_constr(adm_yes_or_no, adm_date, patients)
   bool_5_constraint = bool_admit_mandatory_constr(adm_yes_or_no, patients)

   # Constraint H2  
   bool_2_constraint = bool_incompatible_room_constr(patients, room_x_patient)

   constraint_vector = [
   int(bool_1_7_constraint),   
   int(bool_2_constraint),
   int(bool_3_4_constraint),  
   int(bool_5_constraint),   
   int(bool_6_constraint)  
   ]

   return all([bool_1_7_constraint, bool_3_4_constraint, bool_6_constraint, bool_5_constraint, bool_2_constraint])

def evaluate_obj_func(x, occupants, patients, rooms, nurses, surgeons, D, weights, printing = False):

   """
   Evaluates the objective function for a given solution in the hospital scheduling and admission problem.

   The objective function computes the total cost based on a variety of soft constraints. These soft constraints 
   include factors like room age, nurse workload, operating theater usage, surgeon transfers, and admission delays. 
   Each of these constraints has a weight associated with it, and the function returns the total weighted cost of the 
   current solution.
   """
   adm_yes_or_no, adm_date, room_x_patient, ot_x_patient, nurse_x_room = x

   total_cost = 0
   
   # "list_day_patientAndoccupant" is a useful structure that will be exploited:
   # a list for each day (0 to D-1) containing the indices of all patients and occupants 
   # present in the hospital on that day. 
   
   list_day_patientAndoccupant = build_daily_patient_occupant_list(patients, occupants, adm_yes_or_no, adm_date, D)
   
   # S1) Cost deriving from soft constraint: Room age
   qnt1 = evaluate_age_mixing_penalty(list_day_patientAndoccupant, patients, occupants, adm_yes_or_no, room_x_patient, weights, rooms)

   # S2) Cost deriving from soft constraint: skill level required
   # S3) Cost deriving from soft constraint: Continuity of care
   qnt2, qnt3 = evaluate_nurse_soft_constraints(patients, occupants, adm_yes_or_no, adm_date, room_x_patient, nurse_x_room, nurses, D, weights)

   # S4) Cost deriving from soft constraint: maximum workload for nurse
   qnt4 = evaluate_nurse_workload(occupants, patients, adm_yes_or_no, adm_date, room_x_patient, nurse_x_room, nurses, D, rooms, weights)
   
   # S5) Cost deriving from soft constraint: number of OT with at least one patient (open) lead to a cost 
   qnt5 = evaluate_open_operating_theater(patients, adm_date, ot_x_patient, D, weights)

   # S6) Cost deriving from soft constraint: surgeon transfer
   qnt6 = evaluate_surgeon_transfer(patients, adm_date, ot_x_patient, surgeons, D, weights)

   # S7) Cost deriving from soft constraint: admission delay
   qnt7 = evaluate_admission_delay(patients, adm_yes_or_no, adm_date, weights)

   # S8) Cost deriving from soft constraint: unschedule non mandatory patients
   qnt8 = np.sum(adm_yes_or_no == 0) * weights['unscheduled_optional']

   total_cost = qnt1 + qnt2 + qnt3 + qnt4 + qnt5 + qnt6 + qnt7 + qnt8 

   if printing == True:
     print('weights:', qnt1, qnt2, qnt3, qnt4, qnt5, qnt6, qnt7, qnt8)

   return  total_cost

def build_daily_patient_occupant_list(patients, occupants, adm_yes_or_no, adm_date, D):
    
    list_day_patientAndoccupant = [[] for _ in range(D)]
    occupant_start_index = len(patients)

    # Add admitted patients to each day of their stay
    for p, patient in enumerate(patients):
        if adm_yes_or_no[p] == 1:  
            start_stay = adm_date[p]
            end_stay = min(D, start_stay + patient.length_of_stay)
            for t in range(start_stay, end_stay):
                list_day_patientAndoccupant[t].append(p)

    # Add occupants to each day of their stay
    for o, occupant in enumerate(occupants):  
        start_stay = 0
        end_stay = min(D, start_stay + occupant.length_of_stay)
        for t in range(start_stay, end_stay):
            list_day_patientAndoccupant[t].append(occupant_start_index + o)

    return list_day_patientAndoccupant

def evaluate_age_mixing_penalty(list_day_patientAndoccupant, patients, occupants, 
                                 Adm_yes_or_no, room_x_patient, weights, rooms):
    """    
    Evaluates the penalty for mixing patients of different age groups in the same room.

    This penalty is based on a soft constraint that aims to minimize the mixing of patients from different 
    age groups in the same room. The function iterates over the daily presence of patients and occupants in 
    the hospital, and for each room, it checks the age groups of the patients assigned to that room. 
    If a room contains patients from different age groups, the penalty increases. 
    """

    qnt1 = 0
    for t, list_people in enumerate(list_day_patientAndoccupant):
        list_of_set_age = [set() for _ in range(len(rooms))]
        for i in list_people:
            if i < len(patients) and Adm_yes_or_no[i] == 1:  
                room_id = room_x_patient[i]
                list_of_set_age[room_id].add(patients[i].age_group)
            elif i >= len(patients):     
                occ = occupants[i - len(patients)]
                list_of_set_age[occ.room_id].add(occ.age_group)
        for set_age in list_of_set_age: 
            if len(set_age) != 0:
                qnt1 += (max(set_age) - min(set_age))
    return qnt1 * weights['room_mixed_age']

def evaluate_nurse_soft_constraints(patients, occupants, adm_yes_or_no, adm_date, room_x_patient,
                                nurse_x_room, nurses, D, weights):
   """
   Evaluates the soft constraints related to nurse skill levels and continuity of care.

   This function computes two penalties:
   1. `qnt2`: The penalty for mismatched nurse skills (i.e., if the skill level of the assigned nurse
      is lower than the required skill level for the patient or occupant).
   2. `qnt3`: The penalty for continuity of care, based on the number of nurses assigned to a patient 
      or occupant during their stay. More nurses involved means worse continuity of care.
   """

   qnt2 = 0
   qnt3 = 0

   # Process patients
   for p, patient in enumerate(patients):   
      set_nurse_p = set()
      roomXPat = room_x_patient[p]
      skill_level_req_list = patient.skill_level_required
      if adm_yes_or_no[p] == 1:
         for t in range(adm_date[p], min(adm_date[p]+patient.length_of_stay, D)):
            t_0 = t-adm_date[p]
            # Extract skill requirements for the current day (3 shifts)
            skill_level_req1 = skill_level_req_list[3*(t_0)]
            skill_level_req2 = skill_level_req_list[3*(t_0)+1]
            skill_level_req3 = skill_level_req_list[3*(t_0)+2]
            # Extract the skill levels of the assigned nurses for each shift
            skill_given_shift1 = nurses[nurse_x_room[roomXPat, t, 0]].skill_level
            skill_given_shift2 = nurses[nurse_x_room[roomXPat, t, 1]].skill_level
            skill_given_shift3 = nurses[nurse_x_room[roomXPat, t, 2]].skill_level
            # Add penalties for any skill mismatch for the 3 shifts
            qnt2 += max(0, skill_level_req1 - skill_given_shift1)
            qnt2 += max(0, skill_level_req2 - skill_given_shift2)
            qnt2 += max(0, skill_level_req3 - skill_given_shift3)
            # Add the nurses assigned to the current day and shift
            set_nurse_p.add(nurse_x_room[roomXPat, t, 0])
            set_nurse_p.add(nurse_x_room[roomXPat, t, 1])
            set_nurse_p.add(nurse_x_room[roomXPat, t, 2])
         # Count the number of unique nurses and add the continuity penalty
         num_nurse_p = len(set_nurse_p)
         qnt3 = qnt3 + num_nurse_p
      
   # Process occupants
   for o, occupant in enumerate(occupants):   
      set_nurse_p = set()
      room_id_o = occupant.room_id
      skill_level_req_list = occupant.skill_level_required
      for t in range(0, min(occupant.length_of_stay, D )):
         # Extract skill requirements for the current day (3 shifts)
         skill_level_req1 = skill_level_req_list[3*t]
         skill_level_req2 = skill_level_req_list[3*t+1]
         skill_level_req3 = skill_level_req_list[3*t+2]
         # Extract the skill levels of the assigned nurses for each shift
         skill_given_shift1 = nurses[nurse_x_room[room_id_o, t, 0]].skill_level
         skill_given_shift2 = nurses[nurse_x_room[room_id_o, t, 1]].skill_level
         skill_given_shift3 = nurses[nurse_x_room[room_id_o, t, 2]].skill_level
         # Add penalties for any skill mismatch for the 3 shifts
         qnt2 += max(0, skill_level_req1 - skill_given_shift1)
         qnt2 += max(0, skill_level_req2 - skill_given_shift2)
         qnt2 += max(0, skill_level_req3 - skill_given_shift3)
         set_nurse_p.add(nurse_x_room[room_id_o, t, 0])
         set_nurse_p.add(nurse_x_room[room_id_o, t, 1])
         set_nurse_p.add(nurse_x_room[room_id_o, t, 2])
      # Count the number of unique nurses and add the continuity penalty
      num_nurse_p = len(set_nurse_p)
      qnt3 = qnt3 + num_nurse_p

   qnt2 = qnt2 * weights['room_nurse_skill']
   qnt3 = qnt3 * weights['continuity_of_care']
   return qnt2, qnt3

def evaluate_nurse_workload(occupants, patients, adm_yes_or_no, adm_date, room_x_patient, nurse_x_room, nurses, D, rooms, weights):

   """
   Calculates the workload for nurses based on the workload of the occupants and patients, and checks if any nurse exceeds their maximum workload.
   Returns:
      - qnt4: total penalty value for nurses' excessive workload.
   """

   qnt4 = 0
   
   # Support data structure: 
   # matrix with dimension D x num_rooms x 3 in order to store workload total required in that room in that specific period
   matrix = np.zeros((D, len(rooms), 3))
 
   for o, occupant in enumerate(occupants): 
      for t in range(0, min(D, occupant.length_of_stay)):
         matrix[t, occupant.room_id, :] += [occupant.workload_produced[3 * t + s] for s in range(3)]

   for p, patient in enumerate(patients):   
      if adm_yes_or_no[p] == 0:
         continue
      for t in range(adm_date[p], min(D,adm_date[p] + patient.length_of_stay)):
         matrix[t, room_x_patient[p], :] += [patient.workload_produced[3 * (t - adm_date[p]) + s] for s in range(3)]
   
   # Calculate for each nurse the delta of workload
   for n, nurse in enumerate(nurses):   
      for i, diz in enumerate(nurse.working_shifts):   
         day = diz['day']
         shift = string_conversion(diz['shift'])
         max_work = diz['max_load']
         list_idRoom = np.where(nurse_x_room[:,day,shift] == n)[0]
         qnt4 = qnt4 + max(0, sum(matrix[day,list_idRoom,shift]) - max_work) 
   qnt4 = qnt4 * weights['nurse_eccessive_workload']
   return qnt4
                             
def evaluate_open_operating_theater(patients, adm_date, ot_x_patient, D, weights):
    
   """
   Evaluates the number of open operating theaters for each day and calculates the associated penalty.
   Returns:
   - qnt5: total penalty for the number of open operating theaters.
   """
   
   qnt5 = 0
   for t in range(0, D):
      open_OT = set()
      for p, patient in enumerate(patients):
         if adm_date[p] == t:
               open_OT.add(ot_x_patient[p])
      num_open_OT = len(open_OT)
      qnt5 += num_open_OT
   return qnt5 * weights['open_operating_theater']

def evaluate_surgeon_transfer(patients, adm_date, ot_x_patient, surgeons, D, weights):
    """ 
    Evaluates the penalty based on surgeon transfers across operating theaters.
    Returns:
    - qnt6: The total penalty for surgeon transfers.
    """

    qnt6 = 0
    for t in range(0, D):
        list_surgeonXrooms_in_t = [set() for _ in range(len(surgeons))]
        for p, patient in enumerate(patients):
            if adm_date[p] == t:
                list_surgeonXrooms_in_t[patient.surgeon_id].add(ot_x_patient[p])
        qnt6 += sum(max(0, len(s) - 1) for s in list_surgeonXrooms_in_t)

    return qnt6 * weights['surgeon_transfer']

def evaluate_admission_delay(patients, adm_yes_or_no, adm_date, weights):
   """
   Evaluates the penalty based on the delay between a patient's surgery release day and their admission day.
   Returns:
    - qnt7: The total penalty for patient admission delays.
   """

   qnt7 = 0
   for p, patient in enumerate(patients):
      if adm_yes_or_no[p] == 0:
         continue
      qnt7 += (adm_date[p] - patient.surgery_release_day)
   
   return qnt7 * weights['patient_delay']

## Constructive function:

def admit_constr(adm_yes_or_no, adm_date, room_x_patient, ot_x_patient, patients, D, surgeons, operating_theaters, num_rooms, dont_admit_nonMand):

   """    
   This function decides whether to admit a patient, assigns an admission date, 
   and schedules an operating theater (OT) and surgeon for mandatory and non-mandatory patients.

   Parameters:
   - adm_yes_or_no: List of binary values indicating whether a patient is admitted (1) or not (0).
   - adm_date: List of admission dates for patients.
   - room_x_patient: List of rooms assigned to each patient.
   - ot_x_patient: List of operating theaters assigned to each patient.
   - patients: List of patient objects, each containing patient details (e.g., mandatory status, surgery duration).
   - D: Total number of days in the hospital scheduling.
   - surgeons: List of surgeon objects, each containing surgeon details (e.g., availability, max surgery time).
   - operating_theaters: List of operating theater objects, each containing availability information.
   - num_rooms: Number of rooms available for patients.
   - dont_admit_nonMand: Flag indicating whether non-mandatory patients should be admitted or not.

   Returns:
   - adm_yes_or_no: Updated list indicating which patients have been admitted.
   - adm_date: Updated list of admission dates for the patients.
   - room_x_patient: Updated list of room assignments for each patient.
   - ot_x_patient: Updated list of OT assignments for each patient.
   - flag_find_configuration: Boolean indicating whether a feasible configuration was found.

   The function goes through the following steps:
    1. Admit all mandatory patient and decides whether to admit non-mandatory patients using a probability factor (default set to 1).
    2. Randomly assigns admission dates to mandatory patients within their surgery release window and surgeon availability.
    3. Tries to find a feasible configuration for each mandatory patient assigning an OT and surgeon based on available resources.
    4. If no feasible configuration is found for a mandatory patient flag_find_configuration = false is returned
    5. Same steps for each non mandatory patient with the difference that if no feasible configuration is found, she/he's not admitted.
   When a configuration is found for a certain patient the availability of surgeons and operating theaters (OTs) are updated.
   """

   ## Decision if admit or not a patient
   prob = 1 # Probability with which we decide if admitting or not the non mandatory patient
   initialize_admission_decisions(patients, adm_yes_or_no, adm_date, room_x_patient, ot_x_patient, dont_admit_nonMand, prob)
               
   # Useful structure for keeping track of remaining OT's and surgeon's availability
   surgeons_availability = []
   for s, surgeon in enumerate(surgeons):
      surgeons_availability.append(surgeon.list_max_surgery_time)
   list_timeXsurgeon = [[0] * D for _ in range(len(surgeons))]   
   list_timeXOT = [[0] * D for _ in range(len(operating_theaters))]  

   list_mandatory_p = [p for p, patient in enumerate(patients) if patient.mandatory]
   list_non_mandatory_p = [p for p, patient in enumerate(patients) if not patient.mandatory]

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
      adm_date[p] = random.choice(list(day_available_set.intersection(range(patient.surgery_release_day, patient.surgery_due_day + 1))))

      # Try to find a feasible operating theater (OT) and surgeon configuration for the selected admission day
      while not flag_find_configuration:
         available_OT = operating_theaters[ot_x_patient[p]].availability[adm_date[p]]
         already_used_OT = list_timeXOT[ot_x_patient[p]][adm_date[p]]
         requested_OT = patient.surgery_duration

         # Check if the selected OT has enough free time
         if (available_OT - already_used_OT) > requested_OT:
               available_surg = surgeons_availability[id_surgeonXp][adm_date[p]]
               already_used_surg = list_timeXsurgeon[id_surgeonXp][adm_date[p]]
               requested_surg = patient.surgery_duration

               # Check if the surgeon has enough available time on that day
               if (available_surg - already_used_surg) > requested_surg:
                  # Reserve time slots for both OT and surgeon
                  list_timeXOT[ot_x_patient[p]][adm_date[p]] += patient.surgery_duration
                  list_timeXsurgeon[id_surgeonXp][adm_date[p]] += patient.surgery_duration
                  flag_find_configuration = True  # Feasible scheduling found
               else:
                  # Remove this day from possible choices and retry with another day
                  day_available_set.discard(adm_date[p])
                  possible_day = list(day_available_set.intersection(range(patient.surgery_release_day, patient.surgery_due_day + 1)))
                  if not possible_day:
                     return [adm_yes_or_no, adm_date, room_x_patient, ot_x_patient, flag_find_configuration]
                  adm_date[p] = random.choice(possible_day)

         else:
               # No available time in the initially assigned OT, search for alternative feasible OTs
               list_available_Xp = [
                  i for i in range(len(list_timeXOT))
                  if (operating_theaters[i].availability[adm_date[p]] - (list_timeXOT[i][adm_date[p]] + patient.surgery_duration)) > 0
               ]

               # If no OTs available, change admission day
               if not list_available_Xp:
                  day_available_set.discard(adm_date[p])
                  possible_day = list(day_available_set.intersection(range(patient.surgery_release_day, patient.surgery_due_day + 1)))
                  if not possible_day:
                     return [adm_yes_or_no, adm_date, room_x_patient, ot_x_patient, flag_find_configuration]
                  adm_date[p] = random.choice(possible_day)
               else:
                  # At least one OT is feasible, randomly assign one and check surgeon constraint
                  ot_x_patient[p] = np.random.choice(list_available_Xp)
                  available_surg = surgeons_availability[id_surgeonXp][adm_date[p]]
                  already_used_surg = list_timeXsurgeon[id_surgeonXp][adm_date[p]]
                  requested_surg = patient.surgery_duration

                  if (available_surg - already_used_surg) > requested_surg:
                     # Reserve slots and mark configuration as feasible
                     list_timeXOT[ot_x_patient[p]][adm_date[p]] += patient.surgery_duration
                     list_timeXsurgeon[id_surgeonXp][adm_date[p]] += patient.surgery_duration
                     flag_find_configuration = True
                  else:
                     # Surgeon not available enough; retry with another day
                     day_available_set.discard(adm_date[p])
                     possible_day = list(day_available_set.intersection(range(patient.surgery_release_day, patient.surgery_due_day + 1)))
                     if not possible_day:
                           return [adm_yes_or_no, adm_date, room_x_patient, ot_x_patient, flag_find_configuration]
                     adm_date[p] = random.choice(possible_day)
   
   ## After mandatory,admitted non mandatory are processed                
   for p in list_non_mandatory_p:
      if adm_yes_or_no[p] == 0:
         continue
      patient = patients[p]
      flag_find_configuration = False  # Set to True when a feasible scheduling is found for the patient
      id_surgeonXp = patient.surgeon_id 

      # Get the availability of the surgeon and extract available days
      tot_day_availability = surgeons_availability[id_surgeonXp]
      day_available = np.nonzero(tot_day_availability)[0]
      day_available_set = set(day_available)

      # Randomly select an admission date within the patient’s release-due window and surgeon's availability
      adm_date[p] = random.choice(list(day_available_set.intersection(range(patient.surgery_release_day, D))))

      # Try to find a feasible operating theater (OT) and surgeon configuration for the selected admission day
      while not flag_find_configuration:
         available_OT = operating_theaters[ot_x_patient[p]].availability[adm_date[p]]
         already_used_OT = list_timeXOT[ot_x_patient[p]][adm_date[p]]
         requested_OT = patient.surgery_duration

         # Check if the selected OT has enough free time
         if (available_OT - already_used_OT) > requested_OT:  
                     # Check the availability of the surgeon
                     if (surgeons_availability[id_surgeonXp][adm_date[p]] - list_timeXsurgeon[id_surgeonXp][adm_date[p]]) > patient.surgery_duration:
                        # Reserve time for OT and surgeon
                        list_timeXsurgeon[id_surgeonXp][adm_date[p]] += patient.surgery_duration
                        list_timeXOT[ot_x_patient[p]][adm_date[p]] += patient.surgery_duration
                        flag_find_configuration = True   # Feasible configuration found
                     else:   
                        # Surgeon not available, remove the day from possible choices and try another day
                        day_available_set.discard(adm_date[p]) 
                        possible_day = list(day_available_set.intersection(range(patient.surgery_release_day, D)))
                        if not possible_day:  # No feasible admission day left
                           # the patient is not accepted
                           adm_yes_or_no[p] = 0
                           adm_date[p] = -1
                           room_x_patient[p] = -1
                           ot_x_patient[p] = -1
                           break    # Move on to the next patient
                        adm_date[p] = random.choice(possible_day)
         else:
            # If the selected OT does not have enough available time, look for alternative OTs
            list_available_Xp = [      i for i in range(len(list_timeXOT))
                  if (operating_theaters[i].availability[adm_date[p]] - (list_timeXOT[i][adm_date[p]] + patient.surgery_duration)) > 0     ]   
            # If no available OTs, change the admission date
            if not list_available_Xp:      
               day_available_set.discard(adm_date[p])  # Avoid selecting a date again that leads to a non-feasible configuration
               possible_day = list(day_available_set.intersection(range(patient.surgery_release_day, D)))
               if not possible_day:  # If no feasible day left
                  # Patient is not acceptedd
                  adm_yes_or_no[p] = 0
                  adm_date[p] = -1
                  room_x_patient[p] = -1
                  ot_x_patient[p] = -1
                  break       # Move on to another patient
               adm_date[p] = random.choice(list(day_available_set.intersection(range(patient.surgery_release_day, D))))
            else:
               # At least one OT is feasible, randomly assign one and check surgeon constraint
               ot_x_patient[p] = np.random.choice(list_available_Xp)
               available_surg = surgeons_availability[id_surgeonXp][adm_date[p]]
               already_used_surg = list_timeXsurgeon[id_surgeonXp][adm_date[p]]
               requested_surg = patient.surgery_duration
               if  (( available_surg - already_used_surg) > requested_surg):
                  # Reserve slots and mark configuration as feasible
                  list_timeXOT[ot_x_patient[p]][adm_date[p]] += patient.surgery_duration
                  list_timeXsurgeon[id_surgeonXp][adm_date[p]] += patient.surgery_duration
                  flag_find_configuration = True
               else: 
                  # Surgeon not available or the new OT's time is insufficient, change the admission day
                  day_available_set.discard(adm_date[p])  # avoid to pick another time the admission date that lead to a configuration not feasible
                  possible_day = list(day_available_set.intersection(range(patient.surgery_release_day, D)))
                  if not possible_day: # not feasible admission day
                     # the patient is not accepted
                     adm_yes_or_no[p] = 0
                     adm_date[p] = -1
                     room_x_patient[p] = -1
                     ot_x_patient[p] = -1
                     # move on to another patient
                     break
                  adm_date[p] = random.choice(possible_day)  
   return [adm_yes_or_no, adm_date, room_x_patient, ot_x_patient, flag_find_configuration] 

def initialize_admission_decisions(patients, adm_yes_or_no, adm_date, room_x_patient, ot_x_patient, dont_admit_nonMand, prob):
    
    """
    This function initializes the admission decisions for patients based on their mandatory status and a given probability for non-mandatory patients.
    A different behaviour occurs if the bool variable "dont_admit_nonMand" is true forcing to refuse all non mandatory patients.
    """

    for p, patient in enumerate(patients):
        if patient.mandatory:  # admit all mandatory patients
            adm_yes_or_no[p] = 1
        else:
            if dont_admit_nonMand:
                adm_yes_or_no[p] = 0
                adm_date[p] = -1
                room_x_patient[p] = -1
                ot_x_patient[p] = -1
            else:
                adm_yes_or_no[p] = random.choices([0, 1], weights=[1 - prob, prob])[0]   # admit non mandatory with a certain probability
                if adm_yes_or_no[p] == 0:
                    adm_date[p] = -1
                    room_x_patient[p] = -1
                    ot_x_patient[p] = -1

def follow_shift(nurses, nurse_x_room, D):  
  
   """
      This function updates the nurse assignments for each room, shift, and day based on the nurses' roster.
   """
   
   # Create useful data structure
   # id_nurse_working = 3xD matrix (rows -> shifts, columns -> days)
      
   # Initialize structure to track nurses working on each shift and day
   id_nurse_working = np.empty((3, D), dtype=object)

   # Populate the structure with nurses' shifts
   for s in range(3):
      for d in range(D):
         id_nurse_working[s][d] = []  # Empty list for each shift and day

   for n, nurse in enumerate(nurses):  # Loop through nurses
      for s in range(3):  # Loop through shifts
         for d in range(D):  # Loop through days
               for shift_info in nurse.working_shifts:
                  if shift_info['day'] == d and s == string_conversion(shift_info["shift"]):
                     id_nurse_working[s][d].append(n)

   # Reassign nurses to rooms if the assigned nurse is not compatible
   for s in range(0, 3):
      for d in range(0, D):
         list_nurses_compatible = id_nurse_working[s][d]
         for r in range(0, nurse_x_room.shape[0]):
               id_nurse_assigned = nurse_x_room[r][d][s]
               if id_nurse_assigned not in list_nurses_compatible:
                  nurse_x_room[r][d][s] = random.choice(list_nurses_compatible)

   # Return the updated nurse assignments
   return nurse_x_room

def room_constr(rooms, patients, occupants, room_x_patient, adm_date, adm_yes_or_no, D):
   
   """
   This function attempts to assign patients to rooms while satisfying gender and capacity constraints. 
   The room assignment is performed by shuffling the list of rooms and patients, iteratively checking 
   for feasible configurations, and ensuring all constraints are met.
   The function proceeds with an iterative process, attempting to assign each patient to a room based on the following criteria:
   - Gender Compatibility**: The room must be compatible with the patient's gender for the entire duration of their stay.
   - Capacity Compatibility**: The room must have enough available space for the patient during their stay.
   Returns:
   - The `room_x_patient` list will be updated with the assigned rooms.
   - The `flag` will indicate whether a feasible solution was found (`True`) or not (`False`).
   """

   flag = False
   max_iter = 500  
   iter  =  0
   while not flag and iter <= max_iter:

      # Shuffle rooms and patients randomly
      rooms_shuffled = rooms[:]
      random.shuffle(rooms_shuffled)
      patients_shuffled = patients[:]  
      random.shuffle(patients_shuffled) 

      # Initialize data structure useful for assigning rooms to patients:
      # gender_room_x_day tracks which gender is assigned to each room for each day  -> matrix with a shape of (len(rooms), D) containing:
      # A : gender A
      # B: gender B
      # N : gender not assigned yet (no occupants or patients assigned)
      # availability_room_x_day tracks how many spaces are available in each room for each day  -> matrix with a shape of (len(rooms), D) containing double
      gender_room_x_day, availability_room_x_day = initialize_room_availability(rooms, occupants, D)

      flag = True     # Assume feasible configuration until proven otherwise 

      # Assign each admitted patients to a feasible room
      for _, patient in enumerate(patients_shuffled): 
         if adm_yes_or_no[patient.id] == 0:
            continue
         gender_p = patient.gender
         start_period_of_day = adm_date[patient.id]
         end_period_of_stay = min(adm_date[patient.id] + patient.length_of_stay + 1, D) 

         # Find compatible rooms in terms of gender
         compatible_rooms = get_compatible_rooms_for_gender(rooms_shuffled, gender_room_x_day, start_period_of_day, end_period_of_stay, gender_p, patient)

         if not compatible_rooms:
            flag = False # not a feasible configuration
            iter = iter + 1
            break

         # Find compatible rooms in terms of capacity among the rooms feasible in terms of gender
         compatible_rooms = get_compatible_rooms_for_capacity(compatible_rooms, availability_room_x_day, start_period_of_day, end_period_of_stay)

         if not compatible_rooms:  
            flag = False # not a feasible configuration
            iter = iter + 1
            break

         # Assign randomly a compatible room to the patient
         rr_comp = random.choice(compatible_rooms)
         room_x_patient[patient.id] = rr_comp
         availability_room_x_day[rr_comp, start_period_of_day : end_period_of_stay] = availability_room_x_day[rr_comp, start_period_of_day : end_period_of_stay] - 1
         gender_room_x_day[rr_comp, start_period_of_day : end_period_of_stay] = np.full((end_period_of_stay - start_period_of_day,), gender_p)
         
         iter = iter + 1
   
   return room_x_patient, flag

def initialize_room_availability(rooms, occupants, D):
    
    # Initialize room availability and gender (N = not already assigned)
    gender_room_x_day = np.full((len(rooms), D), 'N', dtype=object)
    availability_room_x_day = np.zeros((len(rooms), D))
    
    # Set initial availability based on room capacities
    for r, room in enumerate(rooms):
        availability_room_x_day[r, :] = room.capacity
    
    # Assign gender's occupants to rooms and update room availability 
    for occupant in occupants: 
        gender_room_x_day[occupant.room_id, :occupant.length_of_stay + 1] = occupant.gender
        end_stay = occupant.length_of_stay
        availability_room_x_day[occupant.room_id, 0:end_stay + 1] -= 1
    
    return gender_room_x_day, availability_room_x_day

def get_compatible_rooms_for_gender(rooms_shuffled, gender_room_x_day, start_period_of_day, end_period_of_stay, gender_p, patient):
    """
    This function finds compatible rooms for a patient based on gender and room availability.
    It ensures that the room either has no patient assigned or is already occupied by patients of the same gender
    during the patient's entire stay.
    Returns:
    - A set of room IDs that are compatible with the patient's gender for the full stay period.
    """

    # Avoid incompatible rooms
    compatible_rooms = set(list(range(len(rooms_shuffled))))-set(patient.incompatible_room_ids)
    # Considering rooms in which in each day of patient's stay there are already patient with the same gender or no patient yet
    room_gender_comp = [
        room.id for room in rooms_shuffled
        if np.all(np.isin(gender_room_x_day[room.id, start_period_of_day:end_period_of_stay], ['N', gender_p]))
    ]
    return compatible_rooms.intersection(room_gender_comp)

def get_compatible_rooms_for_capacity(compatible_rooms, availability_room_x_day, start_period_of_day, end_period_of_stay):
    
   """
   This function checks which rooms have sufficient available capacity to accommodate a patient 
   for the entire duration of their stay.
   Returns:
    - A list of room IDs that have enough available capacity for the entire stay period.
   """
      
   # Consider rooms that still have available capacity.
   compatible_final = [
      id_room for id_room in compatible_rooms
      if np.all(availability_room_x_day[id_room, start_period_of_day:end_period_of_stay] - 1 >= 0)
   ]
   return compatible_final

## Boolean function:

def room_constr_bool(rooms, patients, occupants, room_x_patient, adm_yes_or_no, adm_date, D):   
   """
   This function verifies whether the room assignments in room_x_patient for patients comply with room capacity 
   and gender constraints.
   Returns:
   - `True` if all room assignments are valid and all constraints are met.
   - `False` if any constraint (capacity or gender mix) is violated.
   """
   
   # Initialize the gender assignment matrix for each room across all days, with 'N' indicating no occupant in the room
   gender_room_x_day = np.full((len(rooms), D), 'N', dtype=object)
   availability_room_x_day = np.zeros((len(rooms), D))

   # Initialize the room availability matrix, with each room's capacity for all days
   for r, room in enumerate(rooms):
      availability_room_x_day[r, :] = room.capacity
   
   # Assign the gender of each occupant to the corresponding room for their entire stay and update room availability based on the current occupants' stays
   for o, occupant in enumerate(occupants): 
      gender_room_x_day[occupant.room_id, 0: occupant.length_of_stay + 1] = occupant.gender
      availability_room_x_day[occupant.room_id, :occupant.length_of_stay + 1] -= 1

   # Iterate through the patients to check room assignments and constraints
   for p, patient in enumerate(patients):
      if adm_yes_or_no[p] == 0:
         continue  # Skip patients not admitted

      start_stay = adm_date[p]
      end_period_of_stay = min(D, start_stay + patient.length_of_stay + 1) 
      room_assigned = room_x_patient[p]

      # Check if the room has sufficient availability during the patient's stay period
      availability_check = availability_room_x_day[room_assigned, start_stay : end_period_of_stay] - 1
      if not np.all(availability_check >= 0):  
         Warning("Room constraints failed: maximum capacity exceeded")  # Room exceeds its capacity
         return False

      # Check if the room meets the gender constraints for the patient's stay period
      sub_list = gender_room_x_day[room_x_patient[p], start_stay : end_period_of_stay ]
      if not np.all(np.isin(sub_list, ['N', patient.gender])):  # Ensure no gender mix if a patient is assigned
         Warning("Room constraints failed: gender mix")  # Room has an incompatible gender mix
         return False

      # Update gender assignment and availability based on the patient's room assignment
      gender_room_x_day[room_x_patient[p], start_stay : end_period_of_stay ] = np.full((end_period_of_stay - start_stay,), patient.gender)
      availability_room_x_day[room_assigned, start_stay:end_period_of_stay] -= 1

   return True

def bool_period_of_admission_constr(adm_yes_or_no, adm_date, patients):
   """
   This function checks if the admission dates for the patients meet the constraints regarding
   the surgery release day and due date.
   Returns:
    - `True` if all patients' admission dates satisfy the constraints.
    - `False` if any patient violates the constraints"""

   # Check if every admitted patients has a feasible date of admission
   for p, patient in enumerate(patients):
         amm = adm_yes_or_no[p]
         if adm_yes_or_no[p] == 0:
               continue  
         surgery_release = patient.surgery_release_day

         # Check constraints for mandatory patients: admission date between release date and due date
         if patient.mandatory:
               if not (surgery_release <= adm_date[p] <= patient.surgery_due_day):
                  Warning("Period of admission constraint failed")
                  return False 
         # For non-mandatory patients, ensure the admission date is not before the surgery release day
         elif adm_date[p] < surgery_release:   # for non mandatory
               Warning("Period of admission constraint failed")            
               return False  
   return True

def bool_admit_mandatory_constr(adm_yes_or_no, patients):
    """
   This function checks if all mandatory patients have been admitted. If any mandatory patient
   is not admitted, the function will return `False`.
   """

    for p, current_patient in enumerate(patients):  
        # Ensure that mandatory patients are admitted
        if current_patient.mandatory and adm_yes_or_no[p] == 0:
            return False  # A mandatory patient has not been admitted
    
    return True  # All mandatory patients are admitted

def bool_incompatible_room_constr(patients, room_x_patient):
    """
    Returns:
    - `True` if all patients are assigned to compatible rooms.
    - `False` if at least one patient is assigned to an incompatible room.
    """

    for p, patient in enumerate(patients):
        # Check if the assigned room is in the patient's list of incompatible rooms
        if room_x_patient[p] in patient.incompatible_room_ids:
            return False  # At least one patient is assigned to an incompatible room
    
    return True  # All patients are assigned to compatible room

def OT_and_Surgeon_constr_bool(surgeons, patients, operating_theaters, adm_date, ot_x_patient, D):
    """
    This function checks if the operating theater (OT) and surgeon constraints are satisfied for each day.
    The constraints are:
    - Surgeons' total surgery time on each day should not exceed their maximum allowed time.
    - Operating theaters' total surgery time on each day should not exceed their available time.
        
    Returns:
    - True if all constraints are satisfied for each day.
    - False if any constraint is violated.
    """
    
    for t in range(0, D):
        # Initialize lists to track the total surgery time for each surgeon and operating theater
        list_timeXsurgeon = np.zeros(len(surgeons))
        list_timeXOT = np.zeros(len(operating_theaters))
        
        # Extract patients admitted on day t
        patient_in_t = [i for i in range(len(patients)) if adm_date[i] == t]  # List of patient indices admitted on day t
        info_patient_in_t = [patients[i] for i in patient_in_t]  # List of patient objects admitted on day t
        
        # Accumulate surgery time for each surgeon and operating theater for the patients admitted on day t
        for p, pat in enumerate(info_patient_in_t):
            list_timeXsurgeon[pat.surgeon_id] += pat.surgery_duration  # Add surgery duration to the surgeon's time
            list_timeXOT[ot_x_patient[pat.id]] += pat.surgery_duration  # Add surgery duration to the operating theater's time
        
        # Check if the total surgery time for each surgeon does not exceed their maximum allowed time
        for s, surgeon in enumerate(surgeons):
            if list_timeXsurgeon[s] > surgeon.list_max_surgery_time[t]:
                Warning("Surgeon's constraint violated: maximum time exceeded")
                return False  # Surgeon has exceeded their available surgery time
        
        # Check if the total surgery time for each operating theater does not exceed its availability
        for ot, OT_theater in enumerate(operating_theaters):
            if list_timeXOT[ot] > OT_theater.availability[t]:
                Warning("OT's constraint violated: maximum time exceeded")
                return False  # Operating theater has exceeded its available time
    
    return True  # All constraints are respected for each day

