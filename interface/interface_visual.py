'''
ELECTROPHYSIOLOGICAL DATA ACQUISITION SYSTEM

This code is the configuration part of the electrophysiology recording 
system. This partition contains the front-end, in which the user will be able 
to choose acquisition parameters such as sampling frequency, filters and number 
of channels.

Author: 
    João Pedro Carvalho Moreira
    Belo Horizonte, Minas Gerais, Brasil
    Graduated in Eletrical Engineer, UFSJ
    Mastering in Eletrical Engineer, UFMG
    Member of Núcleo de Neurociências, UFMG

Advisor: 
    Márcio Flávio Dutra Moraes

Version 1.0.2

Releases
Version 1.0.1
- Addition of advanced record programming
- Addition of stop/start button

Releases
Version 1.0.2
- Addition of functions to cammand the microcontroller
'''

#%% IMPORTS

import sys
import numpy 
import serial
import serial.tools.list_ports
import time
import struct
import collections
import interface_functions
import os
from datetime import datetime, timedelta
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QCoreApplication, QTimer
from PyQt5.QtWidgets import QMessageBox, QMainWindow
from tkinter import Tk 
from tkinter.filedialog import (asksaveasfilename as save_dir_popup)

from pyqtgraph.Qt import QtGui
from pyqtgraph import mkPen
import pyqtgraph

#%% PLOT DATA CLASS

class plot_data_class(QObject):
    ''' 
    This class is a worker that will be inserted into a Thread. The functions of this class 
    aim to make the interface graphics and have two main features, one for real-time plots 
    and another for plots executed by interface buttons.
    
    Parameters:
        - file ........... Open file in which the records are being saved
        - option ......... The option dictionary that contains all record configurations
        - plot_viewer .... Is the object that represents the plot viewer in the interface
    '''
    finished = pyqtSignal()                                                                         # Signal that will be output to the interface when the function is complited
    
    def __init__(self, plot_viewer, options, buffer):                                               # Initializes when the thread is started
        ''' 
        This private function is executed when the class is called, and all parameters are
        defined here
        '''
        super(plot_data_class, self).__init__()                                                                             # Super declaration
        self.plot_viewer = plot_viewer                                                                                      # Sets the the interface plot widget as self variable
        self.options = options                                                                                              # Sets the options as self variable
        self.buffer = buffer                                                                                                # Sets the buffer as self variable
        
        self.channels = self.options.channels                                                                               # Gets the channels that will be recorded
        self.number_channels = self.options.number_channels                                                                 # Gets the number of channels that will be recorded
        self.channel_count = list(range(0, self.number_channels))                                                           # Creates a vector with the number of channels lenght        
                
        self.atualization_time = 4                                                                                          # Total time in secons to show in plot (default: 4 seconds)
        self.plot_length = self.atualization_time*self.options.sampling_frequency                                           # Total data length to be plotted per channel in "atualization_time"
        self.bytes_to_plot = self.options.number_channels*self.options.sampling_frequency                                   # Total data length to be plotted
        self.time_in_seconds = numpy.linspace(0, self.atualization_time, self.plot_length)                                  # Time vector in seconds
        self.unpack_format = "<" + str(int(self.bytes_to_plot)) + "h"                                                       # Format to struct.unpack( ) function reads the data (two's complement little edian)     

        self.plot_pen = mkPen('#D88A8A', width=0.8)
        self.clear_plot()
        self.setup_plot()
                                
    def plot(self):
        '''
        This public function will plot the last 4 seconds of record on the interface in real 
        time, updating the values every second
        '''
        byte_data = bytearray(b''.join(self.buffer))                                                                        # Gets all packages in buffer and puts on single binary list
        integer_data = struct.unpack(self.unpack_format, byte_data)                                                         # Transforms binary data in integer with the string in format "self.unpack_format" (two's complement little edian)          
        micro_volts_data = 500*(0.195e-6)*numpy.array(integer_data)                                                         # Transforms data to Volts (0.195*1e-6 -> datasheet) and adds a scale factor to plot (100 -> arbitrary)
        
        for channel in self.channel_count:                                                                                  # For all channels recorded
            self.data_matrix[channel].extend(self.channels[channel] + micro_volts_data[channel+4::self.number_channels])    # Gets the data in Volts "channel" by "channel", puts in matrix to be plotted and for each channel add the channel number for better visualization of the data
            self.lines[channel].setData(self.time_in_seconds,self.data_matrix[channel])                                     # Plots the respective data with set_ydata (this function only changes the data without changes the axes configurations)
        
    def clear_plot(self):
        '''
        This public function resets the plot to initial configurations
        '''
        self.plot_viewer.clear()
        
    def setup_plot(self):
        self.data_matrix = []                                                                                               # Initializes the data matrix to be plotted (each row is a channel)
        self.lines = []                                                                                                     # Initializes a line matrix to be plotted in the begging of acquisition (each row have only "0" = value of the channel)
        for i in self.channel_count:                                                                                        # Creates a row in the matrix for each active channel 
            self.data_matrix.append(collections.deque(maxlen = self.plot_length))                                           # Creates 1 circular buffer to all channels with length of 5 seconds of record                             
            for j in range(0, self.plot_length):                                                                            # For all columns in each row
                self.data_matrix[i].append(self.channels[i])                                                                # Puts the value of the channel (ex: for the channel 6, the row have only 6 to be plotted in correct place)
            self.lines.append(self.plot_viewer.plot(self.time_in_seconds, self.data_matrix[i], pen = self.plot_pen))        # Plots lines in interface
        
    def finish_plot(self):
        '''
        This public function will emit the command to finish the thread 
        '''
        self.finished.emit()                                                                                                # Emits the finish signal to closes the thread

#%% RECEIVE DATA CLASS
    
