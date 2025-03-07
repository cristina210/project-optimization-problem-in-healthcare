from Instances.utils_instances import extract_number

class Nurse:
    def __init__(self, id, skill_level, working_shifts):
        self.id = extract_number(id)
        self.skill_level = skill_level
        self.working_shifts = working_shifts  # List of di dictionary with {day, shift, max_load} as key


    def __repr__(self):
        return f"Nurse({self.id}, Skill Level: {self.skill_level}, Shifts: {self.working_shifts})"
    
    
    