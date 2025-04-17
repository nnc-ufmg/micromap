# ELECTROPHYSIOLOGICAL DATA ACQUISITION SYSTEM

# This code is the configuration part of the electrophysiology recording 
# system. This partition contains the front-end, in which the user will be able 
# to choose acquisition parameters such as sampling frequency, filters and number 
# of channels.

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

#%% IMPORTS

import sys
import numpy 
import serial
import serial.tools.list_ports
import time
import struct
import collections
#import micromap.interface.interface_functions as interface_functions  
import interface_functions as interface_functions      
import os
import platform
import pickle
from datetime import datetime, timedelta
from PyQt5 import QtWidgets, uic    
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QCoreApplication, QTimer, QRunnable, QThreadPool, QMutex
from PyQt5.QtWidgets import QMessageBox, QMainWindow
from tkinter import Tk 
from tkinter.filedialog import (askdirectory as save_dir_popup)
import threading
import csv
from numpy import random

from pyqtgraph.Qt import QtGui
from pyqtgraph import mkPen
import pyqtgraph

mutex = QMutex()

class WorkerSignals(QObject):
    update_progress_bar = pyqtSignal(int)

class DataReceiverThread(QThread):
    data_ready = pyqtSignal(list)

    def __init__(self, usb_port, num_channels, bytes_to_read, sampling_freq, is_recording_mode, save_queue=None):
        super().__init__()
        self.usb = interface_functions.usb_singleton(usb_port, 50000000)
        self.num_channels = num_channels
        self.bytes_to_read = bytes_to_read
        self.running = False
        self.sampling_freq = sampling_freq
        self.is_recording_mode = is_recording_mode
        self.save_queue = save_queue
        unpack_sequence = str(self.bytes_to_read // 2)
        self.unpack_format = "<" + unpack_sequence + "h"

    def run(self):
        self.running = True
        self.usb.connect()
        self.usb.clear_buffer()
        self.usb.request_acquisition()

        while self.running:
            if self.usb.port.in_waiting >= self.bytes_to_read:
                try:
                    byte_data = self.usb.port.read(self.bytes_to_read)
                    integer_data = struct.unpack(self.unpack_format, byte_data)
                    channel_data = [integer_data[i::self.num_channels] for i in range(self.num_channels)]
                    self.data_ready.emit(channel_data)
                    if self.is_recording_mode and self.save_queue:
                        self.save_queue.put(byte_data)
                except Exception as e:
                    print(f"Erro na aquisição: {e}")
        self.usb.stop_acquisition()
        self.usb.disconnect()

    def stop(self):
        self.running = False

class SaveThread(QThread):
    def __init__(self, filename, save_queue):
        super().__init__()
        self.save_queue = save_queue
        self.filename = filename
        self.running = True

    def run(self):
        with open(self.filename, 'wb') as f:
            while self.running or not self.save_queue.empty():
                try:
                    data = self.save_queue.get(timeout=0.1)
                    f.write(data)
                except queue.Empty:
                    continue

    def stop(self):
        self.running = False

#%% INTERFACE CLASS

class TimerUpdater(QRunnable):
    def __init__(self, init_time, run_time_lineshow, sampling_frequency, collected_data_lineshow, total_time, progress_bar_signal = 0):
        super().__init__()
        self.init_time = init_time
        self.run_time_lineshow = run_time_lineshow
        self.sampling_frequency = sampling_frequency
        self.progress_bar_signal = progress_bar_signal
        self.collected_data_lineshow = collected_data_lineshow
        self.total_time = total_time

    def run(self):
        self.record_time_estimate = round(time.perf_counter() - self.init_time)                                 # Calculates the current acquisition time 
        self.run_time_lineshow.setText(str(timedelta(seconds = self.record_time_estimate)))                  # Changes the line edit (Record tab) in the interface
        
        self.amount_data_estimate = self.record_time_estimate*self.sampling_frequency                       # Estimates the total sample that should have been collected so far
        self.collected_data_lineshow.setText(str(round(self.amount_data_estimate)))                         # Shows the estimate in the line edit
        
        self.progress_bar_total = self.total_time*self.sampling_frequency                                   # Expected total of samples
        self.progress_bar_porcentage = round((self.amount_data_estimate/self.progress_bar_total)*100)       # Updates the progress bar according to the estimate
        if self.progress_bar_porcentage <= 100:                                                             # If estimated progress is less than 100%
            # emit signal to interface
            self.progress_bar_signal.update_progress_bar.emit(self.progress_bar_porcentage)                 # Updates the progress
        elif self.progress_bar_porcentage <= 0:                                                             # If estimated progress is more than 100%
            self.progress_bar_signal.update_progress_bar.emit(0)                                            # Updates the progress
        else:                                                                                               # If estimated progress is more than 100% 
            self.progress_bar_signal.update_progress_bar.emit(self.progress_bar_porcentage)                 # Updates the progress

    def clear(self):
        self.run_time_lineshow.setText("--:--:--")                                                          # Changes the line edit (Record tab) in the interface
        self.collected_data_lineshow.setText("--")                                                          # Changes the line edit (Record tab) in the interface
        self.progress_bar.setValue(0)                                                                       # Updates the progress bar to 0

class interface_visual_gui(QMainWindow):
    '''Interface visual gui
    
    This class contains all the commands of the interface as well as the constructors of the 
    interface itself.
    '''
 
#%% CONNECTION AND INITIALIZATION FUNCTIONS
    
    def __init__(self):
        '''__init__
        
        This private function calls the interface of a .ui file created in Qt Designer, starts 
        the dictionaries that contain the desired settings for the registry, and makes the 
        connections between the user's activities and their respective functions.
        '''
        super(interface_visual_gui, self).__init__()                                                            # Calls the inherited classes __init__ method
        QMainWindow.__init__(self)                                                                              # Creates the main window

        if platform.system() == 'Linux':
            self.interface = uic.loadUi(os.path.dirname(__file__) + "/interface_gui.ui", self)                     # Loads the interface design archive (made in Qt Designer)

        elif platform.system() == 'Windows':
            self.interface = uic.loadUi(os.path.dirname(__file__) + "\\interface_gui.ui", self)                     # Loads the interface design archive (made in Qt Designer)

        self.thread_pool = QThreadPool()                                                                        # Creates a thread pool to run the threads
        self.lock = threading.Lock()

        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self.request_plot_update)

        self.timer_updater_timer = QTimer()
        self.timer_updater_timer.timeout.connect(self.request_timer_update)

        self.record_timer = QTimer()
        self.record_timer.timeout.connect(self.complete_record)

        # Signal object for communication
        self.signals = WorkerSignals()
        self.signals.update_progress_bar.connect(self.progress_bar_updater)

        # Variables for threads
        self.data_receiver = None
        self.plot_updater = None

        # INTERFCE DEFAULT OPTIONS
        # This dictionary is the output variable of the interface to start the record
        self.options = interface_functions.acquisition()
        
        self.plot_viewer_function()                                                                             # Calls the plot viewer function
        self.showMaximized()                                                                                    # Maximizes the interface window
        self.show()                                                                                             # Shows the interface to the user

        self.intan_scale = 1000 * 0.195e-6

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
        self.command_send_button.clicked.connect(self.send_command_function)                                    # Called when send button on advanced options is clicked
        self.cancel_advanced_button.clicked.connect(self.cancel_advanced_function)                              # Called when cancel button on advanced options is clicked
        self.continue_to_record_button.clicked.connect(self.continue_to_record_function)                        # Called when record button on advanced options is clicked 
        # General interface interactions
        self.check_all_button.clicked.connect(self.check_all_function)                                          # Called when "check/uncheck all" button is clicked
        self.clear_button.clicked.connect(self.clear_function)                                                  # Called when the clear button is clicked
        self.cancel_button.clicked.connect(self.cancel_function)                                                # Called when the cancel button is clicked
        self.stop_button.clicked.connect(self.stop_function)                                                    # Called when stop button is clicked
        self.record_button.clicked.connect(self.start_view_mode_function)                                       # Called when the clear button is clicked 
        self.plot_next_button.clicked.connect(self.request_plot_update)                                         # Called when the "plot the last samples" button is clicked
        # self.update_statistics_button.clicked.connect(self.update_statistics_function)                          # Called when the "update statistics" button is clicked
                     
