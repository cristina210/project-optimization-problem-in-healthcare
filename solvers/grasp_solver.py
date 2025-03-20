from solvers.utils_grasp import *
import warnings
import time

def grasp_solver(D, weights, occupants, patients, operating_theaters, rooms, nurses, surgeons, max_iter):
   time_create_random = []
   time_local_search = []
   iter = 1
   flag_point_found2 = True
   start_time_create_fea_sol = time.time() 
   while iter < max_iter and flag_point_found2:
      print("Iteration:")
      print(iter)
      x_feasible, flag_point_found1 = construct_feasible_solution(occupants, patients, operating_theaters, rooms, nurses, surgeons, D)
      if flag_point_found1 == False:  # a feasible solution is not found
         print("Firstly, non mandatory patients are not admitted")
         x_feasible, flag_point_found2 = construct_feasible_solution(occupants, patients, operating_theaters, rooms, nurses, surgeons, D, True)    # relaxing soft constraint about admitting non mandatory
         if flag_point_found2 == False:
            warnings.warn("Impossible to find a starting feasible solution")
      end_time_create_fea_sol = time.time()
      time_create_random.append(end_time_create_fea_sol - start_time_create_fea_sol)
      # CONTROLLO se feasible:
      [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom] = x_feasible 
      flag2 = bool_incompatible_room_constr(patients, roomXpatient) # OK
      # ma in certi casi room_constr non trova soluzioni, bisogna mettere ciclo while da qualche parte
      flag3 = OT_and_Surgeon_constr_bool(surgeons, patients, operating_theaters, Adm_Date, otXpatient, D)   # OK ma in alcuni casi viene false ma perchè viene false già in construct, metterli fuori dal ciclo
      flag5 = bool_admit_mandatory_constr(Adm_yes_or_no, patients) # OK
      flag6 = bool_period_of_admission_constr(Adm_yes_or_no, Adm_Date, patients) # OK
      flag7 = room_constr_bool(rooms, patients, occupants, roomXpatient, Adm_yes_or_no, Adm_Date, D) 
      # non mandatory not admitted i21
      # not a feasible solution i20
      print("flag coerenza:")
      print(flag2)
      print(flag3)
      print(flag5)
      print(flag6)
      print(flag7)
      # FINE CONTROLLO
      # initialize f_best_sofar 
      value_feas_sol = evaluate_obj_func(x_feasible, occupants, patients, rooms, nurses, surgeons, D, weights)
      print("restart from a new solution:")
      print(value_feas_sol)
      if iter == 1:
         f_best_sofar = value_feas_sol
         x_best_sofar = x_feasible
      improvements_yes_or_no = False  # avoid to seach in the neighbourhood of not promising point (non so se va bene, pensare magari a mettere una soglia, se la sol fa troppo schifo vai avanti)
      if value_feas_sol < f_best_sofar:
         x_best_sofar = x_feasible
         f_best_sofar =  value_feas_sol
      #worthy_search = (value_feas_sol < f_best_sofar + 1000)  # si può trovare un valore + sensato? Ha senso se non conosco f e se questa è continua
      worthy_search = True
      if worthy_search:
         improvements_yes_or_no = True   
      # explore the neighbourhood:
      while improvements_yes_or_no :
         print("vicino del vicino: ")
         start_time_loc_search = time.time()
         x_best_neighbour, improvements_yes_or_no, f_new = LocalSearch(x_feasible, f_best_sofar, patients, occupants, rooms, nurses, surgeons, D, operating_theaters, weights) 
         end_time_loc_search = time.time()
         time_local_search.append(end_time_loc_search-start_time_loc_search)
         if improvements_yes_or_no:
            print("Improve")
            f_best_sofar = f_new
            print("f = ")
            print(f_new)
            x_best_sofar = x_best_neighbour
            x_feasible = x_best_neighbour
      iter = iter + 1
   if flag_point_found2 == False:
      return [],[]
   return f_best_sofar, x_best_sofar, time_create_random, time_local_search


def grasp_solver_prova(D, weights, occupants, patients, operating_theaters, rooms, nurses, surgeons, max_iter):
   x_feasible, flag_point_found1 = construct_feasible_solution(occupants, patients, operating_theaters, rooms, nurses, surgeons, D)
   if flag_point_found1 == False:  # a feasible solution is not found
      print("Firstly, non mandatory patients are not admitted")
      x_feasible, flag_point_found2 = construct_feasible_solution(occupants, patients, operating_theaters, rooms, nurses, surgeons, D, True)    # relaxing soft constraint about admitting non mandatory
      if flag_point_found2 == False:
         warnings.warn("Impossible to find a starting feasible solution")
   # CONTROLLO se feasible:
   [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom] = x_feasible 
   flag2 = bool_incompatible_room_constr(patients, roomXpatient) # OK
   # ma in certi casi room_constr non trova soluzioni, bisogna mettere ciclo while da qualche parte
   flag3 = OT_and_Surgeon_constr_bool(surgeons, patients, operating_theaters, Adm_Date, otXpatient, D)   # OK ma in alcuni casi viene false ma perchè viene false già in construct, metterli fuori dal ciclo
   flag5 = bool_admit_mandatory_constr(Adm_yes_or_no, patients) # OK
   flag6 = bool_period_of_admission_constr(Adm_yes_or_no, Adm_Date, patients) # OK
   flag7 = room_constr_bool(rooms, patients, occupants, roomXpatient, Adm_yes_or_no, Adm_Date, D) 
   # non mandatory not admitted i21
   # not a feasible solution i20
   print("flag coerenza:")
   print(flag2)
   print(flag3)
   print(flag5)
   print(flag6)
   print(flag7)
   # FINE CONTROLLO
   return 0,0, [], []
