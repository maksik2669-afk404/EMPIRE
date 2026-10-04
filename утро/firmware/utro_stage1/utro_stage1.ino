// utro_stage1.ino — прошивка проверочного стенда «Утро», ЭТАП 1.
//
// Платформа: ESP32-S3, Arduino-ESP32 core 3.x (ESP-IDF 5.1+).
//
// ЗАЧЕМ ЭТО СУЩЕСТВУЕТ
// Этап 1 отвечает на один вопрос: пробивается ли пульс через конкретный
// матрас. Прошивка не считает дыхание и не считает пульс. Её работа —
// отдать хосту сырой сигнал плёнки на РОВНОЙ частоте 200 Гц и честно
// признаться, если хоть один отсчёт потерян. Всё остальное делает
// утро/morning/dsp.py (функция analyze_window, fs=200.0).
//
// Если прошивка соврёт о частоте дискретизации, dsp.py выдаст неверное
// число вдохов и ударов, и человек этого не заметит: 15.3 вдоха в минуту
// выглядит так же правдоподобно, как 15.0. Поэтому вся конструкция ниже
// подчинена одному: ось времени должна быть правдой.
//
// ФИЗИКА, КОТОРУЮ ПРОШИВКА НЕ МОЖЕТ ИСПРАВИТЬ
// PVDF — источник ЗАРЯДА, не напряжения. Ёмкость LDT0-028K около 500 пФ,
// выход высокоимпедансный. Между плёнкой и этим кодом ОБЯЗАН стоять
// зарядовый усилитель (TL072/OPA2134 + резистор обратной связи порядка
// 10 МОм), иначе на входе АЦП не будет ничего, кроме наводки сети.
// Полоса интереса 0.08–20 Гц. Снизу это почти постоянный ток: времена
// установления тракта — секунды, и смещение будет уплывать.
// Амплитуда дыхания на порядок больше сердечной. Если аналоговое усиление
// выставлено так, что дыхание занимает весь диапазон АЦП, пульс утонет в
// одном младшем разряде. Проверять это — командой калибровки (см. ниже),
// с человеком на матрасе: размах не должен превышать примерно половины
// диапазона.
//
// ПРОТОКОЛ (USB-Serial, текст)
//   Строки, начинающиеся с '#', — служебные, хост их пропускает.
//   Строки данных: "<индекс>,<значение>\n", оба числа десятичные без знака.
//   индекс    — НЕ счётчик принятых отсчётов, а ВРЕМЕННАЯ КООРДИНАТА:
//               индекс k означает момент t0 + k*5 мс. Разрыв в индексах
//               равен числу потерянных отсчётов. Хост обязан либо вставить
//               пропуски, либо отбросить окно с разрывом.
//   значение  — СУММА 32 отсчётов АЦП, 0..131040. Не среднее: деление
//               выбросило бы те самые 2.5 разряда, которые дало усреднение.
//               Для вольт делить на 32. Для dsp.py делить не нужно, он
//               инвариантен к масштабу.
//
// ОБЯЗАННОСТЬ ХОСТА, БЕЗ КОТОРОЙ ПУЛЬС НЕ НАЙДЁТСЯ
// Перед вызовом analyze_window из каждого окна НАДО ВЫЧЕСТЬ ЕГО ПЕРВЫЙ
// ОТСЧЁТ:  w = [x - window[0] for x in window].
// Это не косметика. Выход зарядового усилителя сидит на середине питания,
// поэтому в потоке всегда есть большое положительное смещение (около
// 2048*32 = 65536). Биквады в dsp.py стартуют с нулевым состоянием, и это
// смещение для них — ступенька во весь диапазон. Переходный процесс от неё
// попадает в кардиополосу, детектор шевеления видит выброс энергии,
// ставит motion=True, и пульс не выдаётся вовсе. Проверено на синтетике
// (morning/synth.py, 23 положения окна по 60 с, дыхание 15, пульс 63):
//   без вычитания         — пульс найден в  3 окнах из 23
//   вычтено среднее окна  — в 11 из 23
//   вычтен первый отсчёт  — в 23 из 23
// Вычитать среднее недостаточно: окно может начинаться на вершине вдоха, и
// ступенька остаётся. Дыхание, в отличие от пульса, восстанавливается при
// любом варианте — ошибка молчаливая и видна только по пропавшему пульсу.
//
// Почему смещение не убирает прошивка: во-первых, уровень покоя — главная
// проверка, жив ли тракт, и терять его нельзя; во-вторых, вычитание
// скользящего среднего в прошивке — это фильтр верхних частот с
// характеристикой, попадающей прямо в полосу дыхания 0.08-0.7 Гц, то есть
// порча измеряемой величины ради удобства разбора.
//
// КОМАНДЫ (одна строка, завершается \n или \r)
//   s        начать поток
//   x        остановить поток
//   c[N]     калибровка: N секунд (1..60, по умолчанию 10), затем отчёт
//   v        повторить строку-заголовок
//   z        сбросить счётчики потерь
//   ?        справка
//
// ПОРЯДОК РАБОТЫ
//   1. Собрать тракт, НЕ кладя плёнку под матрас. Подать питание.
//   2. "c 10" — проверить, что тракт жив: смещение около середины
//      диапазона, СКО не нулевое, наводка 50 Гц мала.
//   3. Уложить плёнку под матрас на уровне груди, лечь.
//   4. "c 30" — убедиться, что дыхание не упирает тракт в шину.
//   5. "s", писать 10 минут, "x". analyze_window требует минимум 20 с
//      (4000 отсчётов), рабочее окно продукта — 60 с.
//
// ЧТО НЕ ПРОВЕРЕНО НА ЖЕЛЕЗЕ
// Ни одна строка этого файла не работала с реальной плёнкой. Все пороги в
// отчёте калибровки — рассуждение, а не измерение; они помечены по месту.
// Коэффициент передискретизации 32 выбран по арифметике, а не по
// измеренному спектру шума АЦП.

// --------------------------------------------------------------------------
// КОНФИГУРАЦИЯ
// --------------------------------------------------------------------------

#define UTRO_FW_VERSION "1.0.0"
#define UTRO_PROTO      1

// Вход АЦП. ТОЛЬКО ADC1: на ESP32-S3 он выведен на GPIO1..GPIO10, и номер
// канала равен номеру вывода минус один. ADC2 (GPIO11..GPIO20) брать нельзя
// по трём причинам: он делится с радиоблоком, в режиме DMA на S3 он
// проблемен, а GPIO19/20 — это линии USB, через которые идёт сам поток.
// GPIO4 (ADC1_CH3) выбран потому, что он свободен и на DevKitC-1, и на
// XIAO ESP32-S3, не является выводом загрузочной стратегии (в отличие от
// GPIO0/3/45/46), не занят флешем и PSRAM (GPIO26..37 на N16R8) и не
// совпадает со встроенным светодиодом.
#ifndef UTRO_ADC_GPIO
#define UTRO_ADC_GPIO 4
#endif

