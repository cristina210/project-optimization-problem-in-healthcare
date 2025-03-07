from Instances.utils_instances import extract_number

class OperatingTheater:
    def __init__(self, id, availability):
        self.id = extract_number(id)
        self.availability = availability  # list
    
    def __repr__(self):
        return f"OperatingTheater(id={self.id}, availability={self.availability})"