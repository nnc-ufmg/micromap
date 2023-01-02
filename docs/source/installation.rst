Installation
============

To get the program up and running of your Raspberry Pi
you will need to:

1. Install Raspberry Pi OS 
2. Configure the VNC package in the Raspberry Pi
3. Install the the dependecies on the Raspberry Pi

Raspberry Pi OS installation
------------------------------

- Install the Raspberry Pi OS on your Raspberry Pi


Raspberry Pi VNC Configuration
------------------------------

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
