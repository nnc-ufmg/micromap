/*  MAIN CODE
 *
 *  Library for electrophysiology recording system based on a Arduino and a RHD2000 INTAN chip. 
 *  Created by Núcleo de Neurociências (NNC) from Universidade Federal de Minas Gerais (UFMG), April, 2016.
 *  Modificated by Núcelo de Neurociências (NNC) from Universidade Federal de Minas Gerais (UFMG), May, 2022. 
 *
 *  Authors:
 *    Paulo Aparecido Amaral Júnior and
 *    Prof. Márcio Flávio Dutra Moraes
 *
 *  Refactoring:
 *    João Pedro Carvalho Moreira
 */

/*  DEFINES
 *  Defines some variables
 */
#ifndef rhd_functions_h
#define rhd_functions_h

#define SPI_SR_TXEMPTY 0x00000200
  
// INTAN RHD chip has 18 RAM registers (0 to 17) of 8 bits which need to be configured at power up.
// Bits: [7] [6] [5] [4] [3] [2] [1] [0]

// Masks for setting register 0 (to be used when writing on register 0).
#define adc_reference_bw          0xC0        // bits 7 and 6 (always 3 = '11') => '11XXXXXX' = '11000000' = 0xC0.
#define amp_fast_settle_enable    0x20        // bit 5 setted (connects bioamps. outputs to GND).
#define amp_fast_settle_disable   0x00        // bit 5 not setted (normal operation of bioamplifiers).
#define amp_vref_enable           0x10        // bit 4 setted (enable reference voltage used by bioamps.).
#define amp_vref_disable          0x00        // bit 4 not setted (desable bioamps. => reduce 180 uA in power consumption)
#define adc_comparator_bias       0x0C        // bits 3 and 2. Both setted for normal operation => 'XXXX11XX = '00001100' = 0x0C.
#define adc_comparator_select     0x02        // bits 0 and 1. Must be always '10' => 'XXXXXX10' = '00000010' = 0x02.

// Masks for setting register 1 (to be used when writing on register 1).
#define vdd_sense_enable          0x80        // bit 6 setted.
#define vdd_sense_disable         0x00        // bit 6 not setted.
#define adc_buffer_bias_default   0x20        // bits 5 to 0. Initially setted to '10000' (total sampling_frequency ADC <= 120 kS/s).

// Masks for setting register 2 (to be used when writing on register 2).
#define mux_bias_current_default  0x28        // bits 5 a 0. Setados inicialmente para 40 (sampling_frequency total ADC <= 120 kS/s).

// Masks for setting register 3 (to be used when writing on register 3).
#define mux_load                  0x00        // Bits 7, 6 e 5. Devem ser sempre '000'.
#define temp_s2_enable            0x10        // Bit 4 setado (usa-se temp_s2 no processo de medição de temperatura; vide datasheet).
#define temp_s2_disable           0x00        // Bit 4 não setado (economiza energia).
#define temp_s1_enable            0x08        // Bit 3 setado (usa-se temp_s1 no processo de medição de temperatura; vide datasheet).
#define temp_s1_disable           0x00        // Bit 3 não setado (economiza energia).
#define temp_enable               0x04        // Bit 2 setado (habilita o sensor de temperatura do chip INTAN).
#define temp_disable              0x00        // Bit 2 não setado (economiza energia - 70 uA).
#define digout_hiz_disable        0x02        // Bit 1 setado (coloca pino auxout num estado de alta impedância).
#define digout_hiz_enable         0x00        // Bit 1 não setado (habilita o pino auxout).
#define digout_enable             0x01        // Bit 0 setado (pino auxout colocado em VDD).
#define digout_disable            0x00        // Bit 0 não setado (pino auxout colocado em GND).

// Masks for setting register 4 (to be used when writing on register 4).
#define weak_miso_enable          0x80        // Bit 7 setado (quando apenas 1 chip RHD2000 irá usar a linha miso).
#define weak_miso_disable         0x00        // Bit 7 não setado.
#define twoscomp_enable           0x40        // Bit 6 setado (habilita representação binária por complemento de 2).
#define twoscomp_disable          0x00        // Bit 6 não setado (desabilita representação binária por complemento de 2).
#define absmode_enable            0x20        // Bit 5 setado (habilita retificação de onda completa dos bioamplificadores).
#define absmode_disable           0x00        // Bit 5 não setado (desabilita retificação de onda completa dos bioamplificadores).
#define dsp_enable                0x10        // Bit 4 setado (habilita remoção de offset por DSP com filtro IIR Highpass 1ªord)
#define dsp_disable               0x00        // Bit 4 não setado.
#define dsp_cutoff_default        0x00        // Bits [3] [2] [1] e [0]. Valor default é zero (0x00). Vide tabela datasheet.
#define dsp_cutoff_fdpc           0x00        // Bits [3] [2] [1] e [0]. Valor default é zero (0x00). Vide tabela datasheet.

