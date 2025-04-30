#ifndef ads1298_functions_h
#define ads1298_functions_h

#define SPI_CLOCK_DIVIDER 5
#define ID 0x00
// global settings
#define CONFIG1 0x01
#define CONFIG2 0x02
#define CONFIG3 0x03
#define LOFF 0x04

// channel specific settings
#define CHnSET 0x04
#define CH1SET CHnSET + 1
#define CH2SET CHnSET + 2
#define CH3SET CHnSET + 3
#define CH4SET CHnSET + 4
#define CH5SET CHnSET + 5
#define CH6SET CHnSET + 6
#define CH7SET CHnSET + 7
#define CH8SET CHnSET + 8
#define RLD_SENSP 0x0d
#define RLD_SENSN 0x0e
#define LOFF_SENSP 0x0f
#define LOFF_SENSN 0x10
#define LOFF_FLIP 0x11

// lead off status
#define LOFF_STATP 0x12
#define LOFF_STATN 0x13

// other
#define GPIO 0x14
#define PACE 0x15
#define RESP 0x16
#define CONFIG4 0x17
#define WCT1 0x18
#define WCT2 0x19


// CONFIG1
#define HR 0x80        // high-resolution
#define DAISY_EN 0x40  // daisy-chain enable
#define CLK_EN 0x20    // internal clock enable
#define DR2 0x04       // data rate
#define DR1 0x02       // ''
#define DR0 0x01       // ''

// CONFIG2
#define WCT_CHOP 0x20
#define INT_TEST 0x10
#define TEST_AMP 0x04
#define TEST_FREQ1 0x01
#define TEST_FREQ0 0x00

// CONFIG3
#define PD_REFBUF 0x80
#define VREF_4V 0x20
#define RLD_MEAS 0x10
#define RLDREF_INT 0x08
#define PD_RLD 0x04
#define RLD_LOFF_SENS 0x02
#define RLD_STAT 0x01
#define CONFIG3_const 0x40

// LOFF
#define COMP_TH2 0x80
#define COMP_TH1 0x40
#define COMP_TH0 0x20
#define VLEAD_OFF_EN 0x10
#define ILEAD_OFF1 0x08
#define ILEAD_OFF0 0x04
#define FLEAD_OFF1 0x02
#define FLEAD_OFF0 0x01

// CHnSET
#define PDn 0x80
#define PD_n 0x80
#define GAINn2 0x40
#define GAINn1 0x20
#define GAINn0 0x10
#define MUXn2 0x04
#define MUXn1 0x02
#define MUXn0 0x01
#define CHnSET_const 0x00
#define GAIN_1X GAINn0
#define GAIN_2X GAINn1
#define GAIN_3X (GAINn1 | GAINn0)
#define GAIN_4X GAINn2
#define GAIN_6X 0x00
#define GAIN_8X (GAINn2 | GAINn0)
#define GAIN_12X (GAINn2 | GAINn1)
#define ELECTRODE_INPUT 0x00
#define SHORTED MUXn0
#define RLD_INPUT MUXn1
#define MVDD (MUXn1 | MUXn0)
#define TEMP MUXn2
#define TEST_SIGNAL (MUXn2 | MUXn0)
#define RLD_DRP (MUXn2 | MUXn1)
#define RLD_DRN (MUXn2 | MUXn1 | MUXn0)

const char *hardwareType = "unknown";

class ads_1298_chip_class {
public:
  /*  VARIABLES DECLARATION
     *  Declaration of program variables
     */
  ads_1298_chip_class();         // Constructor
  uint16_t sampling_frequency;   // Default sampling frequency
  
  int serial_pinout = 9;           // Output pin for chip selection
  int sync_pinout = 13;            // Output pin for syncronization trigger  --NÃO ENTENDI--
  int data_ready = 25;
  int pin_start = 53;
  int pin_reset = 47;
  const int channel_count = 8;
  uint8_t buffer[27];           // 3 bytes * 8 canais = 24 bytes + 3 (status word) = 27 bytes
  bool dataTestMode = false;

  uint32_t packages_received = 0;  // Count total number of packages with channel DATA received from ADS

  bool usb_serial_flag = true;  // USB connection flag

  /*  METHODS DECLARATION
     *  Declaration of program methods
     */
  void transfer_data(int cmd);  // Declares function thar sends 16-bit command to RHD chip