#%% INTERFACE SELECTIONS FUNCTIONS
        
    # Function to set the data aquisition system
    def method_function(self):
        '''Method function
        
        This public function is called when the acquisition method is changed by the user.
        '''
        method = self.method_combobox.currentIndex()                                                              # Gets the combo box index
        if method == 0:                                                                                           # If is selected ARDUINO
            self.options.method = "ARDUINO"                                                                       # Changes the method on main variables dictionary
            self.method_lineshow.setText("ARDUINO")                                                               # Changes the line edit (Record tab) in the interface
        # elif method == 1:                                                                                       # If is selected FPGA    
        #     self.options.method = "FPGA"                                                                        # Changes the method on main variables dictionary 
        #     self.method_lineshow.setText("FPGA")                                                                # Changes the line edit (Record tab) in the interface

        # elif method == 2:                                                                                       # If is selected PI PICO
        #     self.options.method = "PI PICO"                                                                     # Changes the method on main variables dictionary
        #     self.method_lineshow.setText("PI PICO")                                                             # Changes the line edit (Record tab) in the interface
    
    # Function to set what chip will be used
    def chip_function(self):
        '''Chip function
        
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

        self.get_channels_configuration_function()    
        self.plot_viewer_function(self.options.number_channels)                                                 # Sets the Y axis range and scale


    def _check_chip(self, chip):
        if self.options.usb_port == "None":
            self.warning_message_function("Please select a USB port")
            self.chip_combobox.setCurrentIndex(0)
            return
        
        command = "C500FF00"
        command = int('0x' + command, 16).to_bytes(4,'big')                                                     # Modificates the command to send to Arduino

        self.usb = interface_functions.usb_singleton(self.options.usb_port, 50000000)                           # Configures the USB connection
        
        usb_is_conected = self.usb.connect()                                                                    # Connect the USB port

        if usb_is_conected == False:
            self.warning_message_function("The USB port selected is not connected")
            self.chip_combobox.setCurrentIndex(0)
            return False
        
        answer = self.usb.send_direct(command)                                                                  # Establishes the direct communication to ITAM
        
        intan_id = str(answer.hex())[-1]

        self.usb.disconnect()                                                                                   # Disconnect the USB port

        if chip == "RHD2216" and intan_id == "1":
            return False
        elif chip == "RHD2132" and intan_id == "2":
            return False
        else:
            return True
            
    # Function to set the sampling frequency
    def sampling_frequency_function(self):
        '''Sampling frequency function
        
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
        '''High frequency function
        
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
        '''Lowpass frequency function
        
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
        '''Check all functions
        
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
        '''Get time configuration function
        
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
        '''Get channel configuration function
        
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
        '''Usb port function
        
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
        '''Usb selection function
        
        This public function is auxiliary to the cime function and identifies changes in 
        the combo box
        '''
        if self.usb_selection_enable == 1:                                                                      # If the USB connections were updated at least 1 time and ports were found
            usb_selected = self.online_ports[self.usb_port_combobox.currentIndex()]                             # Gets the port selected by the user
            self.options.usb_port = usb_selected                                                                # Changes the USB port option in the acquisition object

    def configure_acquisition(self):       
        self.usb = interface_functions.usb_singleton(self.options.usb_port, 50000000)                           # Configures the USB connection
        self.usb.connect()                                                                                      # Connect the USB port
        
        self.usb.reset_arduino()                                                                                # Resets the Arduino
        self.usb.set_sampling_frequency(self.options.sampling_frequency)                                        # Sets the sampling frequency
        self.usb.set_highpass_frequency(self.highpass_frequency_slider.value())                                 # Sets the Highpass Filter frequency
        self.usb.set_lowpass_frequency(self.lowpass_frequency_slider.value())                                   # Sets the Lowpass Filter frequency
        self.usb.set_channel_0to15(self.options.channels_bool)                                                  # Sets the 0-15 channels
        self.usb.set_channel_16to31(self.options.channels_bool)                                                 # Sets the 16-32 channels

        self.usb.disconnect()                                                                                   # Disconnects USB port