// Masks for setting register 5 (to be used when writing on register 5).
#define z_check_dac_power_enable  0x40        // Bit 6 setado (habilita o ADC de 8 bits usado para teste de impedância).
#define z_check_dac_power_disable 0x00        // Bit 6 não setado (economiza energia - 120 uA).
#define z_check_load              0x00        // Bit 5 (deve estar sempre em 0).
#define z_check_scale_0p1_pF      0x00        // Bits [4] e [3] = '00'. Ajuste de capacitância (0.1 pF) para teste de impedância.
#define z_check_scale_1p0_pF      0x08        // Bits [4] e [3] = '01'. Ajuste de capacitância (1.0 pF) para teste de impedância.
#define z_check_scale_10p0_pF     0x18        // Bits [4] e [3] = '11'. Ajuste de capacitância (10.0 pF) para teste de impedância.
#define z_check_conn_all_enable   0x04        // Bit 2 setado. Conecta todos os eletrodos ao pino de entrada elec_test.
#define z_check_conn_all_disable  0x00        // Bit 2 não setado (operação normal do chip).
#define z_check_sel_pol_positive  0x00        // Bit 1 não setado (seleciona entrada não-inversora do bioamp. para teste de impedância).
#define z_check_sel_pol_negative  0x02        // Bit 1 setado (seleciona entrada inversora do bioamp. para teste de impedância).
#define z_check_enable            0x01        // Bit 0 setado (habilita modo de teste de impedância).
#define z_check_disable           0x00        // Bit 0 não setado (desabilita modo de teste de impedância).

/*  GLOBAL VARIABLE
 *  Defines variables that will be used in another parts of the program
 */
String firmware_version = "V1.0 2022/04/19";


/*  INTAN RHD CLASS
 *  Defines the class that will control the information flow and settings of the Intan RHD chip
 */
class intan_rhd_chip_class
{
  public:
    /*  VARIABLES DECLARATION
     *  Declaration of program variables
     */
    intan_rhd_chip_class();                                           // Constructor
    uint16_t sampling_frequency = 2000;                               // Default sampling frequency        
    uint16_t highpass_frequency = 20000;                              // Default high pass filter cutoff frequency        
    uint16_t lowpass_frequency = 0.1;                                 // Default low pass filter cutoff frequency           
    uint32_t channels = 0xFFFFFFFF;                                   // Channels to be recorded [32, 31 ... 2, 1] (0 = off and 1 = on)
    uint16_t channel_sequence[32];                                    // Sequence of channels to be sent to INTAN
    uint16_t real_channel[32];                                        // INTAN convert the channel 2 CS after the request, so the real channel are the channel_sequence rolled by 2;
    uint16_t channel_count = 0;                                       // Variable to count the number off channels
    
    int signal = 1;                                                   // Variable to invert the signal for the next channel
    int serial_pinout = 9;                                            // Output pin for chip selection
    int sync_pinout = 13;                                             // Output pin for syncronization trigger
    uint16_t buffer[32 + 1];                                          // Buffer to store data from a single run of all channels (only up to 32 channels at once)
    uint8_t packages_received = 0;                                    // Count total number of packages with channel DATA received from INTAN
    
    bool usb_serial_flag = true;                                      // USB connection flag

    bool dataReadIntanOrTest=true;                                    //If true, reads from intan, else saves channel number
    bool dataWriteIntanOrTest=true;
                
    /*  METHODS DECLARATION
     *  Declaration of program methods
     */
    uint16_t transfer_data(uint16_t data);                            // Declares function thar sends 16-bit command to RHD chip
      
    void convert_channels();                                          // Declares function that sends to RHD chip all converts commands
     
    bool first_sample = true;                                          // Declares variable that indicates if it's the first sample of the run
    uint16_t write(uint16_t register_number, uint8_t data);           // Declares function that writes to RHD chip registers
    uint16_t read(uint16_t register_number);                          // Declares function that reads to RHD chip registers 
    uint16_t clear();                                                 // Declares function that clears the RHD chip configurations
    uint16_t dummy();                                                 // Declares function that sends a dummy command to RHD chip
    void calibrate();                                                 // Declares function that calibartes the RHD chip
    void set_highpass(uint16_t p_highpass_index);                     // Declares function that sets the RHD chip highpass filter cutoff frequency
    void set_lowpass(uint16_t p_lowpass_index);                       // Declares function that sets the RHD chip lowpass filter cutoff frequency
    void set_channels(uint32_t p_channels);                           // Declares function that turns on/off the RHD chip channels
    void build_channel_sequence(uint32_t p_channels);                 // Declares function that builds the cahnnels sequence to data acquisition

    void read_registers(uint16_t *read_values, uint16_t *read_info);  // Declares function that reads all the configuration registers in RHD chip
    void steup_spi(int p_serial_pinout, int p_sync_pinout);           // Declares function that setups the RHD chip
    void init_default(int p_serial_pinout,
                      int p_sync_pinout, 
                      uint32_t p_channels, 
                      uint16_t p_sampling_frequency, 
                      uint16_t p_highpass_index, 
                      double p_lowpass_index);                        // Declares function that setups the communication with RHD chip