// 12 дБ — максимальное ослабление, диапазон примерно 0..3.1 В. Нужен весь
// диапазон: выход зарядового усилителя сидит на середине питания (~1.65 В),
// и сигнал идёт в обе стороны от неё.
#define UTRO_ADC_ATTEN  ADC_ATTEN_DB_12

// На S3 у АЦП только 12 разрядов, выбора нет.
#define UTRO_ADC_BITS   ADC_BITWIDTH_12
#define UTRO_ADC_MAX    4095u

// Итоговая частота. Ровно та, которую ждёт dsp.py по умолчанию.
#define UTRO_OUT_RATE_HZ   200u

// Передискретизация. Четыре причины именно для 32:
//  1) У adc_continuous на S3 есть аппаратный минимум частоты — 611 Гц.
//     200 Гц напрямую DMA выдать не может, усреднение не роскошь, а условие.
//  2) 200*32 = 6400 Гц делит нацело и 80 МГц, и 160 МГц (делители 12500 и
//     25000), поэтому делитель АЦП не округляется и выход получается ровно
//     200.000 Гц от кварца, а не 199.8 или 200.3.
//  3) Усреднение 32 отсчётов давит белый шум в sqrt(32) = 5.66 раза, это
//     2.5 разряда. 12-разрядный АЦП ESP32 шумный; сколько из этих 2.5
//     разрядов получится на самом деле — зависит от того, насколько шум
//     белый, а на железе это НЕ ПРОВЕРЕНО.
//  4) Прямоугольное окно усреднения длиной 1/200 с имеет нули ровно на
//     200 Гц и кратных — то есть именно там, откуда приходит наложение
//     при прореживании до 200 Гц.
// Если менять: UTRO_OUT_RATE_HZ * UTRO_OVERSAMPLE обязано остаться внутри
// [611, 83333] Гц и желательно делить 80 МГц нацело.
#define UTRO_OVERSAMPLE    32u
#define UTRO_RAW_RATE_HZ   (UTRO_OUT_RATE_HZ * UTRO_OVERSAMPLE)

// Скорость порта. Строка данных в худшем случае 18 байт (10 цифр индекса,
// запятая, 6 цифр значения, перевод строки), типично 14. Поток:
// 200 * 18 = 3600 Б/с, на проводе с старт-стоповыми битами 36 кбит/с.
// 460800 бод даёт 46 кБ/с, запас 12-кратный, и это стандартный делитель,
// который без проблем держат CP2102N, CH343 и FTDI на платах DevKitC-1.
// Если мост старый (CH340) и на 460800 сыпятся ошибки — поставить 115200,
// запас останется трёхкратным. При сборке с «USB CDC on boot» значение
// игнорируется: там поток идёт через нативный USB.
#define UTRO_SERIAL_BAUD   460800

// Пул DMA: 1.0 с сигнала. Это запас на случай, когда хост или USB-стек
// задумались. Цена — 25.6 кБ внутренней памяти, на S3 это не проблема.
#define UTRO_POOL_FRAMES   200u

// Буфер передачи: 8 кБ, около 580 строк, то есть ещё примерно 2.9 с.
// Пока он не опустеет, пул DMA не вычерпывается — так два буфера работают
// как один, и потеря возможна только в одном месте: в пуле.
#define UTRO_TX_RING       8192u
#define UTRO_TX_LOW_WATER  256u

// Время установления тракта перед записью. Фильтр верхних частот с углом
// 0.08 Гц имеет постоянную времени 1/(2*pi*0.08) = 2.0 с, и первые
// секунды после включения на выходе переходный процесс, который dsp.py
// увидит как гигантскую низкочастотную составляющую. Две секунды — это
// одна постоянная времени, то есть 63% установления: достаточно, чтобы
// переходный процесс не доминировал, НЕ достаточно для абсолютного
// смещения. Настоящее время установления зависит от аналогового тракта,
// которого ещё нет; мерить дрейфом в отчёте калибровки.
#define UTRO_SETTLE_MS     2000u

// Как часто во время потока отдавать строку статистики.
#define UTRO_STAT_MS       5000u

// Калибровка по умолчанию и максимум.
#define UTRO_CAL_DEF_S     10u
#define UTRO_CAL_MAX_S     60u

// Встроенный светодиод. Вариант платы обычно сам определяет LED_BUILTIN
// (на DevKitC-1 это адресный светодиод, и digitalWrite по нему работает
// через ядро). 21 — запасной вариант, светодиод XIAO ESP32-S3.
#if !defined(UTRO_LED_PIN)
#if defined(LED_BUILTIN)
#define UTRO_LED_PIN LED_BUILTIN
#else
#define UTRO_LED_PIN 21
#endif
#endif
// На XIAO ESP32-S3 светодиод включается низким уровнем. Поставить 1.
#ifndef UTRO_LED_ACTIVE_LOW
#define UTRO_LED_ACTIVE_LOW 0
#endif

// Номинальный размах входа при ослаблении 12 дБ, из документации.
// Используется только когда калибровка по eFuse недоступна; ошибка до 10%.
#define UTRO_FULL_SCALE_MV 3100

// --------------------------------------------------------------------------
// ПОДКЛЮЧЕНИЯ И ПРОВЕРКИ СБОРКИ
// --------------------------------------------------------------------------

#include <Arduino.h>
#include <stdio.h>
#include <string.h>
#include <math.h>

#include "esp_adc/adc_continuous.h"
#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"
#include "esp_timer.h"
#include "soc/soc_caps.h"

// Лучше не собраться, чем собраться и молча выдавать мусор на другой плате:
// распределение каналов АЦП и наличие драйвера adc_continuous у разных
// чипов разное.
#if !defined(CONFIG_IDF_TARGET_ESP32S3)
#error "utro_stage1 рассчитана только на ESP32-S3: распределение каналов ADC1 и режим DMA у других чипов другие. Выберите плату ESP32-S3."
#endif

#if !defined(ESP_ARDUINO_VERSION) || !defined(ESP_ARDUINO_VERSION_VAL)
#error "Нужен Arduino-ESP32 core 3.x: в версиях 2.x нет драйвера adc_continuous (esp_adc), а analogRead в loop() даёт дрожание, из-за которого оценка частоты становится ложью."
#elif ESP_ARDUINO_VERSION < ESP_ARDUINO_VERSION_VAL(3, 0, 0)
#error "Нужен Arduino-ESP32 core 3.x: в версиях 2.x нет драйвера adc_continuous (esp_adc)."
#endif

// ADC1 на S3: GPIO1..GPIO10 -> каналы 0..9.
static_assert(UTRO_ADC_GPIO >= 1 && UTRO_ADC_GPIO <= 10,
              "На ESP32-S3 ADC1 выведен только на GPIO1..GPIO10. GPIO11..GPIO20 - это ADC2, он делится с радиоблоком, а GPIO19/20 заняты USB.");
