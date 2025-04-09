from solvers.grasp_solver import grasp_solver
from solvers.utils_grasp import evaluate_obj_func
from loader_data import load_data_1
from loader_data import load_data_2
from results.output import generate_json 
from results.output import plot_f_obj


if __name__ == "__main__":
    
   ## loading datasets
   json_file = "data/i07.json"
   occupants, patients, operating_theaters, rooms, nurses, surgeons, hospital = load_data_1(json_file)  
   D, num_skill_level, shift_types, age_groups, weights = load_data_2(json_file) 
   # i20 non troviamo una feasible neanche non accettando nessun non mandatory. Ma il problema è in Admit constr che non mi crea soluzione
   ## finding solution with GRASP method
   max_iter = 10
   f_best, solution, time_create_random, time_local_search, f_history = grasp_solver(D, weights, occupants, patients, operating_theaters, rooms, nurses, surgeons, max_iter)
   #f_best, solution = grasp_solver_prova(D, weights, occupants, patients, operating_theaters, rooms, nurses, surgeons, max_iter)
   print("final result:")
   print(f_best)
   print("Time for creating the initial random feasible point:")
   print(time_create_random)
   print("Time for searching a better solution in the neighborhood")
   print(time_local_search)
   print("Weights in the solution:")
   evaluate_obj_func(solution, occupants, patients, rooms, nurses, surgeons, D, weights, True)
   plot_f_obj(f_history)

#per output jason
generate_json(solution, patients, nurses, rooms, operating_theaters)



