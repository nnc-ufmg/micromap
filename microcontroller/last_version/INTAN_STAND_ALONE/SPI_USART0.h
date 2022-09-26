/*-------------------------------------------------------------------------
Instance   Peripheral  Signal  SPI Master  SPI Slave  I/O Line  Arduino Pin
---------------------------------------------------------------------------
USART0     A, ID 17    RXD0    MISO        MOSI       PA10      RX1     19
USART0     A, ID 17    TXD0    MOSI        MISO       PA11      TX1     18
USART0     A, ID 17    RTS0    CS          x          PB25      D2       2
USART0     A, ID 17    CTS0    x           CS         PB26      D22     22
USART0     B, ID 17    SCK0    SCK         SCK        PA17      SDA1    70
---------------------------------------------------------------------------
USART1     A, ID 18    RXD1    MISO        MOSI       PA12      RX2     17
USART1     A, ID 18    TXD1    MOSI        MISO       PA13      TX2     16
USART1     A, ID 18    RTS1    CS          x          PA14      D23     23
USART1     A, ID 18    CTS1    x           CS         PA15      D24     24
USART1     A, ID 18    SCK1    SCK         SCK        PA16      A0      54
----------------------------------------------------------------------------
Register                            Page  Arduino          Settings 
USART Mode Register                 839   USART1->US_MR    CLK0, 8_BIT, SPI_MASTER, CPOL, CPHA
USART Baud Rate Generator Register  855   USART1->US_BRGR  CD
USART Transmit Holding Register     854   USART1->US_THR   Use to write data
USART Receive Holding Register      853   USART1->US_RHR   Use to read data
USART Channel Status Register       849   USART1->US_RHR   Use to control SPI tranfers
----------------------------------------------------------------------------
*/
void USART0config(int CSel) {
  Serial1.begin(9600); delay(1000);
  pinMode(CSel,OUTPUT);
  digitalWriteDirect(CSel,HIGH);
  
  USART0->US_WPMR = 0x55534100;   // Unlock the USART Mode register
  USART0->US_MR |= 0x408CE;       // Set Mode to CLK0=1, 8_BIT, SPI_MASTER
  USART0->US_BRGR = 7;           // Clock Divider (SCK = 12MHz)

  PIOA->PIO_WPMR = 0x50494F00;    // Unlock PIOA Write Protect Mode Register
  PIOB->PIO_WPMR = 0x50494F00;    // Unlock PIOB Write Protect Mode Register
  PIOB->PIO_ABSR |= (0u << 25);   // CS: Assign A14 I/O to the Peripheral A function
  PIOB->PIO_PDR |= (1u << 25);    // CS: Disable PIO control, enable peripheral control
  PIOA->PIO_ABSR |= (1u << 17);   // SCK: Assign A16 I/O to the Peripheral B function
  PIOA->PIO_PDR |= (1u << 17);    // SCK: Disable PIO control, enable peripheral control
  PIOA->PIO_ABSR |= (0u << 10);   // MOSI: Assign PA13 I/O to the Peripheral A function
  PIOA->PIO_PDR |= (1u << 10);    // MOSI: Disable PIO control, enable peripheral control
  PIOA->PIO_ABSR |= (0u << 11);   // MISO: Assign A12 I/O to the Peripheral A function
  PIOA->PIO_PDR |= (1u << 11);    // MISO: Disable PIO control, enable peripheral control
}

uint16_t USART0txfer(uint16_t txBytes,int CSel ) {

  //noInterrupts();
  byte msg2 = txBytes & 0xFF; // least significant byte of value
  byte msg1 = (txBytes >> 8) & 0xFF; // 2nd most significant nibble of value

  digitalWriteDirect(CSel, LOW); // set CS pin LOW (begin SPI transfer)
  //while ((USART0->US_CSR & 0x200)==0); // check txempty before sending the first byte
  
  USART0->US_THR = msg1; // send first byte
  
  while ((USART0->US_CSR & 0x200)==0); // check txempty before sending the second byte
  //while ((USART0->US_CSR & 0x1)==0); // check txempty before sending the first byte XXXXXXXXX
  //while ((USART0->US_CSR & 0x2)==0); // check txempty before sending the second byte
  msg1=USART0->US_RHR; // Receive first byte

  
  USART0->US_THR = msg2; // send second byte
  
  while ((USART0->US_CSR & 0x200)==0); // check txempty before sending the second byte
  //while ((USART0->US_CSR & 0x2)==0); // check txempty before setting CS HIGH
  //while ((USART0->US_CSR & 0x1)==0); // check txempty before sending the first byte XXXXXXXXX
  msg2=USART0->US_RHR; // Receive second byte
 
  digitalWriteDirect(CSel, HIGH); // set CS pin HIGH (end SPI transfer)

  //interrupts();
  return((msg1<<8)|msg2); //return uint16_t
}
/*
 * Buffer out is the outgoing 16bit from master to slave ... BufferIn is the incoming RX from slave
*/
uint16_t USART0txferALL(int CSel,uint16_t *XXbufferOUT,uint16_t *XXbufferIN,int xxCount) {

  //noInterrupts();
  int xc=0;
  char *bufftempOUT=(char *)XXbufferOUT;
  char *bufftempIN=(char *)XXbufferIN;
  while (xc<xxCount)
    {
      digitalWriteDirect(CSel, LOW); // set CS pin LOW (begin SPI transfer)
      USART0->US_THR = bufftempOUT[xc*2+1]; // send first byte
      while ((USART0->US_CSR & 0x200)==0); // check txempty before sending the second byte
      bufftempIN[xc*2+1]=USART0->US_RHR; // Receive first byte
      USART0->US_THR = bufftempOUT[xc*2]; // send second byte
      while ((USART0->US_CSR & 0x200)==0); // check txempty before sending the second byte
      bufftempIN[xc*2+1]=USART0->US_RHR; // Receive second byte
      digitalWriteDirect(CSel, HIGH); // set CS pin HIGH (end SPI transfer)
      xc++;
    }

}

/*
 * PROGRAMMING FOR UART1 ... PLEASE CHECK SPI_UART FILE, IT IS MUCH MORE COMPREEHENSIVE
 */
void USART1config() {
  USART1->US_WPMR = 0x55534100;   // Unlock the USART Mode register
  USART1->US_MR |= 0x408CE;       // Set Mode to CLK0=1, 8_BIT, SPI_MASTER
  USART1->US_BRGR = 21;           // Clock Divider (SCK = 4MHz)

  PIOA->PIO_WPMR = 0x50494F00;    // Unlock PIOA Write Protect Mode Register
  PIOB->PIO_WPMR = 0x50494F00;    // Unlock PIOB Write Protect Mode Register
  PIOA->PIO_ABSR |= (0u << 14);   // CS: Assign A14 I/O to the Peripheral A function
  PIOA->PIO_PDR |= (1u << 14);    // CS: Disable PIO control, enable peripheral control
  PIOA->PIO_ABSR |= (0u << 16);   // SCK: Assign A16 I/O to the Peripheral A function
  PIOA->PIO_PDR |= (1u << 16);    // SCK: Disable PIO control, enable peripheral control
  PIOA->PIO_ABSR |= (0u << 13);   // MOSI: Assign PA13 I/O to the Peripheral A function
  PIOA->PIO_PDR |= (1u << 13);    // MOSI: Disable PIO control, enable peripheral control
  PIOA->PIO_ABSR |= (0u << 12);   // MISO: Assign A12 I/O to the Peripheral A function
  PIOA->PIO_PDR |= (1u << 12);    // MISO: Disable PIO control, enable peripheral control
}
