from Instances.utils_instances import extract_number

class Surgeon:
    def __init__(self, id, max_surgery_time):
        self.id = extract_number(id)
        self.list_max_surgery_time = max_surgery_time # list of value for each day

    def __repr__(self):
        return f"Surgeon({self.id}, Max surgery time: {self.list_max_surgery_time})"