#%% VIEW MODE FUNCTIONS

    # This function is the interface output, where the program will start to sampling 
    def start_view_mode_function(self):
        '''Start view mode function
        
        This public function is called when the record button is clicked. 
        '''
        chip_check = self._check_chip(self.options.chip)
        if chip_check == False:
            self.warning_message_function("The chip selected was not found. Please, check the USB port or if the chip connected is correct")
            return

        self.get_time_configuration_function()                                                                  # Calls the function to define the record time 
        self.get_channels_configuration_function()                                                              # Calls the function to define the channels that will be sampled 
                
        answer = self.resume_message_function()                                                                 # Calls a function to create the configuration resume message
        if answer == "yes" and self.advanced_checkbox.isChecked() == False:                                     # If the user option is "yes" and advanced settings is not selected  
            self.configure_acquisition()                                                                        # Calls the acquisition configuration function
            self.start_threads()                                                                                # Calls the commmunication function to open the data acquisition thread        
            self.frequency_config_area.setEnabled(False)                                                        # Disables all the configuration tab
            self.channel_config_area.setEnabled(False)                                                          # Disables all the configuration tab
            self.record_config_area.setEnabled(False)                                                           # Disables all the configuration tab
            self.record_show_frame.setEnabled(True)                                                             # Enables all the configuration tab
            self.tabWidget.setCurrentIndex(1)                                                                   # Changes to record tab      
        elif answer == "yes" and self.advanced_checkbox.isChecked() == True:                                    # If the user option is "yes" and advanced settings is not selected  
            self.configure_acquisition()                                                                        # Calls the acquisition configuration function
            self.frequency_config_area.setEnabled(False)                                                        # Disables all the configuration tab
            self.channel_config_area.setEnabled(False)                                                          # Disables all the configuration tab
            self.record_config_area.setEnabled(False)                                                           # Disables all the configuration tab
            self.advanced_frame.setEnabled(True)                                                                # Enables all the configuration tab
            self.tabWidget.setCurrentIndex(2)                                                                   # Changes to record tab      
        else:                                                                                                   # If the user option is "no"
            return                                                                                              # The program do nothing
    
    def start_threads(self, plot_real_time = True):        
        if hasattr(self, 'curves') and len(self.curves) > 0:
            for curve in self.curves:
                self.plot_viewer.removeItem(curve)
        
        self.curves = []
        for _ in range(self.options.number_channels):
            pen = pyqtgraph.mkPen(color = 'white', width = 1)
            curve = self.plot_viewer.plot(pen = pen)
            self.curves.append(curve)        

        bytes_per_read = 100
        self.bytes_to_read = int(bytes_per_read*2*self.options.number_channels)                                         # Number of bytes to be read at a time (in this case, at a time will be read 1 sample = 2 bytes per channel)          
        self.buffer_length = 2*self.options.sampling_frequency                                                          # Buffer length to store 1 second of record
        self.scroll_index = 0
        self.window_size = 500
        self.plot_data_arrays = [numpy.zeros(self.window_size, dtype=numpy.float32) for _ in range(self.options.number_channels)]
        self.unpack_format = "<" + str(self.buffer_length/2) + "h"

        # Start the data receiver in the thread pool
        self.save_queue = queue.Queue()
        self.data_receiver_thread = DataReceiverThread(
            usb_port=self.options.usb_port,
            num_channels=self.options.number_channels,
            bytes_to_read=self.bytes_to_read,
            sampling_freq=self.options.sampling_frequency,
            is_recording_mode=self.options.is_recording_mode,
            save_queue=self.save_queue
        )
        self.data_receiver_thread.data_ready.connect(self.update_buffers)
        self.data_receiver_thread.start()

        if self.options.is_recording_mode:
            self.save_thread = SaveThread(self.options.save_directory, self.save_queue)
            self.save_thread.start()

        if not plot_real_time:
            record_time = self.options.get_total_time()
            print(record_time)
            record_time = record_time * 1000
            self.record_timer.start(record_time)
            
            timer_updater_interval = int(60 * 1000)  # Convert seconds to milliseconds
            self.initial_time = time.perf_counter()
            self.timer_updater_timer.start(timer_updater_interval)
        else:
            # Start the timer for plot updates
            update_interval = int(2 * 1000)  # Convert seconds to milliseconds
            self.plot_timer.start(update_interval)

    def stop_threads(self):
        if hasattr(self, 'data_receiver_thread') and self.data_receiver_thread:
            self.data_receiver_thread.stop()
            self.data_receiver_thread.wait()
            self.data_receiver_thread = None

        if hasattr(self, 'save_thread') and self.options.is_recording_mode and self.save_thread:
            self.save_thread.stop()
            self.save_thread.wait()
            self.save_thread = None

        self.plot_timer.stop()
        for curve in self.curves:
            curve.setData([])

        try:
            self.timer_updater.clear()
            self.timer_updater_timer.stop()
        except:
            pass

        try:
            self.record_timer.stop()
        except:
            print("Record timer not started")

    def request_timer_update(self):
        total_time = self.options.get_total_time()
        self.timer_updater = TimerUpdater(self.initial_time, self.run_time_lineshow, self.options.sampling_frequency, 
                                          self.collected_data_lineshow, total_time, self.signals)
        self.thread_pool.start(self.timer_updater)

    def complete_record(self):
        self.progress_bar.setValue(100)
        self.stop_threads()
        self.options.record_time = time.perf_counter() - self.initial_time
        self.successful_function()

    def progress_bar_updater(self, value):
        self.progress_bar.setValue(value)

    def request_plot_update(self):
        for i in range(self.options.number_channels):
            self.curves[i].setData(self.plot_data_arrays[i], copy=False)
            self.curves[i].setPos(self.scroll_index - self.window_size, 0)

        self.plot_viewer.setXRange(self.scroll_index - self.window_size, self.scroll_index)

