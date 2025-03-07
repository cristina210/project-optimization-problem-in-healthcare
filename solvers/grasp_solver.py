from solvers.utils_grasp import *

def grasp_solver(D, weights, occupants, patients, operating_theaters, rooms, nurses, surgeons, max_iteration, id_nurse_working):
   iter = 1
   list_x_already_visit = []
   print("ciao2")
   while iter <= max_iteration:
      flag_point_found = False
      print("ciao6") 
      while not flag_point_found :
         # x is a list of decision variables and is created randomly:
         x = create_random_point(D,len(patients),len(rooms),len(operating_theaters),len(nurses), surgeons, patients,  operating_theaters)
         print("ciao5")
         # x_feasible rapresent the starting point for local search. It is a feasible solution:
         x_feasible, flag_point_found = construct_feasible_solution(x, occupants, patients, operating_theaters, rooms, nurses, surgeons, D, id_nurse_working)
         print("ciao3")
      # initialize f_best_sofar 
      if iter == 1:
         print("ciao4")
         f_best_sofar = evaluate_obj_func(x_feasible, occupants, patients, rooms, nurses, surgeons, D, weights)
         x_best_sofar = x_feasible
      improvements_yes_or_no = True
      # explore the neighbourhood:
      while improvements_yes_or_no:
         x_best_neighbour, improvements_yes_or_no, f_new = LocalSearch(x_feasible, f_best_sofar)  
         if improvements_yes_or_no:
            f_best_sofar = f_new
            x_best_sofar = x_best_neighbour
            x_feasible = x_best_neighbour
      iter = iter + 1
      print(iter)
   return f_best_sofar, x_best_sofar