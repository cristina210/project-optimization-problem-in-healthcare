from Instances.utils_instances import string_conversion
from Instances.utils_instances import extract_number

class Occupant:
    def __init__(self, id, gender, age_group, length_of_stay, workload_produced, skill_level_required, room_id):
        self.id = extract_number(id)
        self.gender = gender
        self.age_group = string_conversion(age_group)
        self.length_of_stay = length_of_stay
        self.workload_produced = workload_produced  # list of workload for each day for each shift
        self.skill_level_required = skill_level_required  # list of skill required for each day for each shift
        self.room_id = extract_number(room_id)  # ID della stanza occupata

    def __repr__(self):
        return f"Occupant({self.id}, Room: {self.room_id}, Stay: {self.length_of_stay} days)"