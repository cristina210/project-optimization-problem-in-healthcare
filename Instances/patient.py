from Instances.utils_instances import string_conversion
from Instances.utils_instances import extract_number

class Patient:
    def __init__(self, id, mandatory, gender, age_group, length_of_stay, surgery_release_day, surgery_due_day, surgery_duration, surgeon_id, incompatible_room_ids, workload_produced, skill_level_required):
        self.id = extract_number(id)
        self.mandatory = mandatory
        self.gender = gender
        self.age_group = string_conversion(age_group)
        self.length_of_stay = length_of_stay
        self.surgery_release_day = surgery_release_day
        self.surgery_due_day = surgery_due_day 
        self.surgery_duration = surgery_duration
        self.surgeon_id = extract_number(surgeon_id)
        self.incompatible_room_ids = [extract_number(id_str) for id_str in incompatible_room_ids]  # list 
        self.workload_produced = workload_produced   # list of workload produced for each day for each shift
        self.skill_level_required = skill_level_required  # list of skill required for each day for each shift

    def __repr__(self):
        return f"Patient({self.id}, Age: {self.age_group}, Stay: {self.length_of_stay} days)"