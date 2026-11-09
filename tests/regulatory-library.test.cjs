const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {test} = require('node:test');

const root = path.join(__dirname, '..');
const page = fs.readFileSync(path.join(root, 'regulatory-library.html'), 'utf8');
const catalog = JSON.parse(fs.readFileSync(path.join(root, 'data/regulatory_library.json'), 'utf8'));
const script = page.match(/<script>([\s\S]*?)<\/script>/)[1];

test('regulatory library frontend code parses', () => {
  new vm.Script(script);
  assert.match(page, /regulatory_library\.json/);
  assert.match(page, /api\/v1\/updates\.json/);
});

test('curated catalogue has source citations, unique IDs and cautious applicability notes', () => {
  assert.equal(catalog.schema, 'lexsignal-regulatory-library-v1');
  assert.equal(catalog.acts.length, 10);
  assert.equal(new Set(catalog.acts.map(a => a.id)).size, 10);
  for (const a of catalog.acts) {
    assert.match(a.source, /^https:\/\/(?:eur-lex\.europa\.eu|www\.esma\.europa\.eu)/);
    assert.match(a.guide, /^https:\/\//);
    assert.ok(a.citation.length >= 14);
    assert.ok(a.summary.length >= 75);
    assert.ok(a.check.length >= 50);
    assert.ok(a.sectors.length > 0);
  }
});

test('all milestone dates are parseable and have an official source', () => {
  assert.equal(catalog.milestones.length, 17);
  const ids=new Set(catalog.acts.map(a=>a.id));
  const used=new Set();
  for (const m of catalog.milestones) {
    assert.ok(ids.has(m.act), 'unknown act: ' + m.act);
    assert.ok(!used.has(m.id), 'duplicate milestone: ' + m.id);
    used.add(m.id);
    assert.match(m.date,/^20\d\d-\d\d-\d\d$/);
    assert.equal(new Date(m.date+'T00:00:00Z').toISOString().slice(0,10),m.date);
    assert.match(m.url,/^https:\/\/(?:[\w-]+\.)+[\w-]+/);
    assert.ok(m.scope.length>28);
  }
});

test('known future dates stay distinct from publication dates and past milestones', () => {
  const mil = new Map(catalog.milestones.map(m=>[m.id,m]));
  assert.equal(mil.get('ai-transition').date,'2026-12-02');
  assert.equal(mil.get('t1-alloc').date,'2026-12-07');
  assert.equal(mil.get('t1-switch').date,'2027-10-11');
  assert.equal(mil.get('cra-main').date,'2027-12-11');
  assert.equal(mil.get('ai-high-risk').date,'2027-12-02');
  assert.equal(mil.get('ai-product-high-risk').date,'2028-08-02');
  assert.equal(mil.get('nis2-trans').kind,'Transposition deadline');
  const nis2=catalog.acts.find(a=>a.id==='nis2');
  assert.match(nis2.special,/8 July 2026/);
});

test('calendar generates correct CRLF and all-day date boundaries, with source URLs', () => {
  const start=script.indexOf('function escICS(');
  const end=script.indexOf("el('sector').addEventListener",start);
  assert.ok(start>0&&end>start);
  const snippet=script.slice(start,end);
  const ctx=vm.createContext({Date,TextEncoder,library:catalog,slug:id=>String(id).replace(/[^a-z0-9-]/gi,'')});
  vm.runInContext(snippet,ctx);
  const m=catalog.milestones.find(x=>x.id==='t1-switch');
  ctx.rows=[m];
  const ics=vm.runInContext('calendarText(rows)',ctx);
  assert.match(ics,/BEGIN:VCALENDAR\r\n/);
  assert.match(ics,/DTSTART;VALUE=DATE:20271011/);
  assert.match(ics,/DTEND;VALUE=DATE:20271012/);
  assert.match(ics,/SUMMARY:EU T\+1: EU securities settlement transitions to T\+1/);
  assert.match(ics,/https:\/\/www\.esma\.europa\.eu/);
  assert.equal((ics.match(/BEGIN:VEVENT/g)||[]).length,1);
});

test('site exposes library from main navigation and publishes its data to Pages',()=>{
  const home=fs.readFileSync(path.join(root,'index.html'),'utf8');
  const workflow=fs.readFileSync(path.join(root,'.github/workflows/publish.yml'),'utf8');
  assert.match(home,/regulatory-library\.html/);
  assert.match(home,/Browse official EU laws/);
  assert.match(workflow,/regulatory-library\.html/);
  assert.match(workflow,/data\/regulatory_library\.json/);
  assert.match(page,/lexsignal-sphere-approved\.webp/);
});
