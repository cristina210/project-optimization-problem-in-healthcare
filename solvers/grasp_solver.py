from solvers.utils_grasp import *

def grasp_solver(D, weights, occupants, patients, operating_theaters, rooms, nurses, surgeons, max_iteration, id_nurse_working):
   iter = 1
   list_x_already_visit = []
   print("ciao2")
   while iter <= max_iteration:
      flag_point_found = False
      while not flag_point_found :
         # x is a list of decision variables and is created randomly:
         x = create_random_point(D,len(patients),len(rooms),len(operating_theaters),len(nurses), surgeons, patients,  operating_theaters)
         # x_feasible rapresent the starting point for local search. It is a feasible solution:
         [Adm_yes_or_no, Adm_Date, roomXpatient, otXpatient, nurseXroom, OT_availability] = x
         x_feasible, flag_point_found, list_day_patientAndoccupant = construct_feasible_solution(x, occupants, patients, operating_theaters, rooms, nurses, surgeons, D, id_nurse_working)
      # initialize f_best_sofar 
      if iter == 1:
         f_best_sofar = evaluate_obj_func(x_feasible, occupants, patients, rooms, nurses, surgeons, D, weights, list_day_patientAndoccupant)
         print(f_best_sofar)
         x_best_sofar = x_feasible
      improvements_yes_or_no = True
      # explore the neighbourhood:
      # PROBLEMA: NON aggiorna quiiiii 
      while improvements_yes_or_no :
         x_best_neighbour, improvements_yes_or_no, f_new = LocalSearch(x_feasible, f_best_sofar, patients, occupants, rooms, nurses, surgeons, D, operating_theaters, list_day_patientAndoccupant, weights)  
         if improvements_yes_or_no:
            print("improve")
            f_best_sofar = f_new
            print(f_new)
            x_best_sofar = x_best_neighbour
            x_feasible = x_best_neighbour
      iter = iter + 1
      print(iter)
      print(f_best_sofar)
      
   return f_best_sofar, x_best_sofar