#define UTRO_ADC_CHANNEL ((adc_channel_t)(UTRO_ADC_GPIO - 1))

#if defined(SOC_ADC_SAMPLE_FREQ_THRES_LOW)
static_assert(UTRO_RAW_RATE_HZ >= SOC_ADC_SAMPLE_FREQ_THRES_LOW,
              "Частота АЦП ниже аппаратного минимума: увеличьте UTRO_OVERSAMPLE.");
#endif
#if defined(SOC_ADC_SAMPLE_FREQ_THRES_HIGH)
static_assert(UTRO_RAW_RATE_HZ <= SOC_ADC_SAMPLE_FREQ_THRES_HIGH,
              "Частота АЦП выше аппаратного максимума: уменьшите UTRO_OVERSAMPLE.");
#endif

// Один кадр DMA = ровно один выходной отсчёт. Это не экономия, а
// упрощение: прерывание кадра приходит на каждый выходной отсчёт, задержка
// получается 5 мс, и после любой чистки пула фаза усреднения
// восстанавливается сама, потому что чтение всегда начинается с границы
// кадра.
#define UTRO_FRAME_CONVS   UTRO_OVERSAMPLE
#define UTRO_FRAME_BYTES   (UTRO_FRAME_CONVS * 4u)
#define UTRO_POOL_BYTES    (UTRO_FRAME_BYTES * UTRO_POOL_FRAMES)
#define UTRO_READ_FRAMES   8u
#define UTRO_READ_BYTES    (UTRO_FRAME_BYTES * UTRO_READ_FRAMES)

static_assert(SOC_ADC_DIGI_RESULT_BYTES == 4,
              "Разбор потока DMA написан под 4 байта на преобразование.");

// На S3 результат DMA приходит в формате TYPE2. Поле unit в нём намеренно
// не читается: режим преобразования задан как «только ADC1», и официальный
// пример IDF тоже читает лишь channel и data.
#define UTRO_CONV_CHANNEL(p) ((p)->type2.channel)
#define UTRO_CONV_DATA(p)    ((p)->type2.data)

#if defined(ADC_CALI_SCHEME_CURVE_FITTING_SUPPORTED) && ADC_CALI_SCHEME_CURVE_FITTING_SUPPORTED
#define UTRO_HAVE_CALI 1
#else
#define UTRO_HAVE_CALI 0
#endif

static const double kPi = 3.14159265358979323846;

// --------------------------------------------------------------------------
// СОСТОЯНИЕ
// --------------------------------------------------------------------------

// Режимы. Намеренно не enum: сборщик Arduino вставляет прототипы функций
// сразу после последнего #include, то есть раньше любого типа, объявленного
// в самом скетче, и сигнатура с собственным типом перестала бы собираться.
#define MODE_IDLE    0u
#define MODE_STREAM  1u
#define MODE_CAL     2u

static uint8_t g_mode = MODE_IDLE;

static adc_continuous_handle_t g_adc = NULL;
static bool g_adc_ok = false;       // драйвер создан и настроен
static bool g_adc_running = false;

// Ось времени. g_n_out — индекс СЛЕДУЮЩЕГО выходного отсчёта; индекс 0
// соответствует моменту g_t0_us.
static uint32_t g_n_out = 0;
static int64_t  g_t0_us = 0;
static bool     g_anchored = false;     // установление закончилось, ось привязана
static uint32_t g_settle_until_ms = 0;

// Накопитель передискретизации.
static uint32_t g_acc_sum = 0;
static uint16_t g_acc_cnt = 0;
static bool     g_acc_bad = false;

// Счётчики потерь. Молчать о них нельзя: потерянные отсчёты сдвигают ось
// времени, а значит врут о частоте дыхания и пульса.
static uint32_t g_lost_pool = 0;    // выброшено из-за переполнения пула DMA
static uint32_t g_lost_tx   = 0;    // не поместилось в буфер передачи
static uint32_t g_lost_bad  = 0;    // в кадре было преобразование чужого канала
static uint32_t g_align_err = 0;    // чтение не кратно 4 байтам (не должно случаться)
static volatile uint32_t g_ovf_events = 0;
static volatile bool     g_resync = false;

static uint32_t g_stream_begin_ms = 0;
static uint32_t g_next_stat_ms = 0;

// Буфер передачи.
static char   g_tx[UTRO_TX_RING];
static size_t g_tx_head = 0;
static size_t g_tx_tail = 0;
static size_t g_tx_len  = 0;
static_assert((UTRO_TX_RING & (UTRO_TX_RING - 1)) == 0,
              "Размер буфера передачи должен быть степенью двойки: индекс считается маской.");

// Приём команд.
static char   g_cmd[24];
static size_t g_cmd_len = 0;

// Калибровка.
static uint32_t g_cal_target = 0;
static uint32_t g_cal_n = 0;
static double   g_cal_mean = 0.0;   // Уэлфорд: среднее
static double   g_cal_m2 = 0.0;     // Уэлфорд: сумма квадратов отклонений
static uint32_t g_cal_min = 0;
static uint32_t g_cal_max = 0;
static int64_t  g_cal_i = 0;        // квадратуры для оценки наводки 50 Гц
static int64_t  g_cal_q = 0;
static double   g_cal_first = 0.0;  // половины окна — для оценки дрейфа
static double   g_cal_second = 0.0;
static uint32_t g_cal_nf = 0;
static uint32_t g_cal_ns = 0;

#if UTRO_HAVE_CALI
static adc_cali_handle_t g_cali = NULL;
#endif

static bool g_led_on = false;
static uint32_t g_led_next_ms = 0;

// --------------------------------------------------------------------------
// ОБЪЯВЛЕНИЯ
// --------------------------------------------------------------------------

static void   tx_flush(void);
static bool   tx_push(const char *p, size_t n);
static size_t tx_free(void);
static void   push_line(const char *s);
static void   push_header(void);
static void   push_help(void);
static void   push_stat(void);
static void   fmt_fixed(char *out, size_t cap, double v, unsigned decimals);
static int    raw_to_mv(int raw);
static double boxcar_gain(double f);
static bool   adc_setup(void);
static bool   adc_start(void);
static void   adc_stop(void);
static void   drain_pool(void);
static bool   pump_adc(void);
static void   handle_overflow(void);
static void   consume_sample(uint32_t v, bool bad);
static void   cal_begin(uint32_t seconds);
static void   cal_feed(uint32_t v);
static void   cal_report(void);
static void   session_start(uint8_t mode);
static void   session_stop(bool quiet);
static void   poll_commands(void);
static void   exec_command(const char *line);
static void   led_task(uint32_t now_ms);

// --------------------------------------------------------------------------
// БУФЕР ПЕРЕДАЧИ
// --------------------------------------------------------------------------
// Всё, что уходит на хост, включая служебные строки, идёт через это кольцо.
// Иначе служебная строка, напечатанная напрямую, вклинилась бы в середину
// строки данных, и хост получил бы битое число вместо отсчёта.

