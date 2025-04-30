/*  INCLUDES
 *  Initializes the librarys that will be used
 */
#include "microcontroller_ads.h"

/*  SETUP THE COMMUNICATION
 *  This function initializes the USB and the SPI ports
 */
void setup() 
{
  SerialUSB.begin(50000000);                                                                      // Starts the high speed USB transfer port (50MB)
  USART0config(8); 
  ads_1298_chip.init_default(4, 13, 25, 53, 2000, 47);
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
    //intan_rhd_chip.setting_command();                                                             // Calls the function that will handle external configuration commands sent via USB
    ads_1298_chip.setting_command();
  }
  
  if(transfer_data_flag)                                                                          // If has data in buffer (flag is True)
  {
    transfer_data_flag = false;                                                                   // Sets the flag to Flase
    SerialUSB.write((byte *)ads_1298_chip.buffer, 3*ads_1298_chip.channel_count + 3);
  }
}


