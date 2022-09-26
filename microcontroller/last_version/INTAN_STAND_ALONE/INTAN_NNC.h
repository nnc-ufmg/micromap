/*################################################################################################################
 
  INTAN_NNC.h - Library for a WiFi electrophysiology recording system based on a ESP8266 (WiFi microcontroler)
  and a RHD2000 INTAN chip (miniaturized electrophysiology chip).
  Created by Núcleo de Neurociências (NNC) from Universidade Federal de Minas Gerais (UFMG), April, 2016.

  Authors:
    Paulo Aparecido Amaral Júnior and
    Prof. Márcio Flávio Dutra Moraes
    
################################################################################################################*/
  #ifndef INTAN_NNC_h
  #define INTAN_NNC_h

/*############################################################################################################
        includes.
############################################################################################################*/


/*############################################################################################################
        defines (we have many of them!)
############################################################################################################*/
  #define SPI_SR_TXEMPTY 0x00000200
  
  #define MAX_PACKET_SIZE 4000 // max packet size supported by UDP library - 2 for UDP Packet ID
  
  // INTAN RHD chip has 18 RAM registers (0 to 17) of 8 bits which need to be configured at power up.
  // Bits: [7] [6] [5] [4] [3] [2] [1] [0]
  
  // Masks for setting register 0 (to be used when writing on register 0).
  #define ADC_reference_BW 0xC0        // bits 7 and 6 (always 3 = '11') => '11XXXXXX' = '11000000' = 0xC0.
  #define amp_fast_settle_enable 0x20  // bit 5 setted (connects bioamps. outputs to GND).
  #define amp_fast_settle_disable 0x00 // bit 5 not setted (normal operation of bioamplifiers).
  #define amp_Vref_enable 0x10         // bit 4 setted (enable reference voltage used by bioamps.).
  #define amp_Vref_disable 0x00        // bit 4 not setted (desable bioamps. => reduce 180 uA in power consumption)
  #define ADC_comparator_bias 0x0C     // bits 3 and 2. Both setted for normal operation => 'XXXX11XX = '00001100' = 0x0C.
  #define ADC_comparator_select 0x02   // bits 0 and 1. Must be always '10' => 'XXXXXX10' = '00000010' = 0x02.
  
  // Masks for setting register 1 (to be used when writing on register 1).
  #define VDD_sense_enable 0x80  // bit 6 setted.
  #define VDD_sense_disable 0x00 // bit 6 not setted.
  #define ADC_buffer_bias_default 0x20 // bits 5 to 0. Initially setted to '10000' (total fs ADC <= 120 kS/s).
  
  // Masks for setting register 2 (to be used when writing on register 2).
  #define MUX_bias_current_default 0x28 // bits 5 a 0. Setados inicialmente para 40 (fs total ADC <= 120 kS/s).
  
  // Masks for setting register 3 (to be used when writing on register 3).
  #define MUX_load 0x00       // Bits 7, 6 e 5. Devem ser sempre '000'.
  #define tempS2_enable 0x10  // Bit 4 setado (usa-se tempS2 no processo de medição de temperatura; vide datasheet).
  #define tempS2_disable 0x00 // Bit 4 não setado (economiza energia).
  #define tempS1_enable 0x08  // Bit 3 setado (usa-se tempS1 no processo de medição de temperatura; vide datasheet).
  #define tempS1_disable 0x00 // Bit 3 não setado (economiza energia).
  #define temp_enable 0x04    // Bit 2 setado (habilita o sensor de temperatura do chip INTAN).
  #define temp_disable 0x00   // Bit 2 não setado (economiza energia - 70 uA).
  #define digout_HiZ_disable 0x02 // Bit 1 setado (coloca pino auxout num estado de alta impedância).
  #define digout_HiZ_enable 0x00  // Bit 1 não setado (habilita o pino auxout).
  #define digout_enable 0x01      // Bit 0 setado (pino auxout colocado em VDD).
  #define digout_disable 0x00     // Bit 0 não setado (pino auxout colocado em GND).
  
  // Masks for setting register 4 (to be used when writing on register 4).
  #define weak_MISO_enable 0x80   // Bit 7 setado (quando apenas 1 chip RHD2000 irá usar a linha MISO).
  #define weak_MISO_disable 0x00  // Bit 7 não setado.
  #define twoscomp_enable 0x40    // Bit 6 setado (habilita representação binária por complemento de 2).
  #define twoscomp_disable 0x00   // Bit 6 não setado (desabilita representação binária por complemento de 2).
  #define absmode_enable 0x20     // Bit 5 setado (habilita retificação de onda completa dos bioamplificadores).
  #define absmode_disable 0x00    // Bit 5 não setado (desabilita retificação de onda completa dos bioamplificadores).
  #define DSP_enable 0x10         // Bit 4 setado (habilita remoção de offset por DSP com filtro IIR Highpass 1ªord)
  #define DSP_disable 0x00        // Bit 4 não setado.
  #define DSP_cutoff_default 0x00 // Bits [3] [2] [1] e [0]. Valor default é zero (0x00). Vide tabela datasheet.
  #define DSP_cutoff_fdpc 0x00    // Bits [3] [2] [1] e [0]. Valor default é zero (0x00). Vide tabela datasheet.
  
  // Masks for setting register 5 (to be used when writing on register 5).
  #define Zcheck_DAC_power_enable 0x40  // Bit 6 setado (habilita o ADC de 8 bits usado para teste de impedância).
  #define Zcheck_DAC_power_disable 0x00 // Bit 6 não setado (economiza energia - 120 uA).
  #define Zcheck_load 0x00              // Bit 5 (deve estar sempre em 0).
  #define Zcheck_scale_0p1_pF  0x00     // Bits [4] e [3] = '00'. Ajuste de capacitância (0.1 pF) para teste de impedância.
  #define Zcheck_scale_1p0_pF  0x08     // Bits [4] e [3] = '01'. Ajuste de capacitância (1.0 pF) para teste de impedância.
  #define Zcheck_scale_10p0_pF 0x18     // Bits [4] e [3] = '11'. Ajuste de capacitância (10.0 pF) para teste de impedância.
  #define Zcheck_conn_all_enable 0x04   // Bit 2 setado. Conecta todos os eletrodos ao pino de entrada elec_test.
  #define Zcheck_conn_all_disable 0x00  // Bit 2 não setado (operação normal do chip).
  #define Zcheck_sel_pol_positive 0x00  // Bit 1 não setado (seleciona entrada não-inversora do bioamp. para teste de impedância).
  #define Zcheck_sel_pol_negative 0x02  // Bit 1 setado (seleciona entrada inversora do bioamp. para teste de impedância).
  #define Zcheck_enable 0x01            // Bit 0 setado (habilita modo de teste de impedância).
  #define Zcheck_disable 0x00           // Bit 0 não setado (desabilita modo de teste de impedância).

