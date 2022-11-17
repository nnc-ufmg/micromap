import struct
import numpy
import matplotlib.pyplot as plt
import Binary
from itertools import cycle
from scipy.signal import correlate, correlation_lags, find_peaks, resample
from os import walk
from open_ephys.analysis import Session
import mne

file_pc = "G:\\Outros computadores\\Desktop\\GitHub\\acquisition_system\\validation\\daq_pc_27-10-2022\\"
file_rpi = "G:\\Outros computadores\\Desktop\\GitHub\\acquisition_system\\validation\\nnc_rpi_27-10-2022\\"
file_open_ehpys = "G:\\Outros computadores\\Desktop\\GitHub\\acquisition_system\\validation\\openephys_27-10-2022\\"

files_pc = next(walk(file_pc), (None, None, []))[2]
files_pc = [file_pc + file for file in files_pc]
files_pc = sorted(files_pc)
files_rpi = next(walk(file_rpi), (None, None, []))[2]
files_rpi = [file_rpi + file for file in files_rpi]
files_rpi = sorted(files_rpi)
files_openehpys = next(walk(file_open_ehpys), (None, [], None))[1]
files_openehpys = [file_open_ehpys + file + "\\Record Node 115" for file in files_openehpys]
files_openehpys = sorted(files_openehpys)

class read_nnc():
    def __init__(self, file, file_number, num_channels, rate):
        print(file[file_number])
        _file = open(file[file_number], "rb")
        _byte_data = _file.read()
        _byte_data = _byte_data[8:]
        _byte_data = _byte_data[:-(num_channels-4)*2]
        _channel_count = range(0, num_channels)                                         # Creates a vector with the number of channels lenght
        _data_length = len(_byte_data)
        _unpack_format = "<" + str(int(_data_length/2)) + "h"                           # Format to struct.unpack( ) function reads the data 

        _integer_data = struct.unpack(_unpack_format, _byte_data)                       # Uses the format struct to unpack the data in integer format
        _micro_volts_data = 0.195*numpy.array(_integer_data)                            # Converts the data to microvolts (INTAN datasheet)

        self.rate = rate
        self.data = []                                                                  # Creates a matrix with the number of channels and the number of samples
        for i in range(0, num_channels):                                                # Creates a row in the matrix for each active channel 
            self.data.append([])                                                        # Creates 1 circular buffer to all channels with length of 5 seconds of record                             

        for _sample, _channel in zip(_micro_volts_data, cycle(_channel_count)):         # Cycles through all the bytes separating them every "number of channels" samples    
            self.data[_channel].append((_sample))                                       # Adds the values on the circular buffer

        self.data = numpy.array(self.data)
        self.data = [a - numpy.mean(a) for a in self.data]
        
        self.max_value = numpy.max(self.data)
        self.min_value = numpy.min(self.data)

    def notch_filter(self, frequencies):
        frequencies = numpy.array(frequencies)
        for a in range(0, len(self.data)):
            self.data[a] = mne.filter.notch_filter(self.data[a], self.rate, frequencies)

    def bandpass_filter(self, low, high):
        for a in range(0, len(self.data)):
            self.data[a] = mne.filter.filter_data(self.data[a], self.rate, low, high, method='iir')

    def resample(self, new_rate):
        self.data = resample(self.data, int(len(self.data[0])/(self.rate/new_rate)), axis=1)
        self.rate = new_rate

# class read_openephys_0():
#     def __init__(self, file, file_number):
#         print(file[file_number])
        
#         session = Session(file[file_number])
#         recordings = session.recordings[0]
#         continuous = recordings.continuous[0]
#         num_samples = continuous.sample_numbers[-1]

#         events = recordings.events
#         init_time = list(events['sample_number'])[-2]
#         end_time = list(events['sample_number'])[-1]
#         _data = continuous.get_samples(start_sample_index=init_time, end_sample_index=end_time)      
                
#         self.data = _data.transpose()
#         #self.data = [a - numpy.mean(a) for a in self.data]
#         self.rate = continuous.metadata['sample_rate']
#         self.samples = len(self.data[0])
#         self.channels = continuous.metadata['num_channels']
#         self.max_value = numpy.max(self.data)
#         self.min_value = numpy.min(self.data)

#     def notch_filter(self, frequencies):
#         frequencies = numpy.array(frequencies)
#         for a in range(0, len(self.data)):
#             self.data[a] = mne.filter.notch_filter(self.data[a], self.rate, frequencies)

#     def bandpass_filter(self, low, high):
#         for a in range(0, len(self.data)):
#             self.data[a] = mne.filter.filter_data(self.data[a], self.rate, low, high, method='iir')

class read_openephys():
    def __init__(self, file, file_number):
        print(file[file_number])
        _data, _rate = Binary.Load(file[file_number])
        _data = _data[list(_data.keys())[0]]
        _data = _data[list(_data.keys())[0]]
        _data = _data[list(_data.keys())[0]]
        _rate = _rate[list(_rate.keys())[0]]
        _rate = _rate[list(_rate.keys())[0]]
        
        self.data = _data.transpose()
        self.data = self.data.astype('float64')
        self.data = [a - numpy.mean(a) for a in self.data]
        self.rate = _rate
        self.samples = len(self.data[0])
        self.channels = len(self.data)
        self.max_value = numpy.max(self.data)
        self.min_value = numpy.min(self.data)

    def notch_filter(self, frequencies):
        frequencies = numpy.array(frequencies)
        for a in range(0, len(self.data)):
            self.data[a] = mne.filter.notch_filter(self.data[a], self.rate, frequencies)

    def bandpass_filter(self, low, high):
        for a in range(0, len(self.data)):
            self.data[a] = mne.filter.filter_data(self.data[a], self.rate, low, high, method='iir')

