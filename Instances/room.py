from Instances.utils_instances import extract_number

class Room:
    def __init__(self, id_orig: str, id: str, capacity: int):
        self.id_orig = id_orig
        self.id = extract_number(id)
        self.capacity = capacity
        self.patients = []  # Lista di pazienti assegnati alla stanza

    def __repr__(self):
        return f"Room({self.id}, Capacity: {self.capacity}, Patients: {self.patients})"
