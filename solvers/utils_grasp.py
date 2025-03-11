from Instances.utils_instances import string_conversion
import numpy as np
import random

'''
ATTENZIONE: abbiamo aggiunto in input surgeons per generale l'admission date in modo furbo, NON considerando i giorni in cui
il paziente NON può essere operato perchè NON c'è il chirurgo!
'''
def create_random_point(D, num_patients, num_rooms, num_operating_theaters, num_nurses, surgeons, patients,  operating_theaters):
   # Choice for admission
   # data structure: binary vector  
   
   # Choice for admission
   # data structure: binary vector  
   Adm_yes_or_no = np.random.randint(0,1, size=(num_patients,)) 
   # Date of admission for each patient from 0 to D ( X_t = D means that the patient is not admit, this is possible if the patient is not mandatory) 
   # data structure: vector of integer
   Adm_Date = np.random.randint(0,D-1, size=(num_patients,))   
   
   # Room id (col) for each patient (rows). It will be use the convention that if an element is -1  it means that the patient is not admit.
   # data structure: vector of integer
   roomXpatient = np.random.randint(0, num_rooms-1, size=(num_patients,))

   # OT id (col) for each patient (rows). It will be use the convention that if an element is -1 it means that the patient is not admit.
   # data structure: vector of integer
   '''
   CONTROLLARE: lo abbiamo modificato per pescare random le OT quando NON sono chiuse considerando la admisison date di OGNI paziente
   '''
   # otXpatient = np.random.randint(0, num_operating_theaters-1, size=(num_patients,))

   otXpatient = [None] * len(patients)

   OT_availability = []
   for ot, operating_theater in enumerate(operating_theaters):
      OT_availability.append(operating_theater.availability)
   
   tot_day_OT_av = [[] for _ in range(D)]
   
   for p,patient in enumerate(patients):
      for ot, op_theater in enumerate(operating_theaters):
         while Adm_Date[p] != -1 and OT_availability[ot][Adm_Date[p]] == 0:
            Adm_Date[p] = np.random.randint(0,D-1) 
         if Adm_Date[p] != -1 and OT_availability[ot][Adm_Date[p]]!= 0  and OT_availability[ot][Adm_Date[p]] not in tot_day_OT_av[Adm_Date[p]]:
            tot_day_OT_av[Adm_Date[p]].append(ot)
         elif Adm_Date[p] == -1:
            otXpatient[p] = -1
      # ATTENZIONE: dobbiamo inserire l'indice della stanza disponibile e NON la disponibilità!
      if Adm_Date[p] != -1:
         otXpatient[p] = random.choice(tot_day_OT_av[Adm_Date[p]])  
         # stiamo selezionando la sala operatoria random per ciascun paziente (nota la loro data di ammissione
         # escludiamo le sale operatorie NON aperte nel giorno specifico) 

   # Nurse for each room (first dim) in each day (second dim) for each shift (third dim)
   # data structure: tridimensional matrix of integer
   nurseXroom = np.random.randint(0, num_nurses-1, size=(num_rooms, D, 3))

   '''
   OT_availability la restituiamo perchè ci serve per admit_mandatory
   '''
   return [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom, OT_availability]

       
