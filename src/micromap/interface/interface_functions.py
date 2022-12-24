# ELECTROPHYSIOLOGICAL DATA ACQUISITION SYSTEM

# Code of functions linked to the electrophysiological recording system interface. 
# This partition contains the backend of the visual interface, in which the 
# parameters programmed by the user will be processed, allocated and modified.

# Author: 
#     João Pedro Carvalho Moreira
#     Belo Horizonte, Minas Gerais, Brasil
#     Graduated in Eletrical Engineer, UFSJ
#     Mastering in Eletrical Engineer, UFMG
#     Member of Núcleo de Neurociências, UFMG

# Advisor: 
#     Márcio Flávio Dutra Moraes

# Version 1.0.2

# Releases
# Version 1.0.1
# - Addition of advanced record programming
# - Addition of stop/start button

# Releases
# Version 1.0.2
# - Addition of functions to cammand the microcontroller

import matplotlib
import serial
matplotlib.use('Qt5Agg')
from numpy import where, array

class acquisition: 
    '''Acquisition
    
    This class defines the main attributes of signal acquisition. As some 
    of these parameters give rise to others through internal operations, 
    these are made private and are only accessed via getters and setters.
    
    Settable attributes: 
        - Method of acquisition (string)
        - ADC chip type (string)
        - Sampling frequency (index int number)
        - Highpass filter cutoff frequency (index int number)
        - Highpass filter cutoff frequency (index int number)
        - Days, hours, minutes and seconds of record (int)
        - Channels to do acquisiton (boolean list)
        - USB connection port between controller and interface (string)
        
    Gettable attributes:
        Normal
        - Method of acquisition (string)
        - ADC chip type (string)
        - Sampling frequency (index int number)
        - Highpass filter cutoff frequency (index int number)
        - Highpass filter cutoff frequency (index int number)
        - Days, hours, minutes and seconds of record (int)
        - Channels to do acquisiton (boolean list)
        - USB connection port between controller and interface (string) 
        Extra
        - Number of channels to do acquisition (int)
        - List of channels to do acquisition (number list)
        - Total time of record (number in seconds)
        
    '''
    def __init__(self):       
        self.is_recording_mode = False                                           # Recording mode is "FALSE"
        self.method = "ARDUINO"                                                  # Acquisition method (Arduino, FPGA or Pi Pico) 
        self.chip = "RHD2216"                                                    # Aquisition chip (RHD or ADS)
        self.sampling_frequency = 2000                                           # Desired sampling frequency
        self.highpass = 0.1                                                      # Desired highpass filter frequency
        self.lowpass = 20000                                                     # Desired lowpass filter frequency
        self.days = 0                                                            # Desired day of data acquisition
        self.hours = 1                                                           # Desired hours of data acquisition
        self.minutes = 0                                                         # Desired minutes of data acquisition
        self.seconds = 0                                                         # Desired seconds of data acquisition
        self.total_time = 3600                                                   # Total acquisition time in seconds
        self.channels = [1]*16                                                   # Channels that will be sampled in a boolean list
        self.number_channels = 16                                                # Number of channels selected
        self.channels_bool = 'ffff'                                              # Bool list of the channels
        self.usb_port = "None"                                                   # USB port connection
        self.save_directory = "None"                                             # Directory to save the data
        self.record_time = 0                                                     # Recorded time
        self.is_recording_mode = False                                           # Recording mode is "FALSE"
    
    # SETTERS METHODS    
    def set_sampling_frequency_by_index(self, slider_index):
        '''Set sampling frequency by index
        
        This public function changes the sampling frequency
        
        Args:
            slider_index (index int number): Interface slider index.
            
        '''
        frequencies = [1, 100, 500, 1000, 2000, 5000, 10000, 20000, 30000]                       # Possible values ​​of sampling frequency
        self.sampling_frequency = frequencies[slider_index]                        # Sets the attribute with the correspondent frequency
            
    def set_highpass_by_index(self, slider_index):
        '''Set highpass by index
        
        This public function changes the highpass fliter cutoff frequency
        
        Args:
            slider_index (index int number): Interface slider index.
            
        '''
        frequencies = [0.1, 0.25, 0.3, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, 5, 7.5,
                       10, 15, 20, 25, 30, 50, 75, 100, 150, 200, 250, 300, 500]    # Possible values ​​of cutoff frequency
        self.highpass = frequencies[slider_index]                                  # Sets the attribute with the correspondent frequency
        
    def set_lowpass_by_index(self, slider_index):
        '''Set lowpass by index
        
        This public function changes the lowpass fliter cutoff frequency
        
        Args:
            slider_index (index int number): Interface slider index.
            
        '''
        frequencies = [100, 150, 200, 250, 300, 500, 750, 1000, 1500,
                       2000, 2500, 3000, 5000, 7500, 10000, 15000, 20000]           # Possible values ​​of cutoff frequency 
        self.lowpass = frequencies[slider_index]                                   # Sets the attribute with the correspondent frequency
                
    def set_channels(self, bool_list):
        '''Set channels
        
        This public function changes the list of channels to be recorded and 
        the boolean list of channels to be recorded
        
        Args:
            bool_list (boolean list): Boolean list with channels on (1 for on and 1 for off).
            
        '''
        if self.chip == "RHD2132":                                                 # If the chip is an RHD2132
            channels_bool = bool_list                                              # Sets the attribute with bool_list of channels
            byte = ''.join([str(item) for item in bool_list])                      # Concatenates the bool_list in a string
            byte = byte[::-1]                                                      # Inverts the string
            byte = int(byte, 2).to_bytes(4, 'big')                                 # Converts the string to Arduino's reading format
            self.channels_bool = byte                                              # Sets the attribute with all 32 channels will be available
        elif self.chip == "RHD2216":                                               # If the chip is an RHD2216
            channels_bool = bool_list[0:16]                                        # Sets the attribute with bool_list of channels
            byte = ''.join([str(item) for item in bool_list[0:16]])                # Concatenates the bool_list in a string
            byte = byte[::-1]                                                      # Inverts the string
            byte = int(byte, 2).to_bytes(4, 'big')                                 # Converts the string to Arduino's reading format
            self.channels_bool = byte                                              # Sets the attribute with only 16 channels will be available
        else:                                                                      # If the chip is an ADS1298        
            channels_bool = bool_list[0:8]                                         # Sets the attribute with sized bool_list of channels
            byte = ''.join([str(item) for item in bool_list[0:8]])                 # Concatenates the bool_list in a string
            byte = byte[::-1]                                                      # Inverts the string
            byte = int(byte, 2).to_bytes(4, 'big')                                 # Converts the string to Arduino's reading format
            self.channels_bool = byte                                              # Sets the attribute with only 8 channels will be available
               
        channels = array(channels_bool)                                            # Turns a list in an array
        self.channels = where(channels == 1)[0]                                    # Gets only the indexes that will be registered 
        self.channels = [x + 1 for x in self.channels]                             # Sets the attribute adding 1 in all elements of a list to eliminate the index 0
        self.number_channels = sum(channels_bool)                                  # Gets the number of channels selected    
       
    def get_total_time(self):
        '''Get total time
        
        This public function outputs to the client class the total time of record in seconds.
        
        '''
        self.total_time = self.days*24*60*60 + self.hours*60*60 + \
                            self.minutes*60 + self.seconds                         # Calculates the total time in seconds
        return self.total_time                                                     # Returns the attribute with the correspondent number

    def resume_options(self):
        self._resume = {}
        self._resume["Method"] = self.method                                                # Updates the Method in the "resume"
        self._resume["Chip"] = self.chip                                                    # Updates the Chip in the "resume"
        self._resume["Sampling Frequency"] = self.sampling_frequency                        # Updates the Sampling Frequency in the "resume"
        self._resume["High Pass Filter"] = self.highpass                                    # Updates the High Pass Filter in the "resume"
        self._resume["Low Pass Filter"] = self.lowpass                                      # Updates the Low Pass Filter in the "resume"
        self._resume["Duration"] = str(self.days) + ':' + str(self.hours) + ':' +  \
                                   str(self.minutes) + ':' +  str(self.seconds)             # Updates the Duration in the "resume"
        self._resume["Total Time"] = self.get_total_time()                                  # Updates the Total Time in the "resume"
        self._resume["Number of Channels"] = self.number_channels                           # Updates the Number of Channels in the "resume"
        self._resume["Channels (Boolean)"] = str(self.channels_bool.hex())                  # Updates the Channels (Boolean) in the "resume"
        self._resume["Channels"] = self.channels                                            # Updates the Channels in the "resume"
        self._resume["USB Port"] = self.usb_port                                            # Updates the USB Port in the "resume"
        self._resume["Save Direcoty"] = self.save_directory                                 # Updates the Save Directory in the "resume"
        
        return self._resume        
           


