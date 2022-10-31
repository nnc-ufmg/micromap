from open_ephys.analysis import Session
from os import walk
import Binary

file_nnc = "G:\\Outros computadores\\Desktop\\GitHub\\acquisition_system\\validation\\validation_data_27-10-2022\\validation_data_nnc_rpi\\"
file_open_ehpys = "G:\\Outros computadores\\Desktop\\GitHub\\acquisition_system\\validation\\validation_data_27-10-2022\\validation_data_openephys\\"


files_nnc = next(walk(file_nnc), (None, None, []))[2][:-1]
files_nnc = [file_nnc + file for file in files_nnc]
files_nnc = sorted(files_nnc)
files_open_ehpys = next(walk(file_open_ehpys), (None, [], None))[1]
files_open_ehpys = [file_open_ehpys + file for file in files_open_ehpys]
files_open_ehpys = sorted(files_open_ehpys)

#T0
session = Session(files_open_ehpys[4])
records = session.recordnodes[0].recordings[0]
continuous = records.continuous[0]

print("OI")

# T1
# Data, Rate = Binary.Load(file)

# print("OI")