  void convert_channels();  // Declares function that sends to RHD chip all converts commands

  void write(uint8_t register_number, uint8_t data);  // Declares function that writes to ADS chip registers
  uint8_t read(uint8_t register_number);                 // Declares function that reads to ADS chip registers
  void start();                                        // Start/restart (synchronize) conversions
  void stop();                                         // Stop conversion
  void reset();                                        // Reset the device
  void sdatac();                                       // Stop Read Data Continuous mode
  void rdatac();                                       // Start Read Data Continuous mode

  void set_sampling_frequency(uint16_t sampling_frequency);
  void setup_spi(int p_serial_pinout, int p_sync_pinout);  // Declares function that setups the RHD chip
  void init_default(int p_serial_pinout, int p_sync_pinout,
                    int p_data_ready, int p_start,  
                    uint16_t p_sampling_frequency, int p_reset);  // Declares function that setups the communication with RHD chip
  void setting_command();                                         // Declares function that reads the serial port to configures the RHD chip
  void treat_command(byte *command_buffer);                       // Declares function that reads the serial message and sents to configures the RHD chip



private:

protected:
};

ads_1298_chip_class::ads_1298_chip_class()
{
  
}


/*  SETUP SPI
 * 
 *  This function initializes the SPI bus
 */
void ads_1298_chip_class::setup_spi(int p_serial_pinout, int p_sync_pinout) {
  serial_pinout = p_serial_pinout;  // Serial pin
  sync_pinout = p_sync_pinout;      // Serial clock ou chip select
  pinMode(serial_pinout, OUTPUT);   // Defines the pin mode
  pinMode(sync_pinout, OUTPUT);     // Defines the pin mode
  SPI.begin();                      // Starts the SPI bus
  SPI.setBitOrder(MSBFIRST); // MSBFIRST or LSBFIRST 
  SPI.setClockDivider(SPI_CLOCK_DIVIDER); 
  SPI.setDataMode(SPI_MODE1);   // SPI_MODE0, SPI_MODE1; SPI_MODE2; SPI_MODE3
}

/*  INIT DEFAULT
 *  
 * todos os pinos conectados, reset start etc 
 */
void ads_1298_chip_class::init_default(int p_serial_pinout, int p_sync_pinout, int p_data_ready, int p_start, uint16_t p_sampling_frequency, int p_reset) {
  sampling_frequency = p_sampling_frequency;
  data_ready = p_data_ready;
  pin_start = p_start;
  pin_reset = p_reset;
  pinMode(data_ready, INPUT);
  pinMode(pin_start, OUTPUT);
  pinMode(pin_reset, OUTPUT);

  setup_spi(p_serial_pinout, p_sync_pinout);  //Here p_serial_pinout is saved into INTAN_NNC SSpin variable ...
  delay(500);
  delay(10);
  delay(1);

  digitalWrite(pin_reset, HIGH);
  delay(1000);// *optional
  digitalWrite(pin_reset, LOW);
  delay(1);// *optional
  digitalWrite(pin_reset, HIGH);
  delay(1);  // *optional Wait for 18 tCLKs AKA 9 microseconds, we use 1 millisecond

  delay(1000);
  sdatac();
  delay(100);

  // configurações iniciais de registradores
  write(GPIO, 0);
  write(CONFIG3, PD_REFBUF | CONFIG3_const | VREF_4V);
  write(CONFIG1, 0x85);
  
  set_sampling_frequency(sampling_frequency);
  //write(CONFIG2, 0x00 | INT_TEST |  TEST_AMP | TEST_FREQ1);

  for (int i = 1; i <= 8; i++) {
    write(CHnSET + i, ELECTRODE_INPUT | GAIN_12X);  //report this channel with x6 gain
    //write(CHnSET + i, TEST_SIGNAL | GAIN_12X); //create square wave
    //write(CHnSET + i,SHORTED); //disable this channel
    //write(CHnSET + i, 0x01); //offset measurement
  }
  delay(100);
}


/*  TRANSFER DATA
 *  
 *  
 */
void ads_1298_chip_class::transfer_data(int cmd) {
  digital_write_direct(serial_pinout, LOW);
  SPI.transfer(cmd);
  delayMicroseconds(1);
  digital_write_direct(serial_pinout, HIGH);
}