static size_t tx_free(void) {
  return UTRO_TX_RING - g_tx_len;
}

// Либо строка целиком, либо ничего: половина строки хуже отсутствия строки.
static bool tx_push(const char *p, size_t n) {
  if (n > tx_free()) return false;
  for (size_t i = 0; i < n; i++) {
    g_tx[g_tx_head] = p[i];
    g_tx_head = (g_tx_head + 1) & (UTRO_TX_RING - 1);
  }
  g_tx_len += n;
  return true;
}

// Отдаём порту ровно столько, сколько он готов принять без блокировки.
// Блокирующая запись остановила бы вычерпывание пула DMA на неизвестное
// время; пусть вместо этого переполнится пул — переполнение мы считаем и
// сообщаем, а зависшую запись никто не заметит.
static void tx_flush(void) {
  int room = Serial.availableForWrite();
  while (room > 0 && g_tx_len > 0) {
    size_t chunk = UTRO_TX_RING - g_tx_tail;      // до конца кольца
    if (chunk > g_tx_len) chunk = g_tx_len;
    if (chunk > (size_t)room) chunk = (size_t)room;
    size_t written = Serial.write((const uint8_t *)&g_tx[g_tx_tail], chunk);
    if (written == 0) break;
    g_tx_tail = (g_tx_tail + written) & (UTRO_TX_RING - 1);
    g_tx_len -= written;
    room -= (int)written;
  }
}

static void push_line(const char *s) {
  tx_push(s, strlen(s));
}

// --------------------------------------------------------------------------
// ФОРМАТИРОВАНИЕ
// --------------------------------------------------------------------------
// Дробные числа печатаются вручную. В сборках с урезанным newlib формат
// "%f" может быть не слинкован и напечатает пустоту, а потерять отчёт
// калибровки из-за формата недопустимо: это единственная проверка, жив ли
// тракт. Поэтому в snprintf ниже встречаются только %s, %d и %lu.
static void fmt_fixed(char *out, size_t cap, double v, unsigned decimals) {
  if (cap == 0) return;
  if (decimals > 4) decimals = 4;
  bool neg = (v < 0.0);
  if (neg) v = -v;
  if (!(v < 1.0e9)) { snprintf(out, cap, "%s", neg ? "-inf" : "inf"); return; }
  uint32_t scale = 1;
  for (unsigned i = 0; i < decimals; i++) scale *= 10u;
  uint32_t fixed = (uint32_t)(v * (double)scale + 0.5);
  uint32_t ip = fixed / scale;
  uint32_t fp = fixed - ip * scale;
  if (decimals == 0) {
    snprintf(out, cap, "%s%lu", neg ? "-" : "", (unsigned long)ip);
    return;
  }
  // Дробную часть печатаем с ведущей единицей и потом её пропускаем —
  // так получается ведущие нули без спецификатора ширины.
  char frac[12];
  snprintf(frac, sizeof frac, "%lu", (unsigned long)(fp + scale));
  snprintf(out, cap, "%s%lu.%s", neg ? "-" : "", (unsigned long)ip, frac + 1);
}

// Один отсчёт АЦП в милливольты. Калибровка по eFuse даёт реальную кривую
// преобразования; без неё остаётся номинальный размах из документации с
// ошибкой до 10% — для вопроса «усилитель сидит на середине питания?»
// этого хватает, для абсолютных измерений нет.
static int raw_to_mv(int raw) {
  if (raw < 0) raw = 0;
  if (raw > (int)UTRO_ADC_MAX) raw = (int)UTRO_ADC_MAX;
#if UTRO_HAVE_CALI
  if (g_cali != NULL) {
    int mv = 0;
    if (adc_cali_raw_to_voltage(g_cali, raw, &mv) == ESP_OK) return mv;
  }
#endif
  return (int)(((long)raw * UTRO_FULL_SCALE_MV) / (long)UTRO_ADC_MAX);
}

// Коэффициент передачи прямоугольного усреднения по N отсчётам на частоте f.
// Нужен, чтобы оценка наводки 50 Гц, снятая с уже усреднённого потока, не
// занижалась: |H(f)| = |sin(pi*f*N/fs_raw)| / (N*|sin(pi*f/fs_raw)|).
// На 50 Гц при N=32 и fs_raw=6400 это 0.900, то есть -0.9 дБ.
static double boxcar_gain(double f) {
  double a = kPi * f * (double)UTRO_OVERSAMPLE / (double)UTRO_RAW_RATE_HZ;
  double b = kPi * f / (double)UTRO_RAW_RATE_HZ;
  double den = (double)UTRO_OVERSAMPLE * sin(b);
  if (den == 0.0) return 1.0;
  double g = sin(a) / den;
  if (g < 0.0) g = -g;
  if (g < 1.0e-6) return 1.0e-6;
  return g;
}

static void push_header(void) {
  char buf[224];
  snprintf(buf, sizeof buf,
           "# utro-stage1 fw=%s proto=%d fs=%lu oversample=%lu raw_fs=%lu "
           "bits=12 scale=%lu vmin=0 vmax=%lu gpio=%d adc=1 ch=%d atten_db=12 "
           "fmt=index,sum baud=%lu\n",
           UTRO_FW_VERSION, UTRO_PROTO,
           (unsigned long)UTRO_OUT_RATE_HZ,
           (unsigned long)UTRO_OVERSAMPLE,
           (unsigned long)UTRO_RAW_RATE_HZ,
           (unsigned long)UTRO_OVERSAMPLE,
           (unsigned long)(UTRO_OVERSAMPLE * UTRO_ADC_MAX),
           (int)UTRO_ADC_GPIO, (int)UTRO_ADC_CHANNEL,
           (unsigned long)UTRO_SERIAL_BAUD);
  push_line(buf);
  push_line("# значение = сумма 32 отсчётов АЦП; для вольт делить на 32; dsp.py масштаб не важен\n");
  push_line("# индекс = время/5мс от начала потока; разрыв индексов = столько отсчётов потеряно\n");
  // Повторяем на самом устройстве: тот, кто пишет разбор, читает вывод, а не этот файл.
  push_line("# ВАЖНО: перед analyze_window вычтите из окна его первый отсчёт, иначе ступенька смещения даст motion=True и пульс не выдастся\n");
#if UTRO_HAVE_CALI
  push_line(g_cali != NULL
            ? "# cali=efuse\n"
            : "# cali=nominal (калибровки в eFuse нет, милливольты с ошибкой до 10%)\n");
#else
  push_line("# cali=nominal (схема калибровки недоступна в этой сборке IDF)\n");
#endif
  if (!g_adc_ok) push_line("# ОШИБКА: драйвер АЦП не поднялся, поток невозможен\n");
}

