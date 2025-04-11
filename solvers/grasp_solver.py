from solvers.utils_grasp import *
import warnings
import time
import copy

def grasp_solver(D, weights, occupants, patients, operating_theaters, rooms, nurses, surgeons, max_iter):
   ## ✅Initialization
   time_create_random = []
   time_local_search = []
   f_history = []
   iter = 1
   flag_point_found2 = True
   start_time_create_fea_sol = time.time() 
   while iter < max_iter and flag_point_found2:
      print("ITERATION:")
      print(iter)
      ## ✅Construct feasible solution:
      x_feasible, flag_point_found1 = construct_feasible_solution(occupants, patients, operating_theaters, rooms, nurses, surgeons, D)
      if flag_point_found1 == False:  # a feasible solution is not found
         print("Firstly, non mandatory patients are not admitted")   # not admitting non mandatory patients
         x_feasible, flag_point_found2 = construct_feasible_solution(occupants, patients, operating_theaters, rooms, nurses, surgeons, D, True)    # relaxing soft constraint about admitting non mandatory
         if flag_point_found2 == False:  # no feasible solution found
            warnings.warn("Impossible to find a starting feasible solution")
      end_time_create_fea_sol = time.time()
      time_create_random.append(end_time_create_fea_sol - start_time_create_fea_sol) 
      value_feas_sol = evaluate_obj_func(x_feasible, occupants, patients, rooms, nurses, surgeons, D, weights)
      f_history.append([value_feas_sol, 1])
      print("Restart from the feasible random point with objective function:")
      print(value_feas_sol)
      if iter == 1:
         f_best_sofar = value_feas_sol
         x_best_sofar = copy.deepcopy(x_feasible) 
      if value_feas_sol < f_best_sofar:
         x_best_sofar = copy.deepcopy(x_feasible)
         f_best_sofar =  value_feas_sol
      improvements_yes_or_no = True    
      ## ✅Explore the neighborhood:
      print("Exploring the neighborhood:")
      while improvements_yes_or_no :
         start_time_loc_search = time.time()
         x_best_neighbour, improvements_yes_or_no, f_new = LocalSearch(x_feasible, f_best_sofar, patients, occupants, rooms, nurses, surgeons, D, operating_theaters, weights) 
         end_time_loc_search = time.time()
         time_local_search.append(end_time_loc_search-start_time_loc_search)
         if improvements_yes_or_no:
            f_history.append([f_new, 0])
            f_best_sofar = f_new
            x_best_sofar = copy.deepcopy(x_best_neighbour)
            x_feasible = copy.deepcopy(x_best_neighbour)
      iter = iter + 1
   if flag_point_found2 == False:
      return [],[]
   return f_best_sofar, x_best_sofar, time_create_random, time_local_search, f_history


