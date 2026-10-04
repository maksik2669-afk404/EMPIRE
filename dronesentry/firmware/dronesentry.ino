// DroneSentry — бортовой детектор дронов для DJI Mavic.
// Платформа: Seeed Xiao ESP32-S3 + RX5808 (SPI mod) + SX1262 + ATGM336H.
//
// Вся геометрия считается относительно носителя. Позиция оператора в прошивке
// не используется и не передаётся.

#include <Arduino.h>
#include <SPI.h>

// ---------- Конфигурация железа ----------
static const int PIN_RX5808_CS   = 2;
static const int PIN_RX5808_CLK  = 3;
static const int PIN_RX5808_DATA = 4;
static const int PIN_RX5808_RSSI = 5;   // ADC

// Полоса аналогового FPV: 5645..5945 МГц. Шаг 5 МГц даёт 61 точку;
// при 30 мс на точку полный свип ~1.8 с, что укладывается в TRACK_TIMEOUT 8 с.
static const uint16_t SWEEP_START_MHZ = 5645;
static const uint16_t SWEEP_STOP_MHZ  = 5945;
static const uint16_t SWEEP_STEP_MHZ  = 5;
static const uint8_t  SWEEP_SETTLE_MS = 30;   // PLL RX5808 захватывает ~25 мс

// Порог детекции над шумовым полом. 8 дБ — компромисс: ниже начинаются
// ложные срабатывания от собственного видеолинка Mavic на 2.4/5.8.
static const float DETECT_MARGIN_DB = 8.0f;

// ---------- Протокол вниз (см. dronesentry/protocol.py) ----------
static const uint8_t PROTO_MAGIC   = 0xD5;
static const uint8_t PROTO_VERSION = 1;
static const uint8_t MAX_TRACKS    = 8;

struct TrackReport {
  uint8_t  id;
  uint8_t  flags;      // bit0-1 класс, bit2 точная дистанция, bit3-4 уровень
  uint8_t  bearing;    // 0..254, 0xFF = неизвестен
  int8_t   elevation;  // градусы
  uint16_t range_m;
  int8_t   closing_mps;
  uint16_t ident_hash;
} __attribute__((packed));

static uint8_t crc8(const uint8_t *data, size_t len) {
  uint8_t crc = 0x00;
  for (size_t i = 0; i < len; i++) {
    crc ^= data[i];
    for (uint8_t b = 0; b < 8; b++) {
      crc = (crc & 0x80) ? (uint8_t)((crc << 1) ^ 0x07) : (uint8_t)(crc << 1);
    }
  }
  return crc;
}

// ---------- Состояние свипа ----------
struct SweepBin {
  uint16_t freq_mhz;
  float    rssi_dbm;
};
static SweepBin sweep[(SWEEP_STOP_MHZ - SWEEP_START_MHZ) / SWEEP_STEP_MHZ + 1];
static size_t sweep_len = 0;
static float  noise_floor_dbm = -95.0f;

// RX5808 принимает 25-битное слово по собственному 3-проводному протоколу.
static void rx5808_set_freq(uint16_t mhz) {
  // Регистр синтезатора: f = 2 * (N * 32 + A) * 2 МГц + 479 МГц
  uint16_t raw = (uint16_t)((mhz - 479) / 2);
  uint16_t n = raw / 32;
  uint16_t a = raw % 32;
  uint32_t word = ((uint32_t)n << 7) | a;

  digitalWrite(PIN_RX5808_CS, LOW);
  // Адрес регистра 0x1 (Synth B), бит R/W = 1 (запись), затем 20 бит данных.
  uint32_t packet = 0x01 | (1u << 4) | (word << 5);
  for (uint8_t i = 0; i < 25; i++) {
    digitalWrite(PIN_RX5808_DATA, (packet >> i) & 1);
    digitalWrite(PIN_RX5808_CLK, HIGH);
    delayMicroseconds(1);
    digitalWrite(PIN_RX5808_CLK, LOW);
    delayMicroseconds(1);
  }
  digitalWrite(PIN_RX5808_CS, HIGH);
}

// Калибровка ADC→дБм снимается в поле на генераторе. Линейная аппроксимация
// RX5808 держится в пределах ±3 дБ на участке -90..-30 дБм.
static float rx5808_read_rssi_dbm() {
  uint32_t acc = 0;
  for (uint8_t i = 0; i < 8; i++) { acc += analogRead(PIN_RX5808_RSSI); }
  const float counts = acc / 8.0f;
  return -0.0183f * counts - 30.0f;   // ЗАГЛУШКА: заменить на свою калибровку
}

static void sweep_step() {
  static size_t idx = 0;
  const uint16_t f = SWEEP_START_MHZ + idx * SWEEP_STEP_MHZ;
  rx5808_set_freq(f);
  delay(SWEEP_SETTLE_MS);
  sweep[idx].freq_mhz = f;
  sweep[idx].rssi_dbm = rx5808_read_rssi_dbm();

  if (++idx >= sweep_len) {
    idx = 0;
    // Шумовой пол — медиана свипа: устойчива к нескольким занятым каналам.
    float tmp[sizeof(sweep) / sizeof(sweep[0])];
    for (size_t i = 0; i < sweep_len; i++) { tmp[i] = sweep[i].rssi_dbm; }
    for (size_t i = 1; i < sweep_len; i++) {
      float v = tmp[i]; size_t j = i;
      while (j > 0 && tmp[j - 1] > v) { tmp[j] = tmp[j - 1]; j--; }
      tmp[j] = v;
    }
    noise_floor_dbm = tmp[sweep_len / 2];
  }
}

// TODO: Open Drone ID (ASTM F3411) поверх WiFi NAN/beacon и BLE.
// Брать opendroneid-core-c, не писать парсер заново.
static void scan_remote_id() {}

// TODO: DJI DroneID. Формат — RUB-SysSec/DroneSecurity.
static void scan_dji_droneid() {}

// TODO: SX1262, кадр собирается ровно как в dronesentry/protocol.py.
static void downlink_send(const uint8_t *frame, size_t len) { (void)frame; (void)len; }

void setup() {
  Serial.begin(115200);
  pinMode(PIN_RX5808_CS, OUTPUT);
  pinMode(PIN_RX5808_CLK, OUTPUT);
  pinMode(PIN_RX5808_DATA, OUTPUT);
  digitalWrite(PIN_RX5808_CS, HIGH);
  analogReadResolution(12);
  sweep_len = sizeof(sweep) / sizeof(sweep[0]);
  Serial.println(F("DroneSentry: свип 5645-5945 МГц, Remote ID, downlink LoRa"));
}

void loop() {
  sweep_step();
  scan_remote_id();
  scan_dji_droneid();

  static uint32_t last_tx_ms = 0;
  if (millis() - last_tx_ms >= 1000) {   // 1 Гц, бюджет LoRa SF9 позволяет
    last_tx_ms = millis();
    uint8_t frame[4 + MAX_TRACKS * sizeof(TrackReport) + 1];
    size_t n = 0;
    // Заголовок заполняется после подсчёта целей; тела пока нет, пока парсеры
    // не подключены — отправляем пустой валидный кадр как keepalive.
    frame[0] = PROTO_MAGIC;
    frame[1] = (uint8_t)((PROTO_VERSION << 4) | 0);
    frame[2] = 0;                 // seq
    frame[3] = 0; frame[4] = 0;   // own_alt_m, little-endian uint16
    n = 5;
    frame[n] = crc8(frame, n);
    downlink_send(frame, n + 1);
  }
}
