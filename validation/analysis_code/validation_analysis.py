import struct
import collections
import numpy
import matplotlib.pyplot as plt
import Binary
from itertools import cycle
from scipy.signal import correlate, correlation_lags, find_peaks
from os import walk
import mne

file_nnc = "G:\\Outros computadores\\Desktop\\GitHub\\acquisition_system\\validation\\nnc_rpi_27-10-2022\\"
file_open_ehpys = "G:\\Outros computadores\\Desktop\\GitHub\\acquisition_system\\validation\\openephys_27-10-2022\\"
files_nnc = next(walk(file_nnc), (None, None, []))[2][:-1]
files_nnc = [file_nnc + file for file in files_nnc]
files_nnc = sorted(files_nnc)
files_open_ehpys = next(walk(file_open_ehpys), (None, [], None))[1]
files_open_ehpys = [file_open_ehpys + file + "\\Record Node 115" for file in files_open_ehpys]
files_open_ehpys = sorted(files_open_ehpys)

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
        #self.data = [a - numpy.mean(a) for a in self.data]
        
        self.max_value = numpy.max(self.data)
        self.min_value = numpy.min(self.data)

    def notch_filter(self, frequencies):
        frequencies = numpy.array(frequencies)
        for a in range(0, len(self.data)):
            self.data[a] = mne.filter.notch_filter(self.data[a], self.rate, frequencies)

    def bandpass_filter(self, low, high):
        for a in range(0, len(self.data)):
            self.data[a] = mne.filter.filter_data(self.data[a], self.rate, low, high, method='iir')

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
    def __init__(self, nnc, open_ephys):
        self.nnc_data = nnc.data
        self.openephys_data = open_ephys.data
        self.num_channels = len(self.nnc_data)
        self.min_value = min(nnc.min_value.all(), open_ephys.min_value.all())
        self.max_value = max(nnc.max_value.all(), open_ephys.max_value.all())

    def plot_all(self):
        plt.figure()                                                                                            # Clears the last plot made in the interface
        for a in range(0, self.num_channels):                                                                   # Loop through all the rows of the matrix
            plt.subplot(self.num_channels//2 + 1, 2, a + 1)    
            #plt.ylim((self.min_value, self.max_value))
            plt.plot(self.nnc_data[a], color = (160/255, 17/255, 8/255, 1), linewidth = 0.5)                    # Plots the respective data and for each channel add the channel number for better visualization of the data                                                      # Draws on the interface
            plt.plot(self.openephys_data[a], color = (75/255, 75/255, 75/255, 1), linewidth = 0.5)
        plt.show()

    def correlaction(self, channel):
        corr = correlate(self.nnc_data[channel][:4000], self.openephys_data[channel][:4000])
        lags = correlation_lags(len(self.nnc_data[channel][:4000]), len(self.openephys_data[channel][:4000]))
        corr /= numpy.max(corr)

        fig, (ax_nnc, ax_ope, ax_corr) = plt.subplots(3, 1, figsize=(4.8, 4.8))
        ax_nnc.plot(self.nnc_data[0][:4000])
        ax_nnc.set_title('NNC DAQ')
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
        fig.tight_layout()
        plt.show()

    def psd(self):
        plt.psd(nnc.data[0], NFFT=None, Fs=2000, Fc=None, detrend=None, window=None, noverlap=100, pad_to=None, sides=None, scale_by_freq=None, return_line=None)
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
        fig.tight_layout()
        plt.show()

file_number = 6 
open_ephys = read_openephys(files_open_ehpys, file_number)
#open_ephys.bandpass_filter(0.1, 50)
num_channels = open_ephys.channels
sample_frequency = open_ephys.rate

nnc = read_nnc(files_nnc, file_number, num_channels, sample_frequency)
#nnc.bandpass_filter(0.1, 50)

comparision = analysis(nnc, open_ephys)
comparision.plot_all()
comparision.correlaction(1)
comparision.average_window()

# plt.figure()                                                                                            # Clears the last plot made in the interface
# for a in range(0, num_channels):                                                                   # Loop through all the rows of the matrix
#     plt.subplot(num_channels//2 + 1, 2, a + 1)    
#     plt.plot(nnc.data[a], color = (160/255, 17/255, 8/255, 1), linewidth = 0.5)                    # Plots the respective data and for each channel add the channel number for better visualization of the data                                                      # Draws on the interface
# plt.show()

pass