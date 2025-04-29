EESchema Schematic File Version 2
LIBS:power
LIBS:device
LIBS:transistors
LIBS:conn
LIBS:linear
LIBS:regul
LIBS:74xx
LIBS:cmos4000
LIBS:adc-dac
LIBS:memory
LIBS:xilinx
LIBS:microcontrollers
LIBS:dsp
LIBS:microchip
LIBS:analog_switches
LIBS:motorola
LIBS:texas
LIBS:intel
LIBS:audio
LIBS:interface
LIBS:digital-audio
LIBS:philips
LIBS:display
LIBS:cypress
LIBS:siliconi
LIBS:opto
LIBS:atmel
LIBS:contrib
LIBS:valves
LIBS:nnclib
LIBS:NNC_ADS_2018-cache
EELAYER 25 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 2
Title "EEG wifi system"
Date "18 jan 2017"
Rev ""
Comp "NNC"
Comment1 "Marcio Moraes"
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Sheet
S 1400 1200 3300 2650
U 5AD0D78A
F0 "ADS1298" 60
F1 "file5AD0D78A.sch" 60
F2 "DVDD" I L 1400 1450 60 
F3 "~DRDY" I L 1400 3500 60 
F4 "DGND" I L 1400 1550 60 
F5 "SPI_MISO" O L 1400 2950 60 
F6 "SPI_SCLK" I L 1400 3050 60 
F7 "~SPI_~CS" I L 1400 3150 60 
F8 "START" I L 1400 3600 60 
F9 "CLK" I L 1400 3800 60 
F10 "SPI_MOSI" I L 1400 2850 60 
F11 "AGND" I L 1400 1350 60 
F12 "IN8N" I R 4700 1300 60 
F13 "IN8P" I R 4700 1400 60 
F14 "IN7N" I R 4700 1550 60 
F15 "IN7P" I R 4700 1650 60 
F16 "IN6N" I R 4700 1800 60 
F17 "IN6P" I R 4700 1900 60 
F18 "IN5N" I R 4700 2050 60 
F19 "IN5P" I R 4700 2150 60 
F20 "IN4N" I R 4700 2300 60 
F21 "IN4P" I R 4700 2400 60 
F22 "IN3P" I R 4700 2650 60 
F23 "IN3N" I R 4700 2550 60 
F24 "IN2P" I R 4700 2900 60 
F25 "IN2N" I R 4700 2800 60 
F26 "IN1P" I R 4700 3150 60 
F27 "IN1N" I R 4700 3050 60 
F28 "RLDOUT" O R 4700 3350 60 
F29 "RLDINV" I L 1400 2300 60 
F30 "CLKSEL" I L 1400 3700 60 
F31 "AVDD" I L 1400 1250 60 
F32 "RLDIN" I L 1400 2500 60 
F33 "VREFP" I L 1400 2200 60 
F34 "RLDREF" I L 1400 2400 60 
F35 "AVSS" I L 1400 1650 60 
F36 "TESTP_PACE_OUT1" I L 1400 1850 60 
F37 "TESTN_PACE_OUT2" I L 1400 1950 60 
F38 "~RESET" I L 1400 3400 60 
$EndSheet
Text Notes 1850 1300 3    60   ~ 0
POWER
Text Notes 4350 3250 1    60   ~ 0
OUT TO PATIENT
Text Notes 1950 3000 0    60   ~ 0
SPI Controller
Text Notes 1800 3650 0    60   ~ 0
uController pins
Text Notes 1900 2400 0    60   ~ 0
RLD circuit
Wire Wire Line
	1400 2850 950  2850
Text Label 950  2850 0    60   ~ 0
MOSI
Wire Wire Line
	1400 2950 950  2950
Wire Wire Line
	1400 3050 950  3050
Wire Wire Line
	1400 3150 950  3150
Text Label 950  2950 0    60   ~ 0
MISO
Text Label 950  3050 0    60   ~ 0
SPI_CLK
Text Label 950  3150 0    60   ~ 0
~CS
Wire Wire Line
	4700 1300 4950 1300
Wire Wire Line
	4700 1400 4950 1400
