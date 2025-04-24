import os
import pickle
import struct
import numpy as np
import matplotlib.pyplot as plt
import numpy
import mne
from scipy.signal import resample

class MicroMAPReader:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self._load_metadata()
        self._load_binary_data()
        self._fill_missing_data()

    def _load_metadata(self):
        # Encontra o .pkl
        for file in os.listdir(self.folder_path):
            if file.endswith("_metadata.pkl"):
                metadata_file = os.path.join(self.folder_path, file)
                break
        else:
            raise FileNotFoundError("Metadata (.pkl) file not found.")

        # Carrega o dicionário de metadados
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
        print(f'Max packet counter: {np.max(folded_packet_counters)}/ Min packet counter: {np.min(folded_packet_counters)}')
        fig, ax  = plt.subplots(2, 1, sharex=True)
        ax[0].plot(folded_packet_counters, label="Packet Counter")
        ax[0].scatter(range(len(folded_packet_counters)), folded_packet_counters, color='red', s=4, label="Samples")
        ax[0].set_title("Packet Counter")
        ax[0].set_xlabel("Samples")
        ax[0].set_ylabel("Counter Value")
        ax[0].legend()     
        
        self.packet_counters = self._get_unfold_counter(folded_packet_counters, max_value = 2^16 - 1)                                                 # Unfold the counter values (counter resets to 0 after reaching 2^16 - 1 - 16bits counter)

        # Unpack to int16 (signed)
        unpacked = struct.unpack('<' + str(len(data) // 2) + 'h', data)
        array = np.array(unpacked, dtype = np.int64).reshape(-1, self.num_channels)

        # Apply Intan scaling: 0.195 µV per bit
        self.data = array.T * 0.195  # Output in µV

        for ch in range(8, 20):
            norm_ch = self.data[ch] - np.mean(self.data[ch])
            norm_ch = norm_ch / np.std(norm_ch)
            ax[1].plot(norm_ch + ch)
        
        ax[1].set_title("Normalized Channels")
        ax[1].set_xlabel("Samples")
        ax[1].set_ylabel("Amplitude (µV)")
        plt.show()

    def get_channel(self, index):
        """Retorna os dados de um canal (index de 1 a N)."""
        return self.data[index - 1, :]

    def get_all_data(self):
        """Retorna todos os dados (channels, samples)."""
        return self.data

    def get_time_vector(self):
        """Retorna vetor de tempo com base na frequência de amostragem."""
        samples = self.data.shape[1]
        return np.arange(samples) / self.sampling_freq
    
    def check_arduino_test(self):
        """The Arduino test is a signal with the number of the channel varying from num_channel to -num_channel, making a sawtooth signal."""
        # Check if the data is a sawtooth signal
        for i in range(self.num_channels):
            channel_data = self.get_channel(i + 1)
            first_value = channel_data[0]
            second_value = channel_data[1]

            if first_value != - second_value:
                print(f"Channel {i + 1} does not have the expected sawtooth pattern.")
                return False
            else:
                only_first = channel_data[0::2]
                print(f"Channel {i + 1} first values: {only_first}")
                only_second = channel_data[1::2]
                print(f"Channel {i + 1} second values: {only_second}")

                if np.all(only_first == first_value) and np.all(only_second == second_value):
                    print(f"Channel {i + 1} has the expected sawtooth pattern.")
                else:
                    fig, ax  = plt.subplots()
                    ax.plot(only_first, label="First values")
                    ax.plot(only_second, label="Second values")
                    ax.legend()
                    ax.set_title(f"Channel {i + 1} - Sawtooth signal")
                    ax.set_xlabel("Samples")
                    ax.set_ylabel("Amplitude (µV)")
                    plt.show()

                    bad_index = np.where(only_first != first_value)[0]
                    print(f"Channel {i + 1} has a bad value at index {bad_index} - {channel_data[bad_index]}")
                    return False
        return True

    def _get_unfold_counter(self, counter_series, max_value = 255):
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

    def _fill_missing_data(self):
        filled_counter = []
        filled_data = []

        for i in range(len(self.packet_counters) - 1):
            curr_val = self.packet_counters[i]
            next_val = self.packet_counters[i + 1]
            
            if curr_val != next_val:
                curr_data = self.data[:, i]

                # Adiciona valor atual
                filled_counter.append(curr_val)
                filled_data.append(curr_data)

                gap = next_val - curr_val - 1
                if gap > 0:
                    for j in range(1, gap + 1):
                        filled_counter.append(curr_val + j)
                        # fill with nans
                        # filled_data.append(np.full(self.num_channels, np.nan))
                        # fill with the last value
                        filled_data.append(curr_data)
            # else:
            #     for ch in range(self.num_channels):
            #         if self.data[ch, i] != self.data[ch, i + 1]:
            #             raise ValueError(f"The sample number is equal to the next one, but the data is different. Check the data {i} and {i + 1}.")
                 
        filled_counter.append(self.packet_counters[-1])
        filled_data.append(self.data[:, -1])

        self.data = np.array(filled_data).T
        print(self.data.shape)
        self.packet_counters = np.array(filled_counter)

    def check_packet_counter(self, plot = False):
        """Verifica se o contador de pacotes está correto."""
        
        if plot:
            fig, ax = plt.subplots()
            ax.plot(self.packet_counters, label="Packet Counter")
            ax.scatter(range(len(self.packet_counters)), self.packet_counters, color='red', s=4, label="Samples")
            ax.set_title("Packet Counter")
            ax.set_xlabel("Samples")
            ax.set_ylabel("Counter Value")
        
        for i in range(len(self.packet_counters) - 1):
            curr_val = self.packet_counters[i]
            next_val = self.packet_counters[i + 1]

            if next_val - curr_val != 1:
                print(f"Packet counter error between {curr_val} and {next_val}.")

                if plot:
                    ax.axvline(x = i, color = 'r', linestyle = '--', label = "Error")
                    ax.legend()
                    plt.show()

                return False
        
        if plot:
            ax.legend()
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