    void setting_command();                                           // Declares function that reads the serial port to configures the RHD chip
    void treat_command(byte *command_buffer);                         // Declares function that reads the serial message and sents to configures the RHD chip


    
    private:

    protected:
};

/*  CONSTRUCTOR
 *  Construct the class
 */
intan_rhd_chip_class::intan_rhd_chip_class()
{
  
}

/*  INIT DEFAULT
 *  
 */
void  intan_rhd_chip_class::init_default(int p_serial_pinout, int p_sync_pinout, uint32_t p_channels, uint16_t p_sampling_frequency, uint16_t p_highpass_index, double p_lowpass_index)
{ 
  build_channel_sequence(p_channels);  

  sampling_frequency = p_sampling_frequency;
    
  steup_spi(p_serial_pinout, p_sync_pinout); //Here p_serial_pinout is saved into INTAN_NNC SSpin variable ...

  write(0x0000, adc_reference_bw | amp_fast_settle_disable | amp_vref_enable | adc_comparator_bias | adc_comparator_select);
  write(0x0001, vdd_sense_disable | adc_buffer_bias_default);
  write(0x0002, mux_bias_current_default);
  write(0x0003, mux_load | temp_s2_disable | temp_s1_disable | temp_disable | digout_hiz_disable | digout_disable);
  write(0x0004, weak_miso_enable | twoscomp_enable | absmode_disable | dsp_disable | dsp_cutoff_default);
  write(0x0005, z_check_dac_power_disable | z_check_load | z_check_scale_0p1_pF | z_check_conn_all_disable | z_check_sel_pol_positive | z_check_disable);
  write(0x0006, 0x00);
  write(0x0007, 0x00);
  set_channels(channels);
  delay(1); // waits 1 ms before calibrating ADC (recommended by RHD2216/RHD2132 datasheet).
  calibrate();

  set_highpass(17);
  set_lowpass(1);
      
  delay(1000);   
}

/*  TRANSFER DATA
 *  
 *  This function is used by functions: write, clear, dummy and calibrate. It sends 16 bits of data on SPI bus
 *  and returns the word (16 bits) sent by INTAN in this transaction (remember that it's a full duplex SPI
 *  communication).
 */
uint16_t intan_rhd_chip_class::transfer_data(uint16_t data)
{
  digital_write_direct(serial_pinout, LOW);
  REG_SPI0_TDR = data;
  while ((REG_SPI0_SR & SPI_SR_TXEMPTY) == 0) {} // wait for data to be sent
  digital_write_direct(serial_pinout, HIGH);
  return (REG_SPI0_RDR & 0xFFFF);
}

/*  CONVERT CHANNELS
 *  
 *  This function sends all CONVERT commands to INTAN chip.
 */
void intan_rhd_chip_class::convert_channels()
{  
  if (first_sample) // If it's the first sample, set the first channel to 0
  {
    packages_received = 0;
    first_sample = false;
  }

  // First 16 bits of the buffer are used as a header (0xFE00) to identify the package
  buffer[0] = packages_received << 8 | 0xFE; // Header of the package (is inverted due to MSB logic, the MicroMAP will read 0xFEXX)
  int channel_actual = 0;

  while (channel_actual < channel_count)
  {  
    digital_write_direct(serial_pinout, LOW);  
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    
    if (dataWriteIntanOrTest) REG_SPI0_TDR = channel_sequence[channel_actual];                // If dataWriteIntanOrTest is true, send the command to INTAN chip
    else REG_SPI0_TDR = 0xFE00;                                                               // Else, send the command to INTAN chip (for testing purposes)
    while ((REG_SPI0_SR & SPI_SR_TXEMPTY) == 0) {}  
    if (dataReadIntanOrTest) buffer[(real_channel[channel_actual]) + 1] = REG_SPI0_RDR & 0xFFFF;           // If dataReadIntanOrTest is true, read the data from INTAN chip
    else buffer[channel_actual + 1] = signal * channel_sequence[channel_actual];                                // Else, save the channel number in the buffer (for testing purposes)
    
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    digital_write_direct(serial_pinout, HIGH);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    asm volatile("nop"::);asm volatile("nop"::);
    channel_actual++;
  }

  if (!dataReadIntanOrTest) signal = signal*-1; // Inverts the signal for the next channel
  packages_received++;
  transfer_data_flag = true;
}

/*  WRITE COMMAND
 * 
 *  This function implements the WRITE command specified by RHD2216/RHD2132 INTAN datasheet.
 *  It writes 8 bits specified by parameter data on register specified by parameter register_number.
 *  Also, it returns the word (16 bits) sent by INTAN in this transaction (remember that it's a full duplex SPI
 *  communication).
 */
