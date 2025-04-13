# Stochastic-opt-assignement

## Purpose
Quello che ha scritto leti

1)  è il problema da risolvere (3 problemi di scheduling in ospedale)

2) Qual è l'approccio (GRASP su istanze ospedaliere).

3) Qual è l'obiettivo (minimizzare costi).

## Project Structure
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

## How to Run
Clone the repository:
    ```bash
    git clone https://github.com/cristina210/Stochastic-opt-assignement.git
    ```
Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```
Run the application:
    ```bash
    python main.py
    ```