Wire Wire Line
	4700 1550 4950 1550
Wire Wire Line
	4700 1650 4950 1650
Wire Wire Line
	4700 1800 4950 1800
Wire Wire Line
	4700 1900 4950 1900
Wire Wire Line
	4700 2050 4950 2050
Wire Wire Line
	4700 2150 4950 2150
Wire Wire Line
	4700 2300 4950 2300
Wire Wire Line
	4700 2400 4950 2400
Wire Wire Line
	4700 2550 4950 2550
Wire Wire Line
	4700 2650 4950 2650
Wire Wire Line
	4700 2800 4950 2800
Wire Wire Line
	4700 2900 4950 2900
Wire Wire Line
	4700 3050 4950 3050
Wire Wire Line
	4700 3150 4950 3150
Wire Wire Line
	4700 3350 4950 3350
Text Label 4950 1300 0    60   ~ 0
IN8N
Text Label 4950 1400 0    60   ~ 0
IN8P
Text Label 4950 1550 0    60   ~ 0
IN7N
Text Label 4950 1650 0    60   ~ 0
IN7P
Text Label 4950 1800 0    60   ~ 0
IN6N
Text Label 4950 1900 0    60   ~ 0
IN6P
Text Label 4950 2050 0    60   ~ 0
IN5N
Text Label 4950 2150 0    60   ~ 0
IN5P
Text Label 4950 2300 0    60   ~ 0
IN4N
Text Label 4950 2400 0    60   ~ 0
IN4P
Text Label 4950 2550 0    60   ~ 0
IN3N
Text Label 4950 2650 0    60   ~ 0
IN3P
Text Label 4950 2800 0    60   ~ 0
IN2N
Text Label 4950 2900 0    60   ~ 0
IN2P
Text Label 4950 3050 0    60   ~ 0
IN1N
Text Label 4950 3150 0    60   ~ 0
IN1P
Text Label 4950 3350 0    60   ~ 0
RDLout
Text Label 6675 2375 2    60   ~ 0
RDLout
Wire Wire Line
	1150 1250 1400 1250
Wire Wire Line
	1150 1350 1400 1350
Wire Wire Line
	1150 1450 1400 1450
Wire Wire Line
	1150 1550 1400 1550
Wire Wire Line
	1150 1650 1400 1650
Wire Wire Line
	1150 1850 1400 1850
Wire Wire Line
	1150 1950 1400 1950
Wire Wire Line
	1150 2200 1400 2200
Wire Wire Line
	1150 2300 1400 2300
Wire Wire Line
	1150 2400 1400 2400
Wire Wire Line
	1150 2500 1400 2500
Wire Wire Line
	950  3500 1400 3500
Wire Wire Line
	950  3600 1400 3600
Wire Wire Line
	950  3700 1400 3700
Wire Wire Line
	950  3800 1400 3800
Text Label 3275 5525 2    60   ~ 0
MOSI
Text Label 3275 5025 2    60   ~ 0
MISO
Text Label 3275 5125 2    60   ~ 0
SPI_CLK
Text Label 3275 5225 2    60   ~ 0
~CS
Text Label 1150 1250 0    60   ~ 0
AVDD
Text Label 1150 1350 0    60   ~ 0
AGND
Text Label 1150 1450 0    60   ~ 0
DVDD
Text Label 1150 1550 0    60   ~ 0
DGND
Text Label 1150 1650 0    60   ~ 0
AVSS
Text Label 950  3500 0    60   ~ 0
~DRDY
Text Label 950  3600 0    60   ~ 0
START
Text Label 950  3700 0    60   ~ 0
CLKSEL
Text Label 950  3800 0    60   ~ 0
CLK
Text Label 1875 5175 2    60   ~ 0
AVDD
Text Label 1875 5275 2    60   ~ 0
AGND
Text Label 4450 5000 2    60   ~ 0
DVDD
Text Label 4450 5100 2    60   ~ 0
DGND
Text Label 1875 5375 2    60   ~ 0
AVSS
Text Label 3275 4925 2    60   ~ 0
~DRDY
Text Label 3275 5325 2    60   ~ 0
START
Wire Wire Line
	950  3400 1400 3400
