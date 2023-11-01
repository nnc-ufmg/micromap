/*
 * adsCommand.h
 *
 * Copyright (c) 2013 by Adam Feuer <adam@adamfeuer.com>
 * Copyright (c) 2012 by Chris Rorden
 * Copyright (c) 2012 by Steven Cogswell and Stefan Rado
 *
 * This library is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this library.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

#include "Arduino.h"

// constants define pins on Arduino 

// Arduino Due
// HackEEG Shield v1.3.1
const int IPIN_RESET  = 47;

const int PIN_START = 53;
const int IPIN_DRDY = 25;
const int PIN_CS = 4;
const int PIN_DOUT = 75;//SPI out
const int PIN_DIN = 74;//SPI in MISO
const int PIN_SCLK = 76;//SPI clock MOSI
//const int PIN_CLK = 37; //clock (não usado pois clock é interno)

//function prototypes
void adc_wreg(int reg, int val); //write register
void adc_send_command(int cmd); 
void adc_send_command_leave_cs_active(int cmd); 
int adc_rreg(int reg); //read register