class usb_singleton():
    '''Usb singleton
    
    This class starts and controls a single USB connection instance
    
    Args:
        usb_port (string): Port that will be connected.
        baund_rate: Data transfer frequency.
        
    '''
    def __init__(self, usb_port, baund_rate = 50000000):                        
        self.usb_port = usb_port                                                # Sets USB port
        self.baund_rate = baund_rate                                            # Sets USB data transfer frequency
     
    def connect(self):
        '''Connect
        
        This function connect the USB port
        '''
        self.port = serial.Serial(self.usb_port, self.baund_rate)               # Initializes the USB port with the especified parameters
        
    def disconnect(self):
        '''Disconnect
        
        This function disconnect the USB port
        '''
        self.port.close()                                                       # Finishes the USB port
        
    def send_direct(self, command):
        '''Send direct
        
        This function sends a generic message to the USB port and receives
        the answer
        
        Args:
            command: Command to be sent in hexadecimal.
            
        '''
        self.port.write(command)                                                # Sends the messsage via USB port
        connection_ok = self.port.read(4)                                       # Reads the 4bytes answer message
        return connection_ok                                                    # Returns the answer message
    
    def request_acquisition(self):
        '''Request acquisition
        
        This function sends to microcontroller the command to initialize the
        data acquisition
        '''
        command = bytearray(b'\x11\x2A\x2A\x2A')                                # Defines thes message to start the acquisition
        self.port.write(command)                                                # Sends via USB port the messsage
        #request_ok = self.port.read(4)                                          # Reads the 4bytes answer message
        #return request_ok                                                       # Returns the answer message
        return
    
    def stop_acquisition(self):
        '''Stop acquisition
        
        This function sends to microcontroller the command to stop the
        data acquisition
        '''
        command = bytearray(b'\xFF\x2A\x2A\x2A')                                # Defines thes message to stop the acquisition
        self.port.write(command)                                                # Sends the messsage via USB port
        #stop_ok = self.port.read(4)                                             # Reads the 4bytes answer message
        #return stop_ok                                                          # Returns the answer message
        return
    
    def set_sampling_frequency(self, frequency):
        '''Set sampling frequency
        
        This function sends to microcontroller the command to set the data 
        acquisition sampling frequency
        
        Args:
            frequency: Data acquisition sampling frequency.
            
        '''
        frequency = int(frequency).to_bytes(2, 'big')                           # Gets the frequency and transforms in bytes type
        command = bytearray(b'\xC0\x00')                                        # Defines the mask to configures the sampling frequency
        command = command + frequency                                           # Concats the mask and the command
        self.port.write(command)                                                # Sends the messsage via USB port
        frequency_ok = self.port.read(4)                                        # Reads the 4bytes answer message
        return frequency_ok                                                     # Returns the answer message
    
    def set_channel_0to15(self, channels_bool):
        '''Set channel 0to15
        
        This function sends to microcontroller the command to set the channels
        that will be recorded (channels 15 to 0 in this order)
        
        Args:
            channels_bool: Channels that will be recorded in bollean list, 1 turns channel on and 0 turns off (order: 31 to 0).
            
        '''
        command = bytearray(b'\xC1\x00')                                        # Defines the mask to configures the channels 31 to 16
        command = command + channels_bool[2].to_bytes(1,'big')                  # Gets the channels 31 to 24 and transforms in bytes type
        command = command + channels_bool[3].to_bytes(1,'big')                  # Gets the channels 23 to 16 and transforms in bytes type
        print(str(command.hex()))                                               # Prints the command
        self.port.write(command)                                                # Sends the messsage via USB port 
        channels_ok = self.port.read(4)                                         # Reads the 4 bytes answer message
        return channels_ok                                                      # Returns the answer message
    
    def set_channel_16to31(self, channels_bool):
        '''Set channel 16to31
        
        This function sends to microcontroller the command to set the channels
        that will be recorded (channels 31 to 16 in this order)
        
        Args:
            channels_bool: Channels that will be recorded in bollean list, 1 turns channel on and 0 turns off (order: 31 to 0).
            
        '''
        command = bytearray(b'\xC2\x00')                                        # Defines the mask to configures the channels 15 to 0
        command = command + channels_bool[0].to_bytes(1,'big')                  # Gets the channels 15 to 8 and transforms in bytes type
        command = command + channels_bool[1].to_bytes(1,'big')                  # Gets the channels 7 to 0 and transforms in bytes type
        print(str(command.hex()))                                               # Prints the command
        self.port.write(command)                                                # Sends the messsage via USB port
        channels_ok = self.port.read(4)                                         # Reads the 4bytes answer message
        return channels_ok                                                      # Returns the answer message
    
    def set_highpass_frequency(self, slider_index):
        '''Ser highpass frequency
        
        This function sends to microcontroller the command to set the high pass
        filter cutoff frequency
        
        Args:
            slider_index: Index that represents the desired frequency (vide table in function "set_highpass").
            
        '''
        slider_index = int(slider_index).to_bytes(2, 'big')                     # Gets the frequency index and transforms in bytes type
        command = bytearray(b'\xC3\x00')                                        # Defines the mask to configures the highpass filter cutoff frequency
        command = command + slider_index                                        # Concats the mask and the command
        self.port.write(command)                                                # Sends the messsage via USB port
        frequency_ok = self.port.read(4)                                        # Reads the 4bytes answer message
        return frequency_ok                                                     # Returns the answer message
     
    def set_lowpass_frequency(self, slider_index):
        '''
        This function sends to microcontroller the command to set the low pass
        filter cutoff frequency
        
        Args:
            slider_index: Index that represents the desired frequency (vide table in function "set_lowpass").
            
        '''
        slider_index = int(slider_index).to_bytes(2, 'big')                     # Gets the frequency index and transforms in bytes type
        command = bytearray(b'\xC4\x00')                                        # Defines the mask to configures the lowpass filter cutoff frequency
        command = command + slider_index                                        # Concats the mask and the command
        self.port.write(command)                                                # Sends the messsage via USB port
        frequency_ok = self.port.read(4)                                        # Reads the 4bytes answer message
        return frequency_ok                                                     # Returns the answer messag

