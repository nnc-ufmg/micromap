import os
import pickle
import struct
import numpy as np
import matplotlib.pyplot as plt

class MicroMAPReader:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self._load_metadata()
        self._load_binary_data()

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
        self.packet_counters = []

        for i in range(0, len(raw), block_size):
            block = raw[i:i+block_size]
            if len(block) == block_size and block[0] == 0xFE:
                self.packet_counters.append(block[1])
                data.extend(block[2:])

        # Unpack to int16 (signed)
        unpacked = struct.unpack('<' + str(len(data) // 2) + 'h', data)
        array = np.array(unpacked, dtype=np.int16).reshape(-1, self.num_channels)

        # Apply Intan scaling: 0.195 µV per bit
        self.data = array.T.astype(np.float32) * 0.195  # Output in µV

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
    
    def check_counter_test(self, plot = False):
        for i in range(len(self.packet_counters) - 1):
            is_ok = []
            if self.packet_counters[i] == 256:
                if self.packet_counters[i + 1] == 0:
                    is_ok.append(True)
                else:
                    is_ok.append(False)
            else:
                if self.packet_counters[i + 1] == self.packet_counters[i] + 1:
                    is_ok.append(True)
                else:
                    is_ok.append(False)

        if plot:
            fig, ax = plt.subplots()
            ax.plot(self.packet_counters, label="Packet Counter")
            ax.legend()
            ax.set_title("Packet Counter Test")
            ax.set_xlabel("Samples")
            ax.set_ylabel("Counter Value")
            plt.show()

        return np.all(is_ok)