/*############################################################################################################
        GLOBAL variables.
############################################################################################################*/ 
    String versao_firmware="V1.0 2022/04/19";



    extern void start_aqT1(uint16_t fsample);
    extern void stop_aqT1();
/*############################################################################################################
        INTAN_NNC class.
############################################################################################################*/
  class INTAN_NNC
  {
    public:
      INTAN_NNC(); // Constructor
  /*############################################################################################################
          CLASS Variables.
  ############################################################################################################*/
      // Bellow are default values, but parameters can be configured by user.
      uint16_t fs=2000;// fs         
      uint16_t fH=100; // fH = 500 Hz        
      uint16_t fL=22;    // fL = 0.5 Hz           
      uint32_t channels=0xFFFFFFFF; /* sample all channels. This variable is used this way:
                                               Each bit field corresponds to a channel. The least significant bit
                                               corresponds to channel 1. The most significant bit corresponds to
                                               channel 32.
                                               Bit = 1 means that the specified channel should be included in the
                                               experiment (should be sampled).
                                               Bit = 0 means that the specified channel should not be included in the
                                               experiment (should not be sampled).
                                            */
      // buildsequence related.
        uint16_t sequence[32]; // sequence of commands to be sent to INTAN.
       // uint16_t lengthseq=0;
                                /* Since sequence is statically allocated, it doesn't mean that it has
                                  50 commands to be sent to INTAN. Actually, the number of commands in
                                  the sequence depends on the number of channels that will be sampled in
                                  the experiment. So, the variable lengthseq indicates the real number of
                                  acquisition commands held in vector sequence[].   

                                  I am going to retire this variable ... for all purposes, it is the same as 
                                  channel_count. Sequence will refer only to commands for reading the channels.
                               */    
      // Count number of channels to be sampled.
        uint16_t channel_count=0;

/*
 * I have added these to class variables ... have taken everything out of the GLOBAL DECLARATION SCOPE
 */
        int SSpin = 9;
        uint16_t buffer[32]; // Buffer for storing data from one single run of all channels .... only up to 32 channels at once
        uint16_t aux[15]; // auxiliary variable used to send RHD2000 configuration and info data to UDP client.
        uint32_t nPackagesReceived=0;   // used to count total number of packages with channel DATA received from INTAN.
        uint8_t num_of_bytes=0;
        char msg[15]; /* variable used for receiving configuration data by user.
                        msg is a string that specifies which parameter is going to be configured and with which value. 
                        F = fs, H = fH, L = fL, C = channels, S = Start and St = Stop.
                      */

        bool bUSBserialNormal=true;
        
    //  uint16_t packet_number=0; /* UDP packet ID. This variable is used to identify UDP packets sent to UDP client,
    //                             allowing the client application to know when an UDP packet is lost. This variable
    //                             is written on beginning of each UDP packet and then it's incremented.
    //                           */
        
  /*############################################################################################################
          Class methods.
  ############################################################################################################*/
      uint16_t mytransfer16(uint16_t data);
      
      void mytransferALL();
      void mytransferALL(int CSel,uint16_t *XXbufferOUT,uint16_t *XXbufferIN,int xxCount);
     
      uint16_t write(uint16_t reg, uint8_t data); //PROGRAMING REGISTERS @ INTAN
      uint16_t read(uint16_t reg);                //READING REGISTERS @ INTAN
      uint16_t clearADC(); //INTAN COMMAND CLEAR ADC ....
      uint16_t dummy(); //SEND 0xFFFF which means nothing ...
      void calibrate(); 
      void setfHIGH(uint16_t fHIGH);
      void setfLOW(uint16_t fLOW);
      void bioamp_power (uint32_t channels);
      void initializeRHD_default();
      void wait_for_configuration();
      void buildsequence(uint32_t ChPROG);
      //void setbuffers();
      void read_config_registers(uint16_t *read_values);
      void read_chip_info(uint16_t *read_info);
      void setupSPI(int xxSSpin);

      void setupINTAN_NNC(int xxSSpin, uint32_t XXchannels, uint16_t XXfs, uint16_t XXfH, double XXfL);


      void USBserialINTAN_NNCread();
      void INTAN_NNCtreatUSBcommand(byte *buffCOM);

      
      private:

      protected:
  };

