from open_ephys.analysis import Session
from os import walk

folder_openehpys = "G:\\Outros computadores\\Desktop\\GitHub\\acquisition_system\\validation\\openephys_27-10-2022\\"

files_openehpys = next(walk(folder_openehpys), (None, [], None))[1]
files_openehpys = [folder_openehpys + file + "\\Record Node 115" for file in files_openehpys]
files_openehpys = sorted(files_openehpys)


session = Session(files_openehpys[0])
recordings = session.recordings[0]
continuous = recordings.continuous[0]
num_samples = continuous.sample_numbers[-1]
data = continuous.get_samples(start_sample_index=0, end_sample_index=num_samples)

events = recordings.events
init_time = list(events['sample_number'])[-2]
end_time = list(events['sample_number'])[-1]



pass