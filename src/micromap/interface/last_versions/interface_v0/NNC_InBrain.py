'''
Electrophysiological data acquisition system

This code is the visual configuration part of the electrophysiology recording 
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

Version 1.0.0
'''

import sys
import numpy
import serial
import serial.tools.list_ports
import time
import struct
import collections
import interface_functions
from itertools import cycle
from os import remove, path, SEEK_END
from datetime import datetime, timedelta
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QCoreApplication, Qt, QTimer
from PyQt5.QtWidgets import QMessageBox, QMainWindow
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from tkinter import Tk 
from tkinter.filedialog import (asksaveasfilename as save_dir_popup)


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
    
    def __init__(self, file, options, plot_viewer):                                                 # Initializes when the thread is started
        ''' 
        This private function is executed when the class is called, and all parameters are
        defined here
        '''
        super(plot_data_class, self).__init__()                                                     # Super declaration
        self.file = file                                                                            # Sets the file as self variable
        self.options = options                                                                      # Sets the options as self variable
        self.plot_viewer = plot_viewer                                                              # Sets the the interface plot widget as self variable
        self.channel_count = range(0, self.options.get_number_channels())                           # Creates a vector with the number of channels lenght
        self.circular_buffer_length = 5*self.options.get_sampling_frequency()                       # Number of samples to make a 5 seconds plot
                
        if self.options.get_save_directory() != "temp_data":                                        # If the interface is in recording mode
            self.data_length = 2*self.options.get_number_channels()*self.circular_buffer_length     # Total data length in bytes: every sample has 2 bytes per channel
            self.unpack_format = "<" + str(int(self.data_length/2)) + "H"                           # Format to struct.unpack( ) function reads the data 

        else:                                                                                       # If the interface is in view mode and not saving data
            self.samples = 0                                                                        # Sets the initial value to number of samples
            self.atualization_time = 1                                                              # Time in seconds to update the graph
            self.atualization_length = self.atualization_time*self.options.get_sampling_frequency() # Number of samples needed to update the graph in (atualization_time) seconds
            self.data_length = 2*self.options.get_number_channels()*self.atualization_length        # Total data length in bytes: every sample has 2 bytes per channel
            self.unpack_format = "<" + str(int(self.data_length/2)) + "H"                           # Format to struct.unpack( ) function reads the data 

            self.data_matrix = []                                                                   # Initializes the data matrix to be ploted
            for i in self.channel_count:                                                            # Creates a row in the matrix for each active channel 
                self.data_matrix.append(collections.deque(maxlen = self.circular_buffer_length))    # Creates 1 circular buffer to all channels with length of 5 seconds of record                             
    
    def run_recording(self):
        '''
        This public function will plot the last 5 seconds of record in the interface when the
        "PLOT THE LAST SAMPLES" was clicked
        '''       
        try:                                                                                        # This command prevents the interface from crashing     
            self.file.seek(-self.data_length, SEEK_END)                                             # Starting from the last sample, anchor the index to the last "n" samples
            self.data = self.file.read(self.data_length)                                            # Reads the last "n" samples of the file
            byte_data = struct.unpack(self.unpack_format, self.data)                                # Converts bytes read into integers
        
            self.data_matrix = numpy.reshape(byte_data, (self.options.get_number_channels(), 
                                                         self.circular_buffer_length), order="F")   # Transforms a "n" vector in a matrix with "number of channels" rows and "n"/"number of channels" columns
  
            self.plot_viewer.canvas.axes.cla()                                                      # Clears the last plot made in the interface
            for channel in self.channel_count:                                                      # Loop through all the rows of the matrix
                self.plot_viewer.canvas.axes.plot(channel + self.data_matrix[channel]/100)          # Plots the respective data and for each channel add the channel number for better visualization of the data 
                self.plot_viewer.canvas.draw_idle()                                                 # Draws on the interface
        except:                                                                                     # If one of the lines in "try" command doesn't works
            return                                                                                  # The program does nothing
            
    def run_view(self):
        '''
        This public function will plot the last 5 seconds of record on the interface in real 
        time, updating the values ​​every second
        '''
        self.samples = self.samples + 100                                                           # Every time that this function is called 1 sample is summed 
        if self.samples == self.atualization_length:                                                # If the sum reaches in the desired number of samples to update
            try:                                                                                    # This command prevents the interface from crashing                                                
                self.samples = 0                                                                    # Restart the count                                                           
                self.file.seek(-self.data_length, SEEK_END)                                         # Starting from the last sample, anchor the index to the last "n" samples                              
                self.data = self.file.read(self.data_length)                                        # Reads the last "n" samples of the file
                byte_data = struct.unpack(self.unpack_format, self.data)                            # Transforms a "n" vector in a matrix with "number of channels" rows and "n"/"number of channels" columns
                                   
                for sample, channel in zip(byte_data, cycle(self.channel_count)):                   # Cycles through all the bytes separating them every "number of channels" samples
                    self.data_matrix[channel].append((channel + 1 + sample/100))                    # Adds the values on the circular buffer
                
                self.plot_viewer.canvas.axes.cla()                                                  # Clears the last plot made in the interface
                for a in self.channel_count:                                                        # Loop through all the rows of the matrix
                    self.plot_viewer.canvas.axes.plot(list(self.data_matrix[a]))                    # Plots the respective data and for each channel add the channel number for better visualization of the data 
                    self.plot_viewer.canvas.draw_idle()                                             # Draws on the interface
            except:                                                                                 # If one of the lines in "try" command doesn't works
                return                                                                              # The program does nothing
            
    def stop(self):
        '''
        This public function will emit the command to finish the thread 
        '''
        self.finished.emit()                                                                        # Emits the finish signal
    
