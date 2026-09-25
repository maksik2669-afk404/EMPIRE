/**
 * WINTER ARC — трекер привычек в Google Таблицах + страница входа по паролю.
 *
 * Установка (5 минут, один раз):
 *  1. script.google.com → «Новый проект». Вставьте этот код в Code.gs.
 *     Создайте HTML-файл «Gate» (Файлы → + → HTML) и вставьте в него Gate.html.
 *  2. Поменяйте пароль в CONFIG.PASSWORDS ниже.
 *  3. Выберите функцию setup → «Выполнить» → разрешите доступ.
 *     На вашем Диске появится таблица-шаблон; ссылки будут в «Журнале выполнения».
 *  4. «Начать развёртывание» → «Новое развёртывание» → тип «Веб-приложение»,
 *     «Запуск от имени»: Я, «У кого есть доступ»: Все → «Начать развёртывание».
 *     Полученная ссылка /exec — это ваш мини-сервис: её вы и даёте покупателям вместе с паролем.
 *
 * Шаблон не содержит кода: покупатель копирует чистую таблицу, пароль и этот скрипт остаются у вас.
 */

const CONFIG = {
  PASSWORDS: ['WINTER2026'],   // регистр не важен; можно несколько (разные коды для разных каналов продаж)
  YEAR: 2026,
  START_MONTH: 10,             // старт арки — 1 октября
  START_DAY: 1,
  DAYS: 92,                    // до 31 декабря включительно
  THRESHOLD: 0.8,              // день засчитан, если выполнено ≥ 80% привычек
};

// Холодная палитра: ночь, лёд, иней.
const C = {
  bg: '#0A1020', panel: '#111A2E', panel2: '#15213A', band: '#0D1528',
  text: '#E6F0FF', muted: '#7F95BA', dim: '#4A5B7C',
};

const PROFILES = [
  {
    sheet: '❄ HIM', title: 'WINTER ARC · HIM', accent: '#7DD3FC', strong: '#38BDF8', checked: '#0C3553', today: '#123E63',
    habits: ['🌅 Подъём до 6:30', '🏋️ Тренировка', '🚿 Холодный душ', '📖 Чтение 20 мин',
             '💧 2 л воды', '🥩 Белок и чистое питание', '📵 Без соцсетей до 12:00', '🎯 1 час на цель'],
  },
  {
    sheet: '❄ HER', title: 'WINTER ARC · HER', accent: '#C7D2FE', strong: '#A5B4FC', checked: '#232A57', today: '#2C3470',
    habits: ['🌅 Подъём до 7:00', '🧘 Тренировка / пилатес', '🧴 Уход утром и вечером', '📖 Чтение 20 мин',
             '💧 2 л воды', '🥗 Чистое питание', '📓 3 благодарности', '🚶 10 000 шагов'],
  },
];

// Раскладка листа-трекера
const HEAD_ROW = 8;          // заголовки таблицы (сюда пользователь вписывает свои привычки)
const FIRST = 9;             // первая строка с днём
const N_HABITS = 8;          // колонки C..J
const COLS = 17;             // A..Q, Q — скрытая служебная колонка серии

// ------------------------------------------------------------------ установка

function setup() {
  const ss = SpreadsheetApp.create('WINTER ARC ' + CONFIG.YEAR + ' — трекер привычек');
  ss.setSpreadsheetLocale('ru_RU');
  ss.setSpreadsheetTimeZone('Europe/Moscow');

  const start = ss.getSheets()[0];
  buildStart_(start);
  PROFILES.forEach(function (p) { buildTracker_(ss, p); });
  ss.setActiveSheet(start);
  SpreadsheetApp.flush();

  // «Все, у кого есть ссылка — читатель»: иначе кнопка «Создать копию» не сработает у покупателя.
  DriveApp.getFileById(ss.getId()).setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
  PropertiesService.getScriptProperties().setProperty('TEMPLATE_ID', ss.getId());

  Logger.log('Шаблон (редактировать можно только вам): ' + ss.getUrl());
  Logger.log('Прямая ссылка «Создать копию»: ' + copyUrl_(ss.getId()));
  Logger.log('Дальше: «Начать развёртывание» → веб-приложение → доступ «Все».');
}

// ------------------------------------------------------------------ страница входа (веб-приложение)