# class rhd_chip():
#     '''
#     This class receives the attributes of an acquisition object, builds 
#     configuration messages to be sent to INTAN and implements the method 
#     that effectively configures and initiates a data acquisition.
    
#     ps: It has private attributes that characterize the chip registers 
#     for eventual changes by the developers
    
#     Parameters:
#         - serial_port ...... USB connection port between controller and interface (string)
#         - channels_bool .... Channels to do acquisiton (boolean list)
#         - highpass ......... Highpass filter cutoff frequency (positive int or float)
#         - lowpass .......... Lowhpass filter cutoff frequency (positive int or float)
#     '''
#     def __init__(self, serial_port, channels_bool, highpass, lowpass):
#         # PRIVATE ATTRIBUTES - GENERAL
#         self._serial_port = serial_port                                             # Passes the USB connection port between controller and interface to a private attribute
#         self._channels_bool = channels_bool                                         # Passes the channels to do acquisiton to a private attribute
#         self._highpass = highpass                                                   # Passes the highpass filter cutoff frequency to a private attribute
#         self._lowpass = lowpass                                                     # Passes the lowpass filter cutoff frequency to a private attribute

#         # PRIVATE ATTRIBUTES - REGISTERS
#         # Masks for setting register 0 (used when writing on register 0)
#         self._adc_reference_bw = 0xC0                                               # 0x 1100 0000 - Configures the bandwidth of an internal ADC reference (should always be set to 3)
#         self._amp_fast_settle_enable = 0x20                                         # 0x 0010 0000 - Connects bioamplifiers outputs to GND
#         self._amp_fast_settle_disable = 0x00                                        # 0x 0000 0000 - Normal operation of bioamplifiers
#         self._amp_vref_enable = 0x10                                                # 0x 0001 0000 - Enables reference voltage used by bioamplifiers
#         self._amp_vref_disable = 0x00                                               # 0x 0000 0000 - Disables bioamplifiers (reduce 180 uA in power consumption)
#         self._adc_comparator_bias = 0x0C                                            # 0x 0000 1100 - Configures the bias current of the ADC comparator (should always be set to 3 in normal operation)
#         self._adc_comparator_select = 0x02                                          # 0x 0000 0010 - Selects between four different comparators that can be used by the ADC (should always be set to 2)
                