def construct_feasible_solution(x, occupants, patients, operating_theaters, rooms, nurses, surgeons, D, id_nurse_working):
   Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom, OT_availability = x

   ## Useful structure: list of lists.
   # Each inner list contains the indices of the patients and occupants who are at the hospital on that specific day. 
   # It is exploited the date of admission and the lenght of stay (for patients not admitted the list is empty)
   
   list_day_patientAndoccupant = [[] for _ in range(D)]

   # Since both occupants and patients start with index 0 in their respective structures,
   # we rescale the occupant indices in this combined structure to differentiate them from patients:
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
         list_day_patientAndoccupant[t].append(occupant_start_index + o)  # rescale index

   # Constraints:

   # 0) Each patient has only one room for all the stay: ensured by data structure
   # 0) Each room has only one nurse for each day and each shift: ensured by data structure



   # VINCOLI 5,6,3,4 da mettere insieme, ricordarsi quando si cicla di prendere random.

   # H5 and H6) Force to admit every mandatory patient and be coherent with other structure (H5)
   # convention: if patient i is not admitted than otXpatient[i] = roomXpatient[i] = Adm_Date[i] = -1
   # H6) Each mandatory patient should be admitted between release day and due day 
   # and Each non mandatory patient should be admitted after release day (H6)
   Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient = admit_mandatory_constr(Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, patients, D, surgeons, operating_theaters, OT_availability)
   # nel caso fissare tutto a 0 per i non mandatory
   # Adm_yes_or_no and Adm_Date obtained is compatible with the constraint 
      # H3 and H4) Each surgeon should not work more than maximum surgery time (H3) and there is a maximum time for each OT (H4) 
   # SOSTITUIRE CON FUNZIONE CHE COSTRUISCE AD HOC I TEMPI DI AMMISSIONE (METTERE INSIEME CON H5 and H6))

   #bool_3_4_constraint = maxTime_constr(surgeons, patients, operating_theaters, Adm_Date, otXpatient, D)
   # facile1: Fissare a 0 se non c'è disponibilità per chirurghi
   # facile2: Fissare a 0 se non c'è disponibilità per OT
   # difficile: aggiornare partendo dal tempo 0 AdmDate in modo tale che:
   # range(surgery time, due_day) per mandatory (senza due_day per non mandatory)

   # DA METTERE A POSTO ✅ 
   # 0) Each nurse schedule should follow the roster given
   nurseXroom = follow_shift(nurses, nurseXroom, D, id_nurse_working) 
   # nurseXroom obtained is compatible with the constraint

   # VINCOLI 1,7,2 da mettere insieme, ricordarsi quando si cicla di prendere random. es ciclo in stanze incompatibili
   # Farlo costruttivo (questo andrà nella local search). ✅

   # METTERE A POSTO NEL GENDER (confrontare con l'occupante) ✅

   # H1 and H7) limit of capacity of each room should not be overcome (H7) and in each room all people are the same gender (H1) 
   # H2) Each patient should not be assigned to incompatible rooms (H2)
   new_roomXpatient = room_constr(rooms, patients, occupants, roomXpatient, Adm_yes_or_no, list_day_patientAndoccupant)


   iter = 1 
   max_iter = 10**7

   """
   while not (bool_0_constraint  and bool_3_4_constraint and bool_1_7_constraint) and iter >= max_iter:
      bool_0_constraint = one_shift_aDay_constr(nurseXroom, D)
      bool_3_4_constraint = maxTime_constr(surgeons, patients, operating_theaters, Adm_Date, otXpatient, D)
      bool_1_7_constraint = room_constr(rooms, patients, occupants, roomXpatient, Adm_yes_or_no, list_day_patientAndoccupant)

   if iter >= max_iter:   
      flag = False     # feasible solution not found, need to restart
   else :
      flag = True
   """
   flag = True
   x_feasible = [Adm_yes_or_no, Adm_Date, new_roomXpatient, otXpatient, nurseXroom, OT_availability]
   return x_feasible, flag, list_day_patientAndoccupant