uint16_t intan_rhd_chip_class::write(uint16_t register_number, uint8_t data)
{
  uint16_t mask = 0x8000; //Mask -> 10XXXXXXXXXXXXXX = 1000000000000000
  uint16_t writecommand = mask | (register_number << 8) | data;
  return(transfer_data(writecommand));
}

/*  READ COMMAND
 * 
 *  This function implements the READ command specified by RHD2216/RHD2132 INTAN datasheet.
 *  It sends a READ command on a specific register and returns the word (16 bits) sent by INTAN in this transaction
 *  (remember that it's a full duplex SPI communication).
 */
uint16_t intan_rhd_chip_class::read(uint16_t register_number)
{
  uint16_t mask = 0xC000; //Mask -> 11XXXXXXXXXXXXXX = 1100000000000000
  uint16_t writecommand = mask | (register_number << 8);
  return(transfer_data(writecommand));
}

/*  CLEAR COMMAND
 * 
 *  This function implements the CLEAR command specified by RHD2216/RHD2132 INTAN datasheet. 
 *  It sends the 16bit-word 0b0110101000000000, which clears the ADC calibration of the on-chip ADC, 
 *  and returns the word (16 bits) sent by INTAN in this transaction (remember that it's a full duplex SPI communication).
 */
uint16_t intan_rhd_chip_class::clear()
{
  return(transfer_data(0b0110101000000000));
}

/*  DUMMY COMMAND
 * 
 *  This function sends a dummy command on SPI bus, which is a command with no specific meaning for INTAN.
 *  It can be useful in some cases (per example: self-calibration takes many clock cycles to execute).
 *  After sending a dummy command, this functions returns the word sent by INTAN in the SPI transaction
 *  (remember that it's a full duplex SPI communication).
 */
uint16_t intan_rhd_chip_class::dummy()
{
  return(transfer_data(0b1111111111111111));
}

/*  CALIBRATE COMMAND
 * 
 *  This function implements the CALIBRATE command specified by RHD2216/RHD2132 INTAN datasheet. It sends the
 *  16bit-word 0b0101010100000000, which initiates the ADC self-calibration routine of INTAN RHD, followed by
 *  9 dummy commands, for generating clock pulses necessary in ADC calibration.
 */
void intan_rhd_chip_class::calibrate()
{
  uint8_t d = 0;
  transfer_data(0b0101010100000000);
  for(d = 0; d < 8; d++)
  {
    dummy();
  }
}

/*  SET LOW PASS FILTER CUTOFF FREQUENCY
 *       
 *  This function sets the cutoff frequency of the RHD on-chip highpass filter.
 *  
 *   _______________Possible Frequencies_______________
 *  |                |                |                |
 *  |  [1]  : 100    |  [9]  : 1500   |  [17] : 20000  |  
 *  |  [2]  : 150    |  [10] : 2000   |                |
 *  |  [3]  : 200    |  [11] : 2500   |                |
 *  |  [4]  : 250    |  [12] : 3000   |                |
 *  |  [5]  : 300    |  [13] : 5000   |                |
 *  |  [6]  : 500    |  [14] : 7500   |                | 
 *  |  [7]  : 750    |  [15] : 10000  |                |
 *  |  [8]  : 1000   |  [16] : 15000  |                |
 *  |________________|________________|________________|
 */
    void intan_rhd_chip_class::set_lowpass (uint16_t p_lowpass_index)
    {
        float lowpass_values[17]{100, 150, 200, 250, 300, 500, 750, 1000, 1500, 2000, 
                                  2500, 3000, 5000, 7500, 10000, 15000, 20000};
        lowpass_frequency = lowpass_values[p_lowpass_index];
        
        int lowpass_registers[17][4]{{38,26, 5,31}, {44,17, 8,21}, {24,13, 7,16}, {42,10, 5,13},
                                      { 6, 9, 2,11}, {30, 5,43, 6}, {41, 3,36, 4}, {46, 2,30, 3},
                                      { 1, 2,23, 2}, {27, 1,44, 1}, {13, 1,25, 1}, { 3, 1,13, 1},
                                      {33, 0,37, 0}, {22, 0,23, 0}, {17, 0,16, 0}, {11, 0, 8, 0},
                                      { 8, 0, 4, 0}};

        uint8_t RH1DAC1 = 0, RH1DAC2 = 0, RH2DAC1 = 0, RH2DAC2 = 0;
        RH1DAC1 = lowpass_registers[p_lowpass_index][0];
        RH1DAC2 = lowpass_registers[p_lowpass_index][1];
        RH2DAC1 = lowpass_registers[p_lowpass_index][2];
        RH2DAC2 = lowpass_registers[p_lowpass_index][3];
        
        write(0x0008, RH1DAC1); // writes RH1DAC1 on register 8 of INTAN RHD.
        write(0x0009, RH1DAC2); // writes RH1DAC2 on register 9 of INTAN RHD.
        write(0x000A, RH2DAC1); // writes RH2DAC1 on register 10 of INTAN RHD.
        write(0x000B, RH2DAC2); // writes RH2DAC2 on register 11 of INTAN RHD.
    }

