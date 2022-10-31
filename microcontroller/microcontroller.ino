/*  INCLUDES
 *  Initializes the librarys that will be used
 */
#include "microcontroller.h"

/*  SETUP THE COMMUNICATION
 *  This function initializes the USB and the SPI ports
 */
void setup() 
{
  SerialUSB.begin(50000000);                                                                      // Starts the high speed USB transfer port (50MB)
  USART0config(8); 
  intan_rhd_chip.init_default(9, 13, 0xFFFFFFFF, 2000, 16, 1);                                    // Starts the SPI bus and configures INTAN RHD
}

/*  COMMUNICATION LOOP
 *  This function initializes the USB and the SPI communication
 */
void loop() 
{
  if(Serial.available())                                                                          // Deal with what comes via USB
  {
      
  }
  
  if(SerialUSB.available())                                                                       // Deal with what comes in via high speed USB
  {
    intan_rhd_chip.setting_command();                                                             // Calls the function that will handle external configuration commands sent via USB
  }
  
  if(transfer_data_flag)                                                                          // If has data in buffer (flag is True)
  {
    transfer_data_flag = false;                                                                   // Sets the flag to Flase
    SerialUSB.write((byte *)intan_rhd_chip.buffer, 2*intan_rhd_chip.channel_count);               // Sends out all data collected via USB
  }
}


/*
 * TRASH TO SAVE ... DELETE LATER
 * 
 * 
//    noInterrupts();                                                                               // Locks any other interrupt on Arduino
//    transfer_dataUSART0(8, intan_rhd_chip.buffer, intan_rhd_chip.buffer, intan_rhd_chip.channel_count);
//    interrupts();                                                                                 // Unlocks any other interrupt on Arduino
 */