def LocalSearch(x_feasible, f_best_sofar, patients, occupants, rooms, nurses, surgeons, D, operating_theaters, list_day_patientAndoccupant, weights):
   # Choice: first Improvement
   max_iter = 1000
   iter = 0

   while iter <= max_iter:
      iter += 1
      # First perturbation: date of admission 
      Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom, OT_availability = x_feasible

      for p in range(0,len(patients)):
         if Adm_Date[p] == D-1:
            continue
         Adm_Date[p] = Adm_Date[p] + 1

         # Check if it's feasible
         x = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom, OT_availability]
         find = check_constraint(x, occupants, patients, rooms, nurses, surgeons, D, operating_theaters, list_day_patientAndoccupant)

         if find == True:

            # Check if it improves the solutions
            value2 = evaluate_obj_func(x, occupants, patients, rooms, nurses, surgeons, D, weights)

            if value2 < f_best_sofar:  # minore così quando perturbiamo non torniamo alla stessa soluzione
               return [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom, OT_availability], find, value2

         # Check if it enhance objective function
      
      for p in range(0,len(patients)):
         if Adm_Date[p] == 0:
            continue
         Adm_Date[p] = Adm_Date[p] - 1

         # Check if it's feasible
         x = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom, OT_availability]
         find = check_constraint(x, occupants, patients, rooms, nurses, surgeons, D, operating_theaters, list_day_patientAndoccupant)

         if find == True:

            # Check if it improves the solutions
            value2 = evaluate_obj_func(x, occupants, patients, rooms, nurses, surgeons, D, weights)

            if value2 < f_best_sofar:  # minore così quando perturbiamo non torniamo alla stessa soluzione
               return [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom, OT_availability], find, value2
      
      # Second perturbation

      for p in range(0,len(patients)):
         if roomXpatient[p] != -1 and roomXpatient[p] != len(rooms)-1:
            continue
         roomXpatient[p] = roomXpatient[p] + 1

         # Check if it's feasible
         x = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom, OT_availability]
         find = check_constraint(x, occupants, patients, rooms, nurses, surgeons, D, operating_theaters, list_day_patientAndoccupant)

         if find == True:

            # Check if it improves the solutions
            x = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom, OT_availability]
            value2 = evaluate_obj_func(x, occupants, patients, rooms, nurses, surgeons, D, weights)

            if value2 < f_best_sofar:  # minore così quando perturbiamo non torniamo alla stessa soluzione
               return [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom, OT_availability], find, value2
         

      for p in range(0,len(patients)):
         if roomXpatient[p] != -1 and roomXpatient[p] != 0:
            continue
         roomXpatient[p] = roomXpatient[p] - 1

         # Check if it's feasible
         x = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom, OT_availability]
         find = check_constraint(x, occupants, patients, rooms, nurses, surgeons, D, operating_theaters, list_day_patientAndoccupant)

         if find == True:

            # Check if it improves the solutions
            x = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom, OT_availability]
            value2 = evaluate_obj_func(x, occupants, patients, rooms, nurses, surgeons, D, weights)

            if value2 < f_best_sofar:  # minore così quando perturbiamo non torniamo alla stessa soluzione
               return [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom, OT_availability], find, value2


      # Third perturbation: swap nurse that work in the same shift
      for t in range(0,D):
         for s in range(0,3):
            for i in range(0,len(rooms)-1):
               for j in range(i+1,len(rooms)):
                  id_n1 = nurseXroom[i,t,s] 
                  id_n2 = nurseXroom[j,t,s] 
                  nurseXroom[i,t,s] = id_n2
                  nurseXroom[j,t,s] = id_n1

                  # Already feasible

                  # Check if it improves the solutions
                  x = [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom, OT_availability]
                  value2 = evaluate_obj_func(x, occupants, patients, rooms, nurses, surgeons, D, weights)
                  
                  if value2 < f_best_sofar:   # minore così quando perturbiamo non torniamo alla stessa soluzione
                     improve = True
                  
                  if find == True and improve == True:
                     return [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom], find, value2
      
      return [], False, 0
                              

      """
                  list_open_room = []
            for p in range(0,len(patients)):
               list_open_room.append(roomXpatient[p])"""


def check_constraint(x, occupants, patients, rooms, nurses, surgeons, D, operating_theaters, list_day_patientAndoccupant):

   [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom, OT_availability] = x

   # Constraint H1, H7
   bool_1_7_constraint = room_constr_bool(rooms, patients, occupants, roomXpatient, Adm_Date, list_day_patientAndoccupant)

   # Constraint H3, H4
   bool_3_4_constraint = maxTime_constr_bool(surgeons, patients, operating_theaters, Adm_Date, otXpatient, D)
   
   # Constraint H5, H6
   # Non ancora controllata ✅ 
   bool_6_constraint = bool_period_of_admission_constr(Adm_yes_or_no, Adm_Date, patients)
   bool_5_constraint = bool_admit_mandatory_constr(Adm_yes_or_no, patients)

   # Scheduling of nurse are already respect because of the perturbation

   # Constraint H2  ✅ 
   bool_2_constraint = bool_incompatible_room_constr(patients, roomXpatient)

   return all([bool_1_7_constraint, bool_3_4_constraint, bool_6_constraint, bool_5_constraint, bool_2_constraint])


def evaluate_obj_func(x, occupants, patients, rooms, nurses, surgeons, D, weights):
   Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom, OT_availability = x
   
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
   qnt8 = np.sum(Adm_yes_or_no == 0) * weights['unscheduled_optional']

   total_cost = qnt1 + qnt2 + qnt3 + qnt4 + qnt5 + qnt6 + qnt7 + qnt8 

   return  total_cost  
   

# Functions regarding each constraint.