/* CONVERT CHANNELS
 *
 *
 */
void ads_1298_chip_class::convert_channels() {
  if (dataTestMode) {
    // Gera pacote de teste simulando ADS1298
    buffer[0] = 0xAA;  // status byte 1
    buffer[1] = 0xAA;  // status byte 2
    buffer[2] = 0xAA;  // status byte 3

    for (int ch = 0; ch < channel_count; ch++) {
      uint32_t val = ch + 1;  // Valor de teste por canal (1, 2, ..., 8)

      // Monta 3 bytes big endian
      buffer[3 + 3 * ch + 0] = (val >> 16) & 0xFF;  // MSB
      buffer[3 + 3 * ch + 1] = (val >> 8) & 0xFF;
      buffer[3 + 3 * ch + 2] = val & 0xFF;          // LSB
    }

  } else {
    // Modo normal: lê do ADS
    digital_write_direct(serial_pinout, LOW);
    for (int i = 0; i < 27; i++) {
      buffer[i] = SPI.transfer(0xFF);
    }
    digital_write_direct(serial_pinout, HIGH);
  }

  packages_received++;
  transfer_data_flag = true;
}

/*  WRITE COMMAND
 * 
 *  
 */
void ads_1298_chip_class::write(uint8_t register_number, uint8_t data) {
  uint8_t writecommand = 0x40 | register_number;

  digital_write_direct(serial_pinout, LOW);
  SPI.transfer(writecommand);
  SPI.transfer(0);
  SPI.transfer(data);
  delayMicroseconds(1);
  digital_write_direct(serial_pinout, HIGH);
}

/*  READ COMMAND
 * 
 *  
 */
uint8_t ads_1298_chip_class::read(uint8_t register_number) {
  uint8_t writecommand = 0x20 | register_number;
  int out = 0;

  digital_write_direct(serial_pinout, LOW);
  SPI.transfer(writecommand); // 0x21    0010 0001
  delayMicroseconds(5);
  SPI.transfer(0);            //0x00     0000 0000
  delayMicroseconds(5);
  out = SPI.transfer(0);      //         0000 0000
  delayMicroseconds(1);
  digital_write_direct(serial_pinout, HIGH);
  return out;
}

void ads_1298_chip_class::set_sampling_frequency(uint16_t sampling_frequency){
  byte dataRateSetting;

  switch (sampling_frequency) {
        case 32000:
            dataRateSetting = 0b000; // DR[2:0] = 000
            break;
        case 16000:
            dataRateSetting = 0b001; // DR[2:0] = 001
            break;
        case 8000:
            dataRateSetting = 0b010; // DR[2:0] = 010
            break;
        case 4000:
            dataRateSetting = 0b011; // DR[2:0] = 011
            break;
        case 2000:
            dataRateSetting = 0b100; // DR[2:0] = 100
            break;
        case 1000:
            dataRateSetting = 0b101; // DR[2:0] = 101
            break;
        case 500:
            dataRateSetting = 0b110; // DR[2:0] = 110
            break;
        case 250:
            dataRateSetting = 0b111; // DR[2:0] = 111
            break;
        default:
            // Invalid frequency, handle error
            Serial.println("Invalid sampling frequency.");
            return;
    }
    // Calculate the value to write to CONFIG1 register
    byte config1Value = (0b00010000 | dataRateSetting); // Other bits are set as default

  write(CONFIG1, config1Value);
}

/*  START COMMAND
 * 
 *  
 */
void ads_1298_chip_class::start() {
  transfer_data(0x08);
}

/*  STOP COMMAND
 * 
 *  
 */
void ads_1298_chip_class::stop() {
  transfer_data(0x0A);
}

/*  RESET COMMAND
 * 
 *  
 */
void ads_1298_chip_class::reset() {
  transfer_data(0x06);
}

/*  SDATAC COMMAND
 * 
 *  
 */
void ads_1298_chip_class::sdatac() {
  transfer_data(0x11);
}

/*  RDATAC COMMAND
 * 
 *  
 */
void ads_1298_chip_class::rdatac() {
  transfer_data(0x10);
}