/*############################################################################################################
        Constructor.
############################################################################################################*/
  INTAN_NNC::INTAN_NNC()
  {
  }

  void  INTAN_NNC::setupINTAN_NNC(int xxSSpin, uint32_t XXchannels, uint16_t XXfs, uint16_t XXfH, double XXfL)
  {
     
     //channels=XXchannels; //I think this is unecessary ... channels is set in build sequence
     buildsequence(XXchannels);  

     fs=XXfs;
     //fH=XXfH; //this became unecessary
     //fL=XXfL; //this bacame unecessary
    
     setupSPI(xxSSpin); //Here xxSSpin is saved into INTAN_NNC SSpin variable ...

     initializeRHD_default();

     
     setfHIGH(XXfH);
     setfLOW(XXfL);
        
     //setbuffers();
     delay(1000);

     
  }

/*############################################################################################################
        uint16_t mytransfer16(uint16_t data)

This function is used by functions: write, clearADC, dummy and calibrate. It sends 16 bits of data on SPI bus
and returns the word (16 bits) sent by INTAN in this transaction (remember that it's a full duplex SPI
                                                                  communication).
############################################################################################################*/
    uint16_t INTAN_NNC::mytransfer16(uint16_t data)
    {
      digitalWriteDirect(SSpin, LOW);
      REG_SPI0_TDR = data;
      while ((REG_SPI0_SR & SPI_SR_TXEMPTY) == 0) {} // wait for data to be sent
      digitalWriteDirect(SSpin, HIGH);
      return (REG_SPI0_RDR & 0xFFFF);
    }
/*############################################################################################################
        void mytransferALL()

Transfering ALL CHANNELS AT ONCE
############################################################################################################*/
    void INTAN_NNC::mytransferALL()
    {  
     int iXC=0;
     while (iXC<channel_count)
     {  
      digitalWriteDirect(SSpin, LOW);  
      REG_SPI0_TDR = sequence[iXC]; //0x63;//Message to be sent vi SPI
      while ((REG_SPI0_SR & SPI_SR_TXEMPTY) == 0) {} // wait for data to be sent 
      buffer[iXC]=REG_SPI0_RDR & 0xFFFF;
      digitalWriteDirect(SSpin, HIGH);
      asm volatile("nop"::);asm volatile("nop"::);asm volatile("nop"::);asm volatile("nop"::);asm volatile("nop"::);
      asm volatile("nop"::);asm volatile("nop"::);asm volatile("nop"::);asm volatile("nop"::);asm volatile("nop"::);
      iXC++;
     }
    nPackagesReceived++;
    bGraveUSART=true;
    }

void INTAN_NNC::mytransferALL(int CSel,uint16_t *XXbufferOUT,uint16_t *XXbufferIN,int xxCount)
    {  
     int iXC=0;
     while (iXC<xxCount)
     {  
      digitalWriteDirect(CSel, LOW);  
      REG_SPI0_TDR = XXbufferOUT[iXC]; //0x63;//Message to be sent vi SPI
      while ((REG_SPI0_SR & SPI_SR_TXEMPTY) == 0) {} // wait for data to be sent 
      XXbufferIN[iXC]=REG_SPI0_RDR & 0xFFFF;
      digitalWriteDirect(CSel, HIGH);
      asm volatile("nop"::);asm volatile("nop"::);asm volatile("nop"::);asm volatile("nop"::);asm volatile("nop"::);
      asm volatile("nop"::);asm volatile("nop"::);asm volatile("nop"::);asm volatile("nop"::);asm volatile("nop"::);
      iXC++;
     }
    nPackagesReceived++;
    bGraveUSART=true;
    }
/*############################################################################################################
        uint16_t write(uint16_t reg, uint8_t data)

This function implements the WRITE command specified by RHD2216/RHD2132 INTAN datasheet.
It writes 8 bits specified by parameter data on register specified by parameter reg.
Also, it returns the word (16 bits) sent by INTAN in this transaction (remember that it's a full duplex SPI
                                                                       communication).
############################################################################################################*/
    uint16_t INTAN_NNC::write(uint16_t reg, uint8_t data)
    {
      // reg = chip register (6 bits. Positions in the 16bit-word: [13, 12, 11, 10, 9 and 8])
      // data = byte to write (8 bits. Positions in the 16bit-word: [7, 6, 5, 4, 3, 2, 1 and 0])
      // Bits 15 and 14 must be 1 and 0, respectively -> 16bit-word: 1 0 R[5] ... R[0] D[7] ... D[0]
      uint16_t mask = 0x8000; //Mask -> 10XXXXXXXXXXXXXX = 1000000000000000
      uint16_t writecommand = mask | (reg << 8) | data;

      return(mytransfer16(writecommand));
    }