def admit_mandatory_constr(Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, patients, D, surgeons, operating_theaters, OT_availability):
   

   # We impose to admit all mandatory patients
   Adm_yes_or_no = [[] for _ in range(len(patients))]
   for p, patient in enumerate(patients):
      if patient.mandatory:
         Adm_yes_or_no[p] = 1
      else:
         Adm_yes_or_no[p] = random.uniform(0, 1)

   Adm_Date = [[] for _ in range(len(patients))]
   surgeons_availability = []
   for s, surgeon in enumerate(surgeons):
      surgeons_availability.append(surgeon.list_max_surgery_time)
   
   list_timeXsurgeon = [[0] * D for _ in range(len(surgeons))]
   list_timeXOT = [[0] * D for _ in range(len(operating_theaters))]
   
   for p, patient in enumerate(patients):
      available = []
      all_ot_available_in_the_day = []
      if patient.mandatory:  
         # if it is False, there are 2 cases: 1. neither surgeon's max time constraint nor OT's constraint or surgeon's max time constraint not respected
         # => change Adm_date
         flag_day = False 
         # if it is False, OT's constraint not respected => change OT
         flag_OT = False 

         id_surgeonXp = patient.surgeon_id 
         tot_day_availability = surgeons_availability[id_surgeonXp]
         day_available = np.nonzero(tot_day_availability)[0]
         # we take the intersection between day availability of the surgeon and interval time between surgery_release and surgery_due_day
         Adm_Date[p] = random.choice(list(set(day_available).intersection(range(patient.surgery_release_day, patient.surgery_due_day + 1))))
         
         while flag_day == False and flag_OT == False:
            
            if (operating_theaters[otXpatient[p]].availability)[Adm_Date[p]] - list_timeXOT[otXpatient[p]][Adm_Date[p]] >= patient.surgery_duration:
               list_timeXOT[otXpatient[p]][Adm_Date[p]] += patient.surgery_duration
               flag_OT = True
               
            else:   
               
               for ot, OT_theater in enumerate(operating_theaters):
                  if OT_availability[ot][Adm_Date[p]] > 0:
                     all_ot_available_in_the_day.append(ot)
               if len(all_ot_available_in_the_day) > 0:
                  otXpatient[p] = np.random.choice(all_ot_available_in_the_day)  

            if surgeons_availability[id_surgeonXp][Adm_Date[p]] - list_timeXsurgeon[id_surgeonXp][Adm_Date[p]] > patient.surgery_duration and flag_OT == True:
               list_timeXsurgeon[id_surgeonXp][Adm_Date[p]] += patient.surgery_duration
               flag_day = True
            elif flag_OT == False:   
               Adm_Date[p] = random.choice(list(set(day_available).intersection(range(patient.surgery_release_day, patient.surgery_due_day + 1))))
               
   



      elif not patient.mandatory and Adm_yes_or_no[p] == 1:
         flag_day = False 
         # if it is False, OT's constraint not respected => change OT
         flag_OT = False 

         id_surgeonXp = patient.id_surgeon 
         tot_day_availability = surgeons_availability[id_surgeonXp]
         day_available = np.nonzero(tot_day_availability)[0]
         # we take the intersection between day availability of the surgeon and interval time between surgery_release and surgery_due_day
         Adm_Date[p] = random.choice(list(set(day_available).intersection(range(patient.surgery_release_day, patient.surgery_due_day + 1))))
         
         while flag_day == False and flag_OT == False:
            if (operating_theaters[otXpatient[p]].availability)[Adm_Date[p]] - list_timeXOT[otXpatient[p]][Adm_Date[p]] > patient.surgery_duration:
               list_timeXOT[otXpatient[p]][Adm_Date[p]] += patient.surgery_duration
               flag_OT = True
            else:   
               available = OT_availability[otXpatient[p]][Adm_Date[p]]
               if available > 0:
                  valid_indices = [i for i, val in enumerate(available) if val > 0]

               if len(valid_indices) > 0:
                  otXpatient[p] = np.random.choice(valid_indices)

            if surgeons_availability[id_surgeonXp][Adm_Date[p]] - list_timeXsurgeon[id_surgeonXp][Adm_Date[p]] > patient.surgery_duration and flag_OT == True:
               list_timeXsurgeon[id_surgeonXp][Adm_Date[p]] += patient.surgery_duration
               flag_day = True
            elif flag_OT == False:   
               Adm_Date[p] = random.choice(list(set(day_available).intersection(range(patient.surgery_release_day, patient.surgery_due_day + 1))))

      else:
         Adm_Date[p] = -1



   # DA FARE LUNEDì: ci sono 2 casi:
   # 1. se non rispetta nè il vincolo di tempo del chirurgo nè della sala OPPURE se NON rispetto il vincolo di tempo del chirurgo => basta cambiare giorno
   # 2. se NON rispetto la sala operatoria => tengo FISSA Adm_date e CAMBIO SOLO la sala operatoria (tra quelle compatibili)
      
   return Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient

