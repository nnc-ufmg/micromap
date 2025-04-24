import os
import pickle
import struct
import numpy as np
import matplotlib.pyplot as plt
import numpy
import mne
from scipy.signal import resample
from scipy.stats import pearsonr

class MicroMAPReader:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self._load_metadata()
        self._load_binary_data()
        self._fill_missing_data()

    def _load_metadata(self):
        for file in os.listdir(self.folder_path):
            if file.endswith("_metadata.pkl"):
                metadata_file = os.path.join(self.folder_path, file)
                break
        else:
            raise FileNotFoundError("Metadata (.pkl) file not found.")

        with open(metadata_file, 'rb') as f:
            self.metadata = pickle.load(f)

        self.num_channels = self.metadata["Number of Channels"]
        self.channels = self.metadata["Channels"]
        self.sampling_freq = self.metadata["Sampling Frequency"]

    def _load_binary_data(self):
        # Find the .bin file
        for file in os.listdir(self.folder_path):
            if file.endswith(".mmap"):
                bin_file = os.path.join(self.folder_path, file)
                break
        else:
            raise FileNotFoundError("Binary (.mmap) file not found.")

        with open(bin_file, "rb") as f:
            raw = f.read()

        block_size = 2 * self.num_channels + 2  # 1 byte header + 1 byte counter + 2*num_channels
        data = bytearray()
        folded_packet_counters = []

        for i in range(0, len(raw), block_size):
            block = raw[i:i+block_size]
            if len(block) == block_size:
                count = int.from_bytes(block[0:2], byteorder='big')
                folded_packet_counters.append(count)
                data.extend(block[2:])

        folded_packet_counters = np.array(folded_packet_counters)        
        self.packet_counters = self._get_unfold_counter(folded_packet_counters, max_value = int(2**16 - 1))                                                 # Unfold the counter values (counter resets to 0 after reaching 2^16 - 1 - 16bits counter)

        # Unpack to int16 (signed)
        unpacked = struct.unpack('<' + str(len(data) // 2) + 'h', data)
        array = np.array(unpacked, dtype = np.int64).reshape(-1, self.num_channels)

        # Apply Intan scaling: 0.195 µV per bit
        self.data = array.T * 0.195  # Output in µV
        self.num_samples = array.shape[1]

        if self.data.shape[0] != self.num_channels:
            raise ValueError(f"Data shape mismatch: expected {self.num_channels} channels, got {self.data.shape[0]} channels.")

    def _get_unfold_counter(self, counter_series, max_value = 255):
        """The counter values are folded, i.e., when the counter reaches the maximum value, it resets to 0. The last implementation the counter
        is a 16 bits counter, so the maximum value is 2^16 - 1. The function unfolds the counter values to get the real incremental values.

        Ex: (if the counter is 0-255) [0, 1, 2, ..., 254, 255, 0, 1, 2, ...] -> [0, 1, 2, ..., 254, 255, 256, 257, ...]
        """
        
        list_max = np.max(counter_series)
        list_min = np.min(counter_series)
        if list_max > max_value or list_min != 0:
            raise ValueError("Counter values out of bounds (0 to max_value)")
        
        counter_series = np.asarray(counter_series)
        unfolded = [counter_series[0]]
        rollover = 0
        
        for i in range(1, len(counter_series)):
            current = counter_series[i]
            prev = counter_series[i-1]
            
            if current < prev:
                rollover += 1
            
            unfolded.append((current + rollover * (max_value + 1)))
        
        return np.array(unfolded)

    def _fill_missing_data(self, fill_method = 'last'):
        """
        This function fills the missing data. If a packet is lost, the data lost the time synchronization (packets after the each packet lost are 
        shifted in time). The function fills the missing data with the last value or with NaN. The function also counts the number of packets lost.

        To perform the filling, the function checks the packet counter values. If the difference between two consecutive packet counters is greater 
        than 1, it means that a packet was lost.     

        ps:  If the lost is bigger than 2^16 - 1, the function will not be able to fill the data correctly.  
        """
        filled_counter = []
        filled_data = []
        packets_lost = 0

        for i in range(len(self.packet_counters) - 1):
            curr_val = self.packet_counters[i]
            next_val = self.packet_counters[i + 1]
            
            if curr_val != next_val:
                curr_data = self.data[:, i]

                filled_counter.append(curr_val)
                filled_data.append(curr_data)

                gap = next_val - curr_val - 1
                if gap > 0:
                    for j in range(1, gap + 1):
                        filled_counter.append(curr_val + j)                        
                        if fill_method == 'last':
                            filled_data.append(curr_data)                               # fill with the last value
                        elif fill_method == 'nan':
                            filled_data.append(np.full(self.num_channels, np.nan))    # fill with nans
                        else:
                            raise ValueError("Invalid fill method. Use 'last' or 'nan'.")
                        packets_lost += 1
                 
        filled_counter.append(self.packet_counters[-1])
        filled_data.append(self.data[:, -1])

        self.data = np.array(filled_data).T
        self.packet_counters = np.array(filled_counter)
        self.packets_lost = packets_lost

    def get_channel_data(self, index):
        """Retorna os dados de um canal (index de 1 a N)."""
        return self.data[index - 1, :]

    def get_data(self):
        """Retorna todos os dados (channels, samples)."""
        return self.data

    def get_time_vector(self):
        """Retorna vetor de tempo com base na frequência de amostragem."""
        samples = self.data.shape[1]
        return np.arange(samples) / self.sampling_freq
    
    def check_arduino_test(self):
        """The Arduino test is a signal with the number of the channel varying from num_channel to -num_channel, making a sawtooth signal."""        
        expected_value = {}
        for i in range(32):
            # Convert the integer to bytes
            byte_array = i.to_bytes(2, byteorder='big', signed=True)
            # Convert value
            unpacked = struct.unpack('<' + str(1) + 'h', byte_array)[0]
            scaled = unpacked * 0.195
            expected_value[i] = scaled

        # Check if the data is a sawtooth signal
        stat = {}
        for i in range(self.num_channels):
            channel_data = self.get_channel_data(i + 1)
            first_value = channel_data[0]
            
            expected_signal = np.ones(len(channel_data))*expected_value[i]       # Expected signal is a sawtooth signal with the number of the channel varying from num_channel to -num_channel
            
            if first_value > 0:
                expected_signal[1::2] = -expected_signal[1::2]                   # Invert the signal for odd samples   
            else:
                expected_signal[0::2] = -expected_signal[0::2]                   # Invert the signal for even samples        

            stat[i] = pearsonr(channel_data, expected_signal)[0]                 # Calculate the correlation coefficient

        return stat

    def check_packet_counter(self, plot = False):
        """
        Function to check the packet counter. The function checks if the packet counter is incremented by 1 for each sample. If the difference between 
        two consecutive packet counters is greater than 1, it means that a packet was lost. The function also plots the packet counter values.
        """
        
        if plot:
            _, ax = plt.subplots()
            ax.plot(self.packet_counters, color = 'dimgrey', label = "Packet Counter")
            ax.scatter(range(len(self.packet_counters)), self.packet_counters, color = 'maroon', s = 4, label = "Samples")
            ax.set_title("Packet Counter")
            ax.set_xlabel("Samples")
            ax.set_ylabel("Counter Value")
        
        for i in range(len(self.packet_counters) - 1):
            curr_val = self.packet_counters[i]
            next_val = self.packet_counters[i + 1]

            if next_val - curr_val != 1:
                print(f"Packet counter error between {curr_val} and {next_val}.")

                if plot:
                    ax.axvline(x = i, color = 'black', linestyle = '--', label = "Error")
                    ax.legend(loc = 'upper right')
                    plt.show()

                return False
        
        if plot:
            ax.legend(loc = 'upper right')
            plt.show()
        
        return True

    def notch_filter(self, frequencies):
        frequencies = numpy.array(frequencies)
        for a in range(0, len(self.data)):
            self.data[a] = mne.filter.notch_filter(self.data[a], self.sampling_freq, frequencies, verbose='WARNING')

    def bandpass_filter(self, low, high):
        for a in range(0, len(self.data)):
            self.data[a] = mne.filter.filter_data(self.data[a], self.sampling_freq, low, high, method='iir', verbose='WARNING')

    def resample(self, new_rate):
        self.data = resample(self.data, int(len(self.data[0])/(self.sampling_freq/new_rate)), axis=1)
        self.sampling_freq = new_rate