#         # Masks for setting register 1 (used when writing on register 1)
#         self._vdd_sense_enable = 0x40                                               # 0x 0100 0000 - Enables the on-chip supply voltage sensor, whose outputs on are channel 48 (optional)
#         self._vdd_sense_disable = 0x00                                              # 0x 0000 0000 - Disables the on-chip supply voltage sensor (reduce 10 uA in power consumption)
#         self._adc_buffer_bias_default = 0x20                                        # 0x 0010 0000 - Configures the bias current of an internal reference buffer in the ADC (initially setted to 32, fs total ADC <= 120 kS/s).
        
#         # Masks for setting register 2 (used when writing on register 2)
#         self._mux_bias_current_default = 0x28                                       # 0x 0010 1000 - Configures the bias current of the MUX that routes the selected analog signal to the ADC input (initially setted to 40, fs total ADC <= 120 kS/s)
        
#         # Masks for setting register 3 (used when writing on register 3)
#         self._mux_load = 0x00                                                       # 0x 0000 0000 - Configures the total capacitance at the input of the ADC (should always be set to 0)
#         self._tempS2_enable = 0x10                                                  # 0x 0001 0000 - Enables the on-chip temperature sensor, whose outputs are on channel 49
#         self._tempS2_disable = 0x00                                                 # 0x 0000 0000 - Disables the on-chip temperature sensor (if is not in use, should be set to zero to save power)
#         self._tempS1_enable = 0x08                                                  # 0x 0000 1000 - Enables the on-chip temperature sensor, whose outputs are on channel 49
#         self._tempS1_disable = 0x00                                                 # 0x 0000 0000 - Disables the on-chip temperature sensor (if is not in use, should be set to zero to save power)
#         self._temp_enable = 0x04                                                    # 0x 0000 0100 - Enables the on-chip temperature sensor
#         self._temp_disable = 0x00                                                   # 0x 0000 0000 - Disables the on-chip temperature sensor (reduce 70 uA in power consumption)
#         self._digout_hiz_enable = 0x02                                              # 0x 0000 0010 - Enables the digital output into high impedance (HiZ) mode
#         self._digout_hiz_disable = 0x00                                             # 0x 0000 0000 - Disables the digital output into high impedance (HiZ) mode
#         self._digout_enable = 0x01                                                  # 0x 0000 0001 - This bit is driven out of the auxiliary CMOS digital output pin, provided that the digout HiZ bit is set to zero
#         self._digout_disable = 0x00                                                 # 0x 0000 0000 - This bit is driven out of the auxiliary CMOS digital output pin, provided that the digout HiZ bit is set to zero
        