static void push_help(void) {
  push_line("# cmd: s=старт потока, x=стоп, c[N]=калибровка N секунд (1..60, по умолч. 10), v=заголовок, z=сброс счётчиков, ?=справка\n");
}

static void push_stat(void) {
  char buf[192];
  snprintf(buf, sizeof buf,
           "# stat n=%lu t_ms=%lu lost=%lu lost_pool=%lu lost_tx=%lu "
           "lost_bad=%lu ovf=%lu align=%lu txfree=%lu\n",
           (unsigned long)g_n_out,
           (unsigned long)(millis() - g_stream_begin_ms),
           (unsigned long)(g_lost_pool + g_lost_tx + g_lost_bad),
           (unsigned long)g_lost_pool, (unsigned long)g_lost_tx,
           (unsigned long)g_lost_bad, (unsigned long)g_ovf_events,
           (unsigned long)g_align_err, (unsigned long)tx_free());
  // Если строка не поместилась — не беда: счётчики накопительные, следующая
  // через пять секунд скажет то же самое.
  tx_push(buf, strlen(buf));
}

// --------------------------------------------------------------------------
// АЦП
// --------------------------------------------------------------------------
// Почему adc_continuous (DMA), а не таймер с прерыванием:
//  - Моменты выборки задаёт делитель самого АЦП, программа в этом не
//    участвует вообще. Ни загрузка процессора, ни USB-стек, ни запись в
//    порт не могут сдвинуть ни один отсчёт. Прерывание по таймеру, даже с
//    IRAM_ATTR, всё равно конкурирует с прерываниями USB и Wi-Fi, и
//    дрожание в десятки микросекунд на 5-миллисекундном шаге пришлось бы
//    либо мерить, либо принять на веру.
//  - analogRead внутри прерывания недопустим: он ждёт готовности АЦП в
//    цикле и берёт блокировки.
//  - DMA даёт передискретизацию бесплатно: 6400 Гц в пул, усреднение по 32
//    в loop(), на выходе ровно 200 Гц.
// Прерывание здесь всё-таки есть — обработчик переполнения пула ниже. Он
// помечен IRAM_ATTR и делает ровно два присваивания: иначе при включённой
// настройке ADC_CONTINUOUS_ISR_IRAM_SAFE он бы падал на обращении к флешу.

static adc_digi_pattern_config_t g_pattern;  // статический: драйвер копирует, но пусть живёт

static bool IRAM_ATTR on_pool_overflow(adc_continuous_handle_t handle,
                                       const adc_continuous_evt_data_t *edata,
                                       void *user_data) {
  (void)handle; (void)edata; (void)user_data;
  g_ovf_events++;
  g_resync = true;
  return false;   // будить задачу не нужно: loop() и так опрашивает пул
}

static bool adc_setup(void) {
  adc_continuous_handle_cfg_t hcfg = {};
  hcfg.max_store_buf_size = UTRO_POOL_BYTES;
  hcfg.conv_frame_size    = UTRO_FRAME_BYTES;
  if (adc_continuous_new_handle(&hcfg, &g_adc) != ESP_OK) { g_adc = NULL; return false; }

  g_pattern = adc_digi_pattern_config_t();
  g_pattern.atten     = (uint8_t)UTRO_ADC_ATTEN;
  g_pattern.channel   = (uint8_t)UTRO_ADC_CHANNEL;
  g_pattern.unit      = (uint8_t)ADC_UNIT_1;
  g_pattern.bit_width = (uint8_t)UTRO_ADC_BITS;

  adc_continuous_config_t ccfg = {};
  ccfg.pattern_num    = 1;
  ccfg.adc_pattern    = &g_pattern;
  ccfg.sample_freq_hz = UTRO_RAW_RATE_HZ;
  ccfg.conv_mode      = ADC_CONV_SINGLE_UNIT_1;
  ccfg.format         = ADC_DIGI_OUTPUT_FORMAT_TYPE2;
  if (adc_continuous_config(g_adc, &ccfg) != ESP_OK) return false;

  adc_continuous_evt_cbs_t cbs = {};
  cbs.on_conv_done = NULL;    // не нужен: пул опрашивается из loop()
  cbs.on_pool_ovf  = on_pool_overflow;
  if (adc_continuous_register_event_callbacks(g_adc, &cbs, NULL) != ESP_OK) return false;

  return true;
}

static bool adc_start(void) {
  if (!g_adc_ok) return false;
  if (g_adc_running) return true;
  if (adc_continuous_start(g_adc) != ESP_OK) return false;
  g_adc_running = true;
  g_resync = false;
  return true;
}

static void adc_stop(void) {
  if (!g_adc_ok || !g_adc_running) return;
  drain_pool();            // вычерпываем, пока драйвер ещё работает
  adc_continuous_stop(g_adc);
  g_adc_running = false;
}

// Выбросить всё, что лежит в пуле. Вызывается перед привязкой оси времени
// и при переполнении.
static void drain_pool(void) {
  if (!g_adc_running) return;
  static uint8_t scratch[UTRO_READ_BYTES] __attribute__((aligned(4)));
  const uint32_t guard_max = (UTRO_POOL_BYTES / UTRO_READ_BYTES) + 4u;
  for (uint32_t guard = 0; guard < guard_max; guard++) {
    uint32_t got = 0;
    if (adc_continuous_read(g_adc, scratch, UTRO_READ_BYTES, &got, 0) != ESP_OK) break;
    if (got == 0) break;
  }
}

static uint32_t index_from_clock(void) {
  int64_t dt = esp_timer_get_time() - g_t0_us;
  if (dt < 0) dt = 0;
  return (uint32_t)((dt * (int64_t)UTRO_OUT_RATE_HZ) / 1000000);
}

// Переполнение пула означает, что loop() не успевал больше секунды.
// Поведение драйвера при переполнении зависит от версии IDF: одни версии
// сохраняют старые данные и выбрасывают новые, другие затирают старые.
// Поэтому обработчик не полагается на это вовсе: он выбрасывает пул
// целиком и заново берёт индекс из системного таймера. Цена — до одной
// секунды выброшенного сигнала даже там, где часть его была цела. Выгода —
// ось времени остаётся правдой при любом поведении драйвера, и разрыв
// индексов, который увидит хост, равен реальному разрыву во времени.
// Точность восстановления индекса примерно +-2 отсчёта на событие: столько
// занимает конвейер между выборкой и чтением из пула.
static void handle_overflow(void) {
  g_resync = false;
  drain_pool();
  g_acc_sum = 0;
  g_acc_cnt = 0;
  g_acc_bad = false;
  if (!g_anchored) return;          // ось ещё не начиналась, терять нечего
  uint32_t n_now = index_from_clock();
  if (n_now > g_n_out) {
    g_lost_pool += (n_now - g_n_out);
    g_n_out = n_now;
  }
}