/*############################################################################################################
        uint16_t read(uint16_t reg)

This function implements the READ command specified by RHD2216/RHD2132 INTAN datasheet.
It sends a READ command on a specific register and returns the word (16 bits) sent by INTAN in this transaction
(remember that it's a full duplex SPI communication).

############################################################################################################*/
    uint16_t INTAN_NNC::read(uint16_t reg)
    {
      // reg = chip register (6 bits in the 16bit-word: [13, 12, 11, 10, 9 and 8])
      // Bits 15 and 14 must be 1 and 1 -> 16bit-word: 1 1 R[5] ... R[0] 0 0 ... 0
      uint16_t mask = 0xC000; //Mask -> 11XXXXXXXXXXXXXX = 1100000000000000
      uint16_t writecommand = mask | (reg << 8);

      return(mytransfer16(writecommand));
    }

/*############################################################################################################
        uint16_t clearADC()

This function implements the CLEAR command specified by RHD2216/RHD2132 INTAN datasheet. It sends the
16bit-word 0b0110101000000000, which clears the ADC calibration of the on-chip ADC, and returns the word
(16 bits) sent by INTAN in this transaction (remember that it's a full duplex SPI communication).
############################################################################################################*/
    uint16_t INTAN_NNC::clearADC()
    {
      return(mytransfer16(0b0110101000000000));
    }

/*############################################################################################################
        uint16_t dummy()

This function sends a dummy command on SPI bus, which is a command with no specific meaning for INTAN.
It can be useful in some cases (From datasheet: "Self-calibration takes many clock cycles to execute;
since the ADC clock is derived solely from SCLK, nine “dummy” commands must be sent after a CALIBRATE command
(along with the usual SCLK and CS pulses) to generate the necessary clock cycles").
After sending a dummy command, this functions returns the word sent by INTAN in the SPI transaction
(remember that it's a full duplex SPI communication).
############################################################################################################*/
    uint16_t INTAN_NNC::dummy()
    {
      return(mytransfer16(0b1111111111111111));
    }


/*############################################################################################################
        void calibrate()

This function implements the CALIBRATE command specified by RHD2216/RHD2132 INTAN datasheet. It sends the
16bit-word 0b0101010100000000, which initiates the ADC self-calibration routine of INTAN RHD, followed by
9 dummy commands, for generating clock pulses necessary in ADC calibration.
############################################################################################################*/
    void INTAN_NNC::calibrate()
    {
      uint8_t k = 0;
      mytransfer16(0b0101010100000000);
      for(k=0;k<8;k++)
      {
        dummy();
      }
    }

/*############################################################################################################
        void setfHIGH(uint16_t fH)

This function is called inside void startaq() function.
This function sets the cutoff frequency of the RHD on-chip lowpass filter.
fH specified in Hertz (the value specified should be on the table of RHD2216/RHD2132 INTAN datasheet page 25).
If not, nothing is done.
############################################################################################################*/
    void INTAN_NNC::setfHIGH (uint16_t fHIGH)
    {
        fH=fHIGH;
        uint8_t RH1DAC1=0, RH1DAC2=0, RH2DAC1=0, RH2DAC2=0;

        if (fH==20000)
        {
            RH1DAC1=8;
            RH1DAC2=0;
            RH2DAC1=4;
            RH2DAC2=0;
        }
        else if (fH==15000)
        {
            RH1DAC1=11;
            RH1DAC2=0;
            RH2DAC1=8;
            RH2DAC2=0;
        }
        else if (fH==10000)
        {
            RH1DAC1=17;
            RH1DAC2=0;
            RH2DAC1=16;
            RH2DAC2=0;
        }
        else if (fH==7500)
        {
            RH1DAC1=22;
            RH1DAC2=0;
            RH2DAC1=23;
            RH2DAC2=0;
        }
        else if (fH==5000)
        {
            RH1DAC1=33;
            RH1DAC2=0;
            RH2DAC1=37;
            RH2DAC2=0;
        }
        else if (fH==3000)
        {
            RH1DAC1=3;
            RH1DAC2=1;
            RH2DAC1=13;
            RH2DAC2=1;
        }
        else if (fH==2500)
        {
            RH1DAC1=13;
            RH1DAC2=1;
            RH2DAC1=25;
            RH2DAC2=1;
        }
        else if (fH==2000)
        {
            RH1DAC1=27;
            RH1DAC2=1;
            RH2DAC1=44;
            RH2DAC2=1;
        }
        else if (fH==1500)
        {
            RH1DAC1=1;
            RH1DAC2=2;
            RH2DAC1=23;
            RH2DAC2=2;
        }
        else if (fH==1000)
        {
            RH1DAC1=46;
            RH1DAC2=2;
            RH2DAC1=30;
            RH2DAC2=3;
        }
        else if (fH==750)
        {
            RH1DAC1=41;
            RH1DAC2=3;
            RH2DAC1=36;
            RH2DAC2=4;
        }
        else if (fH==500)
        {
            RH1DAC1=30;
            RH1DAC2=5;
            RH2DAC1=43;
            RH2DAC2=6;
        }
        else if (fH==300)
        {
            RH1DAC1=6;
            RH1DAC2=9;
            RH2DAC1=2;
            RH2DAC2=11;
        }
        else if (fH==250)
        {
            RH1DAC1=42;
            RH1DAC2=10;
            RH2DAC1=5;
            RH2DAC2=13;
        }
        else if (fH==200)
        {
            RH1DAC1=24;
            RH1DAC2=13;
            RH2DAC1=7;
            RH2DAC2=16;
        }
        else if (fH==150)
        {
            RH1DAC1=44;
            RH1DAC2=17;
            RH2DAC1=8;
            RH2DAC2=21;
        }
        else if (fH==100)
        {
            RH1DAC1=38;
            RH1DAC2=26;
            RH2DAC1=5;
            RH2DAC2=31;
        }
        else
        {
            // if the specified fH value doesn't exist in RHD2000 datasheet table, do nothing.
            return;
        }

        write(0x0008, RH1DAC1); // writes RH1DAC1 on register 8 of INTAN RHD.
        write(0x0009, RH1DAC2); // writes RH1DAC2 on register 9 of INTAN RHD.
        write(0x000A, RH2DAC1); // writes RH2DAC1 on register 10 of INTAN RHD.
        write(0x000B, RH2DAC2); // writes RH2DAC2 on register 11 of INTAN RHD.
    }