class receive_data_class(QObject):
    ''' 
    This class is a worker that will be inserted into a Thread. The functions of this class
    are the most important for the operation of the interface system, they are where the 
    interface will connect to the arduino and read the data sent via UART.
    
    Parameters:
        - file ........... Open file in which the records are being saved
        - option ......... The option dictionary that contains all record configurations
    '''
    finished = pyqtSignal()                                                                                     # Signal that will be output to the interface when the function is complited
    progress = pyqtSignal()                                                                                     # Signal that will be output to the interface to reposrt the progress of the data acquisition 
    
    def __init__(self, plot_viewer, options):
        ''' 
        This private function is executed when the class is called, and all parameters are 
        defined here
        '''
        super(receive_data_class, self).__init__()                                                              # Super declaration
        self.plot_viewer = plot_viewer                                                                          # Sets the the interface plot widget as self variable
        self.options = options                                                                                  # Sets the options as self variable        
        
        self.save_directory = options.save_directory                                                            # Gets the directory to save the data
        self.sampling_frequency = options.sampling_frequency                                                    # Gets the sampling frequency value
        self.number_channels = options.number_channels                                                          # Gets the number of channels to be recorded
        
        self.bytes_to_read = int(2*options.number_channels)                                                     # Number of bytes to be read at a time (in this case, at a time will be read 1 sample = 2 bytes per channel)          
        self.buffer_length = options.sampling_frequency                                                         # Buffer length to store 1 second of record
        self.buffer = collections.deque(maxlen = self.buffer_length)                                            # Circular buffer to store 1 second of record
        
        self._is_running = True                                                                                 # Signal that allows the while loop to be started     
        self._is_stopped = False                                                                                # Signal that allows the while loop to be paused
        self._change_directory = False
        
        self.plot_data_thread = QThread()                                                                       # Creates a QThread object to plot the received data
        self.plot_data_worker = plot_data_class(self.plot_viewer, self.options, self.buffer)                    # Creates a worker object named plot_data_class
        self.plot_data_worker.moveToThread(self.plot_data_thread)                                               # Moves the class to the thread
        self.plot_data_worker.finished.connect(self.plot_data_thread.quit)                                      # When the process is finished, this command quits the worker
        self.plot_data_worker.finished.connect(self.plot_data_thread.wait)                                      # When the process is finished, this command waits the worker to finish completely
        self.plot_data_worker.finished.connect(self.plot_data_worker.deleteLater)                               # When the process is finished, this command deletes the worker
        self.plot_data_thread.finished.connect(self.plot_data_thread.deleteLater)                               # When the process is finished, this command deletes the thread
        self.plot_data_thread.start()                                                                           # Starts the thread 
        
        self.usb = interface_functions.usb_singleton(self.options.usb_port, 50000000)                     # Configures the USB connection
        self.usb.connect()                                                                                      # Connect the USB port
        
    def run_view(self):
        '''
        This public function will read the data being sent by the USB acquisition system when
        recording mode is active. The difference from the previous one is that with each sample, 
        a progress signal will be sent to the interface (this operation decreases the progress 
        frequency a little).  
        '''
        self.usb.request_acquisition()                                                                          # Command to start the data acquisition    
        count_to_plot = 0                                                                                       # Initializes the counter that will control the plot (every 1 second sends the message to plot)
        
        self.start_time = time.perf_counter()                                                                   # Sets the start time of the experiment
        while self._is_running == True:                                                                         # While _isRunning is True
            if (self.usb.port.inWaiting() >= self.bytes_to_read) and (self._is_stopped == False):               # If has any data in UART buffer waiting to be read and the record is not paused
                data = self.usb.port.read(self.bytes_to_read)                                                   # Reads data from SPI port   
                self.buffer.append(data)                                                                        # Saves the data in buffer
                count_to_plot += 1                                                                              # Adds one step in counter 
                if count_to_plot == self.buffer_length:                                                         # Every 1 second 
                    self.plot_data_worker.plot()                                                                # Runs the function that will plot the last 1 second of data in the interface
                    count_to_plot = 0                                                                           # Resets the counter
        self.options.record_time = time.perf_counter() - self.start_time                                        # Shares with the interface the total time of record  
        
        self.usb.stop_acquisition()                                                                             # Stops the acquisition in Arduino   
        self.usb.disconnect()                                                                                   # Disconnect the USB port
        self.plot_data_worker.clear_plot()                                                                      # Clears the plot viewer
        self.plot_data_worker.finish_plot()                                                                     # Closes the plot thread
        self.finished.emit()                                                                                    # Emits the finish signal    
                
    def run_recording(self):
        '''
        This public function will read the data being sent by the USB acquisition system when 
        recording mode is active. This is the most simple and faster function to read UART 
        datas.  
        '''
        self.directory_count = 0                                                                                # Creates the counter to count the number of files (this number goes in the file name)
        self.file = open(self.options.save_directory + "_0.bin", "wb")                                          # Opens/Creates the file to write the binary data
        
        self.usb.request_acquisition()                                                                          # Command to starts the data acquisition (send to Arduino) 
        
        self.start_time = time.perf_counter()                                                                   # Sets the start time of the experiment
                
        while self._is_running == True:                                                                         # While _isRunning is True
            if (self.usb.port.inWaiting() >= self.bytes_to_read) and (self._is_stopped == False):               # If has any data in UART buffer waiting to be read and the record is not paused
                data = self.usb.port.read(self.bytes_to_read)                                                   # Reads data from SPI port   
                self.file.write(data)                                                                           # Writes on file
                self.buffer.append(data)                                                                        # Saves the data in buffer
            elif self._change_directory == True:                                                                # If the flag to change the directory is True
                self.directory_count += 1                                                                       # Adds one step in counter  
                self.file.close()                                                                               # Closes the last file 
                self.file = open(self.options.save_directory + "_" + 
                                 str(self.directory_count) + ".bin", "wb")                                      # Opens/Creates the new file to write the binary data
                self._change_directory = False

        self.options.record_time = time.perf_counter() - self.start_time                                        # Shares with the interface the total time of record
               
        self.file.close()                                                                                       # Closes the binary file
        self.usb.stop_acquisition()                                                                             # Stops the acquisition in Arduino  
        self.usb.disconnect()                                                                                   # Disconnect the USB port
        self.plot_data_worker.clear_plot()                                                                      # Clears the plot viewer
        self.plot_data_worker.finish_plot()                                                                     # Closes the plot thread
        self.finished.emit()                                                                                    # Emits the finish signal
        
    def plot(self):
        self.plot_data_worker.plot()                                                                            # Calls the function in plot_data_class (another thread) to plot the data 
    
    def change_direcotory_function(self):
        self._change_directory = True    
    
    def continue_record(self):
        self.usb.request_acquisition()                                                                          # Command to start the data acquisition    
        self._is_stopped = False                                                                                # Changes state from paused to running

    def stop_record(self):
        self._is_stopped = True                                                                                 # Changes state from running to paused
        self.usb.stop_acquisition()                                                                             # Command to stop the data acquisition                                                      

    def finish_record(self):
        '''
        This public function will break the while loop causing the finish signal to be emitted
        '''
        self._is_running = False                                                                                # Signal that breaks the while loop

#%% INTERFACE CLASS

