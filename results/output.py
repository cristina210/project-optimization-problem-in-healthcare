import json
import os
def change_shift(number):
    if number == 0:
        return "early"
    elif number == 1:
        return "late"
    else:
        return "night"

def L(id_n, matrix, rooms):
    d = [] # day
    s = [] # shift
    r = [] # room
    for id_room in range(len(matrix)):
        for day in range(len(matrix[id_room])):
            for shift in range(len(matrix[id_room][day])):
                id_nurse = matrix[id_room][day][shift]
                if id_nurse == id_n:
                    d.append(day)
                    s.append(shift)
                    r.append(id_room)

    # Eliminare ripetizioni (day, shift) e raggruppare le room
    dictionary = {}
    for day, shift, room in zip(d, s, r):
        key = (day, shift)
        if key not in dictionary:
            dictionary[key] = {
                "day": int(day),
                "shift": change_shift(shift),
                "rooms": []
            }
        dictionary[key]["rooms"].append(rooms[room].id_orig)

    return list(dictionary.values())

def patient_output(Adm_Date, roomXpatient, operating_theaters, patients, rooms):
    """Genera una lista di pazienti con le relative informazioni."""
    patient_list = [] 
    for p in range(len(Adm_Date)):
        id_p = str(patients[p].id_orig)
        if Adm_Date[p] == -1:
            dictionary = {
            "id": id_p, 
            "admission_day": "none",  # Mantieni un numero qui se richiesto
            }
        else:
            dictionary = {
                "id": id_p,
                "admission_day": int(Adm_Date[p]),
                "room": "r0" + str(roomXpatient[p]) if int(roomXpatient[p]) < 10 else "r" + str(roomXpatient[p]),
                # for file i04
                #"room": "r" + str(roomXpatient[p]), 
                "operating_theater": "t" + str(operating_theaters[p])
            }
        patient_list.append(dictionary)  
    return patient_list

def nurse_output(nurses, nurseXroom, rooms):
    result = []
    for n in range(len(nurses)): 
        id_n = str(nurses[n].id_orig)
        info = L(n, nurseXroom, rooms)
        dictionary = {"id": id_n, "assignments": info}
        result.append(dictionary)
    return result

def generate_json(solution, patients, nurses, rooms, operating_theaters):
    """
    Genera un file JSON con la pianificazione dell'ospedale.
    """
    data = {
        "patients": patient_output(solution[1], solution[2], solution[3], patients, rooms),
        "nurses": nurse_output(nurses, solution[4], rooms)
    }

    outputfile = os.path.join("results", "hospital_schedule.json")

    with open(outputfile, "w") as json_file:
        json.dump(data, json_file, indent=4)

    print("File 'hospital_schedule.json' creato con successo!")
