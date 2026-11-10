/* Global Signals data integrity and page contracts: no external dependencies. */
const fs=require('node:fs'), path=require('node:path'), vm=require('node:vm');
const assert=require('node:assert/strict'), {test}=require('node:test');
const root=path.join(__dirname,'..');
const html=fs.readFileSync(path.join(root,'global-signals.html'),'utf8');
const data=JSON.parse(fs.readFileSync(path.join(root,'data/global_signals.json'),'utf8'));
const geo=JSON.parse(fs.readFileSync(path.join(root,'geo/ne_110m_land.geojson'),'utf8'));
test('map script parses, supports keyboard, hover, filters, pan and zoom',()=>{
 const js=html.match(/<script>([\s\S]*?)<\/script>/)[1];
 new vm.Script(js);
 for(const term of ['pointerdown','pointermove','keydown','mouseenter','aria-pressed','source','zoom','select','event-cards'])assert.ok(js.includes(term),term);
});
test('curated event data have source dates, mapped place types and clean IDs',()=>{
 assert.equal(data.schema,'lexsignal-global-events-v1');
 assert.equal(data.events.length,8);
 assert.equal(new Set(data.events.map(e=>e.id)).size,data.events.length);
 const allowed=new Set(['city_of_event','event_venue','institution_venue','institution_location']);
 for(const row of data.events){
  assert.match(row.date,/^20\d{2}-\d{2}-\d{2}$/);
  assert.ok(Number.isFinite(Date.parse(row.date)));
  assert.ok(row.lat>=-70&&row.lat<=80&&row.lon>=-180&&row.lon<=180);
  assert.ok(allowed.has(row.locationType));
  assert.match(row.source,/^https:\/\//);
  assert.match(row.imagePage,/^https:\/\/commons\.wikimedia\.org\/wiki\/File:/);
  assert.ok(row.imageCredit.length>5);
 }
});
test('source events cover major regions but do not claim a live world news service',()=>{
 const regions=new Set(data.events.map(e=>e.country));
 assert.ok(regions.size>=6);
 assert.equal(data.status,'selected_historical_events');
 assert.match(html,/not a live global news feed/);
});
test('Natural Earth geographic data is present and public-domain cited',()=>{
 assert.equal(geo.type,'FeatureCollection');
 assert.ok(geo.features.length>100);
 assert.match(html,/Natural Earth/);
});
test('map is reachable from the product overview and deployment',()=>{
 const home=fs.readFileSync(path.join(root,'index.html'),'utf8');
 const publish=fs.readFileSync(path.join(root,'.github/workflows/publish.yml'),'utf8');
 assert.match(home,/global-signals\.html/);
 const builder=fs.readFileSync(path.join(root,'build_site.py'),'utf8');
 assert.match(publish,/build_site\.py --out _site/);
 assert.match(builder,/global-signals\.html/);
 assert.match(builder,/data\/global_signals\.json/);
 assert.match(builder,/ASSET_DIRS/);
});
test('map preserves the approved brand asset and distinguishes institution hubs',()=>{
 assert.match(html,/lexsignal-sphere-approved\.webp/);
 assert.match(html,/Publisher hub:/);
 assert.match(html,/institution location, not where each law takes effect/);
 assert.match(html,/api\/v1\/updates\.json/);
});