/*############################################################################################################
        void setfLOW(uint16_t fL)

This function is called inside void startaq() function.
It sets the cutoff frequency of the RHD on-chip highpass filter.
fL is an int value that specifies a cutoff frequency for the high-pass filter
based on the position of that cut-off frequency in the table 'Setting Lower Bandwidth:
On-Chip Register Values' (page 26 of RHD2000 INTAN datasheet). In that table, values
are sorted in descending order. This way, if fL = 1, the first value is selected, which
is 500 Hz. If fL = 10, the tenth value is selected, which is 25 Hz.
Note that if the user interface is built properly, the association between the fL selected
and its position on the table from the datasheet is not necessary when configuring parameter
fL at beginning of experiment.
############################################################################################################*/
    void INTAN_NNC::setfLOW(uint16_t fLOW)
    { 
        fL=fLOW;
        uint8_t RLDAC1=0, RLDAC2=0, RLDAC3=0;

        if (fL==1) // 500 Hz
        {
            RLDAC1=13;
            RLDAC2=0;
            RLDAC3=0;
        }
        else if (fL==2) // 300 Hz
        {
            RLDAC1=15;
            RLDAC2=0;
            RLDAC3=0;
        }
        else if (fL==3) // 250 Hz
        {
            RLDAC1=17;
            RLDAC2=0;
            RLDAC3=0;
        }
        else if (fL==4) // 200 Hz
        {
            RLDAC1=18;
            RLDAC2=0;
            RLDAC3=0;
        }
        else if (fL==5) // 150 Hz
        {
            RLDAC1=21;
            RLDAC2=0;
            RLDAC3=0;
        }
        else if (fL==6) // 100 Hz
        {
            RLDAC1=25;
            RLDAC2=0;
            RLDAC3=0;
        }
        else if (fL==7) // 75 Hz
        {
            RLDAC1=28;
            RLDAC2=0;
            RLDAC3=0;
        }
        else if (fL==8) // 50 Hz
        {
            RLDAC1=34;
            RLDAC2=0;
            RLDAC3=0;
        }
        else if (fL==9) // 30 Hz
        {
            RLDAC1=44;
            RLDAC2=0;
            RLDAC3=0;
        }
        else if (fL==10) // 25 Hz
        {
            RLDAC1=48;
            RLDAC2=0;
            RLDAC3=0;
        }
        else if (fL==11) // 20 Hz
        {
            RLDAC1=54;
            RLDAC2=0;
            RLDAC3=0;
        }
        else if (fL==12) // 15 Hz
        {
            RLDAC1=62;
            RLDAC2=0;
            RLDAC3=0;
        }
        else if (fL==13) // 10 Hz
        {
            RLDAC1=5;
            RLDAC2=1;
            RLDAC3=0;
        }
        else if (fL==14) // 7.5 Hz
        {
            RLDAC1=18;
            RLDAC2=1;
            RLDAC3=0;
        }
        else if (fL==15) // 5 Hz
        {
            RLDAC1=40;
            RLDAC2=1;
            RLDAC3=0;
        }
        else if (fL==16) // 3 Hz
        {
            RLDAC1=20;
            RLDAC2=2;
            RLDAC3=0;
        }
        else if (fL==17) // 2.5 Hz
        {
            RLDAC1=42;
            RLDAC2=2;
            RLDAC3=0;
        }
        else if (fL==18) // 2 Hz
        {
            RLDAC1=8;
            RLDAC2=3;
            RLDAC3=0;
        }
        else if (fL==19) // 1.5 Hz
        {
            RLDAC1=9;
            RLDAC2=4;
            RLDAC3=0;
        }
        else if (fL==20) // 1 Hz
        {
            RLDAC1=44;
            RLDAC2=6;
            RLDAC3=0;
        }
        else if (fL==21) // 0.75 Hz
        {
            RLDAC1=49;
            RLDAC2=9;
            RLDAC3=0;
        }
        else if (fL==22) // 0.50 Hz
        {
            RLDAC1=35;
            RLDAC2=17;
            RLDAC3=0;
        }
        else if (fL==23) // 0.30 Hz
        {
            RLDAC1=1;
            RLDAC2=40;
            RLDAC3=0;
        }
        else if (fL==24) // 0.25 Hz
        {
            RLDAC1=56;
            RLDAC2=54;
            RLDAC3=0;
        }
        else if (fL==25) // 0.10 Hz
        {
            RLDAC1=16;
            RLDAC2=60;
            RLDAC3=1;
        }

        write(0x000C, RLDAC1); // writes RLDAC1 on register 12 of INTAN RHD.
        write(0x000D, RLDAC2 | (RLDAC3 << 6)); // writes RLDAC2 and RLDAC3 on register 13 of INTAN RHD.
    }

