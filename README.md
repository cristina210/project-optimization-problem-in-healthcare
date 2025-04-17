# Stochastic-opt-assignement

## Purpose
Integrated healthcare scheduling focuses on coordinating resources across multiple services within a single healthcare system.
The optimization problem under consideration addresses three key challenges in healthcare: surgical case planning, scheduling of patient admissions, and assigning nurses to rooms.
The purpose of the code is to enhance and optimize patient flow throughout the hospital’s various departments and facilities. 
We solve the problem by using the implemented  Greedy Randomized Adaptive Search Procedure (GRASP). The goal of this search method is returning a solution which should be both feasible and it should minimize the objective function. It repeatedly applies local search from different starting feasible solution.
The objective function is defined as the weighted sum of all soft constraint violations. Each soft constraint corresponds to a desired but non-mandatory condition in the hospital setting. When these constraints are not fully satisfied, a penalty cost is incurred. The objective is to minimize the total cost, thus achieving a solution that best respects these preferences while maintaining feasibility.
It is important to note that the GRASP solver relies on local search techniques, which means there is no guarantee that the solution found is a global minimum.

## Project Structure
<pre> ```
├── data/                        # Example of data for the scheduling problem
├── Instances/                   # Definition of hospital-related entities
│   ├── hospital.py              # Hospital class definition
│   ├── nurse.py                 # Nurse class definition
│   ├── occupant.py              # Occupant class definition
│   ├── OT.py                    # Operating Theatre class definition
│   ├── patient.py               # Patient class definition
│   ├── room.py                  # Room class definition
│   ├── surgeon.py               # Surgeon class definition
│   └── utils_instances.py       # Utility functions for managing instances'id and attribute
│
├── results/                     # Output results and validator
│   ├── *.json                   # Sample Output files
│   ├── output.py                # Script for processing and displaying outputs
│   ├── IHTP_Validator.cc        # C++ source code for solution validator
│   └── IHTP_Validator.exe       # Compiled validator executable
│
├── settings/                    # Project settings or configuration files (if used)
│
├── solvers/                     # Solving algorithms for the scheduling problem
│   ├── grasp_solver.py          # GRASP algorithm implementation
│   └── utils_grasp.py           # Helper functions used by the solver GRASP
│
├── loader_data.py               # Script to load and prepare data
├── main.py                      # Main script to run the project
├── README.md                    # Project description
└── requirements.txt             # List of Python dependencies
``` </pre>

## How to Run

```bash
Clone the repository:
git clone https://github.com/cristina210/Stochastic-opt-assignement.git

Install the dependencies:
pip install -r requirements.txt

Run the application:
python main.py