class interface_visual_gui(QMainWindow):
    '''
    This class contains all the commands of the interface as well as the constructors of the 
    interface itself.
    '''
 
#%% CONNECTION AND INITIALIZATION FUNCTIONS
    
    def __init__(self):
        '''
        This private function calls the interface of a .ui file created in Qt Designer, starts 
        the dictionaries that contain the desired settings for the registry, and makes the 
        connections between the user's activities and their respective functions.
        '''
        super(interface_visual_gui, self).__init__()                                                            # Calls the inherited classes __init__ method
        QMainWindow.__init__(self)                                                                              # Creates the main window
        self.interface = uic.loadUi(os.path.dirname(__file__) + "\\interface_gui.ui", self)                                                 # Loads the interface design archive (made in Qt Designer)
                
        self.plot_viewer_function()
        self.showMaximized()
        self.show()                                                                                             # Shows the interface to the user

        # INTERFCE DEFAULT OPTIONS
        # This dictionary is the output variable of the interface to start the record
        self.options = interface_functions.acquisition()
        
        # INTERFACE INTERACTIONS
        # Record configuration interactions
        self.chip_combobox.currentIndexChanged.connect(self.chip_function)                                      # Called when chip combobox is changed
        self.method_combobox.currentIndexChanged.connect(self.method_function)                                  # Called when method combobox is changed
        self.usb_port.clicked.connect(self.usb_port_function)                                                   # Called when the update USB button is clicked
        self.usb_port_combobox.currentIndexChanged.connect(self.usb_selection_function)                         # Called when the USB combo box is changed
        self.sampling_frequency_slider.valueChanged[int].connect(self.sampling_frequency_function)              # Called when sampling frequency slider is changed
        self.highpass_frequency_slider.valueChanged[int].connect(self.highpass_frequency_function)              # Called when high pass cutoff frequency slider is changed
        self.lowpass_frequency_slider.valueChanged[int].connect(self.lowpass_frequency_function)                # Called when low pass cutoff frequency slider is changed
        self.start_recording_button.clicked.connect(self.start_recording_mode_function)                         # Called when the start recording button is clicked
        # Advanced configuration interactions
        self.command_send_button.clicked.connect(self.send_command_function)
        self.cancel_advanced_button.clicked.connect(self.cancel_advanced_function)
        self.continue_to_record_button.clicked.connect(self.continue_to_record_function)
        # General interface interactions
        self.check_all_button.clicked.connect(self.check_all_function)                                          # Called when "check/uncheck all" button is clicked
        self.clear_button.clicked.connect(self.clear_function)                                                  # Called when the clear button is clicked
        self.cancel_button.clicked.connect(self.cancel_function)                                                # Called when the cancel button is clicked
        self.stop_button.clicked.connect(self.stop_function)
        self.record_button.clicked.connect(self.start_view_mode_function)                                       # Called when the clear button is clicked 
        self.plot_next_button.clicked.connect(self.plot_recording_mode_function)                                # Called when the "plot the last samples" button is clicked
        self.update_statistics_button.clicked.connect(self.update_statistics_function)                          # Called when the "update statistics" button is clicked
                     