/*############################################################################################################
        void bioamp_power (uint16_t bioamp_select)

This function is called inside void startaq() function.
This function powers down or up individual biopotential amplifiers specified by bioamp_select.
Each bit field of the variable bioamp_select corresponds to a channel (1 = channel on; 0 = off).

If there are channels that do not need to be observed, it's recommended to turn off the corresponding
bioamplifiers to reduce power consumption. Each amplifier consumes power in proportion to its upper
cutoff frequency. Current consumption is approximately 7.6 μA/kHz per amplifier.
Under normal operation, all amplifiers should be powered up.
############################################################################################################*/
    void INTAN_NNC::bioamp_power(uint32_t bioamp_select)
    {
        uint8_t bioamps0to7 = bioamp_select>>24 & 0xFF;       // bioamps. from 0 to 7.
        uint8_t bioamps8to15 = bioamp_select>>16 & 0xFF;      // bioamps. from 8 to 15.
        uint8_t bioamps16to23 = bioamp_select>>8 & 0xFF;      // bioamps. from 16 to 23.
        uint8_t bioamps24to31 = bioamp_select & 0xFF;         // bioamps. from 24 to 31.
      
        write(0x0E, bioamps0to7);   // writes on register 14.
        write(0x0F, bioamps8to15);   // writes on register 15.
        write(0x10, bioamps16to23); // writes on register 16.
        write(0x11, bioamps24to31); // writes on register 17.
    }

/*############################################################################################################
        void initializeRHD_default();

This functions performs a default initialization of RHD INTAN configuration registers.

Register 0: ADC Configuration and Amplifier Fast Settle
Register 1: Supply Sensor and ADC Buffer Bias Current
Register 2: MUX Bias Current
Register 3: MUX Load, Temperature Sensor, and Auxiliary Digital Output
Register 4: ADC Output Format and DSP Offset Removal
Register 5: Impedance Check Control
Register 6: Impedance Check DAC
Register 7: Impedance Check Amplifier Select
Powers up all bioamplifiers.
Calibrates RHD on-chip analog to digital converter.
############################################################################################################*/
    void INTAN_NNC::initializeRHD_default()
    {
        write(0x0000, ADC_reference_BW | amp_fast_settle_disable | amp_Vref_enable | ADC_comparator_bias | ADC_comparator_select);
        write(0x0001, VDD_sense_disable | ADC_buffer_bias_default);
        write(0x0002, MUX_bias_current_default);
        write(0x0003, MUX_load | tempS2_disable | tempS1_disable | temp_disable | digout_HiZ_disable | digout_disable);
        write(0x0004, weak_MISO_enable | twoscomp_enable | absmode_disable | DSP_disable | DSP_cutoff_default);
        write(0x0005, Zcheck_DAC_power_disable | Zcheck_load | Zcheck_scale_0p1_pF | Zcheck_conn_all_disable | Zcheck_sel_pol_positive | Zcheck_disable);
        write(0x0006, 0x0000);
        write(0x0007, 0x0000);
        bioamp_power(channels);
        delay(1); // waits 1 ms before calibrating ADC (recommended by RHD2216/RHD2132 datasheet).
        calibrate();
    }
    
/*############################################################################################################
        void INTAN_NNC::wait_for_configuration()
############################################################################################################*/
  void INTAN_NNC::wait_for_configuration()
  {
    do 
    {
        num_of_bytes = SerialUSB.available();
        delay(10);
        
        if (num_of_bytes) // if client has sent data, then interpret the data.
        {
          SerialUSB.readBytes(msg, 15);

          if (msg[0] == 'c') // message begining with character c sent by client with configuration parameters
          // The incoming packet has the following structure:
          // packet[0] = byte representing character 'c'
          // packet[1-2] = 2 bytes fo fS
          // packet[3-4] = 2 bytes fo fH
          // packet[5-6] = 2 bytes fo fL
          // packet[7-8] = 2 bytes fo channels
            {
              fs = ( msg[1] << 8 | msg[2]);

              fH = ( msg[3] << 8 | msg[4]);
              setfHIGH(fH);

              fL = ( msg[5] << 8 | msg[6]);
              setfLOW(fL);

              channels = ( msg[7] << 8 | msg[8]);
              
              // Echo confirmation message.
                SerialUSB.write(msg, num_of_bytes);
            }
            else if (msg[0] == 'R') // R of Read.
            {
              read_config_registers(aux);
              SerialUSB.write((char *)aux, 20);
            }
            else if (msg[0] == 'I') // I of Info.
            {
              read_chip_info(aux);
              SerialUSB.write("I", 1);
              SerialUSB.write((char *)aux, 18);
            }
            else if (msg[0] == 'S') // S of Start.
            {
            }
        }     
    } while (msg[0] != 'S'); // S of start
    delay(200);
  }

