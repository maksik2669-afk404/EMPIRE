# Прошивка DroneSentry (ESP32-S3)

Два независимых канала обнаружения, один канал вниз.

| Канал | Железо | Что ловит |
|---|---|---|
| Remote ID / DroneID | WiFi+BLE радио ESP32-S3 | класс A: DJI, Autel, легальные коммерческие |
| RSSI-свип 5.8 ГГц | RX5808 с SPI-модом | класс B: аналоговые и часть цифровых VTX |
| RSSI-свип 2.4 ГГц | WiFi-радио ESP32 в promiscuous | класс B: каналы управления |
| Downlink | SX1262 LoRa 868/915 МГц | телеметрия до оператора, независимо от DJI |
| Своя позиция | ATGM336H UART | дистанция считается ОТ носителя |

## Состояние

- `dronesentry.ino` — каркас: расписание задач, свип RX5808, сборка кадра.
- Парсер Open Drone ID (ASTM F3411) — **заглушка.** Брать готовый:
  [opendroneid/opendroneid-core-c](https://github.com/opendroneid/opendroneid-core-c),
  референс приёмника — [orecchino-esp32](https://github.com/isaacbentley/orecchino-esp32).
- Парсер DJI DroneID — **заглушка.** Формат разобран в
  [RUB-SysSec/DroneSecurity](https://github.com/RUB-SysSec/DroneSecurity).

## Не проверено на железе

Ни одна строка здесь не летала. Калибровка RSSI→дистанция требует измерений
в поле: известная цель, известная мощность, замеры на 50/100/200/400/800 м.
До калибровки константы в `dronesentry/rssi.py` — литература, не ваш модуль.