# CORRETTOOOOOOO!! (PER SICUREZZA CONTROLLARE)
# giusto ma possiamo scriverla in maniera più "costo computazionale friendly"
# idea ross: fisso il tempo e turno e vedo infermieri che possono lavorare in quel turno e assegno le stanze randomicamente
def follow_shift(nurses, nurseXroom, D, id_nurse_working):
   '''
   print(10)
   for n, nurse in enumerate(nurses):
      list_roster = nurse.working_shifts
      print(11)
      for t in range(0,D):
         # boolean which indicates if nurse can work in that day and shift
         for s in range(0,3):
            exist_shift_scheduled = any(d['day'] == t  and string_conversion(d['shift']) == s for d in list_roster)
         if not exist_shift_scheduled:   # the nurse can't work in that period of time
            for r in range(0,nurseXroom.shape[0]):
               id_nurse = nurseXroom[r,t,s]
               while id_nurse == n:  # need to change nurse 
                  Heads_or_Tails = random.randint(0, 1)
                  if Heads_or_Tails == 0:  # change nurse in a random way
                     nurseXroom[r,t,s] = min(nurseXroom[r,t,s] + 1, len(nurses) -1)
                  else:
                     nurseXroom[r,t,s] = max(nurseXroom[r,t,s] - 1, 0)
      return nurseXroom
   '''

   '''
   COMMENTO MODIFICA: controlliamo che la soluzione random dell'assegnazione infermieri-stanze rispetti i
   loro turni nei dati giorni, se no => peschiamo random un infermiere compatibile
   '''
   for s in range(0,3):
      for d in range(0,D):
         list_nurses_compatible = id_nurse_working[s][d]
         for r in range(0, nurseXroom.shape[0]):
            id_nurse_assigned = nurseXroom[r][d][s]
            if id_nurse_assigned not in list_nurses_compatible:
               nurseXroom[r][d][s] = random.choice(list_nurses_compatible)
   return nurseXroom

'''
QUESTO DOVREBBE ESSERE TOLTO PERCHE' LO STIAMO INGLOBANDO IN QUELLO DI SOPRA!
'''
def maxTime_constr(surgeons, patients, operating_theaters, Adm_Date, otXpatient, D):
   for t in range(0,D):
      list_timeXsurgeon = np.zeros(len(surgeons))
      list_timeXOT = np.zeros(len(operating_theaters))
      # extract only patient admitted in t 
      patient_in_t = np.where(Adm_Date == t)[0]
      info_patient_in_t = [patients[i] for i in patient_in_t]
      for p, pat in enumerate(info_patient_in_t):
         list_timeXsurgeon[pat.surgeon_id] = list_timeXsurgeon[pat.surgeon_id] + pat.surgery_duration
         list_timeXOT[otXpatient[p]] = list_timeXOT[otXpatient[p]] + pat.surgery_duration
      # for each surgeon total time should not exceed the surgeon's max time
      for s, time_req in enumerate(list_timeXsurgeon):
         if time_req > surgeons[s].list_max_surgery_time[t]:
            return False
      for s,time_req in enumerate(list_timeXOT):
         if time_req > operating_theaters[s].availability[t]:
            return False
   return True


