import struct
import collections
from itertools import cycle
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq
import numpy

file = open('Sinais/ECG_2000Hz', "rb") 

byte_data = file.read()

byte_data = byte_data[8:]

channel_count = range(0, 32)                                                    # Creates a vector with the number of channels lenght
data_length = len(byte_data)
unpack_format = "<" + str(int(data_length/2)) + "h"                               # Format to struct.unpack( ) function reads the data 

data = struct.unpack(unpack_format, byte_data)

data_matrix = []                                                                       # Initializes the data matrix to be ploted
for i in channel_count:                                                                # Creates a row in the matrix for each active channel 
    data_matrix.append(collections.deque(maxlen = data_length))                   # Creates 1 circular buffer to all channels with length of 5 seconds of record                             

for sample, channel in zip(data, cycle(channel_count)):                           # Cycles through all the bytes separating them every "number of channels" samples    
    data_matrix[channel].append((sample))                                      # Adds the values on the circular buffer

plt.figure()                                                                                  # Clears the last plot made in the interface
for a in channel_count:
#for a in [13]:                                                                # Loop through all the rows of the matrix
    plt.subplot(len(channel_count)/2, 2, a + 1)    
    plt.ylim((-33000, 33000))
    plt.plot(list(data_matrix[a]), linewidth = 0.5)                                             # Plots the respective data and for each channel add the channel number for better visualization of the data                                                      # Draws on the interface

plt.figure() 
N = 2000
T = 1.0 / 500
x = numpy.linspace(0.0, N*T, N, endpoint=False)
yf = fft(list(data_matrix[1]))
xf = fftfreq(N, T)[:N//2]
plt.plot(xf, 2.0/N * numpy.abs(yf[0:N//2]), linewidth = 0.5)
                 
#print(byte_data.hex('/'))
#print(data)
#print(data_matrix[0])
#print(data_matrix[20])