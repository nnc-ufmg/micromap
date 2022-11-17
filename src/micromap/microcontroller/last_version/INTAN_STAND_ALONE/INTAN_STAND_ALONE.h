/*
 * Look at this for help: https://forum.arduino.cc/t/port-manipulation-pinx-commands-with-arduino-due/127121/13
 * This is for FAST DIGITAL PIN SET AND READ
 */
inline void digitalWriteDirect(int pin, boolean val){
  if(val) g_APinDescription[pin].pPort -> PIO_SODR = g_APinDescription[pin].ulPin;
  else    g_APinDescription[pin].pPort -> PIO_CODR = g_APinDescription[pin].ulPin;
}

inline int digitalReadDirect(int pin){
  return !!(g_APinDescription[pin].pPort -> PIO_PDSR & g_APinDescription[pin].ulPin);
}

  //  File myFile; 


  bool bGraveUSART=false;

  #include "Arduino.h"
  #include "SPI.h"
  #include "SD.h"
  #include "DueTimer.h"
  #include "SPI_USART0.h" 
  #include "INTAN_NNC.h"

  

/*############################################################################################################
        GLOBAL functions.
############################################################################################################*/ 
  void isr_aqtimer();
  void isr_aqtimerT1();
 
/*############################################################################################################
        Global variables.
############################################################################################################*/
 
  INTAN_NNC INTANtelemetry;


/*
 * THESE ARE TESTS THAT I SHOULD RUN BEFORE IMPLEMENTING THE FINAL SOLLUTION FOR THIS APPLICAITON
 * 1) Just one SPI transfer every 
 */

/*############################################################################################################
        void start_aq(uint16_t channels, uint16_t fsample, uint16_t fH, float fL)

This function sets RHD filters cutoff frequency as specified by parameters fL and fH and starts
acquisition on specified channels by building the sequence of commands (see function buildsequence(channels))
and activating the two timers aqtimer and bufferstimer, responsible for periodically sending the sequence of
commands to INTAN and checking buffers (if full, then send to client).
############################################################################################################*/
    void start_aqT1(uint16_t fsample)
    {
        /* Preciso escrever código para verificar se os parâmetros passados são válidos.
        A taxa de amostragem máxima é função da frequência do clock SPI e do número de canais
        que o usuário deseja amostrar.
        */
/*
        // Set filters cutoff frequency and build sequence of CONVERT commands.
        INTANtelemetry.setfHIGH(fH);
        INTANtelemetry.setfLOW(fL);
        INTANtelemetry.buildsequence(0XFFFFFFFF);

        // Set buffers
        INTANtelemetry.setbuffers();
        delay(1000);

*/
        

        Timer4.attachInterrupt(isr_aqtimerT1);
        Timer4.setFrequency(fsample);
        Timer4.start();
    }

void stop_aqT1()
    {
        Timer4.stop();
    }

/*############################################################################################################
    void isr_aqtimerT1()
############################################################################################################*/
    void isr_aqtimerT1()
    {
      noInterrupts();
      INTANtelemetry.mytransferALL();
      interrupts();
      
    } // End of isr_aqtimer


    
/*############################################################################################################
        void start_aq(uint16_t channels, uint16_t fsample, uint16_t fH, float fL)

This function sets RHD filters cutoff frequency as specified by parameters fL and fH and starts
acquisition on specified channels by building the sequence of commands (see function buildsequence(channels))
and activating the two timers aqtimer and bufferstimer, responsible for periodically sending the sequence of
commands to INTAN and checking buffers (if full, then send to client).
############################################################################################################*/
    void start_aq(uint16_t channels, uint16_t fsample, uint16_t fH, double fL)
    {
        /* Preciso escrever código para verificar se os parâmetros passados são válidos.
        A taxa de amostragem máxima é função da frequência do clock SPI e do número de canais
        que o usuário deseja amostrar.
        */
/*
        // Set filters cutoff frequency and build sequence of CONVERT commands.
        INTANtelemetry.setfHIGH(fH);
        INTANtelemetry.setfLOW(fL);
        INTANtelemetry.buildsequence(0XFFFFFFFF);

        // Set buffers
        INTANtelemetry.setbuffers();
        delay(1000);

        if (INTANtelemetry.lengthseq >2)
          countseq = 2;
        //SerialUSB.write((char*)&fsample, 2);
        //SerialUSB.write((char*)&INTANtelemetry.channel_count, 2);
        //uint16_t result = INTANtelemetry.channel_count*fsample;
        //SerialUSB.write((char*)&result, 2);
        // Configure timer
        Timer4.attachInterrupt(isr_aqtimer);
        Timer4.setFrequency(double(fsample)*INTANtelemetry.channel_count);
        Timer4.start();
*/
    }

/*############################################################################################################
    void isr_aqtimer()
############################################################################################################*/
/*
    void isr_aqtimer()
    {
      noInterrupts();
      digitalWrite(22, !digitalRead(22));
      buffer[buffer_position] = INTANtelemetry.mytransfer16(INTANtelemetry.sequence[countseq]);
      //buffer[buffer_position] = aux2;
      //aux2++;

      buffer_position++;
      countseq++;
        
      if (buffer_position>=(buffer_size/sizeof(uint16_t))) 
        buffer_position=0;

      if (countseq >= INTANtelemetry.lengthseq)
        countseq=0;
        
      interrupts();
      
    } // End of isr_aqtimer

*/