#         # Masks for setting register 4 (used when writing on register 4)
#         self._weak_miso_enable = 0x80                                               # 0x 1000 0000 - If only one RHD2000 chip will be using a MISO line, this bit may be set to one
#         self._weak_miso_disable = 0x00                                              # 0x 0000 0000 - If more than RHD2000 chip will be using a MISO line, the MISO line goes to high impedance mode (HiZ) when CS is pulled high
#         self._twoscomp_enable = 0x40                                                # 0x 0100 0000 - Amplifier conversions from the ADC are reported using a “signed” two’s complement representation
#         self._twoscomp_disable = 0x00                                               # 0x 0000 0000 - Amplifier conversions from the ADC are reported using “unsigned” offset binary notation where the baseline level is represented as 0x8000
#         self._absmode_enable = 0x20                                                 # 0x 0010 0000 - Passes all amplifier ADC conversions through an absolute value function (full-wave rectification on the signals)
#         self._absmode_disable = 0x00                                                # 0x 0000 0000 - Disables full-wave rectification on the signals
#         self._dsp_enable = 0x10                                                     # 0x 0001 0000 - Performs digital signal processing (DSP) offset removal from all 32 amplifier channels using a first-order high-pass IIR filter
#         self._dsp_disable = 0x00                                                    # 0x 0000 0000 - Disables the digital signal processing (DSP) offset removal from all 32 amplifier channels
#         self._dsp_cutoff_default = 0x00                                             # 0x 0000 0000 - Sets the cutoff frequency of the DSP filter used to for offset removal (default value is 0)
        
#         # Masks for setting register 5 (used when writing on register 5)
#         self._zcheck_dac_power_enable = 0x40                                        # 0x 0100 0000 - Enables the on-chip digital-to-analog converter (DAC) used to generate waveforms for electrode impedance measurement
#         self._zcheck_dac_power_disable = 0x00                                       # 0x 0000 0000 - Disables the on-chip digital-to-analog converter (reduce 120 uA in power consumption) 
#         self._zcheck_load = 0x00                                                    # 0x 0000 0000 - Disables the capacitor load to the impedance checking network (should always be set to 0 in normal operation)
#         self._zcheck_scale_0p1_pF  = 0x00                                           # 0x 0000 0000 - Capacitance adjustment (0.1 pF) for impedance testing
#         self._zcheck_scale_1p0_pF  = 0x08                                           # 0x 0000 1000 - Capacitance adjustment (1.0 pF) for impedance testing
#         self._zcheck_scale_10p0_pF = 0x18                                           # 0x 0001 1000 - Capacitance adjustment (10.0 pF) for impedance testing.
#         self._zcheck_conn_all_enable = 0x04                                         # 0x 0000 0100 - Connects all electrodes together to the elec_test input pin
#         self._zcheck_conn_all_disable = 0x00                                        # 0x 0000 0000 - Disconnects all electrodes together to the elec_test input pin (normal operation)
#         self._zcheck_sel_pol_positive = 0x00                                        # 0x 0000 0000 - Only used on the RHD2216 bipolar biopotential amplifiers: selects impedance testing of the positive input
#         self._zcheck_sel_pol_negative = 0x02                                        # 0x 0000 0010 - Only used on the RHD2216 bipolar biopotential amplifiers: selects impedance testing of the negative input
#         self._zcheck_enable = 0x01                                                  # 0x 0000 0001 - Enables impedance testing mode and connects the on-chip waveform generator
#         self._zcheck_disable = 0x00                                                 # 0x 0000 0000 - Disables impedance testing mode
        