/*  SETTINGS COMMAND 
 * 
 *  This function allows an interface to control data acquisition settings, modifying Arduino and Intan 
 *  chip attributes. It collects the message and forwards it to the command handler function.
 */
void ads_1298_chip_class::setting_command() {
  byte received_message[5];  // Initializes the variable to receive external command (all commands are 32bits)
  received_message[4] = 0;
  if (usb_serial_flag)  // If the circuit is in normal opperation
  {
    while (SerialUSB.available())  // While the serial USB port is avaiable
    {
      SerialUSB.readBytes(received_message, 4);  // Reads the message in serial USB port
      treat_command(received_message);           // Treat the command
    }
  } else {
  }
}

/*  SETTINGS COMMAND HANDLER
 * 
 *  This function allows an interface to control data acquisition settings, modifying Arduino and Intan 
 *  chip attributes. It collects the message, classifies it and finally modifies some parameter.
 */
void ads_1298_chip_class::treat_command(byte *command_buffer) {
  uint8_t *temp_command;
  uint32_t u32TEMP;

  switch (command_buffer[0]) {
    /*  INFORMATION COMMAND
     *  This function returns to USB port the current system status 
     */
    case 0x00:
      {
        int val = read(ID);

        switch (val & B00011111) {  //least significant bits reports channels
          case B10000:              //16
            hardwareType = "ADS1294";
            break;
          case B10001:  //17
            hardwareType = "ADS1296";
            break;
          case B10010:  //18
            hardwareType = "ADS1298";
            break;
          case B11110:  //30
            hardwareType = "ADS1299";
            break;
          default:
            break;
        }
        break;
      }
      
    /*  START ACQUISITION COMMAND
     *  This function starts the sequencial acquisition in regular times (sampling frequency)
     *  and returns "OK"
     */
    case 0x11:
      digital_write_direct(sync_pinout, HIGH);
      start();
      delay(100);
      rdatac();
      delay(100);
      start_acquisition(sampling_frequency);  // Starts the data acquisition
      command_buffer[3] = 'K';                // Sets the byte to answer to interface the ascii ("OK")
      command_buffer[2] = 'O';                // Sets the byte to answer to interface the ascii ("OK")
      break;

    /*  STOPS ACQUISITION COMMAND
     *  This function stops the sequencial acquisition and returns "OK"
     */
    case 0xFF:
      sdatac();
      digital_write_direct(sync_pinout, LOW);
      stop_acquisition();       // Stops the data aquisition
      command_buffer[3] = 'K';  // Sets the byte to answer to interface the ascii ("OK")
      command_buffer[2] = 'O';  // Sets the byte to answer to interface the ascii ("OK")
      break;

    /*  TEST COMMANDS
     *  These functions test the microcontroller control functions 
     */
    
    case 0xE2:             // This command tests the READ function -> ex: 0xe2000003 lê registrador 3
      int valor;
      temp_command = (uint8_t *)(command_buffer + 3);   // Gets the last byte and saves with a pointer as LITTLE ENDIAN
      //*temp_command = *temp_command >> 4 | *temp_command << 4;  // Transforms the pointer to BIG ENDIAN format to send to RHD chip
      valor = read(*temp_command);
      command_buffer[0] = 0;
      command_buffer[1] = 0;
      command_buffer[2] = 0;
      command_buffer[3] = valor;
      break;

    case 0xE3:             // Configurar onda quadrada
      write(CONFIG2, 0x00 | INT_TEST |  TEST_AMP | TEST_FREQ0);
      // write(CONFIG1, 0x85);
      for (int i = 1; i <= 8; i++) {
        write(CHnSET + i, TEST_SIGNAL | GAIN_12X); //create square wave 
      }
      break;

    /*  DEFAULT COMMAND 
     *  This function sends a random message to the USB port if the command given to the 
     *  microcontroller does not fulfill any previous cases. 
     */
    default:                                                // If a command without meaning is sent by the interface
      byte default_answer[4] = { 0x80, 0x7F, 0xFC, 0xFE };  // Sets a random default confirmation message
      command_buffer = default_answer;                      // Returns a random default confirmation message
      break;
    
  }
// If the command is start acquisition, then the answer is not sent
  if (command_buffer[0] != 0x11) 
  {
    SerialUSB.write(command_buffer,4);                        // Sends back the answer message to USB serial port 
  }
}

#endif