#%% INTERFACE SELECTIONS FUNCTIONS
        
    # Function to set the data aquisition system
    def method_function(self):
        '''
        This public function is called when the acquisition method is changed by the user.
        '''
        method = self.method_combobox.currentIndex()                                                             # Gets the combo box index
        if method == 0:                                                                                          # If is selected FPGA
            self.options.method = "ARDUINO"                                                                      # Changes the method on main variables dictionary
            self.method_lineshow.setText("ARDUINO")                                                               # Changes the line edit (Record tab) in the interface
        # elif method == 1:                                                                                       # If is selected ARDUINO    
        #     self.options.method = "FPGA"                                                                        # Changes the method on main variables dictionary 
        #     self.method_lineshow.setText("FPGA")                                                                # Changes the line edit (Record tab) in the interface

        # elif method == 2:                                                                                       # If is selected PI PICO
        #     self.options.method = "PI PICO"                                                                     # Changes the method on main variables dictionary
        #     self.method_lineshow.setText("PI PICO")                                                             # Changes the line edit (Record tab) in the interface
    
    # Function to set what chip will be used
    def chip_function(self):
        '''
        This public function is called when the acquisition chip is changed by the user.
        '''
        chip = self.chip_combobox.currentIndex()                                                                # Gets the combo box index
        if chip == 0:                                                                                           # If is selected RHD2216
            self.highpass_frequency_slider.setEnabled(True)                                                     # Enables high pass filter cutting frequency slider 
            self.highpass_frequency_function()                                                                  # Calls the frequency function to update the information
            self.lowpass_frequency_slider.setEnabled(True)                                                      # Enables low pass filter cutting frequency slider
            self.lowpass_frequency_function()                                                                   # Calls the frequency function to update the information
            self.channel_16_area.setEnabled(True)                                                               # Enables channels 09 - 16        
            self.channel_32_area.setEnabled(False)                                                              # Disables channels 17 - 32
            self.options.chip = "RHD2216"                                                                       # Changes the chip on main variables dictionary 
            self.chip_lineshow.setText("RHD2216")                                                               # Changes the line edit (Record tab) in the interface
        elif chip == 1:                                                                                         # If is selected RHD2132    
            self.highpass_frequency_slider.setEnabled(True)                                                     # Enables high pass filter cutting frequency slider
            self.highpass_frequency_function()                                                                  # Calls the frequency function to update the information
            self.lowpass_frequency_slider.setEnabled(True)                                                      # Enables low pass filter cutting frequency slider 
            self.lowpass_frequency_function()                                                                   # Calls the frequency function to update the information
            self.channel_16_area.setEnabled(True)                                                               # Enables channels 09 - 16
            self.channel_32_area.setEnabled(True)                                                               # Enables channels 17 - 32
            self.options.chip = "RHD2132"                                                                       # Changes the chip on main variables dictionary
            self.chip_lineshow.setText("RHD2132")                                                               # Changes the line edit (Record tab) in the interface
        elif chip == 2:                                                                                         # If is selected ADS1298
            self.highpass_frequency_slider.setEnabled(False)                                                    # Disables high pass filter cutting frequency slider
            self.highpass_frequency_lineshow.setText("--")                                                      # Changes the line edit (Record tab) in the interface                        
            self.lowpass_frequency_slider.setEnabled(False)                                                     # Disables low pass filter cutting frequency slider
            self.lowpass_frequency_lineshow.setText("--")                                                       # Changes the line edit (Record tab) in the interface   
            self.channel_16_area.setEnabled(False)                                                              # Disables channels 09 - 16
            self.channel_32_area.setEnabled(False)                                                              # Disables channels 17 - 32
            self.options.chip = "ADS1298"                                                                       # Changes the chip on main variables dictionary
            self.chip_lineshow.setText("ADS1298")                                                               # Changes the line edit (Record tab) in the interface
    
    # Function to set the sampling frequency
    def sampling_frequency_function(self):
        '''
        This public function is called when the sampling frequency is changed by the user.
        '''
        sampling_frequency_index = self.sampling_frequency_slider.value()                                       # Gets the slider index
        if self.options.method == "ARDUINO" and sampling_frequency_index <= 4:                                  # If an ARDUINO is being used and the sampling frequency is less than or equal to 2KHz
            self.options.set_sampling_frequency_by_index(sampling_frequency_index)                              # Changes the option in the acquisition object
            sampling_frequency = self.options.sampling_frequency                                                # Gets from the acquisition object the sampling frequnecy option
            self.sampling_frequency_lineedit.setText(str(sampling_frequency))                                   # Changes the line edit in the interface
            self.sampling_frequency_lineshow.setText(str(sampling_frequency))                                   # Changes the line edit (Record tab) in the interface
        else:
            text = "The ARDUINO does not perform data acquisitions with more than 2000 Hz"                      # Creates a warning message
            self.warning_message_function(text)                                                                 # Shows warning pop-up      
            self.sampling_frequency_slider.setValue(sampling_frequency_index - 1)                               # Returns to the previus slider value
        
    # Function to set the high pass filter cutoff frequency
    def highpass_frequency_function(self):
        '''
        This public function is called when the high pass filter cutoff frequency is changed 
        by the user.
        '''
        highpass_frequency_index = self.highpass_frequency_slider.value()                                       # Gets the slider index
        self.options.set_highpass_by_index(highpass_frequency_index)                                            # Changes the option in the acquisition object
        if self.options.highpass < self.options.lowpass:                                                        # If LP is greater than HP
            self.highpass_frequency_lineedit.setText(str(self.options.highpass))                                # Changes the line edit in the interface
            self.highpass_frequency_lineshow.setText(str(self.options.highpass))                                # Changes the line edit (Record tab) in the interface
        else:                                                                                                   # If HP is greater than LP
            text = "The cutoff frequency of the high pass filter cannot be \
                    greater than the cutoff frequency of the low pass filter"                                   # Creates a warning message
            self.warning_message_function(text)                                                                 # Shows warning pop-up
            self.highpass_frequency_slider.setValue(highpass_frequency_index - 1)                               # Returns to the previus slider value
            self.options.set_highpass_by_index(highpass_frequency_index - 1)                                    # Returns to the previus high pass frequency   
        
    # Function to set the low pass filter cutoff frequency
    def lowpass_frequency_function(self):
        '''
        This public function is called when the low pass filter cutoff frequency is changed
        by the user.
        '''
        lowpass_frequency_index = self.lowpass_frequency_slider.value()                                         # Gets the slider index
        self.options.set_lowpass_by_index(lowpass_frequency_index)                                              # Changes the option in the acquisition object
        if self.options.lowpass > self.options.highpass:                                                        # If HP is greater than LP
            self.lowpass_frequency_lineedit.setText(str(self.options.lowpass))                                  # Changes the line edit in the interface
            self.lowpass_frequency_lineshow.setText(str(self.options.lowpass))                                  # Changes the line edit (Record tab) in the interface
        else:           
            text = "The cutoff frequency of the high pass filter cannot be \
                    greater than the cutoff frequency of the low pass filter"                                   # Creates a warning message
            self.warning_message_function(text)                                                                 # Shows warning pop-up
            self.lowpass_frequency_slider.setValue(lowpass_frequency_index + 1)                                 # Returns to the previus slider value
            self.options.set_lowpass_by_index(lowpass_frequency_index + 1)                                      # Returns to the previus low pass frequency   
                      
    # Function to check and uncheck the channels radio buttuns
    def check_all_function(self):
        '''
        This public function is called when uncheck/check button is clicked. 
        '''
        check_all = self.check_all_button.text()                                                                # Gets the current text in the button
        if check_all == "Uncheck All":
            self.C01_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel                                   
            self.C02_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C03_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C04_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C05_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C06_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C07_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C08_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C09_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C10_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C11_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C12_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C13_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C14_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C15_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C16_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C17_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C18_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C19_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C20_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C21_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C22_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C23_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C24_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C25_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C26_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C27_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C28_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C29_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C30_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C31_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel 
            self.C32_button.setChecked(False)                                                                   # Sets unchecked the corresponding channel
            self.check_all_button.setText("Check All")                                                          # Changes the text in Check/Uncheck button
        else:
            self.C01_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C02_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C03_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C04_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C05_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C06_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C07_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C08_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C09_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C10_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C11_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C12_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C13_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C14_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C15_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C16_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C17_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C18_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C19_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C20_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C21_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C22_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C23_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C24_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C25_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C26_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C27_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C28_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C29_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C30_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C31_button.setChecked(True)                                                                    # Sets checked the corresponding channel  
            self.C32_button.setChecked(True)                                                                    # Sets checked the corresponding channel
            self.check_all_button.setText("Uncheck All")                                                        # Changes the text in Check/Uncheck button
            
    # This function sets the record time 
    def get_time_configuration_function(self):
        '''
        This public function is called when the registration button is clicked. Here the 
        time settings selected by the user will be changed in the options dictionaries 
        and the total acquisition time will be calculated
        '''
        now = datetime.now()                                                                                    # Gets the current day and hour
        start_date = now.strftime("%d/%m/%Y %H:%M:%S")                                                          # Formats the string with the current day and hour
        self.start_duration_lineshow.setText(start_date)                                                        # Changes the line edit (Record tab) in the interface

        self.options.days = int(self.time_day_spinbox.text())                                                   # Changes the days option in the acquisition object
        self.options.hours = int(self.time_hour_spinbox.text())                                                 # Changes the hours option in the acquisition object
        self.options.minutes = int(self.time_min_spinbox.text())                                                # Changes the minutes option in the acquisition object
        self.options.seconds = int(self.time_sec_spinbox.text())                                                # Changes the seconds option in the acquisition object
        
        self.duration_time_lineshow.setText(str(timedelta(seconds=self.options.get_total_time())))              # Changes the line edit (Record tab) in the interface

    # This public function defines the channels to be sampled
    def get_channels_configuration_function(self):
        '''
        This public function is called when the registration button is clicked. Here 
        the active channels will be identified, organized in a list that will be passed 
        to the option dictionaries
        '''
        channels = []
        channels.append(self.C01_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C02_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C03_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C04_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C05_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C06_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C07_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C08_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C09_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C10_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C11_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C12_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C13_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C14_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C15_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C16_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C17_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C18_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C19_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C20_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C21_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C22_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C23_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C24_button.isChecked())                                                            # Checks if a certain channel is active (True or False)        
        channels.append(self.C25_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C26_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C27_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C28_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C29_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C30_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C31_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        channels.append(self.C32_button.isChecked())                                                            # Checks if a certain channel is active (True or False)
        
        channels = numpy.multiply(channels, 1)                                                                  # Transforms "True" in 1 and "False" in 0
        self.options.set_channels(channels)                                                                     # Changes the channels option in the acquisition object
        self.number_channels_lineshow.setText(str(self.options.number_channels))                                # Changes the line edit (Record tab) in the interface

#%% USB FUNCTIONS 

    def usb_port_function(self):
        '''
        This public function will identify the USB ports connected to the computer, show 
        them to the user and configure the options dictionary.
        '''
        self.usb_selection_enable = 0                                                                           # This variable identifies whether the port update button has already been clicked
        self.usb_port_combobox.clear()                                                                          # Clears the combo box with the USB options
        self.online_ports = []                                                                                  # Initializes the list that will contain the USB port options
        ports = serial.tools.list_ports.comports()                                                              # Gets all ports connected to the computer
        for port, desc, hwid in sorted(ports):                                                                  # From the identified ports 
            self.usb_port_combobox.addItem("{}: {}".format(port, desc))                                         # Gets the port and name of the connected device
            self.online_ports.append(port)                                                                      # Adds the ports in the list
        if len(self.online_ports) != 0:                                                                         # If ports were found 
            self.usb_selection_enable = 1                                                                       # Changes the indentification variable 
            self.usb_selection_function()                                                                       # Calls the function to configure the USB ports in dictionary
        else:                                                                                                   # If no ports were found
            self.options.usb_port = "None"                                                                      # Puts "None" in option dictionary 
            return
    
    def usb_selection_function(self):
        '''
        This public function is auxiliary to the cime function and identifies changes in 
        the combo box
        '''
        if self.usb_selection_enable == 1:                                                                      # If the USB connections were updated at least 1 time and ports were found
            usb_selected = self.online_ports[self.usb_port_combobox.currentIndex()]                             # Gets the port selected by the user
            self.options.usb_port = usb_selected                                                                # Changes the USB port option in the acquisition object

    def configure_acquisition(self):       
        self.usb = interface_functions.usb_singleton(self.options.usb_port, 50000000)
        self.usb.connect()
        
        print(self.options.resume_options())
        
        self.usb.set_sampling_frequency(self.options.sampling_frequency)
        self.usb.set_highpass_frequency(self.highpass_frequency_slider.value())
        self.usb.set_lowpass_frequency(self.lowpass_frequency_slider.value())
        self.usb.set_channel_0to15(self.options.channels_bool)
        self.usb.set_channel_16to31(self.options.channels_bool)
        
        self.usb.disconnect()

#%% VIEW MODE FUNCTIONS
    
    # This function is the interface output, where the program will start to sampling 
    def start_view_mode_function(self):
        '''
        This public function is called when the record button is clicked. 
        '''
        self.get_time_configuration_function()                                                                  # Calls the function to define the record time 
        self.get_channels_configuration_function()                                                              # Calls the function to define the channels that will be sampled 
        
        #if self.options.usb_port == "None":                                                                     # If none USB port was founded
        #    self.warning_message_function("Please select a valid USB port")                                     # Shows a warning message
        #    return                                                                                              # The program do nothing
        
        answer = self.resume_message_function()                                                                 # Calls a function to create the configuration resume message
        if answer == "yes" and self.advanced_checkbox.isChecked() == False:                                     # If the user option is "yes" and advanced settings is not selected  
            #try:                                                                                                # Trys to execute the communication function
            self.configure_acquisition()
            self.view_mode_function()                                                                       # Calls the commmunication function to open the data acquisition thread
            #except:
            #    text = str('The interface failed to try to start the threads responsible' +
            #               ' for signal acquisition. Try starting the record again, if the' +
            #               ' error persists, restart the interface')                                            # Message to be displeyed
            #    self.warning_message_function(text)                                                             # Shows a warning message
            #    return                                                                                          # The program do nothing
            
            self.frequency_config_area.setEnabled(False)                                                        # Disables all the configuration tab
            self.channel_config_area.setEnabled(False)                                                          # Disables all the configuration tab
            self.record_config_area.setEnabled(False)                                                           # Disables all the configuration tab
            self.record_show_frame.setEnabled(True)                                                             # Enables all the configuration tab
            self.tabWidget.setCurrentIndex(1)                                                                   # Changes to record tab      
        elif answer == "yes" and self.advanced_checkbox.isChecked() == True:                                    # If the user option is "yes" and advanced settings is not selected  
            self.configure_acquisition()
            self.frequency_config_area.setEnabled(False)                                                        # Disables all the configuration tab
            self.channel_config_area.setEnabled(False)                                                          # Disables all the configuration tab
            self.record_config_area.setEnabled(False)                                                           # Disables all the configuration tab
            self.advanced_frame.setEnabled(True)                                                                # Enables all the configuration tab
            self.tabWidget.setCurrentIndex(2)                                                                   # Changes to record tab      
        else:                                                                                                   # If the user option is "no"
            return                                                                                              # The program do nothing
    
    def view_mode_function(self):
        self.data_thread = QThread()                                                                            # Creates a QThread object to receive USB data
        self.data_worker = receive_data_class(self.plot_viewer, self.options)                                   # Creates a worker object named receive_data_class
        self.data_worker.moveToThread(self.data_thread)                                                         # Moves worker to the thread
        self.data_thread.started.connect(self.data_worker.run_view)                                             # If the thread was started, connect to worker.run_view       
        self.data_worker.finished.connect(self.data_thread.quit)                                                # When the process is finished, this command quits the worker
        self.data_worker.finished.connect(self.data_thread.wait)                                                # When the process is finished, this command waits the worker to finish completely
        self.data_worker.finished.connect(self.data_worker.deleteLater)                                         # When the process is finished, this command deletes the worker
        self.data_thread.finished.connect(self.data_thread.deleteLater)                                         # When the process is finished, this command deletes the thread       
        self.start_time_estimate = time.perf_counter()                                                          # Gets the time to update the progress statistics
        self.data_thread.start()                                                                                # Starts the thread     

#%% RECORDING MODE FUNCTIONS
    
    def start_recording_mode_function(self):
        self.data_worker.finish_record()                                                                        # Closes the usb port thread
            
        try:
            Tk().withdraw()                                                                                     # Hide a Tk window
            save_directory = save_dir_popup(filetypes=(("Save file","*.bin"),("All files","*")))                # Opens the computer directorys to chose the save file
            if save_directory == '':
                self.options.save_directory = "None" 
                self.view_mode_function()
                return
            else:
                self.experiment_name_lineshow.setText(save_directory.split("/")[-1])
                self.options.save_directory = save_directory                                                    # Changes the save directory on main variables dictionary
                self.options.is_recording_mode = True
        except:
            text = str('\nWARNING: The interface failed to create the binary file,' + 
                       ' please select a valid directory')                                                      # Message to be displeyed
            self.warning_message_function(text)                                                                 # Displays a message in the edit line of the interface
            return
        
        try:
            self.recording_mode_function()                                                                      # Restart the acquisition and plot threads
        except:
            text = str('\nWARNING: The interface failed to try to start the threads responsible' +
                       ' for signal acquisition')                                                               # Message to be displeyed
            self.warning_message_function(text)                                                                 # Displays a message in the edit line of the interface
            return
        
        self.plot_next_button.setEnabled(True)                                                                  # Enables the button to plot the last values acquired
        self.start_recording_button.setEnabled(False)                                                           # Disables the strat recording button
            
    def recording_mode_function(self):
        self.data_thread = QThread()                                                                            # Creates a QThread object to receive USB data
        self.data_worker = receive_data_class(self.plot_viewer, self.options)                                   # Creates a worker object named receive_data_class
        self.data_worker.moveToThread(self.data_thread)                                                         # Moves worker to the thread
        self.data_thread.started.connect(self.data_worker.run_recording)                                        # If the thread was started, connect to worker.run_view       
        self.data_worker.finished.connect(self.data_thread.quit)                                                # When the process is finished, this command quits the worker
        self.data_worker.finished.connect(self.data_thread.wait)                                                # When the process is finished, this command waits the worker to finish completely
        self.data_worker.finished.connect(self.data_worker.deleteLater)                                         # When the process is finished, this command deletes the worker
        self.data_thread.finished.connect(self.data_thread.deleteLater)                                         # When the process is finished, this command deletes the thread       
        self.data_thread.start()                                                                                # Starts the thread     
        self.start_timers_function()                                                                            # Starts user programmed timer        

    def plot_recording_mode_function(self):
        try:
            self.data_worker.plot()                                                                             # Runs the plot function one time
        except:
            return

#%% ADVANCED SETTINGS FUNCTIONS
    
    def continue_to_record_function(self):
        try:                                                                                                    # Trys to execute the communication function
            self.view_mode_function()                                                                           # Calls the commmunication function to open the data acquisition thread
        except:
            text = str('The interface failed to try to start the threads responsible' +
                       ' for signal acquisition. Try starting the record again, if the' +
                       ' error persists, restart the interface')                                                # Message to be displeyed
            self.warning_message_function(text)                                                                 # Shows a warning message
            return                                                                                              # The program do nothing
        
        self.advanced_frame.setEnabled(True)                                                                    # Disables all the advanced tab
        self.record_show_frame.setEnabled(True)                                                                 # Enables all the record tab
        self.tabWidget.setCurrentIndex(1)                                                                       # Changes to record tab      

    def send_command_function(self):
        command = self.command_message_lineedit.text()
        
        if len(command) <= 8:
            command = int('0x' + command, 16).to_bytes(4,'big')
        else:
            self.command_answer_lineedit.setText('cmd > 4 bytes')
            return

        self.usb = interface_functions.usb_singleton(self.options.usb_port, 50000000)
        self.usb.connect()
        
        answer = self.usb.send_direct(command)
        
        self.usb.disconnect()
        
        self.command_answer_lineedit.setText(answer.hex().upper())
        self.show_commands_textedit.append('\nCommand sent ....... 0x' + command.hex() + 
                                                    '\nAnswer received .... 0x' + answer.hex())

#%% WARNING FUNCTIONS
    
    def successful_function(self):
        self.data_worker.finish_record()
        self.update_statistics_function()
        
        self.stop_timers_function()
        
        self.options.is_recording_mode = False
        self.options.save_directory = "None"                                                                    # Change the save directory on main variables dictionary
        
        print(self.options.record_time)
        text = str('Data acquisition completed successfully \n\n' +
                   'Duration: {}\n'.format(timedelta(seconds = round(self.options.record_time))))               # Text to be showed in warning message
        self.warning_message_function(text)                                                                     # Shows a warning message
        
        self.frequency_config_area.setEnabled(True)                                                             # Enables all the configuration tab
        self.channel_config_area.setEnabled(True)                                                               # Enables all the configuration tab                                                  
        self.record_config_area.setEnabled(True)                                                                # Enables all the configuration tab
        self.record_show_frame.setEnabled(False)                                                                # Disables the record tab
        self.tabWidget.setCurrentIndex(0)                                                                       # Changes to configuration tab                                                                          
        self.start_recording_button.setEnabled(True)                                                            # Returns the start recording button to the enable state
        self.plot_next_button.setEnabled(False)                                                                 # Returns the plot button to the disable state
        self.progress_bar.setValue(0)                                                                           # Returns the progress bar to 0%
        self.collected_data_lineshow.setText('0')                                                               # Returns the amount of samples collected line edit to 0     
        self.experiment_name_lineshow.setText("EXPERIMENT NAME")
    
    # This function creates the configuration resume message
    def resume_message_function(self):
        text = "Check the registration data:"                                                                   # Create a warning message
        message = str("Sampling frequency: "                 + 
                  str(self.options.sampling_frequency)       +
                  "Hz\nHigh pass filter cutoff frequency: "  + 
                  str(self.options.highpass)                 +
                  "Hz\nLow pass filter cutoff frequency: "   + 
                  str(self.options.lowpass)                  +  
                  "Hz\nNumber of recorded channels: "        + 
                  str(self.options.number_channels)          + 
                  "\nDuration "                              + 
                  str(self.options.days)      +    "d : "    +
                  str(self.options.hours)     +    "h : "    +   
                  str(self.options.minutes)   +    "m : "    + 
                  str(self.options.seconds)   +     "s"      + 
                  "\n\nDo you wish to continue?")                                                               # Create the resume message
        answer = self.option_message_function(text, message)                                                    # Show a warning pop-up
        return answer
 
    # This function show a warning pop-up
    def option_message_function(self, text, info_text):
        warning = QMessageBox(self.interface)                                                                   # Create the message box
        warning.setWindowTitle("Warning")                                                                       # Message box title
        warning.setText(text)                                                                                   # Message box text
        warning.setInformativeText(info_text)                                                                   # Message box text
        warning.setIcon(QMessageBox.Warning)                                                                    # Message box icon
        warning.setStyleSheet("QMessageBox{background:#353535;}QLabel{font:10pt/Century Gothic/;" + 
                              "font-weight:bold;}QPushButton{border:2px solid #A21F27;border-radius:8px;" +
                              "background-color:#2C53A1;color:#FFFFFF;font:10pt/Century Gothic/;" + 
                              "font-weight:bold;}QPushButton:pressed{border:2px solid #A21F27;" +
                              "border-radius:8px;background-color:#A21F27;color:#FFFFFF;}")
        warning.setStandardButtons(QMessageBox.Yes|QMessageBox.No)                                              # Message box buttons
        answer_yes = warning.button(QMessageBox.Yes)                                                            # Set the button "yes"
        answer_yes.setText('    YES    ')                                                                       # Rename the button "yes"
        answer_no = warning.button(QMessageBox.No)                                                              # Set the button "no"
        answer_no.setText('     NO      ')                                                                      # Rename the button "no"
        warning.exec_()                                                                                         # Execute the message box
        if warning.clickedButton() == answer_yes:                                                               # If the button "yes" is clicked
            return "yes"                                                                                        # Return "yes"
        else:                                                                                                   # If the button "no" is clicked
            return "no"                                                                                         # Return "no"
        
    # This function show a warning pop-up
    def warning_message_function(self, text):
        warning = QMessageBox(self.interface)                                                                   # Create the message box
        warning.setWindowTitle("Warning")                                                                       # Message box title
        warning.setText(text)                                                                                   # Message box text
        warning.setIcon(QMessageBox.Warning)                                                                    # Message box icon
        warning.setStyleSheet("QMessageBox{background:#353535;}QLabel{font:10pt/Century Gothic/;" +
                              "font-weight:bold;}QPushButton{border:2px solid #A21F27;border-radius:8px;" +
                              "background-color:#2C53A1;color:#FFFFFF;font:10pt/Century Gothic/;" +
                              "font-weight:bold;}QPushButton:pressed{border:2px solid #A21F27;" +
                              "border-radius:8px;background-color:#A21F27;color:#FFFFFF;}")
        warning.setStandardButtons(QMessageBox.Yes)                                                             # Message box buttons
        answer_yes = warning.button(QMessageBox.Yes)                                                            # Set the button "yes"
        answer_yes.setText('    OK    ')                                                                        # Rename the button "ok"
        warning.exec_()                                                                                         # Execute the message box

#%% TIMER FUNCTIONS

    def start_timers_function(self):
        '''
        This public function starts the user-programmed timer for the duration of the experiment.
        '''

        '''
        # TODO This function is not working properly. 
        It is not showing the correct time in at the end of the experiment.
        Find out why and fix it.
        '''

        self.timer = QTimer(self)                                                                               # Initializes the timer to end the data acquisition
        self.timer.setInterval(self.options.get_total_time()*1000)                                              # The timer is in milliseconds, so multiply the total time by 1000
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.successful_function)                                                    # Called when timer time is reached 
        
        self.directory_timer = QTimer(self)
        self.directory_timer.setInterval(int(3.6e6))
        self.directory_timer.setSingleShot(False)
        self.directory_timer.timeout.connect(self.change_direcotory_function)
        
        self.update_statistics_timer = QTimer(self)
        self.update_statistics_timer.setInterval(int(self.options.get_total_time()*50))
        self.update_statistics_timer.setSingleShot(False)
        self.update_statistics_timer.timeout.connect(self.update_statistics_function)

        self.update_statistics_timer.start()
        self.directory_timer.start()
        self.timer.start()
        
        self.start_time_estimate = time.perf_counter()                                                          # Gets the time to update the progress statistics
    
    def stop_timers_function(self):
        if self.options.is_recording_mode == True:
            self.timer.stop()                                                                                       # Stops the timer
            self.update_statistics_timer.stop()
            self.directory_timer.stop()
    
    def update_statistics_function(self):
        '''
        This public function is called when the "update statistics" button is clicked. It aims 
        to update the progress bar, the experiment time and estimate the amount of samples 
        acquired.
        '''
        self.record_time_estimate = round(time.perf_counter() - self.start_time_estimate)                       # Calculates the current acquisition time 
        self.run_time_lineshow.setText(str(timedelta(seconds=self.record_time_estimate)))                       # Changes the line edit (Record tab) in the interface
        
        if self.options.is_recording_mode == True:
            self.amount_data_estimate = self.record_time_estimate*self.options.sampling_frequency               # Estimates the total sample that should have been collected so far
            self.collected_data_lineshow.setText(str(round(self.amount_data_estimate)))                         # Shows the estimate in the line edit
            
            self.progress_bar_total = self.options.get_total_time()*self.options.sampling_frequency             # Expected total of samples
            self.progress_bar_porcentage = round((self.amount_data_estimate/self.progress_bar_total)*100)       # Updates the progress bar according to the estimate
            if self.progress_bar_porcentage <= 100:                                                             # If estimated progress is less than 100%
                self.progress_bar.setValue(self.progress_bar_porcentage)                                        # Updates the bar progress
            else:                                                                                               # If estimated progress is more than 100% 
                self.progress_bar.setValue(100)                                                                 # Updates the progress bar to 100%

