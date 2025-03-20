import json
from Instances.patient import Patient
from Instances.nurse import Nurse
from Instances.occupant import Occupant
from Instances.OT import OperatingTheater
from Instances.room import Room
from Instances.surgeon import Surgeon
from Instances.hospital import Hospital

def load_data_1(json_file):

    try:
        with open(json_file, 'r') as file:
            data = json.load(file)
    except Exception as e:
            print(f"Errore durante il caricamento del file {json_file}: {e}")
            return []   
   
    patients = []  # list of patients (object of Patient class)
    occupants = []  # list of occupants (object of Occupant class)
    operating_theaters = []  # list of OTs (object of OT class)
    rooms = []   # list of rooms (object of Room class)
    nurses = []   # list of nurses (object of Nurse class)
    surgeons = []

    # fill list of patients
    for diz_attribute in data['patients']:   # diz_attribute is a dictionary containing info about a patient
         mandatory_or_not = diz_attribute['mandatory']

         if mandatory_or_not == True:
              surgery_due_day_current = diz_attribute["surgery_due_day"]
         else:  # non mandatory does not have a surgery due day
              surgery_due_day_current = None
              
         current_patient = Patient(
                id_orig=diz_attribute['id'],
                id=diz_attribute['id'],
                mandatory = mandatory_or_not,
                gender = diz_attribute['gender'],   # string A or B
                age_group = diz_attribute['age_group'],  # string
                length_of_stay = diz_attribute['length_of_stay'],
                surgery_release_day = diz_attribute['surgery_release_day'],
                surgery_due_day=surgery_due_day_current,
                surgery_duration = diz_attribute['surgery_duration'],
                surgeon_id = diz_attribute['surgeon_id'],
                incompatible_room_ids = diz_attribute['incompatible_room_ids'],  # list
                workload_produced = diz_attribute['workload_produced'],  # list
                skill_level_required = diz_attribute['skill_level_required']  # list
            )
         patients.append(current_patient)

    # fill list of occupants
    for diz_attribute in data['occupants']:   # diz_attribute is a dictionary containing info about an occupant
        current_occupant = Occupant(
                id=diz_attribute['id'],
                gender = diz_attribute['gender'],
                age_group = diz_attribute['age_group'],  
                length_of_stay = diz_attribute['length_of_stay'], 
                workload_produced = diz_attribute['workload_produced'], 
                skill_level_required = diz_attribute['skill_level_required'],  
                room_id = diz_attribute['room_id']
        )
        occupants.append(current_occupant)

    # fill list of OT
    for diz_attribute in data['operating_theaters']:
        current_OT = OperatingTheater(
              id = diz_attribute['id'],
              availability = diz_attribute['availability']   # list
        )
        operating_theaters.append(current_OT)
    
    
    # fill list of rooms
    for diz_attribute in data['rooms']:
        current_room = Room(
            id=diz_attribute['id'],
            capacity=diz_attribute['capacity']
        )
        rooms.append(current_room)

    # fill list of nurses
    for diz_attribute in data['nurses']:
        current_nurse = Nurse(
        id_orig = diz_attribute['id'],
        id = diz_attribute['id'],
        skill_level=diz_attribute['skill_level'],
        working_shifts=diz_attribute['working_shifts']   # list of diz (keys = day, shift, maxload)
        )
        nurses.append(current_nurse)

    # fill list of surgeons
    for diz_attribute in data['surgeons']:
        current_surgeon = Surgeon(
            id = diz_attribute['id'],
            max_surgery_time = diz_attribute['max_surgery_time']
        )
        surgeons.append(current_surgeon)

    # info about 
    hospital = Hospital(
        surgeon=data['surgeons'],
        room=data['rooms'],
        nurse=data['nurses'],
        operating_theater = data['operating_theaters']
    )
    

    return occupants, patients, operating_theaters, rooms, nurses, surgeons, hospital


def load_data_2(json_file):
    try:
        with open(json_file, 'r') as file:
            data = json.load(file)
    except Exception as e:
            print(f"Errore durante il caricamento del file {json_file}: {e}")
            return []   
    
    D = data['days']  
    num_skill_level = data['skill_levels']
    shift_types = data['shift_types']  
    age_groups = data['age_groups']    # list
    weights = data['weights']    # dictionary (key = type of weight)

    return D, num_skill_level, shift_types, age_groups, weights