/*  SET HIGH PASS FILTER CUTOFF FREQUENCY
 * 
 *  This function sets the cutoff frequency of the RHD on-chip lowpass filter.
 *   
 *   
 *   ___________________Possible Frequencies____________________ 
 *  |              |              |              |              |
 *  |  [1] : 0.1   |  [9]  : 2.5  |  [17] : 30   |  [25] : 500  |
 *  |  [2] : 0.25  |  [10] : 3    |  [18] : 50   |              |
 *  |  [3] : 0.3   |  [11] : 5    |  [19] : 75   |              |
 *  |  [4] : 0.5   |  [12] : 7.5  |  [20] : 100  |              |  
 *  |  [5] : 0.75  |  [13] : 10   |  [21] : 150  |              |
 *  |  [6] : 1     |  [14] : 15   |  [22] : 200  |              |
 *  |  [7] : 1.5   |  [15] : 20   |  [23] : 250  |              |
 *  |  [8] : 2     |  [16] : 25   |  [24] : 300  |              | 
 *  |______________|______________|______________|______________|
 */
    void intan_rhd_chip_class::set_highpass(uint16_t p_highpass_index)
    { 
        float highpass_values[25]{0.1, 0.25, 0.3, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, 5,
                                 7.5, 10, 15, 20, 25, 30, 50, 75, 100, 150, 200,
                                 250, 300, 500};
        highpass_frequency = highpass_values[p_highpass_index];
               
        int highpass_registers[25][3]{{16,60, 1}, {56,54, 0}, { 1,40, 0}, {35,17, 0},
                                     {49, 9, 0}, {44, 6, 0}, { 9, 4, 0}, { 8, 3, 0},
                                     {42, 2, 0}, {20, 0, 0}, {40, 1, 0}, {18, 1, 0},
                                     { 5, 1, 0}, {62, 0, 0}, {54, 0, 0}, {48, 0, 0},
                                     {44, 0, 0}, {34, 0, 0}, {28, 0, 0}, {25, 0, 0},
                                     {21, 0, 0}, {18, 0, 0}, {17, 0, 0}, {15, 0, 0},
                                     {13, 0, 0}};

        uint8_t RLDAC1=0, RLDAC2=0, RLDAC3=0;
        RLDAC1 = highpass_registers[p_highpass_index][0];
        RLDAC2 = highpass_registers[p_highpass_index][1];
        RLDAC3 = highpass_registers[p_highpass_index][2];
        
        write(0x000C, RLDAC1); // writes RLDAC1 on register 12 of INTAN RHD.
        write(0x000D, RLDAC2 | (RLDAC3 << 6)); // writes RLDAC2 and RLDAC3 on register 13 of INTAN RHD.
    }


/*  SET ON/OFF CHANNELS (SAVE POWER)
 * 
 *  This function powers down or up individual biopotential amplifiers specified by p_channels.
 *  Each bit field of the variable p_channels corresponds to a channel (1 = channel on; 0 = off).
 *  If there are channels that do not need to be observed, it's recommended to turn off the corresponding
 *  bioamplifiers to reduce power consumption. Each amplifier consumes power in proportion to its upper
 *  cutoff frequency. Current consumption is approximately 7.6 μA/kHz per amplifier. Under normal operation,
 *  all amplifiers should be powered up.
 */
void intan_rhd_chip_class::set_channels(uint32_t p_channels)
{
  uint8_t bioamps0to7 = p_channels & 0xFF;          // Sets the turn on/off bioamps. from 0 to 7.
  uint8_t bioamps8to15 = p_channels >> 8 & 0xFF;    // Sets the turn on/off bioamps. from 8 to 15.
  uint8_t bioamps16to23 = p_channels >> 16 & 0xFF;  // Sets the turn on/off bioamps. from 16 to 23.
  uint8_t bioamps24to31 = p_channels >> 24 & 0xFF;  // Sets the turn on/off bioamps. from 24 to 31.
  
  write(0x000E, bioamps0to7);                         // Writes on register 14.
  write(0x000F, bioamps8to15);                        // Writes on register 15.
  write(0x0010, bioamps16to23);                       // Writes on register 16.
  write(0x0011, bioamps24to31);                       // Writes on register 17.
}


/*  BUILD CHANNEL SEQUENCE
 * 
 *  This function builds the sequence of CONVERT commands to be sent periodically (period = 1/sampling_frequency),
 *  in order to retrieve samples from the specified channels.
 */