class receive_data_class(QObject):
    ''' 
    This class is a worker that will be inserted into a Thread. The functions of this class
    are the most important for the operation of the interface system, they are where the 
    interface will connect to the arduino and read the data sent via UART.
    
    Parameters:
        - file ........... Open file in which the records are being saved
        - option ......... The option dictionary that contains all record configurations
    '''
    finished = pyqtSignal()                                                                         # Signal that will be output to the interface when the function is complited
    progress = pyqtSignal()                                                                         # Signal that will be output to the interface to reposrt the progress of the data acquisition 
    
    def __init__(self, file, usb, options):
        ''' 
        This private function is executed when the class is called, and all parameters are 
        defined here
        '''
        super(receive_data_class, self).__init__()                                                  # Super declaration
        self.file = file                                                                            # Sets the file as self variable
        self.usb = usb
        self.options = options                                                                      # Sets the options as self variable
        
        #connection_ok = self.usb.identification()
        #print(connection_ok)
        #self.serial_port.timeout = 1                                                               # The maximum time to try get a data 
        
        
    def run_recording(self):
        '''
        This public function will read the data being sent by the USB acquisition system when 
        recording mode is active. This is the most simple and faster function to read UART 
        datas.  
        '''
        self._is_running = True                                                                     # Signal that allows the while loop to be started     
        
        self.start_time = time.perf_counter()                                                       # Sets the start time of the experiment
        while self._is_running == True:                                                             # While _isRunning is True
            if self.usb.port.inWaiting() > 0:                                                       # If has any data in UART buffer waiting to be read
                self.file.write(self.usb.port.read(6400))                                           # Read 64 bytes (1 sample) and write them to the binary file
        self.options.set_record_time(time.perf_counter() - self.start_time)                         # Share if the interface the total time of record
                
        self.file.close()                                                                           # Closes the binary file
        self.finished.emit()                                                                        # Emits the finish signal
    
    def run_view(self):
        '''
        This public function will read the data being sent by the USB acquisition system when
        recording mode is active. The difference from the previous one is that with each sample, 
        a progress signal will be sent to the interface (this operation decreases the progress 
        frequency a little).  
        '''
        
        #acquisition_ok = self.usb.request_acquisition()                                             # Command to statr the data acquisition    
        #print(acquisition_ok)
        
        self._is_running = True                                                                     # Signal that allows the while loop to be started

        self.start_time = time.perf_counter()                                                       # Sets the start time of the experiment
        while self._is_running == True:                                                             # While _isRunning is True
            if self.usb.port.inWaiting() > 0:                                                       # If has any data in UART buffer waiting to be read
                self.file.write(self.usb.port.read(6400))                                           # Read 64 bytes (1 sample) and write them to the binary file
                self.progress.emit()                                                                # Emits the progress signal to update the graph in the interface
        self.options.set_record_time(time.perf_counter() - self.start_time)                         # Share with the interface the total time of record  
        
        self.file.close()                                                                           # Closes the binary file
        self.finished.emit()                                                                        # Emits the finish signal
                
    def stop(self):
        '''
        This public function will break the while loop causing the finish signal to be emitted
        '''
        self._is_running = False                                                                    # Signal that breaks the while loop

