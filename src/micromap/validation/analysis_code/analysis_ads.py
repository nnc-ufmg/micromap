def read_binary_file(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
    return data

def process_binary_data(data, bytes_per_sample=27):
    # Number of channels (8 channels, 3 bytes each, excluding the status word)
    num_channels = 8
    hex_data = [[] for _ in range(num_channels)]
    
    # Iterate over the binary data in chunks of `bytes_per_sample` (27 bytes)
    for i in range(0, len(data), bytes_per_sample):
        sample = data[i:i + bytes_per_sample]
        sample_data = sample.hex()
        
        # Skip the first 3 bytes (status word)
        channel_data = sample_data[6:]
        
        # Assign the appropriate hex values to each channel
        for count in range(num_channels):
            hex_data[count].append(channel_data[count * 6:(count + 1) * 6])

    # Convert hex data to voltage data
    volt_data = [
        [
            (int(value, 16) - 2**24) * 7.9473e-8 if int(value, 16) & 0x800000 else int(value, 16) * 7.9473e-8
            for value in channel
        ]
        for channel in hex_data
    ]

    return volt_data

import matplotlib.pyplot as plt

def plot_voltage_data(volt_data, sampling_rate=1000):
    num_channels = len(volt_data)
    time = [i / sampling_rate for i in range(len(volt_data[0]))]  # Generate time axis based on sampling rate
    
    plt.figure(figsize=(15, 10))
    
    for i in range(num_channels):
        plt.subplot(num_channels, 1, i + 1)
        plt.plot(time, volt_data[i])
        plt.title(f'Channel {i + 1}')
        plt.xlabel('Time (s)')
        plt.ylabel('Voltage (V)')
    
    plt.tight_layout()
    plt.show()

file_path = r"C:\Users\luizv\Desktop\square_0.bin"

# Step 1: Read the binary file
binary_data = read_binary_file(file_path)

# Step 2: Process the binary data
volt_data = process_binary_data(binary_data)

# Step 3: Plot the voltage data for each channel
plot_voltage_data(volt_data)