void intan_rhd_chip_class::build_channel_sequence(uint32_t p_channels)
{
  channel_count = 0;                                              // Initializes the sequence counting in zero
  channels = p_channels;                                          // Set the channels attirbute
   
  for (uint16_t channel = 0; channel < 32; channel++)             // Runs for all 32 possible channels
    if(channels & ((0b1) << channel))                             // If the channel iss on (channel bit * 1) = 1
    {
      *(channel_sequence + channel_count) = channel << 8;         // Adds the channel in CONVERT(ch) command sequence.
      channel_count++;                                            // Adds the counting
    } 

  // Roll by two the channel sequence to match the INTAN RHD chip sequence and save the sequence in the real_channel array
  if (channel_count >= 3) {
    for (uint16_t i = 0; i < channel_count; i++) {
      real_channel[i] = (i + channel_count - 2) % channel_count;
    }
  } else {
    for (uint16_t i = 0; i < channel_count; i++) {
      real_channel[i] = i;
    }
  }

  uint16_t buffer[channel_count + 1];
}

/*  READ CHIP INFORMATION (ROM and RAM)
 * 
 *  This function is used to read all registers of the RHD chip
 */    
void intan_rhd_chip_class::read_registers(uint16_t *read_values, uint16_t *read_info)
{
  read((uint16_t)0);                                              // Reads the Register 0: ADC Configuration and Amplifier Fast Settle
  read((uint16_t)4);                                              // Reads the Register 4: ADC Output Format and DSP Offset Removal
  read_values[0] = read((uint16_t)8);                             // Reads the Register 8: On-Chip Amplifier Bandwidth Select (here comes the answer to the first read command)
  read_values[1] = read((uint16_t)9);                             // Reads the Register 9: On-Chip Amplifier Bandwidth Select (here comes the answer to the second read command)
  read_values[2] = read((uint16_t)10);                            // Reads the Register 10: On-Chip Amplifier Bandwidth Select (so on...)
  read_values[3] = read((uint16_t)11);                            // Reads the Register 11: On-Chip Amplifier Bandwidth Select 
  read_values[4] = read((uint16_t)12);                            // Reads the Register 12: On-Chip Amplifier Bandwidth Select 
  read_values[5] = read((uint16_t)13);                            // Reads the Register 13: On-Chip Amplifier Bandwidth Select 
  read_values[6] = read((uint16_t)14);                            // Reads the Register 14: Individual Amplifier Power
  read_values[7] = read((uint16_t)15);                            // Reads the Register 15: Individual Amplifier Power
  read_values[8] = read((uint16_t)14);                            // Reads the Register 16: Individual Amplifier Power
  read_values[9] = read((uint16_t)15);                            // Reads the Register 17: Individual Amplifier Power
  read_values[10] = dummy();                                      // Need to send two dummies to retrieve answer of the last two READ commands
  read_values[11] = dummy();                                      // Need to send two dummies to retrieve answer of the last two READ commands

  read((uint16_t)40);                                             // Reads the Register 40: INTAN characters in ASCII code
  read((uint16_t)41);                                             // Reads the Register 41: INTAN characters in ASCII code
  read_info[0] = read((uint16_t)42);                              // Reads the Register 42: INTAN characters in ASCII code (Here comes the answer to the first read command)
  read_info[1] = read((uint16_t)43);                              // Reads the Register 43: INTAN characters in ASCII code (Here comes the answer to the first read command)
  read_info[2] = read((uint16_t)44);                              // Reads the Register 44: INTAN characters in ASCII code (son on...)
  read_info[3] = read((uint16_t)60);                              // Reads the Register 60: die revision.
  read_info[4] = read((uint16_t)61);                              // Reads the Register 61: unipolar/bipolar amplifiers.
  read_info[5] = read((uint16_t)62);                              // Reads the Register 62: number of amplifiers.
  read_info[6] = read((uint16_t)63);                              // Reads the Register 63: chip ID.
  read_info[7] = dummy();                                         // Need to send two dummies to retrieve answer of the last two READ commands
  read_info[8] = dummy();                                         // Need to send two dummies to retrieve answer of the last two READ commands
}

/*  SETUP SPI
 * 
 *  This function initializes the SPI bus
 */     
void intan_rhd_chip_class::steup_spi(int p_serial_pinout, int p_sync_pinout)
{
  serial_pinout = p_serial_pinout;                                // Serial pin             
  sync_pinout = p_sync_pinout;
  pinMode(serial_pinout, OUTPUT);                                 // Defines the pin mode
  pinMode(sync_pinout, OUTPUT);                                   // Defines the pin mode
  SPI.begin();                                                    // Starts the SPI bus   

  REG_SPI0_CR = SPI_CR_SWRST;                                     // Resets SPI
  REG_SPI0_CR = 0x1;                                              // Turns the SPI enable
  REG_SPI0_MR = SPI_MR_MODFDIS|0x00000001;                        // Sets master and no modefault
  REG_SPI0_CSR = SPI_MODE0|(0x00000780);                          // Sets DLYBCT = 0, DLYBS = 0, SCBR = 2A, 16 bit transfer   
}

/*  SETTINGS COMMAND 
 * 
 *  This function allows an interface to control data acquisition settings, modifying Arduino and Intan 
 *  chip attributes. It collects the message and forwards it to the command handler function.
 */   