/*############################################################################################################
        void INTAN_NNC::buildsequence(uint16_t channels)

This function is called inside void startaq() function. When the user defines which channels are going to be
sampled, this function builds the sequence of CONVERT commands to be sent periodically (period = 1/fsample),
in order to retrieve samples from the specified channels.
############################################################################################################*/
    void INTAN_NNC::buildsequence(uint32_t ChPROG)
    {
      //lengthseq=0; //This variable is depricated.
      channel_count=0;//Let's initialize the sequence in ZERO length to start with
      channels=ChPROG; //Set channels here ... this is where we program the channels ...
       
      for (uint16_t j=0; j<32; j++) //there is a max of 32 channels in an INTAN CHIP ... let's run all possibilities.
        if(channels & ((0b1) << j))
        {
            //*(sequence+lengthseq) = j << 8; //CONVERT(ch) command.
            *(sequence+channel_count) = j << 8; //CONVERT(ch) command.
            //lengthseq = lengthseq + 1;
            channel_count++;
        }
    }

/*############################################################################################################
        void INTAN_NNC::setbuffers()

This function calculates buffer size and number of buffers to create, in a way that with the specified fsample
and number of channels to sample, the buffers are filled with data and sent to client 10 times per second.
This function returns the buffer size (parameter to isr_buffertimer function).
############################################################################################################*/
/*    void INTAN_NNC::setbuffers()
    {
      
        uint32_t bytesper50ms=0;
        uint32_t aux_size;
            
        //Determine number of bytes generated in a 50 ms interval (buffer has to be sent 20 times/s, that is, each 50 ms)
        bytesper50ms = (uint32_t)fs * 2 * channel_count / 20;
        packet_size = bytesper50ms; // IN BYTES
    
        if (packet_size > MAX_PACKET_SIZE) 
            packet_size = MAX_PACKET_SIZE; // IN BYTES
    
        // Calculating packet size so the number of samples in it is a multiple of the number of channels.
        // This way, it's easier to read the samples on the application that receives data.
        aux_size = 0;
        while (aux_size <= packet_size)
        {
            aux_size = aux_size + 2*channel_count; // Make aux_size grow in steps of 2*channel_count bytes.
        }
        
        packet_size = aux_size - 2*channel_count; // Need to do this because in the last while iteration, packet_size limit is violated.
        
        buffer_size = (packet_size*5); //IN BYTES
    
        // Allocate memory for buffers and UDP packet.
        buffer = (uint16_t *) malloc(buffer_size);
        
    } // end setbuffers

*/

/*############################################################################################################
        void read_config_registers(uint16_t *read_values)
############################################################################################################*/    
void INTAN_NNC::read_config_registers(uint16_t *read_values)
{
  read((uint16_t)0); // read Register 0: ADC Configuration and Amplifier Fast Settle
  read((uint16_t)4); // read Register 4: ADC Output Format and DSP Offset Removal
  read_values[0] = read((uint16_t)8);  // Here comes the answer to the first read command. Read Registers 8-13: On-Chip Amplifier Bandwidth Select
  read_values[1] = read((uint16_t)9); // Here comes the answer to the second read command.
  read_values[2] = read((uint16_t)10); // And so on...
  read_values[3] = read((uint16_t)11);
  read_values[4] = read((uint16_t)12);
  read_values[5] = read((uint16_t)13); // finish reading amplifier bandwith select registers
  read_values[6] = read((uint16_t)14); // read Registers 14 and 15: Individual Amplifier Power
  read_values[7] = read((uint16_t)15);
  read_values[8] = dummy(); // Need to send two dummies to retrieve answer of the last two READ commands.
  read_values[9] = dummy();
}

/*############################################################################################################
        void read_chip_info(uint16_t *read_info)
############################################################################################################*/    
void INTAN_NNC::read_chip_info(uint16_t *read_info)
{
  read((uint16_t)40); // Read registers 40-44 with INTAN characters in ASCII code.
  read((uint16_t)41);
  read_info[0] = read((uint16_t)42);  // Here comes the answer to the first read command.
  read_info[1] = read((uint16_t)43); // Here comes the answer to the second read command.
  read_info[2] = read((uint16_t)44); // And so on...
  read_info[3] = read((uint16_t)60); // Read die revision.
  read_info[4] = read((uint16_t)61); // Read unipolar/bipolar amplifiers.
  read_info[5] = read((uint16_t)62); // Read number of amplifiers.
  read_info[6] = read((uint16_t)63); // Read chip ID.
  read_info[7] = dummy(); // Need to send two dummies in order to retrieve answers of the last two READ commands.
  read_info[8] = dummy();
}

