Mounting
========

This tutorial will describe the complete process of making a MicroMAP 
system from assembling the housing to the connections for making registers:

1. Shopping List
2. Building the case on a 3D printer 
3. Placing the components and connecting the wires
4. Installing dependencies and microcontroller configuration
5. Connecting the system to the analog-to-digital converter

Shopping List
-------------

- Arduino Due
- Raspberry Pi (optional)
- 3D printer filament (optional)
- Cooler 30x30mm (optional)
- Jumpers
- Chip Intan RHD Family
- Intan RHD PCB board
- 10-way power cable slip ring
- Flat conector

Building the case on a 3D printer
---------------------------------

- Open the *Raspbperry Pi Configurations* in *Applications Menu*
- Go to *Interfaces* tab and turns on the VNC
- Go to *Display* tab and sets the *Headlesss Resolution* to maximum value (1920x1080)
- On the task bar right side a VNC symbol will appear
- Click on it and gets the IP on left side of the window (ex. 192.168.1.222)
- Install and open the *VNC Viewer* on another computer (https://www.realvnc.com/pt/connect/download/viewer/)
- Open the *VNC Viewer*, click in *file* tab and after, in *new connection* 
- Put the Raspberry Pi VNC IP on *VNC Server* item and complete with the login
- Turns on the Raspberry Pi and connect with VNC Viewer to acess remotely

Installing dependecies
----------------------

- Open a terminal inside the Raspberry Pi
- Install the libraries with the command:

.. code-block:: bash

  $ pip install -r requirements.txt