'''
CONTROLLARE: abbiamo reso room_constr costruttiva, modificando le assegnazioni dei pazienti alle stanze qualora 
NON soddisfacessero i vincoli delle stanze (la versione booleana è SOTTO)
'''
def room_constr(rooms, patients, occupants, roomXpatient, Adm_Date, list_day_patientAndoccupant):
   new_roomXpatient = roomXpatient.copy()

   # per modifiche sul vincolo di GENERE: consideriamo gli occupanti (che sono attribuiti a una stanza ciascuno)
   # estraiamo per ogni stanza il genere del primo occupante (sono per forza TUTTI uguali perchè il vincolo di genere è FORTE)
   # mentre per le stanze SENZA occupanti estraiamo il genere del primo paziente che inseriamo (considerando l'admission date) 
   
   genderXroom = dict() 
   gender_A = [] 
   gender_B = []
   for o, occupant in enumerate(occupants):
      gender_occupant = occupant.gender
      if occupant.room_id not in genderXroom:
         genderXroom[occupant.room_id] = gender_occupant

         if occupant.gender == "A":
            gender_A.append(occupant.room_id)
         else:
            gender_B.append(occupant.room_id)
   
   missing_rooms = list(set(range(len(rooms))) - set(genderXroom.keys()))
   # estraiamo da roomXpatient gli id dei pazienti che stanno nelle missing_rooms, tra quelli che stanno nella stessa, selezioniamo
   # quello con data di ammissione più piccola e prendiamo il suo genere
   # IMPORTANTE: ASSUNZIONE CHE STIAMO FACENDO -> supponiamo che il primo paziente/occpuante nella stanza determini anche in futuro
   # il genere perchè sennò bisognerebbe trovare pazienti/occupanti che liberano tutti insieme la stanza nello stesso momento
   # e da lì in avanti far ripartire il genere (caso molto particolare, quindi lo escludiamo), per questo NON consideriamo list_of_set_gender
   # MA creiamo genderXroom
   
   for id_room in missing_rooms:
      id_patients = [i for i, x in enumerate(roomXpatient) if x == id_room]

      if not id_patients: # if there are no patients in the room, skip it
        continue

      index_min_adm_date = np.argmin([Adm_Date[i] for i in id_patients])
      min_patient = id_patients[index_min_adm_date]
      genderXroom[id_room] = patients[min_patient].gender
      
      if patients[min_patient].gender == "A":
         gender_A.append(id_room)
      else:
         gender_B.append(id_room)

   
      

   for t, list_people in enumerate(list_day_patientAndoccupant):
      #list_of_set_gender = [set() for _ in range(len(rooms))]
      num_of_people = np.zeros(len(rooms))

      for i in list_people:
         if i < len(patients):   # i is an admitted patient
            room_id = roomXpatient[i]
            num_of_people[room_id] += 1
         
         else:                   # i is an occupant
            room_id = occupants[i-len(patients)].room_id 
            num_of_people[room_id] += 1
            '''print("Length of patients:", len(patients))
            print("Length of occupants:", len(occupants))
            print("i:", i)'''
      
      for r, room in enumerate(rooms):
         while num_of_people[r] > room.capacity:  # if it overcomes maximum capacity => find a new room
            for p, patient in enumerate(patients):
                  compatible_rooms = list(set(list(range(len(rooms))))-set(patient.incompatible_room_ids))
                  if patient.room_id == r or patient.gender != genderXroom[r]:
                     valid_rooms_A = [rr for rr in compatible_rooms if rr not in gender_A and num_of_people[rr] < rooms[rr].capacity]
                     valid_rooms_B = [rr for rr in compatible_rooms if rr not in gender_B and num_of_people[rr] < rooms[rr].capacity]

                     if patient.gender == "A" and valid_rooms_A:
                        new_r = random.choice(list(compatible_rooms - set(gender_A)))
                     elif patient.gender == "B" and valid_rooms_B:
                        new_r = random.choice(list(compatible_rooms - set(gender_B)))
                     else:
                        Warning('No compatible rooms.')
                        continue
                     
                     new_roomXpatient[patient.id] = new_r
                     num_of_people[r] -= 1
                     num_of_people[new_r] += 1
                  
                     break

   return new_roomXpatient

####################### vedere se può servire in futuro
'''
ATTENZIONE: la funzione che segue serve in seguito per verificare che i vincoli per le stanze siano 
soddisfatti, noi sopra la sostituiamo con una versione COSTRUTTIVA!!!!
'''
def room_constr_bool(rooms, patients, occupants, roomXpatient, Adm_yes_or_no, list_day_patientAndoccupant):
   for t, list_people in enumerate(list_day_patientAndoccupant):
      list_of_set_gender = [set() for _ in range(len(rooms))]
      num_of_people = np.zeros(len(rooms))
      for i in list_people:
         if i < len(patients):   # i is an admitted patient
            room_id = roomXpatient[i]
            num_of_people[room_id] = num_of_people[room_id] + 1
            list_of_set_gender[room_id].add(patients[i].gender)
         elif i >= len(patients):     # i is an occupant
            room_id = occupants[i-len(patients)].room_id 
            num_of_people[room_id] = num_of_people[room_id] + 1
            '''print("Length of patients:", len(patients))
            print("Length of occupants:", len(occupants))
            print("i:", i)'''
            list_of_set_gender[room_id].add(occupants[i-len(patients)].gender) # oss: list_of_set serve per ottenere il booleano dovuto al numero di generi diversi, perde l'info dell'id che serve nella parte costruttiva
      for r, room in enumerate(rooms):
         if num_of_people[r] > room.capacity:   # overcome maximum capacity of a room
            return False
      for room_set in list_of_set_gender:
        if len(room_set) > 1:  # more than one gender in a room
            return False
   return True

