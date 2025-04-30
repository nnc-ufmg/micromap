/* SERIAL DIGITAL WRITE   
 *  
 */
inline void digital_write_direct(int pin, boolean val){
  if(val) g_APinDescription[pin].pPort -> PIO_SODR = g_APinDescription[pin].ulPin;
  else    g_APinDescription[pin].pPort -> PIO_CODR = g_APinDescription[pin].ulPin;
}

/* SERIAL DIGITAL READ 
 *  
 */
inline int digital_read_direct(int pin){
  return !!(g_APinDescription[pin].pPort -> PIO_PDSR & g_APinDescription[pin].ulPin);
}

//EXTERN DECLARATIONS 
extern bool transfer_data_flag;
extern void start_acquisition(uint16_t sampling_frequency);
extern void stop_acquisition();

/*  INCLUDES
 *  Initializes the librarys that will be used
 */
#include "Arduino.h"
#include "SPI.h"
#include "SD.h"
#include "DueTimer.h"
#include "spi_usart.h" 
#include "ads_functions.h"

/*  GLOBAL VARIABLE
 *  Defines variables that will be used in another parts of the program
 */
bool transfer_data_flag = false;
void acquisition_interrupt();
ads_1298_chip_class ads_1298_chip;

/*  START ACQUISITION
 *  This function starts the thread that will be in charge of making records at regular intervals
 *
 *  Parameters:
 *  - sampling_frequency ...... Frequency that the thread will be called
 */
void start_acquisition(uint16_t sampling_frequency){
  attachInterrupt(digitalPinToInterrupt(ads_1298_chip.data_ready), acquisition_interrupt, FALLING);
}

// For testing purposes
// void start_acquisition(uint16_t sampling_frequency)
// {
//   Timer4.attachInterrupt(acquisition_interrupt);    // Defines the interrupt/worker function for the thread
//   Timer4.setFrequency(sampling_frequency);          // Configures the frequency that the thread will be called
//   Timer4.start();                                   // Starts the thread
// }

/*  INTERRUPT FOR DATA ACQUISITION
 *  This function will acquire the channels that are configured with high temporal priority
 */
void acquisition_interrupt(){
  noInterrupts();                                   // Locks any other interrupt on Arduino
  ads_1298_chip.convert_channels();
  interrupts();                                     // Unlocks any other interrupt on Arduino
} 

/*  STOP ACQUISITION
 *  This function stops the thread that will be in charge of making records at regular intervals
 */
void stop_acquisition(){
  detachInterrupt(digitalPinToInterrupt(ads_1298_chip.data_ready));                                    // Stops the thread
}
