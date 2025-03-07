# function which is used to convert shift string and age string in number in order to quantify them.

def string_conversion(string):
    if string == 'infant' or string == 'early' :
        string_converted = 0
    elif string == 'adult' or string == 'late':
       string_converted = 1
    else:
        string_converted = 2
    return string_converted


# function used to transform an alphanumerical id to number, es p02 -> 2
def extract_number(id_str):
    return int(id_str[1:])  