#         # PRIVATE METHODS CALLED IN INITIALIZATION
#         self._messages = self.__create_configuration_messages()                     # Constructs messages to be sent to configure INTAN
    
#     def __create_16bits_word(self, _register, _data):    
#         '''
#         This function creates a word with 16 bits to be sent in to INTAN
        
#         Consider the word [15][14][13][12][11][10][9][8][7][6][5][4][3][2][1][0]
#         Mask             -> [15][14], always 0b10 to write
#         Register Number  -> [13][12][11][10][9][8], can represent 64 registers 
#         Data to transfer -> [7][6][5][4][3][2][1][0], data sheet indication  
        
#         Parameters:
#             PRIVATE
#             _register .... Register number to be changed
#             _data ........ Configuration to be sent to the registry
#         '''
#         _mask = 0x8000                                                              # Every write command initialize with a mask equal to '10'
#         return (_mask | (_register << 8) | _data)                                   # Returns the word
    
#     def __reverse_8bits(self, _word):
#         '''
#         This function reverses the bit sequence of a word. For example, consider 
#         the word 0b00010010, the result is 0b01001000
        
#         Parameters:
#             PRIVATE
#             - _word .... word to be reversed
        
#         Returns:
#             PRIVATE
#             - _word .... reversed word
#         '''
#         _word = ((_word & 0x55555555) << 1) | ((_word & 0xAAAAAAAA) >> 1)           # Changes position bit by bit (ex: 0b10100101 -> 0b01011010)
#         _word = ((_word & 0x33333333) << 2) | ((_word & 0xCCCCCCCC) >> 2)           # Changes position 2-bits by 2-bits (ex: 0b00110011 -> 0b11001100)
#         _word = ((_word & 0x0F0F0F0F) << 4) | ((_word & 0xF0F0F0F0) >> 4)           # Changes position 4-bits by 4-bits (ex: 0b00001111 -> 0b11110000)
#         return _word                                                                # Returns the reversed word    
    
#     def __create_filter_messages(self):
#         '''
#         This function creates the messages to be sent for the INTAN filters configuration
        
#         Returns:
#             PRIVATE
#             - _register08 .... Message to change the register 08 (high pass filter)
#             - _register09 .... Message to change the register 09 (high pass filter)
#             - _register10 .... Message to change the register 10 (high pass filter)
#             - _register11 .... Message to change the register 11 (high pass filter)
#             - _register12 .... Message to change the register 12 (low pass filter)
#             - _register13 .... Message to change the register 13 (low pass filter)
#         '''
#         _highpass_registers = {100  : [38,26, 5,31], 150  : [44,17, 8,21],
#                                200  : [24,13, 7,16], 250  : [42,10, 5,13],
#                                300  : [ 6, 9, 2,11], 500  : [30, 5,43, 6],
#                                750  : [41, 3,36, 4], 1000 : [46, 2,30, 3],
#                                1500 : [ 1, 2,23, 2], 2000 : [27, 1,44, 1],
#                                2500 : [13, 1,25, 1], 3000 : [ 3, 1,13, 1],
#                                5000 : [33, 0,37, 0], 7500 : [22, 0,23, 0],
#                                10000: [17, 0,16, 0], 15000: [11, 0, 8, 0],
#                                20000: [ 8, 0, 4, 0]}                                                # Data to change in records for all possible frequencies (high pass filter)
        
#         _register08 = self.__create_16bits_word(0x0008, _highpass_registers[self._highpass][0])     # Writes RH1DAC1 on register 8 of INTAN RHD.
#         _register09 = self.__create_16bits_word(0x0009, _highpass_registers[self._highpass][1])     # Writes RH1DAC2 on register 9 of INTAN RHD.
#         _register10 = self.__create_16bits_word(0x000A, _highpass_registers[self._highpass][2])     # Writes RH2DAC1 on register 10 of INTAN RHD.
#         _register11 = self.__create_16bits_word(0x000B, _highpass_registers[self._highpass][3])     # Writes RH2DAC2 on register 11 of INTAN RHD.
  
