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
import math
import serial.tools.list_ports
import time
import struct
import collections
import queue
#import micromap.interface.interface_functions as interface_functions  
import interface_functions as interface_functions      
import os
import platform
import pickle
from datetime import datetime, timedelta
from PyQt5 import QtWidgets, uic    
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QCoreApplication, QTimer, QRunnable, QThreadPool, QMutex
from PyQt5.QtWidgets import QMessageBox, QMainWindow, QInputDialog, QFileDialog
from tkinter import Tk
import threading
import csv
from numpy import random
import platform

from pyqtgraph.Qt import QtGui
from pyqtgraph import mkPen
import pyqtgraph
# pyqtgraph.setConfigOptions(useOpenGL = True)
pyqtgraph.setConfigOptions(antialias = False)

class DataReceiverThread(QThread):
    raw_data_ready = pyqtSignal(bytearray)
    message = pyqtSignal(str)

    def __init__(self, usb_port, num_channels, samples_to_read, is_recording_mode, save_queue = None):
        super().__init__()
        self.usb = interface_functions.usb_singleton(usb_port, 50000000)
        self.num_channels = num_channels
        self.samples_to_read = samples_to_read
        self.bytes_to_read = int(samples_to_read*(2*(self.num_channels + 1)))                                                                         # Number of bytes to be read at a time (in this case, at a time will be read 1 sample = 2 bytes per channel + 1 byte header)
        self.running = False
        self.is_recording_mode = is_recording_mode
        self.save_queue = save_queue
        self.expected_counter = None
        self.buffer = bytearray()
        self.read_number = 0

    def run(self):
        self.running = True
        self.usb.connect()
        self.usb.clear_buffer()
        self.usb.request_acquisition()

        while self.running:
            if self.usb.port.in_waiting > 0:
                try:
                    partial_data = self.usb.port.read(self.usb.port.in_waiting)
                    self.buffer += partial_data

                    while len(self.buffer) >= self.bytes_to_read:                      
                        full_packet = self.buffer[:self.bytes_to_read]
                        self.buffer = self.buffer[self.bytes_to_read:]

                        if self.expected_counter is None:
                            self.expected_counter = full_packet[1]

                        packet_counter = full_packet[1]  # Get the packet counter from the second byte
                        if packet_counter != self.expected_counter:
                            self.message.emit(f"[ERROR] Packet counter mismatch: expected {self.expected_counter}, got {packet_counter}")

                        self.expected_counter = (self.expected_counter + self.samples_to_read) % 256  # Increment the expected counter

                        if self.is_recording_mode and self.save_queue:
                            self.save_queue.put(full_packet)

                        self.raw_data_ready.emit(bytearray(full_packet))
                        self.message.emit(f'[RECEIVE] {self.read_number}')
                        self.read_number += 1

                except Exception as e:
                    self.message.emit(f"[ERROR]: {e}")

        self.usb.stop_acquisition()
        self.usb.disconnect()

    def stop(self):
        self.running = False