// Вычерпать пул, усреднить, отдать. Возвращает true, если была работа.
static bool pump_adc(void) {
  if (!g_adc_running || g_mode == MODE_IDLE) return false;

  // Пока буфер передачи не разгрузился, пул не трогаем: пусть данные
  // лежат в нём. Два буфера так работают как один длинный, и потеря
  // остаётся возможной только в одном месте — в пуле, где она считается.
  if (g_mode == MODE_STREAM && tx_free() < UTRO_TX_LOW_WATER) return false;

  if (g_resync) handle_overflow();

  uint32_t now_ms = millis();

  if (!g_anchored) {
    if ((int32_t)(now_ms - g_settle_until_ms) < 0) {
      // Установление тракта: читаем и выбрасываем, иначе пул переполнится.
      static uint8_t waste[UTRO_READ_BYTES] __attribute__((aligned(4)));
      uint32_t got = 0;
      if (adc_continuous_read(g_adc, waste, UTRO_READ_BYTES, &got, 0) != ESP_OK) return false;
      return got != 0;
    }
    // Установление закончилось. Чистим пул, чтобы фаза усреднения
    // началась с границы кадра, и только теперь привязываем ось времени.
    drain_pool();
    g_acc_sum = 0;
    g_acc_cnt = 0;
    g_acc_bad = false;
    g_t0_us = esp_timer_get_time();
    g_n_out = 0;
    g_anchored = true;
    if (g_mode == MODE_STREAM) {
      char buf[96];
      snprintf(buf, sizeof buf, "# begin t_boot_ms=%lu settle_ms=%lu\n",
               (unsigned long)now_ms, (unsigned long)UTRO_SETTLE_MS);
      push_line(buf);
      g_next_stat_ms = now_ms + UTRO_STAT_MS;
      g_stream_begin_ms = now_ms;
    }
    return true;
  }

  static uint8_t buf[UTRO_READ_BYTES] __attribute__((aligned(4)));
  uint32_t got = 0;
  if (adc_continuous_read(g_adc, buf, UTRO_READ_BYTES, &got, 0) != ESP_OK) return false;
  if (got == 0) return false;

  // Кольцевой буфер драйвера байтовый, но все записи в него кратны четырём
  // и его размер кратен четырём, поэтому остатка быть не может. Если он
  // всё же появится, фаза усреднения съедет на всю оставшуюся запись —
  // поэтому не замалчиваем, а считаем и пересинхронизируемся.
  if ((got & 3u) != 0) {
    g_align_err++;
    g_resync = true;
    got &= ~3u;
  }

  for (uint32_t i = 0; i + 4u <= got; i += 4u) {
    adc_digi_output_data_t *p = (adc_digi_output_data_t *)&buf[i];
    if ((adc_channel_t)UTRO_CONV_CHANNEL(p) != UTRO_ADC_CHANNEL) {
      g_acc_bad = true;          // чужой канал: весь кадр недостоверен
    } else {
      g_acc_sum += (uint32_t)UTRO_CONV_DATA(p);
    }
    if (++g_acc_cnt < (uint16_t)UTRO_OVERSAMPLE) continue;
    uint32_t v = g_acc_sum;
    bool bad = g_acc_bad;
    g_acc_sum = 0;
    g_acc_cnt = 0;
    g_acc_bad = false;
    consume_sample(v, bad);
  }
  return true;
}

static void consume_sample(uint32_t v, bool bad) {
  if (bad) {
    // Подставлять сюда предыдущее значение значило бы придумать отсчёт.
    // Лучше разрыв индекса: хост его увидит.
    g_lost_bad++;
    g_n_out++;
    return;
  }
  if (g_mode == MODE_STREAM) {
    char line[24];
    int len = snprintf(line, sizeof line, "%lu,%lu\n",
                       (unsigned long)g_n_out, (unsigned long)v);
    if (len > 0 && !tx_push(line, (size_t)len)) {
      // Не должно случаться: выше стоит порог UTRO_TX_LOW_WATER, которого
      // хватает на целое чтение. Если счётчик не ноль — сломана эта
      // арифметика, а не порт.
      g_lost_tx++;
    }
    g_n_out++;
  } else if (g_mode == MODE_CAL) {
    cal_feed(v);
    g_n_out++;
  }
}

// --------------------------------------------------------------------------
// КАЛИБРОВКА
// --------------------------------------------------------------------------
// Смысл команды: до укладки плёнки под матрас ответить на вопрос «тракт
// жив?». Мёртвый тракт выглядит правдоподобно — ровная линия на середине
// диапазона, — и обнаружить его потом, по десяти минутам бесполезной
// записи, дороже.
//
// Что считается:
//  - среднее и СКО по Уэлфорду. Не через сумму квадратов: при смещении
//    около 2000 и 12000 отсчётах сумма квадратов теряет значащие разряды
//    на вычитании, и СКО выходит заниженным.
//  - минимум, максимум, размах.
//  - дрейф: среднее второй половины окна минус среднее первой. Прямо
//    показывает, установился ли зарядовый усилитель.
//  - амплитуда наводки 50 Гц. На частоте 200 Гц сеть попадает ровно в
//    fs/4, поэтому синус и косинус принимают значения 1, 0, -1, 0 — и
//    квадратуры считаются двумя сложениями на отсчёт, без умножений и без
//    таблиц. Знакопеременные суммы заодно сами вычитают постоянную
//    составляющую, если число отсчётов кратно четырём.

static void cal_begin(uint32_t seconds) {
  if (seconds < 1) seconds = 1;
  if (seconds > UTRO_CAL_MAX_S) seconds = UTRO_CAL_MAX_S;
  g_cal_target = seconds * UTRO_OUT_RATE_HZ;
  g_cal_target &= ~3u;                 // кратно четырём: см. про квадратуры
  g_cal_n = 0;
  g_cal_mean = 0.0;
  g_cal_m2 = 0.0;
  g_cal_min = 0xFFFFFFFFu;
  g_cal_max = 0;
  g_cal_i = 0;
  g_cal_q = 0;
  g_cal_first = 0.0;
  g_cal_second = 0.0;
  g_cal_nf = 0;
  g_cal_ns = 0;
  char buf[96];
  snprintf(buf, sizeof buf, "# cal start sec=%lu n=%lu settle_ms=%lu\n",
           (unsigned long)seconds, (unsigned long)g_cal_target,
           (unsigned long)UTRO_SETTLE_MS);
  push_line(buf);
}

static void cal_feed(uint32_t v) {
  g_cal_n++;
  double x = (double)v;
  double d = x - g_cal_mean;
  g_cal_mean += d / (double)g_cal_n;
  g_cal_m2 += d * (x - g_cal_mean);
  if (v < g_cal_min) g_cal_min = v;
  if (v > g_cal_max) g_cal_max = v;

  switch ((g_cal_n - 1u) & 3u) {        // фаза на fs/4
    case 0: g_cal_i += (int64_t)v; break;
    case 1: g_cal_q += (int64_t)v; break;
    case 2: g_cal_i -= (int64_t)v; break;
    default: g_cal_q -= (int64_t)v; break;
  }

  if (g_cal_n <= g_cal_target / 2u) { g_cal_first += x;  g_cal_nf++; }
  else                              { g_cal_second += x; g_cal_ns++; }

  if (g_cal_n >= g_cal_target) cal_report();
}