/*############################################################################################################
        void INTAN_NNC::setupESP8266WiFi()
############################################################################################################*/    
  void INTAN_NNC::setupSPI(int xxSSpin) // Configure SPI communication
  {
    SSpin=xxSSpin;
    pinMode(SSpin, OUTPUT);
    SPI.begin();

    REG_SPI0_CR = SPI_CR_SWRST; // reset SPI
    REG_SPI0_CR=0x1; //SPI enable
    REG_SPI0_MR = SPI_MR_MODFDIS|0x00000001;    // master and no modefault
    REG_SPI0_CSR = SPI_MODE0|(0x00000780); // DLYBCT=0, DLYBS=0, SCBR=2A, 16 bit transfer
    // second hexadecilam configures the number of bits of the SPI word. 0x8 = 16 bits (see datasheet)
    //third and fourth hexadecimal numbers configure SCBR parameter, which is related to SCLK by the equation: 84 MHz (Due Master Clock) / SCBR

    
  }



/*############################################################################################################
        void INTAN_NNC::USBserialINTAN_NNCread()
        Function to treat incoming messages from Raspberryt Controler
############################################################################################################*/    
  void INTAN_NNC::USBserialINTAN_NNCread() // Configure SPI communication
  {
    byte buffIN[5]; // ALL COMMANDS START WITH 4 BYTES (32bits)
    buffIN[4]=0;
    if (bUSBserialNormal) // Normal opperation ... readcommand. 
        {

        while (SerialUSB.available())
          {
            SerialUSB.readBytes(buffIN,4);
            INTAN_NNCtreatUSBcommand(buffIN);
          }

        
        } else
          {
          
          }


 
  }

void INTAN_NNC::INTAN_NNCtreatUSBcommand(byte *buffCOM) // Configure SPI communication
  {
    uint16_t* uiTEMP;
    switch(buffCOM[0])
    {
      case 0x00:
          SerialUSB.println("Firmware version: "+ versao_firmware);
          SerialUSB.println(String("SETTINGS: Sampling(") + fs + "); Channels(" + channel_count + ")");
          return;       
       break;

          
      case 0x41: 
        buffCOM[3]++;
        buffCOM[0]=DSP_cutoff_fdpc|0x43;
        buffCOM[1]=DSP_cutoff_fdpc|0x55;
        break;

      case 0x11:
          start_aqT1(fs);
          break;

      case 0xFF:
          stop_aqT1();
          buffCOM[3]='K';buffCOM[2]='O';
          break;

      case 0xC0: //We are receiving this data as BIG ENDIAN (MSB at the begining)
          uiTEMP=(uint16_t *)(buffCOM+2);  
          *uiTEMP=__builtin_bswap16(*uiTEMP); //Transform in LITTLE ENDIAN - Arduino C++ format for uint16
          fs=*uiTEMP;
          break;
          
      case 0xC1: //Program chgannels 15-0 in this order
          //uiTEMP=(uint16_t *)(buffCOM+2);  
          //*uiTEMP=__builtin_bswap16(*uiTEMP);
          channels=(channels&0xFFFF0000)|((buffCOM[2])<<8)|((buffCOM[3]));
          buildsequence(channels);
          buffCOM=(byte *)&channels;
          break;
              
      case 0xC2: //Program chgannels 31-16 in this order
          //uiTEMP=(uint16_t *)(buffCOM+2); 
          //*uiTEMP=__builtin_bswap16(*uiTEMP);
          channels=(channels&0x0000FFFF)|((buffCOM[2])<<24)|((buffCOM[3])<<16);
          buildsequence(channels);
          buffCOM=(byte *)&channels;
          break;
          
      case 0xC3: //We are receiving this data as BIG ENDIAN (MSB at the begining)
          uiTEMP=(uint16_t *)(buffCOM+2);  
          *uiTEMP=__builtin_bswap16(*uiTEMP);  //Transform in LITTLE ENDIAN - Arduino C++ format for uint16
          setfHIGH(*uiTEMP);
          break;

      case 0xC4: //We are receiving this data as BIG ENDIAN (MSB at the begining)
          uiTEMP=(uint16_t *)(buffCOM+2);  
          *uiTEMP=__builtin_bswap16(*uiTEMP); //Transform in LITTLE ENDIAN - Arduino C++ format for uint16
          setfLOW(*uiTEMP);
          break; 
          
      case 0xC5: //We are receiving this data as BIG ENDIAN (MSB at the begining)
          uiTEMP=(uint16_t *)(buffCOM+2);  
          *uiTEMP=__builtin_bswap16(*uiTEMP);
          mytransfer16(*uiTEMP);
          dummy();
          *uiTEMP=dummy();
          *uiTEMP=__builtin_bswap16(*uiTEMP); //Transform in LITTLE ENDIAN into BIG ENDIAN to send back to PYTHON
          break; 

      default:
        byte  xB[4]={0x80,0x7F,0xFC,0xFE};
        buffCOM = xB;
        break;
     
    }

 SerialUSB.write(buffCOM,4);   
  }
  
#endif