def bool_period_of_admission_constr(Adm_yes_or_no, Adm_Date, patients):
   for p, patient in enumerate(patients):
        if Adm_yes_or_no[p] == 0:
            continue  
        surgery_release = patient.surgery_release_day
        if patient.mandatory:
            if not (surgery_release <= Adm_Date[p] <= patient.surgery_due_day):
               return False  # at least one admission date is wrong
        elif Adm_Date[p] < surgery_release:   # for non mandatory
            return False  # at least one admission date is wrong
   return True



def bool_admit_mandatory_constr(Adm_yes_or_no, patients):
   for p, current_patient in enumerate(patients):  
    if current_patient.mandatory and Adm_yes_or_no[p] == 0 :   
       return False
   return True


def bool_incompatible_room_constr(patients, roomXpatient):
   for p, patient in enumerate(patients):
      if roomXpatient[p] in patient.incompatible_room_ids:
         return False
   return True


def one_shift_aDay_constr(nurseXroom, D):
   for t in range(0,D):
      idN_1Shift = set(nurseXroom[:,t,0] ) 
      idN_2Shift = set(nurseXroom[:,t,1] )
      idN_3Shift = set(nurseXroom[:,t,2] )
      if idN_1Shift.intersection(idN_2Shift) or idN_1Shift.intersection(idN_3Shift) or idN_2Shift.intersection(idN_3Shift):
         return False   # there is at least one nurse which work in more shift one day
   return True

'''
ATTENZIONE: usare in verifyingconstr!!!!!
'''

def maxTime_constr_bool(surgeons, patients, operating_theaters, Adm_Date, otXpatient, D):
   for t in range(0,D):
      list_timeXsurgeon = np.zeros(len(surgeons))
      list_timeXOT = np.zeros((D, len(operating_theaters)))
      # extract only patient admitted in t 
      patient_in_t = [i for i in range(len(Adm_Date)) if Adm_Date[i] == t]
      info_patient_in_t = [patients[i] for i in patient_in_t]
      for p, pat in enumerate(info_patient_in_t):
         list_timeXsurgeon[pat.surgeon_id] = list_timeXsurgeon[pat.surgeon_id] + pat.surgery_duration
         #list_timeXOT[t, otXpatient[p]] += pat.surgery_duration
         
         if 0 <= otXpatient[p] < len(operating_theaters):
            list_timeXOT[t, otXpatient[p]] += pat.surgery_duration
         else:
            print(f"Errore: otXpatient[{p}] = {otXpatient[p]} fuori dai limiti!")
      # for each surgeon total time should not exceed the surgeon's max time
      for s, time_req in enumerate(list_timeXsurgeon):
         if time_req > surgeons[s].list_max_surgery_time[t]:
            return False
      for s, time_req in enumerate(list_timeXOT):
         for ot, OT_theater in enumerate(operating_theaters):
            if time_req[ot] > OT_theater.availability[s]:
               return False
   return True


'''
ATTENZIONE: lo abbiamo inserito in room_constr!!!!
'''
def imcopatible_room_constr_vecchia(patients, roomXpatient, num_rooms):
   for p, patient in enumerate(patients):
         diff = list(set(list(range(num_rooms)))-set(patient.incompatible_room_ids)) # remove incompatible rooms
         roomXpatient[p] = random.sample(diff,1)[0]
         """
         while roomXpatient[p] in patient.incompatible_room_ids:
         Heads_or_Tails = random.randint(0, 1)
         if Heads_or_Tails == 0:
            roomXpatient[p] = min(roomXpatient[p] + 1, num_rooms -1)
         else:
            roomXpatient[p] = max(roomXpatient[p] - 1, 0)
         """
   return roomXpatient


