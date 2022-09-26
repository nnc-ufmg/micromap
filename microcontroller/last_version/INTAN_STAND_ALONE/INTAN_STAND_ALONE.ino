/*############################################################################################################
        includes.
############################################################################################################*/
#include "INTAN_STAND_ALONE.h"

/*############################################################################################################
        Setup.
############################################################################################################*/
uint16_t xxx[32];
void setup() {
  // put your setup code here, to run once:

  SerialUSB.begin(50000000); //Transferencia de dados via USB HighSpeed ... até 50MB
  for(int i=0;i<32;i++) xxx[i]=i;
  //Serial.begin(9600); //SAIDA SERIAL NORMAL UART

/*
 * TEMOS QUE VER A NECESSIDADE DE ESPERAR POR ESTES SINAIS DE CONECÇÃO ENTRE OS PERIFÉRICOS
 */
//  while (!Serial) {
     // wait for serial port to connect. Needed for native USB port only
//  }
//  while (!SerialUSB) {
     // wait for serial port to connect. Needed for native USB port only
//  }
  

   USART0config(8); 
   INTANtelemetry.setupINTAN_NNC(9, 0xFFFFFFFF, 2000, 1000, 22); //void setupINTAN_NNC(int xxSSpin, uint32_t XXchannels, uint16_t XXfs, uint16_t XXfH, double XXfL);
   //INTANtelemetry.setupSPI(9); delay(1000);
  //INTANtelemetry.initializeRHD_default();
  //INTANtelemetry.wait_for_configuration();
  //start_aq(INTANtelemetry.channels, INTANtelemetry.fs, INTANtelemetry.fH, INTANtelemetry.fL);
  
  
  //start_aqT1(INTANtelemetry.fs);


  //SerialUSB.println("ALGUMA COISA FOI .....");

}

/*############################################################################################################
        Loop.
############################################################################################################*/

bool flip=true;


void loop() 
  {

  if(Serial.available()) //deal with what comes in
    {
      
    }
  
  if(SerialUSB.available()) //deal with what comes in
    {
      INTANtelemetry.USBserialINTAN_NNCread();
    }
  
  if(bGraveUSART) //Send buffered data via SerialUSB
    {
    
    bGraveUSART=false;
    
    noInterrupts();
    USART0txferALL(8,INTANtelemetry.buffer,INTANtelemetry.buffer,INTANtelemetry.channel_count);
    interrupts();
   
    SerialUSB.write((char *)INTANtelemetry.buffer,64);

    }

  }