#%% RECORDING MODE FUNCTIONS
    def update_buffers(self, channel_data):
        for i in range(self.options.number_channels):
            n = len(channel_data[i])
            new_data = numpy.empty(n, dtype=numpy.float32)
            numpy.multiply(channel_data[i], self.intan_scale, out=new_data)
            numpy.add(new_data, self.options.channels[i], out=new_data)

            # Atualiza buffer circular de plot
            self.plot_data_arrays[i][:-n] = self.plot_data_arrays[i][n:]
            self.plot_data_arrays[i][-n:] = new_data

        self.scroll_index += len(channel_data[0])
        if self.scroll_index > 10000:
            self.scroll_index = 0

        self.request_plot_update()

    def start_recording_mode_function(self):
        self.stop_threads()

        try:
            Tk().withdraw()                                                                                             # Hide a Tk window
            save_directory = save_dir_popup(title = "Select the directory to save the data")                             # Opens a window to select the directory to save the data
            str_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")                                                     # Creates a string with the current date and time
            save_directory = save_directory + "/record_" + str_time + ".mmap"       

            # check if the directory exists
            if not os.path.exists(save_directory):
                os.makedirs(save_directory)

            file_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")                                                        # Creates a string with the current date and time
            file_name = 'data_' + file_name +  ".bin"                                                                       # Adds a prefix to the file name  
            save_directory = save_directory + "/" + file_name                                                                    # Creates the file path

            if save_directory == '':                                                                                    # If nameless  
                self.options.save_directory = "None"                                                                    # Name with "None"
                self.view_mode_function()                                                                               # Starts view mode function
                return      
            else:       
                self.experiment_name_lineshow.setText(save_directory.split("/")[-1])                                    # Sets the name in directory
                self.options.save_directory = save_directory                                                            # Changes the save directory on main variables dictionary
                self.options.is_recording_mode = True                                                                   # Changes the recording mode flag to "true"
        except:     
            text = str('\nWARNING: The interface failed to create the binary file,' +       
                       ' please select a valid directory')                                                              # Message to be displeyed
            self.warning_message_function(text)                                                                         # Displays a message in the edit line of the interface
            return
        
        #try:
        self.start_threads(plot_real_time = False)                                                          # Restart the acquisition and plot threads
        # except:
        #     text = str('\nWARNING: The interface failed to try to start the threads responsible' +
        #                ' for signal acquisition')                                                               # Message to be displeyed
        #     self.warning_message_function(text)                                                                 # Displays a message in the edit line of the interface
        #     return
        
        self.plot_next_button.setEnabled(True)                                                                  # Enables the button to plot the last values acquired
        self.start_recording_button.setEnabled(False)                                                           # Disables the strat recording button


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
        command = self.command_message_lineedit.text()                                                          # The command is writed in the line edit interface
        
        if len(command) <= 8:                                                                                   # If the command's length is less or equal to 8 characters
            command = int('0x' + command, 16).to_bytes(4,'big')                                                 # Modificates the command to send to Arduino
        else:                                                                                                   # Else the command's length is largest to 8 characters
            self.command_answer_lineedit.setText('cmd > 4 bytes')                                               # Answer in the line edit the text: 'cmd > 4 bytes'
            return

        self.usb = interface_functions.usb_singleton(self.options.usb_port, 50000000)                           # Configures the USB connection
        self.usb.connect()                                                                                      # Connect the USB port
        
        answer = self.usb.send_direct(command)                                                                  # Establishes the direct communication to ITAM
        
        self.usb.disconnect()                                                                                   # Disconnect the USB port
        
        self.command_answer_lineedit.setText(answer.hex().upper())                                              # Returns the answer in the line edit interface
        self.show_commands_textedit.append('\nCommand sent ....... 0x' + command.hex() + 
                                                    '\nAnswer received .... 0x' + answer.hex())                 # Shows the resume of communication