Text Label 950  3400 0    60   ~ 0
~RESET
Text Label 3275 5425 2    60   ~ 0
~RESET
$Comp
L FFCfemale20 J1
U 1 1 5AD0F5CF
P 6675 1375
F 0 "J1" H 6925 1375 50  0000 C CNN
F 1 "FFCfemale20" H 6975 175 50  0000 C CNN
F 2 "NNClib:FFCfemale20" H 6875 775 50  0001 C CNN
F 3 "" H 6875 775 50  0001 C CNN
	1    6675 1375
	1    0    0    -1  
$EndComp
Text Label 6675 1575 2    60   ~ 0
IN8N
Text Label 7175 1575 0    60   ~ 0
IN8P
Text Label 6675 1675 2    60   ~ 0
IN7N
Text Label 7175 1675 0    60   ~ 0
IN7P
Text Label 6675 1775 2    60   ~ 0
IN6N
Text Label 7175 1775 0    60   ~ 0
IN6P
Text Label 6675 1875 2    60   ~ 0
IN5N
Text Label 7175 1875 0    60   ~ 0
IN5P
Text Label 6675 1975 2    60   ~ 0
IN4N
Text Label 7175 1975 0    60   ~ 0
IN4P
Text Label 6675 2075 2    60   ~ 0
IN3N
Text Label 7175 2075 0    60   ~ 0
IN3P
Text Label 6675 2175 2    60   ~ 0
IN2N
Text Label 7175 2175 0    60   ~ 0
IN2P
Text Label 6675 2275 2    60   ~ 0
IN1N
Text Label 7175 2275 0    60   ~ 0
IN1P
Text Label 7175 1475 0    60   ~ 0
RDLout
Text Label 7175 2375 0    60   ~ 0
AGND
Text Label 6675 1475 2    60   ~ 0
AGND
$Comp
L Conn_01x08 SPI1
U 1 1 5AD13533
P 3475 5225
F 0 "SPI1" H 3475 5625 50  0000 C CNN
F 1 "Conn_01x08" H 3475 4725 50  0000 C CNN
F 2 "Pin_Headers:Pin_Header_Straight_1x08_Pitch2.00mm" H 3475 5225 50  0001 C CNN
F 3 "" H 3475 5225 50  0001 C CNN
	1    3475 5225
	1    0    0    -1  
$EndComp
$Comp
L Conn_01x03 APwd1
U 1 1 5AD21670
P 2075 5275
F 0 "APwd1" H 2075 5475 50  0000 C CNN
F 1 "Conn_01x03" H 2075 5075 50  0000 C CNN
F 2 "Pin_Headers:Pin_Header_Straight_1x03_Pitch2.00mm" H 2075 5275 50  0001 C CNN
F 3 "" H 2075 5275 50  0001 C CNN
	1    2075 5275
	1    0    0    -1  
$EndComp
$Comp
L Conn_01x02 DPwd1
U 1 1 5AD21769
P 4650 5000
F 0 "DPwd1" H 4650 5100 50  0000 C CNN
F 1 "Conn_01x02" H 4650 4800 50  0000 C CNN
F 2 "Pin_Headers:Pin_Header_Straight_1x02_Pitch2.00mm" H 4650 5000 50  0001 C CNN
F 3 "" H 4650 5000 50  0001 C CNN
	1    4650 5000
	1    0    0    -1  
$EndComp
Text Label 3275 5625 2    60   ~ 0
CLK
$Comp
L Conn_01x01 jDGND1
U 1 1 5B082391
P 6500 4100
F 0 "jDGND1" H 6500 4200 50  0000 C CNN
F 1 "Conn_01x01" H 6500 4000 50  0000 C CNN
F 2 "SMD_Packages:1Pin" H 6500 4100 50  0001 C CNN
F 3 "" H 6500 4100 50  0001 C CNN
	1    6500 4100
	1    0    0    -1  
$EndComp
Text Label 6300 4100 2    60   ~ 0
DGND
$EndSCHEMATC
