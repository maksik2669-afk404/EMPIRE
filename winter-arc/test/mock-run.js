// Runs Code.gs against a strict mock of the Apps Script API: validates range shapes,
// formula syntax, freeze/merge conflicts and the password gate. Usage: node test/mock-run.js
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const log = [], errors = [];
const chain = (name) => new Proxy(function () {}, {
  get: (t, p) => p === 'build' ? () => ({ built: name }) : (...a) => chain(name),
  apply: () => chain(name),
});
function a1(s) {  // "A1:P1" -> {r,c,nr,nc}
  const m = s.match(/^([A-Z]+)(\d+)(?::([A-Z]+)(\d+))?$/); if (!m) throw new Error('bad A1 ' + s);
  const col = (L) => [...L].reduce((n, ch) => n * 26 + ch.charCodeAt(0) - 64, 0);
  const r = +m[2], c = col(m[1]), r2 = m[4] ? +m[4] : r, c2 = m[3] ? col(m[3]) : c;
  return { r, c, nr: r2 - r + 1, nc: c2 - c + 1 };
}
function checkFormula(f, where) {
  if (!f.startsWith('=')) errors.push(`${where}: formula must start with = : ${f}`);
  const noStr = f.replace(/"[^"]*"/g, '""');
  if ((f.match(/"/g) || []).length % 2) errors.push(`${where}: unbalanced quotes: ${f}`);
  let d = 0; for (const ch of noStr) { d += ch === '(' ? 1 : ch === ')' ? -1 : 0; if (d < 0) break; }
  if (d !== 0) errors.push(`${where}: unbalanced parentheses: ${f}`);
  if (/;/.test(noStr)) errors.push(`${where}: API formulas need commas, found ';': ${f}`);
}
function makeSheet(ss, name) {
  const sh = { name, maxR: 1000, maxC: 26, merges: [], frozen: 0, cells: {}, protections: 0, rules: [] };
  const inGrid = (g, what) => { if (g.r < 1 || g.c < 1 || g.r + g.nr - 1 > sh.maxR || g.c + g.nc - 1 > sh.maxC)
    errors.push(`${name}: ${what} out of grid ${JSON.stringify(g)} (grid ${sh.maxR}x${sh.maxC})`); };
  const range = (g) => {
    inGrid(g, 'range');
    const R = new Proxy({}, { get: (t, p) => {
      if (p === 'setValues' || p === 'setFormulas') return (arr) => {
        if (arr.length !== g.nr || arr.some(row => row.length !== g.nc))
          errors.push(`${name}: ${p} shape ${arr.length}x${arr[0] && arr[0].length} != range ${g.nr}x${g.nc}`);
        arr.forEach((row, i) => row.forEach((v, j) => {
          if (p === 'setFormulas') checkFormula(v, `${name}!R${g.r + i}C${g.c + j}`);
          sh.cells[`${g.r + i},${g.c + j}`] = v; }));
        return R; };
      if (p === 'setValue' || p === 'setFormula') return (v) => {
        if (p === 'setFormula') checkFormula(v, `${name}!R${g.r}C${g.c}`);
        sh.cells[`${g.r},${g.c}`] = v; return R; };
      if (p === 'merge') return () => { sh.merges.push(g); return R; };
      if (p === 'protect') return () => { sh.protections++; return chain('protection'); };
      if (p === 'applyRowBanding') return () => chain('banding');
      if (p === 'setBorder') return (...a) => { if (a.length !== 8) errors.push(`${name}: setBorder needs 8 args`); return R; };
      return () => R;
    } });
    return R;
  };
  return {
    _s: sh,
    getName: () => name,
    setName: (n) => { sh.name = n; return sh; },
    getRange: (...a) => typeof a[0] === 'string' ? range(a1(a[0])) : range({ r: a[0], c: a[1], nr: a[2] || 1, nc: a[3] || 1 }),
    getMaxRows: () => sh.maxR, getMaxColumns: () => sh.maxC,
    deleteRows: (s, n) => { assert(s + n - 1 <= sh.maxR); sh.maxR -= n; },
    deleteColumns: (s, n) => { assert(s + n - 1 <= sh.maxC); sh.maxC -= n; },
    insertRowsAfter: (s, n) => { sh.maxR += n; }, insertColumnsAfter: (s, n) => { sh.maxC += n; },
    setFrozenRows: (n) => { sh.frozen = n;
      sh.merges.forEach(m => { if (m.r <= n && m.r + m.nr - 1 > n) errors.push(`${name}: freeze ${n} splits merge`); }); },
    setConditionalFormatRules: (r) => { sh.rules = r; },
    setHiddenGridlines: function () { return this; }, setTabColor: function () { return this; },
    setColumnWidth: (c) => { if (c > sh.maxC) errors.push(`${name}: width col ${c} > ${sh.maxC}`); },
    setColumnWidths: (c, n) => { if (c + n - 1 > sh.maxC) errors.push(`${name}: widths ${c}+${n} > ${sh.maxC}`); },
    setRowHeight: (r) => { if (r > sh.maxR) errors.push(`${name}: height row ${r} > ${sh.maxR}`); },
    setRowHeights: (r, n) => { if (r + n - 1 > sh.maxR) errors.push(`${name}: heights ${r}+${n} > ${sh.maxR}`); },
    hideColumns: (c) => { if (c > sh.maxC) errors.push(`${name}: hide col ${c}`); },
  };
}
const sheets = [];
const ss = {
  getSheets: () => sheets, getNumSheets: () => sheets.length, getId: () => 'TEMPLATE123', getUrl: () => 'https://sheet',
  insertSheet: (n, i) => { const s = makeSheet(ss, n); sheets.splice(i, 0, s); return s; },
  setActiveSheet: () => {}, setSpreadsheetLocale: () => {}, setSpreadsheetTimeZone: () => {},
};
sheets.push(makeSheet(ss, 'Лист1'));
const props = {};
const ctx = {
  SpreadsheetApp: { create: () => ss, flush: () => {}, newConditionalFormatRule: () => chain('cf'),
    newDataValidation: () => chain('dv'), BorderStyle: { SOLID_THICK: 1, SOLID_MEDIUM: 2 }, BandingTheme: { BLUE: 1 } },
  DriveApp: { getFileById: () => ({ setSharing: () => {} }), Access: { ANYONE_WITH_LINK: 1 }, Permission: { VIEW: 1 } },
  PropertiesService: { getScriptProperties: () => ({ getProperty: (k) => props[k] || null, setProperty: (k, v) => { props[k] = v; } }) },
  LockService: { getScriptLock: () => ({ waitLock: () => {}, releaseLock: () => {} }) },
  Utilities: { sleep: () => {} }, Logger: { log: (m) => log.push(m) },
  HtmlService: { createTemplateFromFile: () => { const t = { evaluate: () => ({ t, setTitle() { return this; }, addMetaTag() { return this; } }) }; return t; } },
};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(__dirname + '/../Code.gs', 'utf8'), ctx);

// before setup: gate refuses politely
assert.deepStrictEqual(ctx.unlock('winter2026').ok, false);
ctx.setup();
assert.strictEqual(errors.length, 0, errors.join('\n'));
assert.deepStrictEqual(sheets.map(s => s._s.name), ['❄ СТАРТ', '❄ HIM', '❄ HER']);
const him = sheets[1]._s;
assert.strictEqual(him.maxR, 101);  // 92 days + 8 header rows + 1 bottom margin assert.strictEqual(him.maxC, 17); assert.strictEqual(him.frozen, 8);
assert.strictEqual(him.cells['9,1'], '=DATE(2026,10,1)+0');
assert.strictEqual(him.cells['100,1'], '=DATE(2026,10,1)+91');       // 31.12
assert.strictEqual(him.cells['8,3'], '🌅 Подъём до 6:30');
assert.strictEqual(him.cells['10,17'], '=IF(K10>=0.8,Q9+1,0)');
assert.ok(him.cells['4,1'].includes('K9:K100') && him.cells['4,1'].includes('A9:A100'));
assert.strictEqual(him.rules.length, 4); assert.strictEqual(him.protections, 4);
assert.ok(ctx.unlock(' winter2026 ').url.endsWith('/d/TEMPLATE123/copy'));
assert.strictEqual(ctx.unlock('nope').ok, false);
assert.strictEqual(props.UNLOCKS, '1');
const page = ctx.doGet();
assert.deepStrictEqual([page.t.year, page.t.days, page.t.range], [2026, 92, '01.10 — 31.12']);
const html = fs.readFileSync(__dirname + '/../Gate.html', 'utf8');
for (const v of html.match(/<\?=\s*(\w+)\s*\?>/g)) assert.ok(v.match(/(year|days|range)/), 'unknown scriptlet ' + v);
assert.ok(html.includes('.unlock('));
console.log('OK:', sheets.map(s => s._s.name).join(', '), '| formulas checked:',
  Object.values(him.cells).filter(v => String(v).startsWith('=')).length, '| log:', log[1]);