static void cal_report(void) {
  const double os = (double)UTRO_OVERSAMPLE;
  // Всё переводим в единицы ОДНОГО отсчёта АЦП, чтобы числа можно было
  // сравнивать с документацией на чип.
  double mean = g_cal_mean / os;
  double var  = (g_cal_n > 1) ? (g_cal_m2 / (double)(g_cal_n - 1)) : 0.0;
  double sd   = (var > 0.0) ? sqrt(var) / os : 0.0;
  double vmin = (double)g_cal_min / os;
  double vmax = (double)g_cal_max / os;
  double pp   = vmax - vmin;
  double drift = 0.0;
  if (g_cal_nf > 0 && g_cal_ns > 0) {
    drift = (g_cal_second / (double)g_cal_ns - g_cal_first / (double)g_cal_nf) / os;
  }
  // Амплитуда синусоиды из квадратур: A = 2*sqrt(I^2+Q^2)/N.
  double ii = (double)g_cal_i;
  double qq = (double)g_cal_q;
  double mains = 2.0 * sqrt(ii * ii + qq * qq) / (double)g_cal_n / os;
  mains /= boxcar_gain(50.0);          // компенсация усреднения

  char a[24], b[24], c[24], d[24], e[24], f[24];
  char buf[256];

  snprintf(buf, sizeof buf, "# cal n=%lu fs=%lu\n",
           (unsigned long)g_cal_n, (unsigned long)UTRO_OUT_RATE_HZ);
  push_line(buf);

  fmt_fixed(a, sizeof a, mean, 3);
  fmt_fixed(b, sizeof b, sd, 3);
  fmt_fixed(c, sizeof c, vmin, 3);
  fmt_fixed(d, sizeof d, vmax, 3);
  fmt_fixed(e, sizeof e, pp, 3);
  snprintf(buf, sizeof buf, "# cal lsb mean=%s sd=%s min=%s max=%s pp=%s\n", a, b, c, d, e);
  push_line(buf);

  int raw_mean = (int)(mean + 0.5);
  int mv_mean = raw_to_mv(raw_mean);
  // Локальный наклон кривой преобразования: разность на +-100 LSB. Считать
  // СКО в милливольтах по номинальному размаху значило бы врать там, где
  // калибровка eFuse доступна. Опорную точку отодвигаем от краёв диапазона,
  // иначе обе точки упрутся в один предел и наклон выйдет вдвое меньше.
  int base = raw_mean;
  if (base < 100) base = 100;
  if (base > (int)UTRO_ADC_MAX - 100) base = (int)UTRO_ADC_MAX - 100;
  double slope = (double)(raw_to_mv(base + 100) - raw_to_mv(base - 100)) / 200.0;
  fmt_fixed(a, sizeof a, sd * slope, 3);
  fmt_fixed(b, sizeof b, pp * slope, 2);
  fmt_fixed(c, sizeof c, drift, 3);
  fmt_fixed(d, sizeof d, mains, 3);
  fmt_fixed(e, sizeof e, mains * slope, 3);
  fmt_fixed(f, sizeof f, slope * 1000.0, 2);
  snprintf(buf, sizeof buf,
           "# cal mv mean=%d sd=%s pp=%s uv_per_lsb=%s\n", mv_mean, a, b, f);
  push_line(buf);
  snprintf(buf, sizeof buf, "# cal drift_lsb=%s mains50_lsb=%s mains50_mv=%s\n", c, d, e);
  push_line(buf);

  // Пороги ниже — рассуждение, НЕ измерение. Ни одно из этих чисел не
  // проверено на реальном тракте; мерить их надо на собранном усилителе,
  // сравнивая вывод с осциллографом.
  bool quiet = true;
  if (mean < 0.03 * (double)UTRO_ADC_MAX || mean > 0.97 * (double)UTRO_ADC_MAX) {
    push_line("# cal ВНИМАНИЕ: смещение упёрто в шину питания. Выход усилителя должен сидеть примерно на середине диапазона (~2048), иначе сигнал обрежется с одной стороны.\n");
    quiet = false;
  }
  if (sd < 0.5) {
    push_line("# cal ВНИМАНИЕ: шума нет совсем. У живого АЦП с подключённым высокоимпедансным входом СКО не бывает нулевым: похоже, вход ни к чему не подключён или усилитель не питается.\n");
    quiet = false;
  }
  if (mains > 0.025 * (double)UTRO_ADC_MAX) {
    push_line("# cal ВНИМАНИЕ: наводка 50 Гц больше 2.5% диапазона. Проверьте экран кабеля (оплётка на землю усилителя, с ОДНОЙ стороны), длину проводов до плёнки и питание от аккумулятора вместо сетевого адаптера.\n");
    quiet = false;
  }
  if (pp > 0.80 * (double)UTRO_ADC_MAX) {
    push_line("# cal ВНИМАНИЕ: размах больше 80% диапазона. Если это запись с человеком на матрасе, дыхание насыщает тракт и сердечная составляющая, которая на порядок слабее, потеряется. Уменьшите аналоговое усиление.\n");
    quiet = false;
  }
  if (quiet) {
    push_line("# cal тракт похож на живой. Это НЕ доказательство, что сигнал плёнки проходит: доказательство даст только analyze_window на записи с человеком.\n");
  }
  push_line("# cal end\n");
  session_stop(true);
}

// --------------------------------------------------------------------------
// СЕАНС
// --------------------------------------------------------------------------

static void session_start(uint8_t mode) {
  if (!g_adc_ok) {
    push_line("# err драйвер АЦП не поднялся\n");
    return;
  }
  if (g_mode != MODE_IDLE) session_stop(true);
  g_mode = mode;
  g_anchored = false;
  g_n_out = 0;
  g_t0_us = 0;
  g_acc_sum = 0;
  g_acc_cnt = 0;
  g_acc_bad = false;
  g_settle_until_ms = millis() + UTRO_SETTLE_MS;
  g_stream_begin_ms = millis();
  g_next_stat_ms = g_settle_until_ms + UTRO_STAT_MS;
  if (!adc_start()) {
    g_mode = MODE_IDLE;
    push_line("# err не удалось запустить АЦП\n");
  }
}

static void session_stop(bool quiet) {
  if (g_mode == MODE_STREAM) {
    char buf[160];
    snprintf(buf, sizeof buf,
             "# end n=%lu lost=%lu lost_pool=%lu lost_tx=%lu lost_bad=%lu ovf=%lu\n",
             (unsigned long)g_n_out,
             (unsigned long)(g_lost_pool + g_lost_tx + g_lost_bad),
             (unsigned long)g_lost_pool, (unsigned long)g_lost_tx,
             (unsigned long)g_lost_bad, (unsigned long)g_ovf_events);
    push_line(buf);
  } else if (g_mode == MODE_IDLE && !quiet) {
    push_line("# err поток не запущен\n");
  }
  adc_stop();
  g_mode = MODE_IDLE;
  g_anchored = false;
  g_acc_sum = 0;
  g_acc_cnt = 0;
  g_acc_bad = false;
}

