#include "DueTimer.h"

// Variáveis globais
volatile uint32_t interrupt_start_count = 0;
volatile uint32_t interrupt_end_count = 0;
volatile uint32_t total_exec_time = 0; // Em microssegundos
volatile uint32_t num_measures = 0;

unsigned long last_print_time = 0;
const double target_frequency = 2000; // Frequência de disparo do Timer4 (Hz)

void setup() {
  SerialUSB.begin(115200);
  while (!SerialUSB); // Aguarda conexão USB

  SerialUSB.println("Iniciando teste de impacto de acquisition_interrupt()...");

  Timer4.attachInterrupt(acquisition_interrupt);
  Timer4.setFrequency(target_frequency);
  Timer4.start();
}

void loop() {
  if (millis() - last_print_time >= 1000) { // A cada 1 segundo
    noInterrupts();
    uint32_t start = interrupt_start_count;
    uint32_t end = interrupt_end_count;
    uint32_t avg_exec_time = (num_measures > 0) ? (total_exec_time / num_measures) : 0;
    
    // Zera contadores
    interrupt_start_count = 0;
    interrupt_end_count = 0;
    total_exec_time = 0;
    num_measures = 0;
    interrupts();
    
    SerialUSB.print("[STATUS] Comecos: ");
    SerialUSB.print(start);
    SerialUSB.print(" | Finais: ");
    SerialUSB.print(end);
    SerialUSB.print(" | Diferenca: ");
    SerialUSB.print(start - end);
    SerialUSB.print(" | Tempo medio execucao: ");
    SerialUSB.print(avg_exec_time);
    SerialUSB.println(" us");
    
    last_print_time = millis();
  }
}

// Simula o acquisition_interrupt do seu MicroMAP
void acquisition_interrupt() {
  interrupt_start_count++;
  
  unsigned long t_start = micros();
  
  simulate_convert_channels(); // Aqui simulamos a função que lê canais
  
  unsigned long t_end = micros();
  
  // Acumula o tempo de execução
  total_exec_time += (t_end - t_start);
  num_measures++;
  
  interrupt_end_count++;
}

// Função simulada para substituir convert_channels()
void simulate_convert_channels() {
  noInterrupts(); // Simulando que você trava outras interrupções durante aquisição

  const uint16_t num_channels = 16; // Simulando 16 canais lidos
  volatile uint16_t dummy_read;

  for (uint16_t i = 0; i < num_channels; i++) {
    // Simula o tempo de mandar comando SPI + receber resposta
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    dummy_read = i; // só para não otimizar via compilador
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
    asm volatile("nop"::); asm volatile("nop"::); asm volatile("nop"::);
  }

  interrupts(); // Libera novamente
}