void intan_rhd_chip_class::setting_command() 
{
  byte received_messge[5];                                        // Initializes the variable to receive external command (all commands are 32bits)
  received_messge[4] = 0;                                            
  if (usb_serial_flag)                                            // If the circuit is in normal opperation 
  {
    while (SerialUSB.available())                                 // While the serial USB port is avaiable
    {
      SerialUSB.readBytes(received_messge,4);                     // Reads the message in serial USB port
      treat_command(received_messge);                             // Treat the command
    } 
  }
  else
  {
  
  }
}

/*  SETTINGS COMMAND HANDLER
 * 
 *  This function allows an interface to control data acquisition settings, modifying Arduino and Intan 
 *  chip attributes. It collects the message, classifies it and finally modifies some parameter.
 */
void intan_rhd_chip_class::treat_command(byte *command_buffer)
{
  uint16_t* temp_command;
  uint32_t u32TEMP;
  
  switch(command_buffer[0])
  {
    /*  INFORMATION COMMAND
     *  This function returns to USB port the current system status 
     */
    case 0x00:
      SerialUSB.println("Firmware version: "+ firmware_version);
      SerialUSB.println(String("SETTINGS: Sampling(") + sampling_frequency + "); ChannelCount(" + channel_count + "); CHANNEL32bit(" + channels + ")");     
      SerialUSB.println(String("Filters ==> HIGHPASS (") + highpass_frequency +"); LOWPASS (" + lowpass_frequency + ")"); 
      break;

    /*  DSP CUTOFF COMMAND
     *  This function sets the DSP cutoff 
     */
    case 0x41: 
      command_buffer[3]++;                                  // Adds the last bytes to return to the interface
      command_buffer[0] = dsp_cutoff_fdpc | 0x43;           // Configures the DSP cutoff
      command_buffer[1] = dsp_cutoff_fdpc | 0x55;           // Configures the DSP cutoff
      break;

    /*  START ACQUISITION COMMAND
     *  This function starts the sequencial acquisition in regular times (sampling frequency)
     *  and returns "OK"
     */
    case 0x11:
        digital_write_direct(sync_pinout, HIGH);
        start_acquisition(sampling_frequency);              // Starts the data acquisition
        command_buffer[3] = 'K';                            // Sets the byte to answer to interface the ascii ("OK")
        command_buffer[2] = 'O';                            // Sets the byte to answer to interface the ascii ("OK")
        first_sample = true;                                // Sets the first sample to true (to start the acquisition)
        break;

    /*  STOPS ACQUISITION COMMAND
     *  This function stops the sequencial acquisition and returns "OK"
     */
    case 0xFF:
      digital_write_direct(sync_pinout, LOW);
      stop_acquisition();                                   // Stops the data aquisition
      command_buffer[3] = 'K';                              // Sets the byte to answer to interface the ascii ("OK")
      command_buffer[2] = 'O';                              // Sets the byte to answer to interface the ascii ("OK")
      break;

    /*  SAMPLING FREQUENCY COMMAND
     *  This function sets the sampling frequency
     */
    case 0xC0:                                              // This data was received as BIG ENDIAN (MSB at the begining)
      temp_command = (uint16_t *)(command_buffer+2);        // Gets the last two bytes and saves with a pointer as LITTLE ENDIAN   
      *temp_command = __builtin_bswap16(*temp_command);     // Transforms the pointer to BIG ENDIAN format to configure correctly the RHD chip
      sampling_frequency = *temp_command;                   // Sets the sampling frequency
      break;

    /*  CHANNELS 15 TO 0 COMMAND
     *  This function turns on/off the channels 15 to 0
     */
    case 0xC1:                                              // This data was received as BIG ENDIAN and programs channels 15-0 in this order
      channels = (channels & 0xFFFF0000)|
                 (((uint32_t)(command_buffer[2]))<<8)|
                 (((uint32_t)(command_buffer[3])));     // Sets off (0) to all channels that will be changed and adds the new on/off bit configurations
      build_channel_sequence(channels);                     // Makes a new sequence of channels that will be recorded
      set_channels(channels);                               // Turns on the channels that will be recorded and turns off the others
      u32TEMP=__builtin_bswap32(channels);
      command_buffer = (byte *)&u32TEMP;
      break;

    /*  CHANNELS 31 TO 16 COMMAND
     *  This function turns on/off the channels 31 to 16
     */
    case 0xC2:                                              // This data was received as BIG ENDIAN and programs channels 31-16 in this order
      channels = (channels & 0x0000FFFF) |
                 (((uint32_t)(command_buffer[2]))<<24)|
                 (((uint32_t)(command_buffer[3]))<<16);     // Sets off (0) to all channels that will be changed and adds the new on/off bit configurations
      build_channel_sequence(channels);                     // Makes a new sequence of channels that will be recorded
      set_channels(channels);                               // Turns on the channels that will be recorded and turns off the others
      u32TEMP=__builtin_bswap32(channels);
      command_buffer = (byte *)&u32TEMP;
      break;

    /*  HIGHPASS FILTER COMMAND
     *  This function sets the highpass filter cutoff frequency 
     */
    case 0xC3:                                              // This data was received as BIG ENDIAN (MSB at the begining)
      temp_command=(uint16_t *)(command_buffer+2);          // Gets the last two bytes and saves with a pointer as LITTLE ENDIAN 
      *temp_command=__builtin_bswap16(*temp_command);       // Transforms the pointer to BIG ENDIAN format to configure correctly the RHD chip
      set_highpass(*temp_command);                          // Sets the high pass filter cutoff frequency
      break;

    /*  LOWPASS FILTER COMMAND
     *  This function sets the lowpass filter cutoff frequency 
     */
    case 0xC4:                                              // This data was received as BIG ENDIAN (MSB at the begining)
      temp_command = (uint16_t *)(command_buffer+2);        // Gets the last two bytes and saves with a pointer as LITTLE ENDIAN
      *temp_command = __builtin_bswap16(*temp_command);     // Transforms the pointer to BIG ENDIAN format to configure correctly the RHD chip
      set_lowpass(*temp_command);                           // Sets the low pass filter cutoff frequency
      break; 

    /*  TRANSFER DATA COMMAND
     *  This function trasnfers to SPI the data in the last 2 bytes command  
     */
    case 0xC5:                                              // This data was received as BIG ENDIAN (MSB at the begining)
      temp_command = (uint16_t *)(command_buffer+2);        // Gets the last two bytes and saves with a pointer as LITTLE ENDIAN
      *temp_command =__builtin_bswap16(*temp_command);      // Transforms the pointer to BIG ENDIAN format to send to RHD chip
      transfer_data(*temp_command);                         // Transfers the that to the RHD chip
      dummy();                                              // Sends the first dummy   
      *temp_command = dummy();                              // Sends the second dummy, gets the RHD chip answer and saves with a pointer as LITTLE ENDIAN
      *temp_command = __builtin_bswap16(*temp_command);     // Transforms the pointer to BIG ENDIAN to send back to USB serial port
      break; 

    /*  TEST COMMANDS
     *  These functions test the microcontroller control functions 
     */ 
    case 0xE1:                                              // This command tests the WRITE function
      write(0x000E, 0xEE);                                  // Sends the write command to change the Register 14 (turns on/off some bioamplifiers)
      break; 

    case 0xE2:                                              // This command tests the READ function
      read(0x000E);                                         // Sends the read command to read the Register 14 (on/off bioamplifiers)
      dummy();                                              // Sends the first dummy nessessery to read the RHD chip output
      temp_command = (uint16_t *)(command_buffer+2);        // Initializes the variable to receive the RHD chip command 
      *temp_command = dummy();                              // Sends the second dummy and save the RHD chip output
      *temp_command = __builtin_bswap16(*temp_command);     // As the temp_command is int16_t (little endian) it is changed to big endian format  
      break; 

    case 0xE3:                                              // This command tests the SET_CHANNELS function
      set_channels(0xEE0081FF);                             // Calls the ser channels to specific configuration of channels
      read(0x000E);                                         // Sends the read command to read the Register 14 (on/off bioamplifiers)
      dummy();                                              // Sends the first dummy nessessery to read the RHD chip output
      temp_command = (uint16_t *)(command_buffer+2);        // Initializes the variable to receive the RHD chip command 
      *temp_command = dummy();                              // Sends the second dummy and save the RHD chip output
      *temp_command = __builtin_bswap16(*temp_command);     // As the temp_command is int16_t (little endian) it is changed to big endian format  
      break; 
    
    case 0xE4:                                              // This command tests the WRITE function
      write(0x000E, 0xAA);                                  // Sends the write command to change the Register 14 (turns on/off some bioamplifiers)
      break;

    // This command tests the READ function. If the command is 0xE5, it sends for each CS pulse the value of the channel
    // that is being read. If the command is 0xE6, it sends for each CS pulse the value of the channel that is being written.
    case 0xE5:                                              // This command changes the DATA READ TEST FUNCION 
      if (command_buffer[3] == 1)   
        dataReadIntanOrTest = true;
      else dataReadIntanOrTest = false; 
      break;
     
    case 0xE6:                                              // This command changes the DATA READ TEST FUNCION 
      if (command_buffer[3] == 1) 
        dataWriteIntanOrTest = true;
      else dataWriteIntanOrTest = false; 
      break;
              
    /*  DEFAULT COMMAND 
     *  This function sends a random message to the USB port if the command given to the 
     *  microcontroller does not fulfill any previous cases. 
     */
    default:                                                // If a command without meaning is sent by the interface
      byte  default_answer[4] = {0x80,0x7F,0xFC,0xFE};      // Sets a random default confirmation message
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