// --------------------------------------------------------------------------
// КОМАНДЫ
// --------------------------------------------------------------------------

static void exec_command(const char *line) {
  // Пропускаем ведущие пробелы.
  while (*line == ' ' || *line == '\t') line++;
  char op = *line;
  if (op == 0) return;
  const char *arg = line + 1;

  switch (op) {
    case 's':
      session_start(MODE_STREAM);
      if (g_mode == MODE_STREAM) push_header();
      break;

    case 'x':
      session_stop(false);
      break;

    case 'c': {
      uint32_t sec = 0;
      bool have = false;
      while (*arg == ' ' || *arg == '\t' || *arg == '=') arg++;
      while (*arg >= '0' && *arg <= '9') {
        sec = sec * 10u + (uint32_t)(*arg - '0');
        if (sec > 100000u) sec = 100000u;   // защита от длинного мусора
        arg++;
        have = true;
      }
      if (!have) sec = UTRO_CAL_DEF_S;
      session_start(MODE_CAL);
      if (g_mode == MODE_CAL) cal_begin(sec);
      break;
    }

    case 'v':
      push_header();
      break;

    case 'z':
      g_lost_pool = 0;
      g_lost_tx = 0;
      g_lost_bad = 0;
      g_align_err = 0;
      g_ovf_events = 0;
      push_line("# счётчики потерь сброшены\n");
      break;

    case '?':
    case 'h':
      push_header();
      push_help();
      break;

    default: {
      char buf[64];
      snprintf(buf, sizeof buf, "# err неизвестная команда '%c'\n", op);
      push_line(buf);
      break;
    }
  }
}

static void poll_commands(void) {
  while (Serial.available() > 0) {
    int ch = Serial.read();
    if (ch < 0) break;
    if (ch == '\n' || ch == '\r') {
      if (g_cmd_len > 0) {
        g_cmd[g_cmd_len] = 0;
        exec_command(g_cmd);
        g_cmd_len = 0;
      }
      continue;
    }
    if (g_cmd_len + 1 < sizeof(g_cmd)) {
      g_cmd[g_cmd_len++] = (char)ch;
    }
    // Переполнение строки команды игнорируем: лишние символы отбрасываются,
    // команда разберётся по первому символу.
  }
}

// --------------------------------------------------------------------------
// ИНДИКАЦИЯ
// --------------------------------------------------------------------------
// Один светодиод, четыре различимых состояния. Мигание, а не цвет: на
// DevKitC-1 встроенный светодиод адресный и цветной, на XIAO — обычный
// одноцветный, и рисунок мигания читается на обоих.
//   короткая вспышка раз в 2 с  — ждём команду
//   горит ровно                 — идёт запись, потерь нет
//   мигает 2 Гц                 — идёт запись, но отсчёты терялись
//   мигает 5 Гц                 — калибровка
// Отдельный рисунок для потерь нужен потому, что человек, который укладывает
// плёнку, смотрит на устройство, а не в терминал: испорченную запись надо
// видеть сразу, а не через десять минут.

static void led_write(bool on) {
  if (on == g_led_on) return;
  g_led_on = on;
#if UTRO_LED_ACTIVE_LOW
  digitalWrite(UTRO_LED_PIN, on ? LOW : HIGH);
#else
  digitalWrite(UTRO_LED_PIN, on ? HIGH : LOW);
#endif
}

static void led_task(uint32_t now_ms) {
  if ((int32_t)(now_ms - g_led_next_ms) < 0) return;
  bool losses = (g_lost_pool + g_lost_tx + g_lost_bad) > 0;

  if (g_mode == MODE_CAL) {
    led_write(!g_led_on);
    g_led_next_ms = now_ms + 100;             // 5 Гц
    return;
  }
  if (g_mode == MODE_STREAM) {
    if (!losses) {
      led_write(true);
      g_led_next_ms = now_ms + 200;
    } else {
      led_write(!g_led_on);
      g_led_next_ms = now_ms + 250;           // 2 Гц
    }
    return;
  }
  // Ожидание команды: короткая вспышка, чтобы было видно, что плата жива.
  if (g_led_on) {
    led_write(false);
    g_led_next_ms = now_ms + 1960;
  } else {
    led_write(true);
    g_led_next_ms = now_ms + 40;
  }
}

// --------------------------------------------------------------------------
// ТОЧКИ ВХОДА
// --------------------------------------------------------------------------

void setup() {
  pinMode(UTRO_LED_PIN, OUTPUT);
  g_led_on = true;          // чтобы led_write гарантированно записал LOW
  led_write(false);

  Serial.begin(UTRO_SERIAL_BAUD);
  // Намеренно не ждём подключения хоста: прошивка должна подниматься и без
  // него. Поэтому стартовый заголовок может потеряться — он повторяется на
  // каждую команду 's' и по команде 'v', и хост обязан опираться на это, а
  // не на баннер при включении.

  g_adc_ok = adc_setup();

#if UTRO_HAVE_CALI
  {
    adc_cali_curve_fitting_config_t cc = {};
    cc.unit_id  = ADC_UNIT_1;
    cc.atten    = UTRO_ADC_ATTEN;
    cc.bitwidth = UTRO_ADC_BITS;
    // Поле chan в этой структуре появилось не во всех версиях IDF и на S3
    // на результат не влияет: калибровочные коэффициенты в eFuse хранятся
    // по ослаблению, а не по каналу. Оставляем нулевым.
    if (adc_cali_create_scheme_curve_fitting(&cc, &g_cali) != ESP_OK) {
      g_cali = NULL;
    }
  }
#endif

  push_header();
  push_help();
}

void loop() {
  uint32_t now_ms = millis();

  // Порядок важен: сначала освобождаем место в буфере передачи, потом
  // вычерпываем пул. Наоборот — и порог UTRO_TX_LOW_WATER будет срабатывать
  // на полном буфере, которого уже нет.
  tx_flush();

  bool worked = pump_adc();

  if (g_mode == MODE_STREAM && g_anchored && (int32_t)(now_ms - g_next_stat_ms) >= 0) {
    push_stat();
    g_next_stat_ms = now_ms + UTRO_STAT_MS;
  }

  poll_commands();
  led_task(now_ms);

  // Если работы не было — отдаём такт системе. Без этого задача loop()
  // крутится вплотную и сторожевой таймер простаивающей задачи может
  // сработать. Миллисекунда безопасна: кадр приходит раз в 5 мс, а пул
  // держит секунду.
  if (!worked) delay(1);
}