class analysis():
    def __init__(self, nnc, open_ephys, experiment_name):
        self.nnc_data = nnc.data
        self.openephys_data = open_ephys.data
        self.experiment_name = experiment_name
        self.num_channels = len(self.nnc_data)
        self.min_value = min(nnc.min_value.all(), open_ephys.min_value.all())
        self.max_value = max(nnc.max_value.all(), open_ephys.max_value.all())

    def plot_all(self):                                                                                             # Clears the last plot made in the interface
        fig, ax_0 = plt.subplots(self.num_channels//2 + self.num_channels%2, 2, sharex=True, sharey=True)
        ax = ax_0.flatten()
        for a in range(0, self.num_channels):                                                                     # Loop through all the rows of the matrix
            #ax[a].ylim((self.min_value, self.max_value))
            ax[a].plot(self.nnc_data[a], color = (160/255, 17/255, 8/255, 1), linewidth = 0.5)                      # Plots the respective data and for each channel add the channel number for better visualization of the data                                                      # Draws on the interface
            ax[a].plot(self.openephys_data[a], color = (75/255, 75/255, 75/255, 1), linewidth = 0.5)
            ax[a].set_ylabel(str(a+1))
            if a >= self.num_channels - 1:
                ax[a].set_xlabel("Samples")

        plt.suptitle(self.experiment_name + " (in uV)")
        plt.tight_layout()
        plt.show()

    def correlaction(self, channel):
        corr = correlate(self.nnc_data[channel][:4000], self.openephys_data[channel][:4000])
        lags = correlation_lags(len(self.nnc_data[channel][:4000]), len(self.openephys_data[channel][:4000]))
        corr /= numpy.max(corr)

        fig, (ax_nnc, ax_ope, ax_corr) = plt.subplots(3, 1, figsize=(4.8, 4.8))
        ax_nnc.plot(self.nnc_data[0][:4000])
        ax_nnc.set_title(self.experiment_name + '\n\n' + 'NNC DAQ')
        ax_nnc.set_xlabel('Sample Number')
        ax_nnc.set_ylabel('uV')
        ax_ope.plot(self.openephys_data[0][:4000])
        ax_ope.set_title('Open Ephys')
        ax_ope.set_xlabel('Sample Number')
        ax_ope.set_ylabel('uV')
        ax_corr.plot(lags, corr)
        ax_corr.set_title('Cross-correlated signal')
        ax_corr.set_xlabel('Lag')
        ax_nnc.margins(0, 0.1)
        ax_ope.margins(0, 0.1)
        ax_corr.margins(0, 0.1)
        
        plt.tight_layout()
        plt.show()

    def psd(self):
        plt.psd(nnc.data[0], NFFT=None, Fs=2000, Fc=None, detrend=None, window=None, noverlap=100, pad_to=None, sides=None, scale_by_freq=None, return_line=None)
        plt.title(self.experiment_name)
        plt.show()

    def average_window(self):
        heart_beat_nnc = []
        for a in range(0, self.num_channels):
            peaks_nnc = find_peaks(self.nnc_data[a], height=180, distance=300)
            for peak in peaks_nnc[0][1:-1]:
                heart_beat_nnc.append(list(self.nnc_data[a][peak-200:peak+200]))

        heart_beat_nnc = numpy.array(heart_beat_nnc)
        self.average_nnc = numpy.mean(heart_beat_nnc, axis=0)

        heart_beat_openephys = []
        for a in range(0, self.num_channels):
            peaks_openephys = find_peaks(self.openephys_data[a], height=180, distance=300)
            for peak in peaks_openephys[0][1:-1]:
                heart_beat_openephys.append(list(self.openephys_data[a][peak-200:peak+200]))

        heart_beat_openephys = numpy.array(heart_beat_openephys)
        self.average_openephys = numpy.mean(heart_beat_openephys, axis=0)

        fig, (ax) = plt.subplots(1, 1, figsize=(4.8, 4.8))
        ax.plot(self.average_nnc, color = (160/255, 17/255, 8/255, 1), linewidth = 2)
        ax.plot(self.average_openephys, color = (75/255, 75/255, 75/255, 1), linewidth = 2)
        ax.set_xlabel('Sample Number')
        ax.set_ylabel('uV')
        ax.margins(0, 0.1)
        ax.margins(0, 0.1)
        ax.legend(['NNC DAQ','Open Ephys'])
        plt.title(self.experiment_name)
        fig.tight_layout()
        plt.show()

file_number = 0  

open_ephys = read_openephys(files_openehpys, file_number)

#open_ephys.bandpass_filter(0.1, 50)
num_channels = open_ephys.channels
sample_frequency = open_ephys.rate

if file_number <= 7:
    nnc = read_nnc(files_rpi, file_number, num_channels, sample_frequency)
    #nnc.bandpass_filter(0.1, 50)
    if file_number >= 4:
        nnc.rate = 2000
        nnc.resample(1000)
    experiment_name = files_rpi[file_number].rsplit('\\', 1)[1].rsplit('.', 1)[0]
    experiment_name = experiment_name.replace('_', ' ')
    experiment_name = experiment_name.upper()
else:
    nnc = read_nnc(files_pc, file_number - 8, num_channels, sample_frequency)
    #nnc.bandpass_filter(0.1, 50)
    if file_number == 11:
        nnc.rate = 2000
        nnc.resample(1000)
    experiment_name = files_pc[file_number - 8].rsplit('\\', 1)[1].rsplit('.', 1)[0]
    experiment_name = experiment_name.replace('_', ' ')
    experiment_name = experiment_name.upper()

comparision = analysis(nnc, open_ephys, experiment_name)
comparision.plot_all()
comparision.correlaction(0)
comparision.average_window()

pass