#%% WARNING FUNCTIONS
    
    def successful_function(self):
        self.options.is_recording_mode = False                                                                  # Changes the recording mode flag to 'false'
            
        text = str('Data acquisition completed successfully \n\n' +
                   'Duration: {}\n'.format(timedelta(seconds = round(self.options.record_time))))               # Text to be showed in warning message
        self.warning_message_function(text)                                                                     # Shows a warning message
        
        options_resume = self.options.resume_options()                                                          # Gets the data resume
        options_resume_file = self.options.save_directory[:-4] + '_options_resume.pkl'                          # Creates the file name to write the resume
        with open(options_resume_file, 'wb') as file:                                                           # Opens the file to write the resume
            pickle.dump(options_resume, file)                                                                   # Writes the resume in the file

        self.options.save_directory = "None"                                                                    # Change the save directory on main variables dictionary

        self.frequency_config_area.setEnabled(True)                                                             # Enables all the configuration tab
        self.channel_config_area.setEnabled(True)                                                               # Enables all the configuration tab                                                  
        self.record_config_area.setEnabled(True)                                                                # Enables all the configuration tab
        self.record_show_frame.setEnabled(False)                                                                # Disables the record tab
        self.tabWidget.setCurrentIndex(0)                                                                       # Changes to configuration tab                                                                          
        self.start_recording_button.setEnabled(True)                                                            # Returns the start recording button to the enable state
        self.plot_next_button.setEnabled(False)                                                                 # Returns the plot button to the disable state
        self.progress_bar.setValue(0)                                                                           # Returns the progress bar to 0%
        self.collected_data_lineshow.setText('0')                                                               # Returns the amount of samples collected line edit to 0     
        self.experiment_name_lineshow.setText("EXPERIMENT NAME")                                                # Returns the name text to 'Experiment Name'
    
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