function doGet() {
  const t = HtmlService.createTemplateFromFile('Gate');
  t.year = CONFIG.YEAR;
  t.days = CONFIG.DAYS;
  t.range = fmt_(arcStart_()) + ' — ' + fmt_(arcEnd_());
  return t.evaluate()
    .setTitle('WINTER ARC ' + CONFIG.YEAR + ' ❄')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

/** Вызывается со страницы: проверяет пароль и отдаёт ссылку на копию. */
function unlock(password) {
  const pw = String(password || '').trim().toUpperCase();
  const ok = pw && CONFIG.PASSWORDS.some(function (p) { return String(p).trim().toUpperCase() === pw; });
  if (!ok) {
    Utilities.sleep(800);  // замедляет перебор паролей
    return { ok: false, error: 'Неверный пароль' };
  }
  const id = PropertiesService.getScriptProperties().getProperty('TEMPLATE_ID');
  if (!id) return { ok: false, error: 'Шаблон ещё не создан: владелец должен запустить setup()' };
  countUnlock_();
  return { ok: true, url: copyUrl_(id) };
}

/** Сколько раз открывали доступ — запустите вручную, результат в журнале. */
function stats() {
  Logger.log('Успешных входов: ' + (PropertiesService.getScriptProperties().getProperty('UNLOCKS') || 0));
}

function countUnlock_() {
  const lock = LockService.getScriptLock();
  try {
    lock.waitLock(3000);
    const props = PropertiesService.getScriptProperties();
    props.setProperty('UNLOCKS', String(Number(props.getProperty('UNLOCKS') || 0) + 1));
  } catch (e) {
    // счётчик не критичен — вход не должен ломаться из-за него
  } finally {
    lock.releaseLock();
  }
}

function copyUrl_(id) {
  return 'https://docs.google.com/spreadsheets/d/' + id + '/copy';
}

// ------------------------------------------------------------------ лист «СТАРТ»

function buildStart_(sh) {
  sh.setName('❄ СТАРТ');
  fitGrid_(sh, 30, 8);
  sh.setHiddenGridlines(true).setTabColor('#E0F2FE');
  sh.getRange(1, 1, 30, 8).setBackground(C.bg).setFontColor(C.text).setFontFamily('Montserrat')
    .setFontSize(11).setVerticalAlignment('middle');
  sh.setColumnWidth(1, 28);
  sh.setColumnWidths(2, 6, 130);
  sh.setColumnWidth(8, 28);
  sh.setRowHeights(1, 30, 26);

  const T = CONFIG.THRESHOLD * 100;
  const lines = [
    [2, '❄  WINTER ARC ' + CONFIG.YEAR, 'title'],
    [3, CONFIG.DAYS + ' дней, чтобы к Новому году стать версией себя, которой будешь гордиться.', 'accent'],
    [5, 'КАК ПОЛЬЗОВАТЬСЯ', 'label'],
    [6, '1.  Открой свой лист — ❄ HIM или ❄ HER (вкладки внизу).', ''],
    [7, '2.  Впиши свои привычки в заголовки таблицы (строка 8) — всё пересчитается само.', ''],
    [8, '3.  Каждый вечер отмечай галочки. Сегодняшний день подсвечен.', ''],
    [9, '4.  День засчитан, если выполнено ≥ ' + T + '% привычек. Серия — дни подряд без провала.', ''],
    [10, '5.  Сон, вес, настроение и заметка — по желанию. Через ' + CONFIG.DAYS + ' дней это твой дневник перемен.', ''],
    [12, 'ПРАВИЛА АРКИ', 'label'],
    [13, '—  Никаких нулевых дней: в плохой день сделай хотя бы минимум.', ''],
    [14, '—  Не обсуждай — показывай. Результат скажет за тебя.', ''],
    [15, '—  Сорвался — не жди понедельника. Начни со следующей галочки.', ''],
    [16, '—  Меньше экрана, больше жизни. Зима — время строить.', ''],
    [18, 'МОИ 3 ЦЕЛИ К ' + fmt_(arcEnd_()), 'label'],
    [23, 'СТАРТ ' + fmt_(arcStart_()) + '.' + CONFIG.YEAR + '   ·   ФИНИШ ' + fmt_(arcEnd_()) + '.' + CONFIG.YEAR, 'muted'],
  ];
  lines.forEach(function (l) {
    const r = sh.getRange(l[0], 2, 1, 6).merge().setValue(l[1]).setWrap(true);
    if (l[2] === 'title') { r.setFontFamily('Oswald').setFontSize(30).setFontWeight('bold'); sh.setRowHeight(l[0], 60); }
    if (l[2] === 'accent') r.setFontColor('#7DD3FC');
    if (l[2] === 'label') r.setFontColor(C.muted).setFontSize(9).setFontWeight('bold');
    if (l[2] === 'muted') r.setFontColor(C.dim).setFontSize(9);
  });
  // три поля для целей
  for (let i = 0; i < 3; i++) {
    const row = 19 + i;
    sh.getRange(row, 2).setValue((i + 1) + '.').setFontColor('#7DD3FC').setHorizontalAlignment('right');
    sh.getRange(row, 3, 1, 5).merge().setBackground(C.panel2).setFontColor(C.text)
      .setBorder(true, true, true, true, null, null, C.bg, SpreadsheetApp.BorderStyle.SOLID_THICK);
    sh.setRowHeight(row, 32);
  }
}

// ------------------------------------------------------------------ листы-трекеры HIM / HER

function buildTracker_(ss, p) {
  const sh = ss.insertSheet(p.sheet, ss.getNumSheets());
  const last = FIRST + CONFIG.DAYS - 1;
  const rows = last + 1;
  fitGrid_(sh, rows, COLS);
  sh.setHiddenGridlines(true).setTabColor(p.strong);
  sh.getRange(1, 1, rows, COLS).setBackground(C.bg).setFontColor(C.text).setFontFamily('Montserrat')
    .setFontSize(10).setVerticalAlignment('middle');

  // размеры
  sh.setColumnWidth(1, 64);
  sh.setColumnWidth(2, 42);
  sh.setColumnWidths(3, N_HABITS, 88);
  sh.setColumnWidth(11, 58);
  sh.setColumnWidth(12, 108);
  sh.setColumnWidths(13, 3, 64);
  sh.setColumnWidth(16, 240);
  sh.setColumnWidth(17, 30);
  [[1, 56], [2, 26], [3, 22], [4, 44], [5, 34], [6, 10], [7, 26], [8, 58]].forEach(function (h) {
    sh.setRowHeight(h[0], h[1]);
  });
  sh.setRowHeights(FIRST, CONFIG.DAYS, 28);

  const start = 'DATE(' + CONFIG.YEAR + ',' + CONFIG.START_MONTH + ',' + CONFIG.START_DAY + ')';
  const end = '(' + start + '+' + (CONFIG.DAYS - 1) + ')';
  const col = function (letter) { return letter + FIRST + ':' + letter + last; };  // напр. K9:K100
  const T = CONFIG.THRESHOLD;

  // ---- шапка
  sh.getRange('A1:P1').merge().setValue('  ❄ ' + p.title + ' ' + CONFIG.YEAR)
    .setFontFamily('Oswald').setFontSize(26).setFontWeight('bold');
  sh.getRange('A2:P2').merge()
    .setValue('   ' + fmt_(arcStart_()) + ' → ' + fmt_(arcEnd_()) + '  ·  ' + CONFIG.DAYS + ' дней  ·  день засчитан при ≥ '
      + (T * 100) + '%  ·  не рви серию')
    .setFontColor(p.accent).setFontSize(10);

  const kpis = [
    ['A', 'C', 'ОБЩИЙ ПРОГРЕСС', '=IFERROR(AVERAGEIFS(' + col('K') + ',' + col('A') + ',"<="&TODAY()),0)', '0%'],
    ['D', 'F', 'ДНЕЙ ЗАСЧИТАНО', '=COUNTIF(' + col('K') + ',">="&' + T + ')', '0'],
    ['G', 'I', 'СЕРИЯ СЕЙЧАС', '=MAX(IFERROR(INDEX(' + col('Q') + ',MATCH(TODAY(),' + col('A') + ',0)),0),'
      + 'IFERROR(INDEX(' + col('Q') + ',MATCH(TODAY()-1,' + col('A') + ',0)),0))', '0'],
    ['J', 'L', 'ЛУЧШАЯ СЕРИЯ', '=MAX(' + col('Q') + ')', '0'],
    ['M', 'P', 'ДО ФИНИША', '=IF(TODAY()<' + start + ',"старт через "&(' + start + '-TODAY())&" дн.",'
      + 'IF(TODAY()>' + end + ',"арка пройдена ❄",(' + end + '-TODAY())&" дн."))', '@'],
  ];
  kpis.forEach(function (k) {
    sh.getRange(k[0] + '3:' + k[1] + '3').merge().setValue(k[2]).setBackground(C.panel).setFontColor(C.muted)
      .setFontSize(8).setFontWeight('bold').setHorizontalAlignment('center');
    sh.getRange(k[0] + '4:' + k[1] + '4').merge().setFormula(k[3]).setNumberFormat(k[4]).setBackground(C.panel)
      .setFontColor(p.accent).setFontFamily('Oswald').setFontSize(20).setFontWeight('bold').setHorizontalAlignment('center');
    // «зазоры» между карточками — толстая рамка цвета фона
    sh.getRange(k[0] + '3:' + k[1] + '4')
      .setBorder(true, true, true, true, null, null, C.bg, SpreadsheetApp.BorderStyle.SOLID_THICK);
  });
  sh.getRange('A5:P5').merge()
    .setFormula('=REPT("▰",ROUND(A4*40))&REPT("▱",40-ROUND(A4*40))&"   "&TEXT(A4,"0%")')
    .setFontColor(p.accent).setFontSize(13).setHorizontalAlignment('center');

  // ---- итог по каждой привычке (строка 7)
  sh.getRange('A7:B7').merge().setValue('ИТОГ').setFontColor(C.muted).setFontSize(8).setFontWeight('bold')
    .setHorizontalAlignment('center');
  const habitStats = [];
  for (let i = 0; i < N_HABITS; i++) {
    const L = letter_(3 + i);
    habitStats.push('=IFERROR(COUNTIF(' + col(L) + ',TRUE)/COUNTIF(' + col('A') + ',"<="&TODAY()),0)');
  }
  sh.getRange(7, 3, 1, N_HABITS).setFormulas([habitStats]);
  sh.getRange(7, 11).setFormula('=A4');
  sh.getRange(7, 3, 1, N_HABITS + 1).setNumberFormat('0%').setFontColor(p.accent).setFontWeight('bold')
    .setHorizontalAlignment('center').setBackground(C.panel);

  // ---- заголовки таблицы
  const head = ['ДАТА', 'ДЕНЬ'].concat(p.habits, ['%', 'ПРОГРЕСС', 'СОН, ч', 'ВЕС', 'НАСТР. 1–5', 'ЗАМЕТКА ДНЯ', '']);
  sh.getRange(HEAD_ROW, 1, 1, COLS).setValues([head]).setBackground(C.panel2).setFontSize(9).setFontWeight('bold')
    .setWrap(true).setHorizontalAlignment('center');
  sh.getRange(HEAD_ROW, 3, 1, N_HABITS).setFontColor(p.accent);
  sh.getRange(HEAD_ROW, 1, 1, 16)
    .setBorder(null, null, true, null, null, null, p.strong, SpreadsheetApp.BorderStyle.SOLID_MEDIUM);

  // ---- дни
  const ab = [], kl = [], q = [];
  for (let i = 0; i < CONFIG.DAYS; i++) {
    const r = FIRST + i;
    ab.push(['=' + start + '+' + i, '=CHOOSE(WEEKDAY(A' + r + ',2),"Пн","Вт","Ср","Чт","Пт","Сб","Вс")']);
    kl.push(['=COUNTIF(C' + r + ':J' + r + ',TRUE)/' + N_HABITS,
             '=REPT("▰",ROUND(K' + r + '*10))&REPT("▱",10-ROUND(K' + r + '*10))']);
    q.push([i === 0 ? '=IF(K' + r + '>=' + T + ',1,0)' : '=IF(K' + r + '>=' + T + ',Q' + (r - 1) + '+1,0)']);
  }
  sh.getRange(FIRST, 1, CONFIG.DAYS, 2).setFormulas(ab);
  sh.getRange(FIRST, 11, CONFIG.DAYS, 2).setFormulas(kl);
  sh.getRange(FIRST, 17, CONFIG.DAYS, 1).setFormulas(q);

  sh.getRange(FIRST, 1, CONFIG.DAYS, 1).setNumberFormat('dd.mm').setHorizontalAlignment('center').setFontWeight('bold');
  sh.getRange(FIRST, 2, CONFIG.DAYS, 1).setFontColor(C.muted).setHorizontalAlignment('center').setFontSize(9);
  sh.getRange(FIRST, 3, CONFIG.DAYS, N_HABITS).insertCheckboxes().setFontColor(p.accent).setHorizontalAlignment('center');
  sh.getRange(FIRST, 11, CONFIG.DAYS, 1).setNumberFormat('0%').setHorizontalAlignment('center').setFontWeight('bold');
  sh.getRange(FIRST, 12, CONFIG.DAYS, 1).setFontColor(p.accent).setHorizontalAlignment('center');
  sh.getRange(FIRST, 13, CONFIG.DAYS, 3).setHorizontalAlignment('center');
  sh.getRange(FIRST, 13, CONFIG.DAYS, 2).setNumberFormat('0.0');
  sh.getRange(FIRST, 16, CONFIG.DAYS, 1).setFontColor(C.muted).setWrap(false);

  // полосы через строку — легче вести глазами
  sh.getRange(FIRST, 1, CONFIG.DAYS, 16).applyRowBanding(SpreadsheetApp.BandingTheme.BLUE, false, false)
    .setFirstRowColor(C.bg).setSecondRowColor(C.band);

  // ограничения ввода
  const num = function (min, max, help) {
    return SpreadsheetApp.newDataValidation().requireNumberBetween(min, max).setAllowInvalid(false)
      .setHelpText(help).build();
  };
  sh.getRange(FIRST, 13, CONFIG.DAYS, 1).setDataValidation(num(0, 24, 'Сколько часов спал(а): от 0 до 24'));
  sh.getRange(FIRST, 14, CONFIG.DAYS, 1).setDataValidation(num(20, 300, 'Вес в кг'));
  sh.getRange(FIRST, 15, CONFIG.DAYS, 1).setDataValidation(num(1, 5, 'Настроение от 1 до 5'));

  // условное форматирование: сегодня, выполненные галочки, градиент прогресса, будущие дни
  const data = sh.getRange(FIRST, 1, CONFIG.DAYS, 16);
  const checks = sh.getRange(FIRST, 3, CONFIG.DAYS, N_HABITS);
  const pct = sh.getRange(FIRST, 11, CONFIG.DAYS, 1);
  const dates = sh.getRange(FIRST, 1, CONFIG.DAYS, 2);
  const rules = [
    SpreadsheetApp.newConditionalFormatRule().whenFormulaSatisfied('=$A' + FIRST + '=TODAY()')
      .setBackground(p.today).setFontColor('#FFFFFF').setBold(true).setRanges([data]).build(),
    SpreadsheetApp.newConditionalFormatRule().whenFormulaSatisfied('=C' + FIRST + '=TRUE')
      .setBackground(p.checked).setRanges([checks]).build(),
    SpreadsheetApp.newConditionalFormatRule().whenFormulaSatisfied('=$A' + FIRST + '>TODAY()')
      .setFontColor(C.dim).setRanges([dates]).build(),
    SpreadsheetApp.newConditionalFormatRule().setGradientMinpoint('#16203A').setGradientMaxpoint(p.strong)
      .setRanges([pct]).build(),
  ];
  sh.setConditionalFormatRules(rules);

  // защита формул от случайного удаления (только предупреждение — владелец копии может всё)
  [sh.getRange(1, 1, 7, 16), sh.getRange(FIRST, 1, CONFIG.DAYS, 2), sh.getRange(FIRST, 11, CONFIG.DAYS, 2),
   sh.getRange(FIRST, 17, CONFIG.DAYS, 1)].forEach(function (r) {
    r.protect().setDescription('Формулы трекера').setWarningOnly(true);
  });

  sh.hideColumns(17);
  sh.setFrozenRows(HEAD_ROW);
  return sh;
}

// ------------------------------------------------------------------ helpers

function fitGrid_(sh, rows, cols) {
  const mr = sh.getMaxRows();
  const mc = sh.getMaxColumns();
  if (mr > rows) sh.deleteRows(rows + 1, mr - rows);
  else if (mr < rows) sh.insertRowsAfter(mr, rows - mr);
  if (mc > cols) sh.deleteColumns(cols + 1, mc - cols);
  else if (mc < cols) sh.insertColumnsAfter(mc, cols - mc);
}

function letter_(n) {
  let s = '';
  while (n > 0) { const m = (n - 1) % 26; s = String.fromCharCode(65 + m) + s; n = Math.floor((n - 1) / 26); }
  return s;
}

function arcStart_() { return new Date(CONFIG.YEAR, CONFIG.START_MONTH - 1, CONFIG.START_DAY, 12); }
function arcEnd_() { const d = arcStart_(); d.setDate(d.getDate() + CONFIG.DAYS - 1); return d; }
function fmt_(d) { return ('0' + d.getDate()).slice(-2) + '.' + ('0' + (d.getMonth() + 1)).slice(-2); }