#%% CONTOL FUNCTIONS
    
    def change_direcotory_function(self):
        self.data_worker.change_direcotory_function()

    def stop_function(self): 
        if self.stop_button.text() == "STOP":
            self.data_worker.stop_record()                                                                      # 
            self.stop_button.setText("START")
        else:
            self.data_worker.continue_record()                                                                  # 
            self.stop_button.setText("STOP")
    
    # Function to clear all selections made
    def clear_function(self):
        '''
        This public function is called when the clear button is clicked. All user selections 
        will be cleared
        '''
        text = "Do you want to clear all changes made?"                                                         # Text to be write in message box
        option = self.option_message_function(text, "")                                                         # Sets the message in message box
        if option == "yes":                                                                                     # If the user option is "yes"
            self.chip_combobox.setCurrentIndex(0)                                                               # Clears the chip selection
            self.sampling_frequency_slider.setValue(0)                                                          # Clears the sampling frequency selection
            self.highpass_frequency_slider.setValue(0)                                                          # Clears the high pass filter cutoff selection
            self.lowpass_frequency_slider.setValue(7)                                                           # Clears the low pass filter cutoff selection                     
            self.time_day_spinbox.setValue(0)                                                                   # Clears the days selction
            self.time_hour_spinbox.setValue(1)                                                                  # Clears the hours selection    
            self.time_min_spinbox.setValue(0)                                                                   # Clears the minutes selection
            self.time_sec_spinbox.setValue(0)                                                                   # Clears the seconds selection
            self.auto_save_button.setChecked(False)                                                             # Clears the auto save selection
            self.check_all_button.setText("Check All")                                                          # Clears the "Unchecked All" or "Check All" selection  
            self.chip_function()                                                                                # Calls the function to update the interface
            self.sampling_frequency_function()                                                                  # Calls the function to update the interface    
            self.highpass_frequency_function()                                                                  # Calls the function to update the interface
            self.lowpass_frequency_function()                                                                   # Calls the function to update the interface
            self.timed_record_function()                                                                        # Calls the function to update the interface
            self.check_all_function()                                                                           # Calls the function to update the interface 
        else:                                                                                                   # If the user option is "no"
            return                                                                                              # The program do nothing
       
    # Function to cancel the data acquisition     
    def cancel_function(self):
        self.data_worker.finish_record()                                                                        # Closes the usb port thread
        self.stop_timers_function()
                
        self.is_recording_mode = False
        self.options.save_directory = "None"                                                                    # Change the save directory on main variables dictionary
        
        text = str('Data acquisition has been canceled \n\n' +
                   'Duration: {}\n'.format(timedelta(seconds = round(self.options.record_time))))               # Text to be showed in warning message
        self.warning_message_function(text)                                                                     # Shows a warning message
        
        self.stop_button.setText("STOP")
        self.frequency_config_area.setEnabled(True)                                                             # Enables all the configuration tab
        self.channel_config_area.setEnabled(True)                                                               # Enables all the configuration tab                                                  
        self.record_config_area.setEnabled(True)                                                                # Enables all the configuration tab
        self.record_show_frame.setEnabled(False)                                                                # Disables the record tab
        self.tabWidget.setCurrentIndex(0)                                                                       # Changes to configuration tab                                                                          
        self.start_recording_button.setEnabled(True)                                                            # Returns the start recording button to the enable state
        self.plot_next_button.setEnabled(False)                                                                 # Returns the plot button to the disable state
        self.progress_bar.setValue(0)                                                                           # Returns the progress bar to 0%
        self.collected_data_lineshow.setText('0')                                                               # Returns the amount of samples collected line edit to 0  
        self.experiment_name_lineshow.setText("EXPERIMENT NAME")

    def cancel_advanced_function(self):
        self.frequency_config_area.setEnabled(True)                                                             # Enables all the configuration tab
        self.channel_config_area.setEnabled(True)                                                               # Enables all the configuration tab                                                  
        self.record_config_area.setEnabled(True)                                                                # Enables all the configuration tab
        self.advanced_frame.setEnabled(False)                                                                   # Disables the record tab
        self.command_message_lineedit.setText('Type here')
        self.command_answer_lineedit.setText('')
        self.tabWidget.setCurrentIndex(0)                                                                       # Changes to configuration tab                                                                          
        
    def closeEvent(self, event):                                                                    
        super(interface_visual_gui, self).closeEvent(event)                                                     # Defines the close event                                                             
        self.stop_timers_function()        
        try:                                                                                                    # Trys to close the view mode
            self.data_worker.finish_record()                                                                    # Closes the usb port thread
        except:                                                                                                # If the threads do not exists
            QCoreApplication.instance().quit                                                                    # Quits of the window                

    def plot_viewer_function(self):
        #self.plot_viewer.setDownsampling(ds=4, auto=True, mode='mean')
        
        self.plot_viewer.setBackground(None)
        self.plot_viewer.setLimits(xMin = 0, yMin = 0, xMax = 4, yMax = 33)
        self.plot_viewer.setXRange(0, 4, padding=0.0001)
        self.plot_viewer.setYRange(0, 33, padding=-0.001)
        
        y_axis = self.plot_viewer.getAxis('left')
        y_axis.setStyle(tickLength=0, showValues=True)
        
        x_axis = self.plot_viewer.getAxis('bottom')
        x_axis.setStyle(tickLength=10, showValues=True)
        
        label_style = {'family':'DejaVu Sans', 'color': '#969696', 'font-size': '10pt', 'font-weight': 'bold'}
        self.plot_viewer.setLabel('bottom', "Time [seconds]", **label_style)
        self.plot_viewer.setLabel('left', "Channels", **label_style)
        
        y_ticks_length = range(1,33)
        y_axis.setTicks([[(v, str(v)) for v in y_ticks_length]])

        font = QtGui.QFont()
        font.setPixelSize(10)
        font.setBold(True)
        font.setFamily("DejaVu Sans")
        x_ticks = self.plot_viewer.getAxis("bottom")
        y_ticks = self.plot_viewer.getAxis("left")
        x_ticks.setStyle(tickFont = font)
        y_ticks.setStyle(tickFont = font)
        x_ticks.setPen('#969696')
        y_ticks.setPen('#969696')
        x_ticks.setTextPen('#969696')
        y_ticks.setTextPen('#969696')
        x_ticks.setStyle(tickTextOffset = 10)
        y_ticks.setStyle(tickTextOffset = 10)

        range_ = self.plot_viewer.getViewBox().viewRange() 
        self.plot_viewer.getViewBox().setLimits(xMin=range_[0][0], xMax=range_[0][1], yMin=range_[1][0], yMax=range_[1][1])  

#%% INITIALIZANTION FUNCTION

def main(): 
  app = QtWidgets.QApplication(sys.argv)   # Create an instance of QtWidgets.QApplication
  window = interface_visual_gui()          # Create an instance of our class
  app.exec_()                              # Start the application
 
if __name__ == '__main__': 
  show = main()    

# app = QtWidgets.QApplication(sys.argv)
# app.setStyle("windows")
# window = Ui_NNC_InBrain()
# app.exec_()
    
    
    
    
    