#%% CONTOL FUNCTIONS
    
    def change_direcotory_function(self):
        self.data_worker.change_direcotory_function()

    def stop_function(self): 
        if self.stop_button.text() == "STOP":                                                                   # If the button text is 'stop'
            self.stop_threads()                                                                                 # Stops the record
            self.stop_button.setText("START")                                                                   # Changes the text on the button to 'start'
        else:
            self.start_threads()                                                                                # Continues the record
            self.stop_button.setText("STOP")                                                                    # Changes the text on the button to 'stop'
    
    # Function to clear all selections made
    def clear_function(self):
        '''Clear function
        
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
        self.stop_threads()                                                                                     # Closes the usb port threas
        self.plot_viewer_function(self.options.number_channels)                                                 # Sets the Y axis range and scale  

        self.is_recording_mode = False                                                                          # Change the recording mode flag to 'false'
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
        self.experiment_name_lineshow.setText("EXPERIMENT NAME")                                                # Returns the name text to 'Experiment Name'

    def cancel_advanced_function(self):
        self.frequency_config_area.setEnabled(True)                                                             # Enables all the configuration tab
        self.channel_config_area.setEnabled(True)                                                               # Enables all the configuration tab                                                  
        self.record_config_area.setEnabled(True)                                                                # Enables all the configuration tab
        self.advanced_frame.setEnabled(False)                                                                   # Disables the record tab
        self.command_message_lineedit.setText('Type here')                                                      # Returns the command message text to 'Type here'
        self.command_answer_lineedit.setText('')                                                                # Cleans the answer line
        self.tabWidget.setCurrentIndex(0)                                                                       # Changes to configuration tab                                                                          
        
    def closeEvent(self, event):                                                                    
        self.stop_threads()
        self.thread_pool.waitForDone()
        super().closeEvent(event)
        QCoreApplication.instance().quit                                                                        # Quits of the window                

    def plot_viewer_function(self, num_channels = 16):
        self.plot_viewer.setDownsampling(ds=4, auto=True, mode='mean')
        
        self.plot_viewer.setBackground(None)                                                                    # Sets the plot background
        self.plot_viewer.setLimits(xMin = 0, yMin = 0, xMax = 4000, yMax = num_channels + 1)                    # Sets the plot limits 
        self.plot_viewer.setXRange(0, 4000, padding=0.0001)                                                     # Sets the X axis range and scale

        x_axis = self.plot_viewer.getAxis('bottom')                                                             # Sets the X axis to bottom
        x_axis.setStyle(tickLength=10, showValues=True)                                                         # Sets ticks lenght and values on
        
        self.plot_viewer.setYRange(0, num_channels + 1, padding=0.0001)                                         # Sets the Y axis range and scale
        y_axis = self.plot_viewer.getAxis('left')                                                               # Sets the Y axis to left
        y_axis.setStyle(tickLength=0, showValues=True)                                                          # Sets without ticks and with values
        y_ticks_length = range(1, num_channels + 1)                                                             # Sets y Axis range to 32 channels
        y_axis.setTicks([[(v, str(v)) for v in y_ticks_length]])                                                # Fixes the axis at integer values referring to the channels

        label_style = {'family':'DejaVu Sans', 'color': '#969696', 'font-size': '10pt', 'font-weight': 'bold'}  # Sets the label
        self.plot_viewer.setLabel('bottom', "Time [seconds]", **label_style)                                    # Sets the X axis subtitle
        self.plot_viewer.setLabel('left', "Channels", **label_style)                                            # Sets th Y axis subtitle
        
        font = QtGui.QFont()                                                                                    # Uses the QtGui fonts
        font.setPixelSize(10)                                                                                   # Sets pixel size
        font.setBold(True)                                                                                      # Sets the bold font
        font.setFamily("DejaVu Sans")                                                                           # Sets the family font
        x_ticks = self.plot_viewer.getAxis("bottom")                                                            # Sets the X axis ticks position
        y_ticks = self.plot_viewer.getAxis("left")                                                              # Sets the Y axis ticks position
        x_ticks.setStyle(tickFont = font)                                                                       # Sets the X axis ticks font
        y_ticks.setStyle(tickFont = font)                                                                       # Sets the Y axis ticks font
        x_ticks.setPen('#969696')                                                                               # Sets the X axis color
        y_ticks.setPen('#969696')                                                                               # Sets the Y axis color
        x_ticks.setTextPen('#969696')                                                                           # Sets the X axis text color
        y_ticks.setTextPen('#969696')                                                                           # Sets the Y axis text color
        x_ticks.setStyle(tickTextOffset = 10)                                                                   # Sets the spacing between tick text and X axis
        y_ticks.setStyle(tickTextOffset = 10)                                                                   # Sets the spacing between tick text and Y axis

        range_ = self.plot_viewer.getViewBox().viewRange()                                                                       # Sets the range 
        self.plot_viewer.getViewBox().setLimits(xMin=range_[0][0], xMax=range_[0][1], yMin=range_[1][0], yMax=range_[1][1])      # Sets max and min limits on axis

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
    
    
    
    
    