class Ui_NNC_InBrain(QMainWindow):
    '''
    This class contains all the commands of the interface as well as the constructors of the 
    interface itself.
    '''
    def __init__(self):
        '''
        This private function calls the interface of a .ui file created in Qt Designer, starts 
        the dictionaries that contain the desired settings for the registry, and makes the 
        connections between the user's activities and their respective functions.
        '''
        super(Ui_NNC_InBrain, self).__init__()                                                      # Calls the inherited classes __init__ method
        QMainWindow.__init__(self)                                                                  # Creates the main window
        self.interface = uic.loadUi("NNC_InBrain_GUI.ui", self)                                     # Loads the interface design archive (made in Qt Designer)
        
        self.nav = NavigationToolbar(self.plot_viewer.canvas, self)                                 # Creates a navigation toolbar to command the plot
        self.nav.setMaximumWidth(20)                                                                # Sets the width of the navigation toolbar
        self.nav.setStyleSheet("QToolBar{background-color:#969696;border:0px}")                     # Sets the style of the navigation toolbar
        self.addToolBar(Qt.RightToolBarArea, self.nav)                                              # Puts the navigation toolbar on the right side of the interface
        
        self.show()                                                                                 # Shows the interface to the user

        # INTERFCE DEFAULT OPTIONS
        # This dictionary is the output variable of the interface to start the record
        self.options = interface_functions.acquisition()

        # INTERFACE INTERACTIONS
        # Record configuration interactions
        self.chip_combobox.currentIndexChanged.connect(self.chip_function)                          # Called when chip combobox is changed
        self.method_combobox.currentIndexChanged.connect(self.method_function)                      # Called when method combobox is changed
        self.usb_port.clicked.connect(self.usb_port_function)                                       # Called when the update USB button is clicked
        self.usb_port_combobox.currentIndexChanged.connect(self.usb_selection_function)             # Called when the USB combo box is changed
        self.sampling_frequency_slider.valueChanged[int].connect(self.sampling_frequency_function)  # Called when sampling frequency slider is changed
        self.highpass_frequency_slider.valueChanged[int].connect(self.highpass_frequency_function)  # Called when high pass cutoff frequency slider is changed
        self.lowpass_frequency_slider.valueChanged[int].connect(self.lowpass_frequency_function)    # Called when low pass cutoff frequency slider is changed
        self.start_recording_button.clicked.connect(self.start_recording_mode_function)             # Called when the start recording button is clicked
        # General interface interactions
        self.check_all_button.clicked.connect(self.check_all_function)                              # Called when "check/uncheck all" button is clicked
        self.clear_button.clicked.connect(self.clear_function)                                      # Called when the clear button is clicked
        self.cancel_button.clicked.connect(self.cancel_function)                                    # Called when the cancel button is clicked
        self.record_button.clicked.connect(self.start_view_mode_function)                           # Called when the clear button is clicked 
        self.plot_next_button.clicked.connect(self.plot_recording_mode_function)                    # Called when the "plot the last samples" button is clicked
        self.update_statistics_button.clicked.connect(self.update_statistics_function)              # Called when the "update statistics" button is clicked
        self.timer = QTimer()                                                                       # Initializes the timer to end the data acquisition
        self.timer.timeout.connect(self.successful_function)                                        # Called when timer time is reached 
               
    def record_timer_function(self):
        '''
        This public function starts the user-programmed timer for the duration of the experiment.
        '''        
        self.timer.start(self.options.get_total_time()*1000)                                        # The timer is in milliseconds, so multiply the total time by 1000
    
    def update_statistics_function(self):
        '''
        This public function is called when the "update statistics" button is clicked. It aims 
        to update the progress bar, the experiment time and estimate the amount of samples 
        acquired.
        '''
        self.record_time_estimate = time.perf_counter() - self.start_time_estimate                      # Calculates the current acquisition time 
        
        self.run_time_lineshow.setText(str(timedelta(seconds=round(self.record_time_estimate))))        # Changes the line edit (Record tab) in the interface
        self.amount_data_estimate = self.record_time_estimate*self.options.get_sampling_frequency()     # Estimates the total sample that should have been collected so far
        self.collected_data_lineshow.setText(str(round(self.amount_data_estimate)))                     # Shows the estimate in the line edit
        
        self.progress_bar_total = self.options.get_total_time()*self.options.get_sampling_frequency()   # Expected total of samples
        self.progress_bar_porcentage = round((self.amount_data_estimate/self.progress_bar_total)*100)   # Updates the progress bar according to the estimate
        if self.progress_bar_porcentage <= 100:                                                         # If estimated progress is less than 100%
            self.progress_bar.setValue(self.progress_bar_porcentage)                                    # Updates the bar progress
        else:                                                                                           # If estimated progress is more than 100% 
            self.progress_bar.setValue(100)                                                             # Updates the progress bar to 100%

        
    # Function to set the data aquisition system
    def method_function(self):
        '''
        This public function is called when the acquisition method is changed by the user.
        '''
        method = self.method_combobox.currentIndex()                                                # Gets the combo box index
        if method == 0:                                                                             # If is selected FPGA
            self.options.set_method("ARDUINO")                                                      # Changes the method on main variables dictionary
            self.method_lineshow.setText("ARDUINO")                                                 # Changes the line edit (Record tab) in the interface
        # elif method == 1:                                                                           # If is selected ARDUINO    
        #     self.options.set_method("FPGA")                                                         # Changes the method on main variables dictionary 
        #     self.method_lineshow.setText("FPGA")                                                    # Changes the line edit (Record tab) in the interface

        # elif method == 2:                                                                           # If is selected PI PICO
        #     self.options.set_method("PI PICO")                                                      # Changes the method on main variables dictionary
        #     self.method_lineshow.setText("PI PICO")                                                 # Changes the line edit (Record tab) in the interface
    
    # Function to set what chip will be used
    def chip_function(self):
        '''
        This public function is called when the acquisition chip is changed by the user.
        '''
        chip = self.chip_combobox.currentIndex()                                                    # Gets the combo box index
        if chip == 0:                                                                               # If is selected RHD2216
            self.highpass_frequency_slider.setEnabled(True)                                         # Enables high pass filter cutting frequency slider 
            self.highpass_frequency_function()                                                      # Calls the frequency function to update the information
            self.lowpass_frequency_slider.setEnabled(True)                                          # Enables low pass filter cutting frequency slider
            self.lowpass_frequency_function()                                                       # Calls the frequency function to update the information
            self.channel_16_area.setEnabled(True)                                                   # Enables channels 09 - 16        
            self.channel_32_area.setEnabled(False)                                                  # Disables channels 17 - 32
            self.options.set_chip("RHD2216")                                                        # Changes the chip on main variables dictionary 
            self.chip_lineshow.setText("RHD2216")                                                   # Changes the line edit (Record tab) in the interface
        elif chip == 1:                                                                             # If is selected RHD2132    
            self.highpass_frequency_slider.setEnabled(True)                                         # Enables high pass filter cutting frequency slider
            self.highpass_frequency_function()                                                      # Calls the frequency function to update the information
            self.lowpass_frequency_slider.setEnabled(True)                                          # Enables low pass filter cutting frequency slider 
            self.lowpass_frequency_function()                                                       # Calls the frequency function to update the information
            self.channel_16_area.setEnabled(True)                                                   # Enables channels 09 - 16
            self.channel_32_area.setEnabled(True)                                                   # Enables channels 17 - 32
            self.options.set_chip("RHD2132")                                                        # Changes the chip on main variables dictionary
            self.chip_lineshow.setText("RHD2132")                                                   # Changes the line edit (Record tab) in the interface
        elif chip == 2:                                                                             # If is selected ADS1298
            self.highpass_frequency_slider.setEnabled(False)                                        # Disables high pass filter cutting frequency slider
            self.highpass_frequency_lineshow.setText("--")                                          # Changes the line edit (Record tab) in the interface                        
            self.lowpass_frequency_slider.setEnabled(False)                                         # Disables low pass filter cutting frequency slider
            self.lowpass_frequency_lineshow.setText("--")                                           # Changes the line edit (Record tab) in the interface   
            self.channel_16_area.setEnabled(False)                                                  # Disables channels 09 - 16
            self.channel_32_area.setEnabled(False)                                                  # Disables channels 17 - 32
            self.options.set_chip("ADS1298")                                                        # Changes the chip on main variables dictionary
            self.chip_lineshow.setText("ADS1298")                                                   # Changes the line edit (Record tab) in the interface
    
    # Function to set the sampling frequency
    def sampling_frequency_function(self):
        '''
        This public function is called when the sampling frequency is changed by the user.
        '''
        sampling_frequency_index = self.sampling_frequency_slider.value()                           # Gets the slider index
        if self.options.get_method() == "ARDUINO" and sampling_frequency_index <= 1:                # If an ARDUINO is being used and the sampling frequency is less than or equal to 2KHz
            self.options.set_sampling_frequency(sampling_frequency_index)                           # Changes the option in the acquisition object
            sampling_frequency = self.options.get_sampling_frequency()                              # Gets from the acquisition object the sampling frequnecy option
            self.sampling_frequency_lineedit.setText(str(sampling_frequency))                       # Changes the line edit in the interface
            self.sampling_frequency_lineshow.setText(str(sampling_frequency))                       # Changes the line edit (Record tab) in the interface
        else:
            text = "The ARDUINO does not perform data acquisitions with more than 2000 Hz"          # Creates a warning message
            self.warning_message_function(text)                                                     # Shows warning pop-up      
            self.sampling_frequency_slider.setValue(sampling_frequency_index - 1)                   # Returns to the previus slider value
        
    # Function to set the high pass filter cutoff frequency
    def highpass_frequency_function(self):
        '''
        This public function is called when the high pass filter cutoff frequency is changed 
        by the user.
        '''
        highpass_frequency_index = self.highpass_frequency_slider.value()                           # Gets the slider index
        self.options.set_highpass(highpass_frequency_index)                                         # Changes the option in the acquisition object
        if self.options.get_highpass() < self.options.get_lowpass():                                # If LP is greater than HP
            self.highpass_frequency_lineedit.setText(str(self.options.get_highpass()))              # Changes the line edit in the interface
            self.highpass_frequency_lineshow.setText(str(self.options.get_highpass()))              # Changes the line edit (Record tab) in the interface
        else:                                                                                       # If HP is greater than LP
            text = "The cutoff frequency of the high pass filter cannot be \
                    greater than the cutoff frequency of the low pass filter"                       # Creates a warning message
            self.warning_message_function(text)                                                     # Shows warning pop-up
            self.highpass_frequency_slider.setValue(highpass_frequency_index - 1)                   # Returns to the previus slider value
            self.options.set_highpass(highpass_frequency_index - 1)                                 # Returns to the previus high pass frequency   
        
    # Function to set the low pass filter cutoff frequency
    def lowpass_frequency_function(self):
        '''
        This public function is called when the low pass filter cutoff frequency is changed
        by the user.
        '''
        lowpass_frequency_index = self.lowpass_frequency_slider.value()                             # Gets the slider index
        self.options.set_lowpass(lowpass_frequency_index)                                           # Changes the option in the acquisition object
        if self.options.get_lowpass() > self.options.get_highpass():                                # If HP is greater than LP
            self.lowpass_frequency_lineedit.setText(str(self.options.get_lowpass()))                # Changes the line edit in the interface
            self.lowpass_frequency_lineshow.setText(str(self.options.get_lowpass()))                # Changes the line edit (Record tab) in the interface
        else:           
            text = "The cutoff frequency of the high pass filter cannot be \
                    greater than the cutoff frequency of the low pass filter"                       # Creates a warning message
            self.warning_message_function(text)                                                     # Shows warning pop-up
            self.lowpass_frequency_slider.setValue(lowpass_frequency_index + 1)                     # Returns to the previus slider value
            self.options.set_lowpass(lowpass_frequency_index + 1)                                   # Returns to the previus low pass frequency   
                      
    # Function to check and uncheck the channels radio buttuns
    def check_all_function(self):
        '''
        This public function is called when uncheck/check button is clicked. 
        '''
        check_all = self.check_all_button.text()                                                    # Gets the current text in the button
        if check_all == "Uncheck All":
            self.C01_button.setChecked(False)                                                       # Sets unchecked the corresponding channel                                   
            self.C02_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C03_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C04_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C05_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C06_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C07_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C08_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C09_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C10_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C11_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C12_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C13_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C14_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C15_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C16_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C17_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C18_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C19_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C20_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C21_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C22_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C23_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C24_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C25_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C26_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C27_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C28_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C29_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C30_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C31_button.setChecked(False)                                                       # Sets unchecked the corresponding channel 
            self.C32_button.setChecked(False)                                                       # Sets unchecked the corresponding channel
            self.check_all_button.setText("Check All")                                              # Changes the text in Check/Uncheck button
        else:
            self.C01_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C02_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C03_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C04_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C05_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C06_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C07_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C08_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C09_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C10_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C11_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C12_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C13_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C14_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C15_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C16_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C17_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C18_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C19_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C20_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C21_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C22_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C23_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C24_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C25_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C26_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C27_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C28_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C29_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C30_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C31_button.setChecked(True)                                                        # Sets checked the corresponding channel  
            self.C32_button.setChecked(True)                                                        # Sets checked the corresponding channel
            self.check_all_button.setText("Uncheck All")                                            # Changes the text in Check/Uncheck button
            
    # This function sets the record time 
    def time_record_function(self):
        '''
        This public function is called when the registration button is clicked. Here the 
        time settings selected by the user will be changed in the options dictionaries 
        and the total acquisition time will be calculated
        '''
        now = datetime.now()                                                                        # Gets the current day and hour
        start_date = now.strftime("%d/%m/%Y %H:%M:%S")                                              # Formats the string with the current day and hour
        self.start_duration_lineshow.setText(start_date)                                            # Changes the line edit (Record tab) in the interface

        self.options.set_days(int(self.time_day_spinbox.text()))                                    # Changes the days option in the acquisition object
        self.options.set_hours(int(self.time_hour_spinbox.text()))                                  # Changes the hours option in the acquisition object
        self.options.set_minutes(int(self.time_min_spinbox.text()))                                 # Changes the minutes option in the acquisition object
        self.options.set_seconds(int(self.time_sec_spinbox.text()))                                 # Changes the seconds option in the acquisition object
        
        self.duration_time_lineshow.setText(str(timedelta(seconds=self.options.get_total_time())))  # Changes the line edit (Record tab) in the interface

    # This public function defines the channels to be sampled
    def channels_function(self):
        '''
        This public function is called when the registration button is clicked. Here 
        the active channels will be identified, organized in a list that will be passed 
        to the option dictionaries
        '''
        channels = []
        channels.append(self.C01_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C02_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C03_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C04_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C05_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C06_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C07_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C08_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C09_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C10_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C11_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C12_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C13_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C14_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C15_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C16_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C17_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C18_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C19_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C20_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C21_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C22_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C23_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C24_button.isChecked())                                                # Checks if a certain channel is active (True or False)        
        channels.append(self.C25_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C26_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C27_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C28_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C29_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C30_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C31_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        channels.append(self.C32_button.isChecked())                                                # Checks if a certain channel is active (True or False)
        
        channels = numpy.multiply(channels, 1)                                                      # Transforms "True" in 1 and "False" in 0
        self.options.set_channels(channels)                                                         # Changes the channels option in the acquisition object
        self.number_channels_lineshow.setText(str(self.options.get_number_channels()))              # Changes the line edit (Record tab) in the interface

    # Function to clear all selections made
    def clear_function(self):
        '''
        This public function is called when the clear button is clicked. All user selections 
        will be cleared
        '''
        text = "Do you want to clear all changes made?"                                             # Text to be write in message box
        option = self.option_message_function(text, "")                                             # Sets the message in message box
        if option == "yes":                                                                         # If the user option is "yes"
            self.chip_combobox.setCurrentIndex(0)                                                   # Clears the chip selection
            self.sampling_frequency_slider.setValue(0)                                              # Clears the sampling frequency selection
            self.highpass_frequency_slider.setValue(0)                                              # Clears the high pass filter cutoff selection
            self.lowpass_frequency_slider.setValue(7)                                               # Clears the low pass filter cutoff selection                     
            self.time_day_spinbox.setValue(0)                                                       # Clears the days selction
            self.time_hour_spinbox.setValue(1)                                                      # Clears the hours selection    
            self.time_min_spinbox.setValue(0)                                                       # Clears the minutes selection
            self.time_sec_spinbox.setValue(0)                                                       # Clears the seconds selection
            self.auto_save_button.setChecked(False)                                                 # Clears the auto save selection
            self.check_all_button.setText("Check All")                                              # Clears the "Unchecked All" or "Check All" selection  
            self.chip_function()                                                                    # Calls the function to update the interface
            self.sampling_frequency_function()                                                      # Calls the function to update the interface    
            self.highpass_frequency_function()                                                      # Calls the function to update the interface
            self.lowpass_frequency_function()                                                       # Calls the function to update the interface
            self.timed_record_function()                                                            # Calls the function to update the interface
            self.check_all_function()                                                               # Calls the function to update the interface 
        else:                                                                                       # If the user option is "no"
            return                                                                                  # The program do nothing
     
    def usb_port_function(self):
        '''
        This public function will identify the USB ports connected to the computer, show 
        them to the user and configure the options dictionary.
        '''
        self.usb_selection_enable = 0                                                               # This variable identifies whether the port update button has already been clicked
        self.usb_port_combobox.clear()                                                              # Clears the combo box with the USB options
        self.online_ports = []                                                                      # Initializes the list that will contain the USB port options
        ports = serial.tools.list_ports.comports()                                                  # Gets all ports connected to the computer
        for port, desc, hwid in sorted(ports):                                                      # From the identified ports 
            self.usb_port_combobox.addItem("{}: {}".format(port, desc))                             # Gets the port and name of the connected device
            self.online_ports.append(port)                                                          # Adds the ports in the list
        if len(self.online_ports) != 0:                                                             # If ports were found 
            self.usb_selection_enable = 1                                                           # Changes the indentification variable 
            self.usb_selection_function()                                                           # Calls the function to configure the USB ports in dictionary
        else:                                                                                       # If no ports were found
            self.options.set_usb_port("None")                                                       # Puts "None" in option dictionary 
            return
    
    def usb_selection_function(self):
        '''
        This public function is auxiliary to the cime function and identifies changes in 
        the combo box
        '''
        if self.usb_selection_enable == 1:                                                          # If the USB connections were updated at least 1 time and ports were found
            usb_selected = self.online_ports[self.usb_port_combobox.currentIndex()]                 # Gets the port selected by the user
            self.options.set_usb_port(usb_selected)                                                 # # Changes the USB port option in the acquisition object
    
    # This function is the interface output, where the program will start to sampling 
    def start_view_mode_function(self):
        '''
        This public function is called when the record button is clicked. 
        '''
        self.time_record_function()                                                                 # Calls the function to define the record time 
        self.channels_function()                                                                    # Calls the function to define the channels that will be sampled 
        if self.experiment_name_lineedit.text() == "Type here":                                     # If the experiment name was not entered 
            text = str("Put the name of the experiment you want to do the data acquisition")        # Text to be showed in warning message
            self.warning_message_function(text)                                                     # Shows a warning message
            self.experiment_name_lineedit.setStyleSheet("QLineEdit{background-color:#A21F27}")      # Changes the color of the experiment name line edit
            return                                                                                  # The program do nothing
        else:
            self.experiment_name_lineshow.setText(self.experiment_name_lineedit.text())             # Changes the experiment name in record tab
            self.experiment_name_lineedit.setStyleSheet("QLineEdit{background-color:#606060}")      # Changes the color of the experiment name line edit 
        
        if self.options.get_usb_port() == "None":                                                   # If none USB port was founded
            self.warning_message_function("Please select a valid USB port")                         # Shows a warning message
            return                                                                                  # The program do nothing
        
        answer = self.resume_message_function()                                                     # Calls a function to create the configuration resume message
        if answer == "yes":                                                                         # If the user option is "yes"     
            # try:                                                                                    # Trys to execute the communication function
            self.view_mode_function()                                                           # Calls the commmunication function to open the data acquisition thread
            # except:
            #     text = str('The interface failed to try to start the threads responsible' +
            #                ' for signal acquisition. Try starting the record again, if the' +
            #                ' error persists, restart the interface')                                # Message to be displeyed
            #     self.warning_message_function(text)                                                 # Shows a warning message
            #     return                                                                              # The program do nothing
            
            text = str('VIEW MODE\nSignals are being collected and plotted but data is not' +
                       ' being saved. To switch to "recording mode" and start saving the data,' +
                       ' click "START RECORDING"')                                                  # Message to be displeyed
            self.show_record_textedit.setText(text)                                                 # Displays a message in the edit line of the interface                                  
            self.frequency_config_area.setEnabled(False)                                            # Disables all the configuration tab
            self.channel_config_area.setEnabled(False)                                              # Disables all the configuration tab
            self.record_config_area.setEnabled(False)                                               # Disables all the configuration tab
            self.record_show_frame.setEnabled(True)                                                 # Enables all the configuration tab
            self.tabWidget.setCurrentIndex(1)                                                       # Changes to record tab      
        else:                                                                                       # If the user option is "no"
            return                                                                                  # The program do nothing
         
    def view_mode_function(self):
        self.file = open(self.options.get_save_directory(), "w+b")                                  # Opens or create the file to write and read data
        self.usb = interface_functions.usb_singleton(self.options.get_usb_port(), 50000000)
        self.usb.connect()
        
        self.plot_view_thread = QThread()                                                           # Creates a QThread object to plot the received data
        self.plot_view_worker = plot_data_class(self.file, self.options, self.plot_viewer)          # Creates a worker object named plot_data_class
        self.plot_view_worker.moveToThread(self.plot_view_thread)                                   # Moves the class to the thread
        self.plot_view_worker.finished.connect(self.plot_view_thread.quit)                          # When the process is finished, this command quits the worker
        self.plot_view_worker.finished.connect(self.plot_view_thread.wait)                          # When the process is finished, this command waits the worker to finish completely
        self.plot_view_worker.finished.connect(self.plot_view_worker.deleteLater)                   # When the process is finished, this command deletes the worker
        self.plot_view_thread.finished.connect(self.plot_view_thread.deleteLater)                   # When the process is finished, this command deletes the thread
        self.plot_view_thread.start()                                                               # Starts the thread
        
        self.data_view_thread = QThread()                                                           # Creates a QThread object to receive USB data
        self.data_view_worker = receive_data_class(self.file, self.usb, self.options)               # Creates a worker object named receive_data_class
        self.data_view_worker.moveToThread(self.data_view_thread)                                   # Moves worker to the thread
        self.data_view_thread.started.connect(self.data_view_worker.run_view)                       # If the thread was started, connect to worker.run_view       
        self.data_view_worker.progress.connect(self.plot_view_mode_function)                        # If the thread emit a progress signal, connect to plot_view_mode_function
        self.data_view_worker.finished.connect(self.data_view_thread.quit)                          # When the process is finished, this command quits the worker
        self.data_view_worker.finished.connect(self.data_view_thread.wait)                          # When the process is finished, this command waits the worker to finish completely
        self.data_view_worker.finished.connect(self.data_view_worker.deleteLater)                   # When the process is finished, this command deletes the worker
        self.data_view_thread.finished.connect(self.data_view_thread.deleteLater)                   # When the process is finished, this command deletes the thread       
        self.data_view_thread.finished.connect(self.usb.disconnect)                                 #        
        self.start_time_estimate = time.perf_counter()                                              # Gets the time to update the progress statistics
        self.data_view_thread.start()                                                               # Starts the thread     
    
    def plot_view_mode_function(self):
        try:
            self.plot_view_worker.run_view()                                                        # Runs the time function every progress signal from the thread
        except:
            text = str('\nWARNING: The interface failed when trying to reproduce the graph' +
                       '\nError type: ' + sys.exc_info()[0])                                        # Message to be displeyed
            self.show_record_textedit.insertText(text)                                              # Displays a message in the edit line of the interface
    
    def start_recording_mode_function(self):
        self.data_view_worker.stop()                                                                # Closes the usb port thread
        self.plot_view_worker.stop()                                                                # Closes the plot thread
        
        try:                                                                    
            remove(self.options.get_save_directory())                                               # Deletes the temporary data file    
        except:
            time.sleep(1)                                                                           # Wait for the thread to finish executing
            remove(self.options.get_save_directory())                                               # Deletes the temporary data file 
        
        try:
            Tk().withdraw()                                                                         # Hide a Tk window
            save_directory = save_dir_popup(filetypes=(("Save file","*.bin"),("All files","*")))    # Opens the computer directorys to chose the save file
            self.options.set_save_directory(save_directory)                                         # Changes the save directory on main variables dictionary
        except:
            text = str('\nWARNING: The interface failed to create the binary file,' + 
                       ' please select a valid directory\nError type: ') + sys.exc_info()[0]        # Message to be displeyed
            self.show_record_textedit.insertPlainText(text)                                         # Displays a message in the edit line of the interface
            return
                    
        try:
            self.recording_mode_function()                                                          # Restart the acquisition and plot threads
        except:
            text = str('\nWARNING: The interface failed to try to start the threads responsible' +
                       ' for signal acquisition\nError type: ') + sys.exc_info()[0]                 # Message to be displeyed
            self.show_record_textedit.setText(text)                                                 # Displays a message in the edit line of the interface
            return
        
        self.plot_next_button.setEnabled(True)                                                      # Enables the button to plot the last values acquired
        self.start_recording_button.setEnabled(False)                                               # Disables the strat recording button
        text = str('RECORDING MODE\nSignals are being collected and data is being saved.')          # Message to be displeyed
        self.show_record_textedit.setText(text)                                                     # Displays a message in the edit line of the interface
    
    def recording_mode_function(self):
        self.file = open(self.options.get_save_directory(), "w+b")                                  # Opens or create the file to write and read data
        self.usb = interface_functions.usb_singleton(self.options.get_usb_port(), 50000000)
        self.usb.connect()
        
        self.plot_recording_thread = QThread()                                                      # Creates a QThread object to plot the received data
        self.plot_recording_worker = plot_data_class(self.file, self.options, self.plot_viewer)     # Creates a worker object named plot_data_class
        self.plot_recording_worker.moveToThread(self.plot_recording_thread)                         # Moves the class to the thread
        self.plot_recording_worker.finished.connect(self.plot_recording_thread.quit)                # When the process is finished, this command quits the worker
        self.plot_recording_worker.finished.connect(self.plot_recording_thread.wait)                # When the process is finished, this command waits the worker to finish completely
        self.plot_recording_worker.finished.connect(self.plot_recording_worker.deleteLater)         # When the process is finished, this command deletes the worker
        self.plot_recording_thread.finished.connect(self.plot_recording_thread.deleteLater)         # When the process is finished, this command deletes the thread
        self.plot_recording_thread.start()                                                          # Starts the thread
        
        self.data_recording_thread = QThread()                                                      # Creates a QThread object to receive USB data
        self.data_recording_worker = receive_data_class(self.file, self.usb, self.options)          # Creates a worker object named receive_data_class
        self.data_recording_worker.moveToThread(self.data_recording_thread)                         # Moves worker to the thread 
        self.data_recording_thread.started.connect(self.data_recording_worker.run_recording)        # If the thread was started, connect to worker.run
        self.data_recording_worker.finished.connect(self.data_recording_thread.quit)                # When the process is finished, this command quits the worker
        self.data_recording_worker.finished.connect(self.data_recording_thread.wait)                # When the process is finished, this command waits the worker to finish completely
        self.data_recording_worker.finished.connect(self.data_recording_worker.deleteLater)         # When the process is finished, this command deletes the worker
        self.data_recording_thread.finished.connect(self.data_recording_thread.deleteLater)         # When the process is finished, this command deletes the thread
        self.data_recording_thread.finished.connect(self.usb.disconnect)                            # 
        self.record_timer_function()                                                                # Starts user programmed timer        
        self.start_time_estimate = time.perf_counter()                                              # Gets the time to update the progress statistics
        self.data_recording_thread.start()                                                          # Starts the thread     
    
    def plot_recording_mode_function(self):
        try:
            self.plot_recording_worker.run_recording()                                              # Runs the plot function one time
        except:
            text = str('\nWARNING: The interface failed when trying to reproduce the graph' +
                       '\nError type: ') + sys.exc_info()[0]                                        # Message to be displeyed
            self.show_record_textedit.insertText(text)                                              # Displays a message in the edit line of the interface
    
    def successful_function(self):
        self.update_statistics_function()
        
        self.timer.stop()                                                                           # Stops the timer
        self.data_recording_worker.stop()                                                           # Closes the usb port thread
        self.plot_recording_worker.stop()                                                           # Closes the plot thread
        
        self.real_data_size = path.getsize(self.options.get_save_directory())                       # Gets the size of the recorded file until the acquisition is canceled 
        self.options.set_save_directory("temp_data")                                                # Change the save directory on main variables dictionary
        
        text = str('Data acquisition completed successfully \n\n' +
                'Duration: {}\n'.format(timedelta(seconds = self.options.get_record_time())) +
                'Data size: {} bytes\n'.format(self.real_data_size))                                # Text to be showed in warning message
        self.warning_message_function(text)                                                         # Shows a warning message
        
        self.frequency_config_area.setEnabled(True)                                                 # Enables all the configuration tab
        self.channel_config_area.setEnabled(True)                                                   # Enables all the configuration tab                                                  
        self.record_config_area.setEnabled(True)                                                    # Enables all the configuration tab
        self.record_show_frame.setEnabled(False)                                                    # Disables the record tab
        self.tabWidget.setCurrentIndex(0)                                                           # Changes to configuration tab                                                                          
        self.start_recording_button.setEnabled(True)                                                # Returns the start recording button to the enable state
        self.plot_next_button.setEnabled(False)                                                     # Returns the plot button to the disable state
        self.progress_bar.setValue(0)                                                               # Returns the progress bar to 0%
        self.collected_data_lineshow.setText('0')                                                   # Returns the amount of samples collected line edit to 0     

    
    # Function to cancel the data acquisition     
    def cancel_function(self):
        self.timer.stop()                                                                           # Stops the timer
        if self.options.get_save_directory() == "temp_data":                                                                                        # Trys to close the view mode
            self.data_view_worker.stop()                                                            # Closes the usb port thread
            self.plot_view_worker.stop()                                                            # Closes the plot thread
        else:                                                                                       # Trys to close the recording mode
            self.data_recording_worker.stop()                                                       # Closes the usb port thread
            self.plot_recording_worker.stop()                                                       # Closes the plot thread
        
        self.real_data_size = path.getsize(self.options.get_save_directory())                       # Gets the size of the recorded file until the acquisition is canceled 
         
        if self.options.get_save_directory() == "temp_data":
             try:                                                                    
                 remove(self.options.get_save_directory())                                          # Deletes the temporary data file    
             except:
                 time.sleep(1)                                                                      # Wait for the thread to finish executing
                 remove(self.options.get_save_directory())                                          # Deletes the temporary data file 
        
        self.options.set_save_directory("temp_data")                                                # Change the save directory on main variables dictionary
        
        text = str('Data acquisition has been canceled \n\n' +
                   'Duration: {}\n'.format(timedelta(seconds = self.options.get_record_time())) +
                   'Data size: {} bytes\n'.format(self.real_data_size))                             # Text to be showed in warning message
        self.warning_message_function(text)                                                         # Shows a warning message
        
        self.frequency_config_area.setEnabled(True)                                                 # Enables all the configuration tab
        self.channel_config_area.setEnabled(True)                                                   # Enables all the configuration tab                                                  
        self.record_config_area.setEnabled(True)                                                    # Enables all the configuration tab
        self.record_show_frame.setEnabled(False)                                                    # Disables the record tab
        self.tabWidget.setCurrentIndex(0)                                                           # Changes to configuration tab                                                                          
        self.start_recording_button.setEnabled(True)                                                # Returns the start recording button to the enable state
        self.plot_next_button.setEnabled(False)                                                     # Returns the plot button to the disable state
        self.progress_bar.setValue(0)                                                               # Returns the progress bar to 0%
        self.collected_data_lineshow.setText('0')                                                   # Returns the amount of samples collected line edit to 0     
    
    # This function creates the configuration resume message
    def resume_message_function(self):
        text = "Check the registration data:"                                                       # Create a warning message
        message = str("Sampling frequency: "                 + 
                  str(self.options.get_sampling_frequency()) +
                  "Hz\nHigh pass filter cutoff frequency: "  + 
                  str(self.options.get_highpass())           +
                  "Hz\nLow pass filter cutoff frequency: "   + 
                  str(self.options.get_lowpass())            +  
                  "Hz\nNumber of recorded channels: "        + 
                  str(self.options.get_number_channels())    + 
                  "\nDuration " + 
                  str(self.options.get_days())    +  "d : "  +
                  str(self.options.get_hours())   +  "h : "  + 
                  str(self.options.get_minutes()) +  "m : "  + 
                  str(self.options.get_seconds()) +   "s"    + 
                  "\n\nDo you wish to continue?")                                                   # Create the resume message
        answer = self.option_message_function(text, message)                                        # Show a warning pop-up
        return answer
 
    # This function show a warning pop-up
    def option_message_function(self, text, info_text):
        warning = QMessageBox(self.interface)                                                       # Create the message box
        warning.setWindowTitle("Warning")                                                           # Message box title
        warning.setText(text)                                                                       # Message box text
        warning.setInformativeText(info_text)                                                       # Message box text
        warning.setIcon(QMessageBox.Warning)                                                        # Message box icon
        warning.setStyleSheet("QMessageBox{background:#353535;}QLabel{font:10pt/Century Gothic/;font-weight:bold;}QPushButton{border:2px solid #A21F27;border-radius:8px;background-color:#2C53A1;color:#FFFFFF;font:10pt/Century Gothic/;font-weight:bold;}QPushButton:pressed{border:2px solid #A21F27;border-radius:8px;background-color:#A21F27;color:#FFFFFF;}")
        warning.setStandardButtons(QMessageBox.Yes|QMessageBox.No)                                  # Message box buttons
        answer_yes = warning.button(QMessageBox.Yes)                                                # Set the button "yes"
        answer_yes.setText('    YES    ')                                                           # Rename the button "yes"
        answer_no = warning.button(QMessageBox.No)                                                  # Set the button "no"
        answer_no.setText('     NO      ')                                                          # Rename the button "no"
        warning.exec_()                                                                             # Execute the message box
        if warning.clickedButton() == answer_yes:                                                   # If the button "yes" is clicked
            return "yes"                                                                            # Return "yes"
        else:                                                                                       # If the button "no" is clicked
            return "no"                                                                             # Return "no"
        
    # This function show a warning pop-up
    def warning_message_function(self, text):
        warning = QMessageBox(self.interface)                                                       # Create the message box
        warning.setWindowTitle("Warning")                                                           # Message box title
        warning.setText(text)                                                                       # Message box text
        warning.setIcon(QMessageBox.Warning)                                                        # Message box icon
        warning.setStyleSheet("QMessageBox{background:#353535;}QLabel{font:10pt/Century Gothic/;font-weight:bold;}QPushButton{border:2px solid #A21F27;border-radius:8px;background-color:#2C53A1;color:#FFFFFF;font:10pt/Century Gothic/;font-weight:bold;}QPushButton:pressed{border:2px solid #A21F27;border-radius:8px;background-color:#A21F27;color:#FFFFFF;}")
        warning.setStandardButtons(QMessageBox.Yes)                                                 # Message box buttons
        answer_yes = warning.button(QMessageBox.Yes)                                                # Set the button "yes"
        answer_yes.setText('    OK    ')                                                            # Rename the button "ok"
        warning.exec_()                                                                             # Execute the message box

    def closeEvent(self, event):                                                                    
        super(Ui_NNC_InBrain, self).closeEvent(event)                                               # Defines the close event                                                             
        self.timer.stop()                                                                           # Stops the timer
        try:                                                                                        # Trys to close the view mode
            self.data_view_worker.stop()                                                            # Closes the usb port thread
            self.plot_view_worker.stop()                                                            # Closes the plot thread
        except:                                                                                     # If the threads do not exists
            self.data_recording_worker.stop()                                                       # Closes the usb port thread
            self.plot_recording_worker.stop()                                                       # Closes the plot thread
        finally:                                                                                    # If the threads do not exists
            QCoreApplication.instance().quit                                                        # Quits of the window                

if __name__ == '__main__':   
    def main():
        if not QtWidgets.QApplication.instance():
            QtWidgets.QApplication(sys.argv)
        else:
            QtWidgets.QApplication.instance()
            main = Ui_NNC_InBrain()
            main.show()
            return main  
    show = main()

# app = QtWidgets.QApplication(sys.argv)
# app.setStyle("windows")
# window = Ui_NNC_InBrain()
# app.exec_()
    
    
    
    
    