#         _lowpass_registers = {0.1 : [16,60, 1], 0.25: [56,54, 0],
#                               0.3 : [ 1,40, 0], 0.5 : [35,17, 0],
#                               0.75: [49, 9, 0], 1   : [44, 6, 0],
#                               1.5 : [ 9, 4, 0], 2   : [ 8, 3, 0],
#                               2.5 : [42, 2, 0], 3   : [20, 0, 0],
#                               5   : [40, 1, 0], 7.5 : [18, 1, 0],
#                               10  : [ 5, 1, 0], 15  : [62, 0, 0],
#                               20  : [54, 0, 0], 25  : [48, 0, 0],
#                               30  : [44, 0, 0], 50  : [34, 0, 0],
#                               75  : [28, 0, 0], 100 : [25, 0, 0],
#                               150 : [21, 0, 0], 200 : [18, 0, 0],
#                               250 : [17, 0, 0], 300 : [15, 0, 0],
#                               500 : [13, 0, 0]}                                                     # Data to change in records for all possible frequencies (low pass filter)
        
#         _register12 = self.__create_16bits_word(0x000C, _lowpass_registers[self._lowpass][0])       # Writes RLDAC1 on register 12 of INTAN RHD.
#         _register13 = self.__create_16bits_word(0x000D, _lowpass_registers[self._lowpass][1] | 
#                                                 (_lowpass_registers[self._lowpass][2] << 6))        # Writes RLDAC2 and RLDAC3 on register 13 of INTAN RHD.
 
#         return _register08, _register09, _register10, _register11, _register12, _register13         # Returns 4 messages to be changed in respective registers    
    
#     def __create_configuration_messages(self):
#         '''
#         This function collects all messages from the registers that must be changed 
#         and creates a dictionary of commands to be sent to INTAN. Dictionary keys 
#         are the integers corresponding to the registers

#         Retunrs:
#             PRIVATE
#             - _messages .... Dictionary of commands to be sent to INTAN
            
#         '''
#         self._messages = {}                                                         # Creates an empty dictionary 
        
#         #self._messages.append(0x6A00)                                             # Clear command
        
#         # Builds message from register 0
#         _register00 = self.__create_16bits_word(0x0000, (self._adc_reference_bw | self._amp_fast_settle_disable | self._amp_vref_enable | self._adc_comparator_bias | self._adc_comparator_select))
#         self._messages[0] = _register00                                             # Sets the message on dictionary
        
#         # Builds message from register 1
#         _register01 = self.__create_16bits_word(0x0001, self._vdd_sense_disable | self._adc_buffer_bias_default)
#         self._messages[1] = _register01                                             # Sets the message on dictionary
        
#         # Builds message from register 2
#         _register02 = self.__create_16bits_word(0x0002, self._mux_bias_current_default)
#         self._messages[2] = _register02                                             # Sets the message on dictionary
        
#         # Builds message from register 3
#         _register03 = self.__create_16bits_word(0x0003, self._mux_load | self._tempS2_disable | self._tempS1_disable | self._temp_disable | self._digout_hiz_disable | self._digout_disable)
#         self._messages[3] = _register03                                             # Sets the message on dictionary
        
#         # Builds message from register 4
#         _register04 = self.__create_16bits_word(0x0004, self._weak_miso_enable | self._twoscomp_enable | self._absmode_disable | self._dsp_disable | self._dsp_cutoff_default)
#         self._messages[4] = _register04                                             # Sets the message on dictionary
        
#         # Builds message from register 5
#         _register05 = self.__create_16bits_word(0x0005, self._zcheck_dac_power_disable | self._zcheck_load | self._zcheck_scale_0p1_pF | self._zcheck_conn_all_disable | self._zcheck_sel_pol_positive | self._zcheck_disable)
#         self._messages[5] = _register05                                             # Sets the message on dictionary
        
#         # Builds message from register 6
#         _register06 = self.__create_16bits_word(0x0006, 0x0000)
#         self._messages[6] = _register06                                             # Sets the message on dictionary
        
#         # Builds message from register 7
#         _register07 = self.__create_16bits_word(0x0007, 0x0000)
#         self._messages[7] = _register07                                             # Sets the message on dictionary
        