class PlotThread(QThread):
    channel_data_ready = pyqtSignal(numpy.ndarray)
    message = pyqtSignal(str)

    def __init__(self, num_channels, samples_to_read, update_samples = 1000, parent=None):
        super().__init__(parent)
        if update_samples < samples_to_read:
            raise ValueError("Update rate must be greater than or equal to samples to read.")        
        
        self.queue = queue.Queue()
        self.num_channels = num_channels
        self.samples_to_read = samples_to_read
        self.update_samples = update_samples
        self.bytes_to_read = int(samples_to_read*(2*(self.num_channels + 1)))
        self.intan_scale = 1000 * 0.195e-6
        self.running = True
        self.update_buffer = numpy.zeros((self.num_channels, self.update_samples), dtype=numpy.float32)
        self.update_index = 0
        self.buffer_size = self.update_buffer.shape[1]

        unpack_sequence = str((int(samples_to_read*2*self.num_channels)) // 2)   
        self.unpack_format = "<" + unpack_sequence + "h"

        self.flag_indexes = [[i, i + 1] for i in range(0, self.bytes_to_read, 2*(self.num_channels + 1))]
        self.flag_indexes = numpy.array(self.flag_indexes).flatten()
        self.header_indexes = self.flag_indexes[0::2]
        self.count_indexes = self.flag_indexes[1::2]

    def push_data(self, byte_data):
        self.queue.put(byte_data)

    def run(self):
        while self.running:
            try:
                byte_data = self.queue.get(timeout=0.1)

                clean_bytes = []
                for i, b in enumerate(byte_data):
                    if i not in self.flag_indexes:
                        clean_bytes.append(b)
                    else:
                        if i in self.header_indexes and b != 0xFE:
                            self.message.emit(f"[Error] Invalid header byte: {b:#04x} at index {i}")  # Debug: print error message

                clean_bytes = bytearray(clean_bytes)
                values = struct.unpack(self.unpack_format, clean_bytes)
                channel_data = numpy.array([values[i::self.num_channels] for i in range(self.num_channels)], dtype=numpy.float32)

                channel_data = channel_data * self.intan_scale

                update_length = channel_data.shape[1]
                end_index = self.update_index + update_length

                if end_index <= self.buffer_size:
                    self.update_buffer[:, self.update_index:end_index] = channel_data
                else:
                    # Parte final
                    first_part = self.buffer_size - self.update_index
                    self.update_buffer[:, self.update_index:] = channel_data[:, :first_part]
                    # Parte inicial
                    self.update_buffer[:, :update_length - first_part] = channel_data[:, first_part:]

                self.update_index = (self.update_index + update_length) % self.buffer_size

                if self.update_index == 0:
                    self.channel_data_ready.emit(self.update_buffer.copy())

            except queue.Empty:
                continue

    def stop(self):
        self.running = False

class SaveThread(QThread):
    message = pyqtSignal(str)
    
    def __init__(self, filename, save_queue):
        super().__init__()
        self.save_queue = save_queue
        self.filename = filename
        self.running = True
        self.save_number = 0

    def run(self):
        with open(self.filename, 'wb') as f:
            while self.running or not self.save_queue.empty():
                try:
                    data = self.save_queue.get(timeout=0.1)
                    f.write(data)
                    f.flush()
                    self.message.emit(f'[SAVE] {self.save_number}')
                    self.save_number += 1
                except queue.Empty:
                    continue

    def stop(self):
        self.running = False

# INTERFACE CLASS

class interface_visual_gui(QMainWindow):
    '''Interface visual gui
    
    This class contains all the commands of the interface as well as the constructors of the 
    interface itself.
    '''
 
    # CONNECTION AND INITIALIZATION FUNCTIONS ---------------------------------------------------
    
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

        self.is_raspberry = interface_functions.is_raspberry_pi()
        # self.is_raspberry = True
        if self.is_raspberry:
            self.machine_lineedit.setText('Raspberry Pi')
        else:
            self.machine_lineedit.setText('PC')

        # Variables for threads
        self.data_receiver = None
        self.plot_updater = None

        # INTERFCE DEFAULT OPTIONS
        # This dictionary is the output variable of the interface to start the record
        self.options = interface_functions.acquisition()

        self.ads_scale = 0
        self.plot_online = True                                                                                  # Variable to check if the plot is online or offline
        
        if self.is_raspberry:
            self.plot_window_sec = 2                                                                                # Number of seconds to be plotted (X axis limit)
            self.seconds_to_read = 2                                                                                # Number of seconds to be read at time (number of consecutive samples to be read)
            # If update_samples = 100 and samples_to_read_sec = 0.05, then the number of packets to be plotted at time is 100*0.05 = 5 seconds
            self.update_samples = 1                                                                                 # Number of packets (packetd = samples_to_read_sec) to be plotted at time (number of consecutive samples to be plotted)
        else:
            self.plot_window_sec = 5                                                                                 # Number of seconds to be plotted (X axis limit)
            self.seconds_to_read = 0.2                                                                               # Number of seconds to be read at time (number of consecutive samples to be read)
            # If update_samples = 100 and samples_to_read_sec = 0.05, then the number of packets to be plotted at time is 100*0.05 = 5 seconds
            self.update_samples = 1                                                                                  # Number of packets (packetd = samples_to_read_sec) to be plotted at time (number of consecutive samples to be plotted)

        self.plot_window = self.plot_window_sec * self.options.sampling_frequency
        if self.update_samples*self.seconds_to_read > self.plot_window_sec:
            raise ValueError("Update rate must be greater than or equal to samples to read.")

        self.plot_viewer_function()                                                                             # Calls the plot viewer function
        self.showMaximized()                                                                                    # Maximizes the interface window
        self.show()                                                                                             # Shows the interface to the user

        self.timer_updater_timer = QTimer()
        self.timer_updater_timer.timeout.connect(self.update_experiment_timer)

        self.timer_to_test = QTimer()
        self.timer_to_test.timeout.connect(self.stop_function)

        # INTERFACE INTERACTIONS
        # Record configuration interactions
        self.chip_combobox.currentIndexChanged.connect(self.chip_function)                                          # Called when chip combobox is changed
        self.usb_port.clicked.connect(self.usb_port_function)                                                       # Called when the update USB button is clicked
        self.usb_port_combobox.currentIndexChanged.connect(self.usb_selection_function)                             # Called when the USB combo box is changed
        self.sampling_frequency_slider.valueChanged[int].connect(self.sampling_frequency_function)                  # Called when sampling frequency slider is changed
        self.highpass_frequency_slider.valueChanged[int].connect(self.highpass_frequency_function)                  # Called when high pass cutoff frequency slider is changed
        self.lowpass_frequency_slider.valueChanged[int].connect(self.lowpass_frequency_function)                    # Called when low pass cutoff frequency slider is changed
        self.start_recording_button.clicked.connect(self.start_recording_mode_function)                             # Called when the start recording button is clicked
        # Advanced configuration interactions
        self.command_send_button.clicked.connect(self.send_command_function)                                        # Called when send button on advanced options is clicked
        self.cancel_advanced_button.clicked.connect(self.cancel_advanced_function)                                  # Called when cancel button on advanced options is clicked
        self.continue_to_record_button.clicked.connect(self.continue_to_record_function)                            # Called when record button on advanced options is clicked 
        # General interface interactions
        self.check_all_button.clicked.connect(self.check_all_function)                                              # Called when "check/uncheck all" button is clicked
        self.clear_button.clicked.connect(self.clear_function)                                                      # Called when the clear button is clicked
        self.stop_button.clicked.connect(self.stop_function)                                                        # Called when stop button is clicked
        self.record_button.clicked.connect(self.start_view_mode_function)                                           # Called when the clear button is clicked 
        self.show_plot_checkbox.stateChanged.connect(self.show_plot_function)                                       # Called when the "show plot" checkbox is clicked
                     
    # INTERFACE SELECTIONS FUNCTIONS ------------------------------------------------------------
            
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

        if chip == "RHD2216" and intan_id == "2":
            return True
        elif chip == "RHD2132" and intan_id == "1":
            return True
        else:
            print("Chip not found, the message received was: ", answer.hex())
            return False
            
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
        self.number_channels_lineshow.setText(str(self.options.num_channels))                                   # Changes the line edit (Record tab) in the interface
        
        self.plot_viewer_function(max(self.options.channels))                                                    # Sets the Y axis range and scale

    # USB FUNCTIONS -----------------------------------------------------------------------------

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

    # VIEW MODE FUNCTIONS -----------------------------------------------------------------------

    # This function is the interface output, where the program will start to sampling 
    def start_view_mode_function(self):
        '''Start view mode function
        
        This public function is called when the record button is clicked. 
        '''
        chip_check = self._check_chip(self.options.chip)
        if chip_check == False:
            self.warning_message_function("The chip selected was not found. Please, check the USB port or if the chip connected is correct")
            return

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
    
    def start_threads(self):        
        if hasattr(self, 'curves') and len(self.curves) > 0:
            for curve in self.curves:
                self.plot_viewer.removeItem(curve)      
        
        self.plot_window = self.plot_window_sec * self.options.sampling_frequency                                                                     # Number of samples to be plotted at a time (in this case, 5 seconds of samples will be plotted)
        self.plot_viewer.setXRange(0, self.plot_window)                                                                                               # Sets the X axis range

        # The USB port buffer has a size of 12342 bytes, so, if the samples to be read is bigger than this value, the program will not work properly.
        # The number of bytes "in_waiting" never will reach above 12342, so, the samples will never be read.
        self.samples_to_read = math.ceil(self.seconds_to_read * self.options.sampling_frequency)                                                            # Number of samples to be read in each iteration
        
        if self.samples_to_read <= 0:
            raise ValueError("samples_to_read must be greater than 0")

        if self.samples_to_read > self.plot_window:
            raise ValueError("samples_to_read must be less than or equal to plot_window")
        
        self.write_index = 0
        self.plot_data_arrays = [numpy.zeros(self.plot_window, dtype=numpy.float32) + self.options.channels[i] for i in range(self.options.num_channels)]

        self.x_values = numpy.arange(self.plot_window)
        self.curves = []
        for i in range(self.options.num_channels):
            pen = pyqtgraph.mkPen('white', width=1)
            curve = self.plot_viewer.plot(self.x_values, self.plot_data_arrays[i], pen=pen)
            if self.is_raspberry:
                ds = math.ceil(self.options.sampling_frequency/200)
                curve.setDownsampling(auto=False, ds=ds, method='peak')  # Downsample the curve to reduce the number of points plotted
                curve.setClipToView(True)
                curve.setSkipFiniteCheck(True)
            # curve.setDownsampling(auto=False, ds=10, method='peak')  # Downsample the curve to reduce the number of points plotted
            self.curves.append(curve)

        self.plot_thread = PlotThread(
            num_channels = self.options.num_channels,
            samples_to_read = self.samples_to_read,
            update_samples = self.update_samples*self.samples_to_read, 
        )
        self.plot_thread.message.connect(self.logging.appendPlainText)
        self.plot_thread.channel_data_ready.connect(self.update_buffers)

        # Start the data receiver in the thread pool
        self.save_queue = queue.Queue()
        self.data_receiver_thread = DataReceiverThread(
            usb_port=self.options.usb_port,
            num_channels=self.options.num_channels,
            samples_to_read=self.samples_to_read,
            is_recording_mode=self.options.is_recording_mode,
            save_queue=self.save_queue
        )
        self.data_receiver_thread.message.connect(self.logging.appendPlainText)
        self.data_receiver_thread.raw_data_ready.connect(self.plot_thread.push_data)
        self.initial_time = time.perf_counter()
        
        self.data_receiver_thread.start()
        self.plot_thread.start()
        self.timer_updater_timer.start(10000)

        if self.options.is_recording_mode:
            self.save_thread = SaveThread(self.options.save_directory, self.save_queue)
            self.save_thread.message.connect(self.logging.appendPlainText)
            self.save_thread.start()
            test_minutes = 30
            test_time = test_minutes * 60 * 1000  # Convert to milliseconds
            self.timer_to_test.start(test_time)   # Start the timer to test the connection

    def stop_threads(self):
        self.timer_updater_timer.stop()

        if hasattr(self, 'data_receiver_thread') and self.data_receiver_thread:
            self.data_receiver_thread.stop()
            self.data_receiver_thread.wait()
            self.data_receiver_thread = None

        if hasattr(self, 'plot_thread') and self.plot_thread:
            self.plot_thread.stop()
            self.plot_thread.wait()
            self.plot_thread = None

        if hasattr(self, 'save_thread') and self.options.is_recording_mode and self.save_thread:
            self.save_thread.stop()
            self.save_thread.wait()
            self.save_thread = None

        if hasattr(self, 'curves') and len(self.curves) > 0:
            for curve in self.curves:
                curve.setData([])

    # RECORDING MODE FUNCTIONS ------------------------------------------------------------------

    def update_experiment_timer(self):
        elapsed = int(time.perf_counter() - self.initial_time)
        formatted = str(timedelta(seconds=elapsed))
        self.run_time_lineshow.setText(formatted)  # substitua pelo nome do widget correto

    def update_buffers(self, channel_data):
        if self.plot_online: 
            overflow = None
            end = self.write_index + channel_data.shape[1]
            
            for i in range(self.options.num_channels):
                data = channel_data[i] + self.options.channels[i]
                if end <= self.plot_window:
                    self.plot_data_arrays[i][self.write_index:end] = data
                else:
                    # Parte final + parte inicial
                    overflow = end - self.plot_window
                    self.plot_data_arrays[i][self.write_index:] = data[:-overflow]
                    self.plot_data_arrays[i][:overflow] = data[-overflow:]
                
                self.curves[i].setData(x = self.x_values, y = self.plot_data_arrays[i], copy=False)

            if overflow is not None:
                self.write_index = overflow
            else:
                self.write_index = end

    def show_plot_function(self):
        if self.show_plot_checkbox.isChecked():
            self.plot_online = True
        else:
            self.plot_online = False

    def start_recording_mode_function(self):
        self.stop_threads()

        # try:                                                                                                      # Hide a Tk window
        str_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")                                                     # Creates a string with the current date and time
        default_name = f"record_{str_time}"                                                                         # Suggests a default file name

        folder_path = self.select_and_create_folder_qt(suggested_name=default_name)                                    # Calls the function to select and create a folder

        if folder_path == '' or folder_path is None:                                                                # If the user cancels or gives empty input
            self.options.save_directory = "None"                                                                    # Name with "None"
            self.start_threads()                                                                                    # Starts view mode function
            return
        else:
            if not os.path.exists(folder_path):                                                                     # If the folder exists
                os.makedirs(folder_path)                                                                            # Creates the folder

            file_path = os.path.join(folder_path, f"{default_name}.mmap")                                           # Creates the file name to write the data

            self.experiment_name_lineshow.setText(folder_path.split("/")[-1])                                       # Sets the name in directory
            self.run_time_lineshow.setText("00:00:00")                                                              # Returns the run time text to '00:00:00'
            self.options.save_directory = file_path                                                                 # Changes the save directory on main variables dictionary
            self.options.is_recording_mode = True                                                                   # Changes the recording mode flag to "true"

        # except:
        #     text = str('\nWARNING: The interface failed to create the binary file,' +       
        #             ' please select a valid directory')                                                              # Message to be displayed
        #     self.warning_message_function(text)                                                                         # Displays a message in the edit line of the interface
        #     return
        
        self.start_recording_button.setEnabled(False)                                                           # Disables the strat recording button

        self.start_threads()                                                                                     # Restart the acquisition and plot threads

    # ADVANCED SETTINGS FUNCTIONS ---------------------------------------------------------------

    def continue_to_record_function(self):
        self.start_threads()                                                                                    # Calls the commmunication function to open the data acquisition thread
        
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

    # WARNING FUNCTIONS -------------------------------------------------------------------------      
    
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
                  str(self.options.num_channels)          + 
                  "\nIs Raspberry: " + str(self.is_raspberry) +
                  "\nUpdata samples: " + str(self.update_samples) +
                  "\nRead time: " + str(self.seconds_to_read) +
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

    # CONTOL FUNCTIONS -------------------------------------------------------------------------
    
    def select_and_create_folder_qt(self, suggested_name=''):
        # Abre seletor de diretório
        base_dir = QFileDialog.getExistingDirectory(self, "Select base directory to create new folder")

        if not base_dir:
            self.warning_message_function("No directory selected.")
            return None

        input_dialog = QInputDialog(self)
        input_dialog.setWindowTitle("Folder Name")
        input_dialog.setLabelText("Enter the name of the new folder:")
        input_dialog.setTextValue(suggested_name)
        input_dialog.setStyleSheet(
            "QInputDialog{background:#353535;}QLabel{font:10pt 'Century Gothic';font-weight:bold;color:white;}"
            "QLineEdit{background:white;color:black;border:2px solid #A21F27;border-radius:5px;padding:5px;}"
            "QPushButton{border:2px solid #A21F27;border-radius:8px;background-color:#2C53A1;color:#FFFFFF;"
            "font:8pt 'Century Gothic';font-weight:bold;}QPushButton:pressed{border:2px solid #A21F27;"
            "border-radius:8px;background-color:#A21F27;color:#FFFFFF;}"
        )
        input_dialog.setModal(True)

        if input_dialog.exec_() == QInputDialog.Accepted:
            folder_name = input_dialog.textValue()
        else:
            folder_name = None

        # Caminho final
        new_folder_path = os.path.join(base_dir, folder_name)

        try:
            os.makedirs(new_folder_path, exist_ok = True)
            return new_folder_path
        except Exception as e:
            self.warning_message_function(f"Could not create folder:\n{e}")
            return None

    def stop_function(self): 
        self.stop_threads()                                                                                     # Calls the function to stop the threads
        
        record_time = time.perf_counter() - self.initial_time                                                   # Gets the time of the recording
        text = str('Data acquisition completed successfully \n\n' +
                   'Duration: {}\n'.format(timedelta(seconds = round(record_time))))                            # Text to be showed in warning message
        self.warning_message_function(text)                                                                     # Shows a warning message
        
        if self.options.is_recording_mode:                                                                    # If the recording mode is active
            options_resume = self.options.resume_options()                                                          # Gets the data resume
            options_resume_file = self.options.save_directory[:-5] + '_metadata.pkl'                                # Creates the file name to write the resume
            with open(options_resume_file, 'wb') as file:                                                           # Opens the file to write the resume
                pickle.dump(options_resume, file)                                                                   # Writes the resume in the file

        self.options.is_recording_mode = False                                                                  # Changes the recording mode flag to 'false'

        self.options.save_directory = "None"                                                                    # Change the save directory on main variables dictionary

        self.frequency_config_area.setEnabled(True)                                                             # Enables all the configuration tab
        self.channel_config_area.setEnabled(True)                                                               # Enables all the configuration tab                                                  
        self.record_config_area.setEnabled(True)                                                                # Enables all the configuration tab
        self.record_show_frame.setEnabled(False)                                                                # Disables the record tab
        self.tabWidget.setCurrentIndex(0)                                                                       # Changes to configuration tab                                                                          
        self.start_recording_button.setEnabled(True)                                                            # Returns the start recording button to the enable state
        self.experiment_name_lineshow.setText("EXPERIMENT NAME")                                                # Returns the name text to 'Experiment Name'
        self.run_time_lineshow.setText("00:00:00")                                                              # Returns the run time text to '00:00:00'

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
            self.check_all_button.setText("Check All")                                                          # Clears the "Unchecked All" or "Check All" selection  
            self.chip_function()                                                                                # Calls the function to update the interface
            self.sampling_frequency_function()                                                                  # Calls the function to update the interface    
            self.highpass_frequency_function()                                                                  # Calls the function to update the interface
            self.lowpass_frequency_function()                                                                   # Calls the function to update the interface
            self.check_all_function()                                                                           # Calls the function to update the interface 
        else:                                                                                                   # If the user option is "no"
            return                                                                                              # The program do nothing
       
    # Function to cancel the data acquisition     

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
        super().closeEvent(event)
        QCoreApplication.instance().quit                                                                        # Quits of the window                

    def plot_viewer_function(self, num_channels = 16):
        self.plot_viewer.clear()

        self.plot_viewer.setBackground(None)
        self.plot_viewer.setXRange(0, self.plot_window, padding=0)
        self.plot_viewer.setLimits(xMin=0, xMax=self.plot_window)
        self.plot_viewer.setLabel('bottom', "Samples")

        # LIBERA O AUTO-RANGE E LIMITES ANTIGOS
        self.plot_viewer.enableAutoRange(axis='y', enable=True)
        self.plot_viewer.autoRange()
        vb = self.plot_viewer.getViewBox()
        vb.setLimits(xMin=0, xMax=self.plot_window, yMin=0, yMax=num_channels + 1)

        self.plot_viewer.setYRange(0, num_channels + 1, padding=0)

        # Eixo X
        x_axis = self.plot_viewer.getAxis('bottom')
        x_axis.setStyle(tickLength=10, showValues=True)

        # Eixo Y
        y_axis = self.plot_viewer.getAxis('left')
        y_axis.setStyle(tickLength=0, showValues=True)
        y_ticks_length = range(1, num_channels + 1)
        y_axis.setTicks([[(v, str(v)) for v in y_ticks_length]])

        # Estilo
        label_style = {'family': 'DejaVu Sans', 'color': '#969696', 'font-size': '10pt', 'font-weight': 'bold'}
        self.plot_viewer.setLabel('bottom', "Time [seconds]", **label_style)
        self.plot_viewer.setLabel('left', "Channels", **label_style)

        font = QtGui.QFont()
        font.setPixelSize(10)
        font.setBold(True)
        font.setFamily("DejaVu Sans")
        x_ticks = self.plot_viewer.getAxis("bottom")
        y_ticks = self.plot_viewer.getAxis("left")
        x_ticks.setStyle(tickFont=font)
        y_ticks.setStyle(tickFont=font)
        x_ticks.setPen('#969696')
        y_ticks.setPen('#969696')
        x_ticks.setTextPen('#969696')
        y_ticks.setTextPen('#969696')
        x_ticks.setStyle(tickTextOffset=10)
        y_ticks.setStyle(tickTextOffset=10)



# INITIALIZANTION FUNCTION

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
    
    
    
    
    