#         # Builds message from registers 8 to 13 by __create_filter_messages function 
#         _register08, _register09, _register10, _register11, _register12, _register13 = self.__create_filter_messages()
#         self._messages[8] = _register08                                             # Sets the message on dictionary
#         self._messages[9] = _register09                                             # Sets the message on dictionary
#         self._messages[10] = _register10                                            # Sets the message on dictionary
#         self._messages[11] = _register11                                            # Sets the message on dictionary
#         self._messages[12] = _register12                                            # Sets the message on dictionary
#         self._messages[13] = _register13                                            # Sets the message on dictionary
        
#         # Builds message from register 14
#         _channels_0_to_7 = (self._channels_bool >> 24) & 0xFF
#         _channels_0_to_7 = self.__reverse_8bits(_channels_0_to_7)
#         _register14 = self.__create_16bits_word(0x0E, _channels_0_to_7)
#         self._messages[14] = _register14                                            # Sets the message on dictionary
        
#         # Builds message from register 15
#         _channels_8_to_15 = (self._channels_bool >> 16) & 0xFF
#         _channels_8_to_15 = self.__reverse_8bits(_channels_8_to_15)
#         _register15 = self.__create_16bits_word(0x0F, _channels_8_to_15)
#         self._messages[15] = _register15                                            # Sets the message on dictionary
        
#         # Builds message from register 16
#         _channels_16_to_23 = (self._channels_bool >> 8) & 0xFF
#         _channels_16_to_23 = self.__reverse_8bits(_channels_16_to_23)
#         _register16 = self.__create_16bits_word(0x10, _channels_16_to_23)
#         self._messages[16] = _register16                                            # Sets the message on dictionary
        
#         # Builds message from register 17 
#         _channels_17_to_31 = self._channels_bool & 0xFF
#         _channels_17_to_31 = self.__reverse_8bits(_channels_17_to_31)
#         _register17 = self.__create_16bits_word(0x11, _channels_17_to_31)
#         self._messages[17] = _register17                                            # Sets the message on dictionary
        
#         self._messages["Calibrate"] = 0x5500                                        # Calibrate command
#         self._messages["Dummy"] = 0xFFFF                                            # 9 dummys after calibrate (data sheet)
        
#         return self._messages                                                       # Returns the dictionary  
                       
#     def initialize_rhd_default(self):
#         self._answers = []
        
#         self._serial_port.write(self._messages[0])
#         self._answers.append(self._serial_port.read(16))
        
#         self._serial_port.write(self._messages[1])
#         self._answers.append(self._serial_port.read(16))
        
#         self._serial_port.write(self._messages[2])
#         self._answers.append(self._serial_port.read(16))
        
#         self._serial_port.write(self._messages[3])
#         self._answers.append(self._serial_port.read(16))
        
#         self._serial_port.write(self._messages[4])
#         self._answers.append(self._serial_port.read(16))
        
#         self._serial_port.write(self._messages[5])
#         self._answers.append(self._serial_port.read(16))
        
#         self._serial_port.write(self._messages[6])
#         self._answers.append(self._serial_port.read(16))
        
#         self._serial_port.write(self._messages[7])
#         self._answers.append(self._serial_port.read(16))
        
#         self._serial_port.write(self._messages[8])
#         self._answers.append(self._serial_port.read(16))
        
#         self._serial_port.write(self._messages[9])
#         self._answers.append(self._serial_port.read(16))
        
#         self._serial_port.write(self._messages[10])
#         self._answers.append(self._serial_port.read(16))
        
#         self._serial_port.write(self._messages[11])
#         self._answers.append(self._serial_port.read(16))
        
#         self._serial_port.write(self._messages[12])
#         self._answers.append(self._serial_port.read(16))
        
#         self._serial_port.write(self._messages[13])
#         self._answers.append(self._serial_port.read(16))
                                 
#         self._serial_port.write(self._messages["dummy"])
#         self._answers.append(self._serial_port.read(16))
        
#         self._serial_port.write(self._messages["dummy"])
#         self._answers.append(self._serial_port.read(16))
        
#         self._serial_port.write(self._messages[14])
#         self._answers.append(self._serial_port.read(16))
        
#         self._serial_port.write(self._messages[15])
#         self._answers.append(self._serial_port.read(16))
        
#         self._serial_port.write(self._messages[16])
#         self._answers.append(self._serial_port.read(16))
        
#         self._serial_port.write(self._messages[17])
#         self._answers.append(self._serial_port.read(16))
         
#         time.sleep(1)
        
#         self._serial_port.write(self._messages["Calibrate"])
#         self._answers.append(self._serial_port.read(16))
        
#         for a in range(0,10):
#             self._serial_port.write(self._messages["dummy"])
#             self._answers.append(self._serial_port.read(16))
        
#         return self._answers
            
#     def get_messages(self):
#         return self._messages
