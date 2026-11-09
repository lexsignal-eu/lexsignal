/* LexSignal's inline dashboard integration tests: no npm dependencies. */
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const {test}=require('node:test');

const root=path.join(__dirname,'..');
const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
const script=html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
const prelaunch=script.split("document.getElementById('profile').value=state.profile;sync();updateSnapshotStatus();autoloadSnapshot();")[0];
function context(){
  const node={value:'',addEventListener(){}};
  const mock={getElementById(){return node;},querySelectorAll(){return [];}};
  const ctx=vm.createContext({document:mock,window:{addEventListener(){}},localStorage:{getItem(){return null;},setItem(){}},URL,console});
  vm.runInContext(prelaunch,ctx);
  return ctx;
}
test('dashboard JS syntax is valid and application can initialize core functions',()=>{
  new vm.Script(script);
  assert.equal(vm.runInContext("typeof isBriefIncluded",context()),"function");
});
test('unreviewed RSS cannot enter a brief through manual include',()=>{
  const ctx=context();
  vm.runInContext("state.profile='fin'; state.imported=[{id:'rss-0123456789abcdef',sourceType:'rss',sectors:['fin'],signalTier:'background',date:'2026-10-20'}];state.briefIncluded.push('rss-0123456789abcdef');",ctx);
  assert.equal(vm.runInContext("isBriefIncluded(state.imported[0])",ctx),false);
});
test('reviewed background item can be included by analyst and explicitly excluded',()=>{
  const ctx=context();
  vm.runInContext("state.profile='fin'; state.imported=[{id:'rss-0123456789abcdef',sourceType:'rss',sectors:['fin'],signalTier:'background',date:'2026-10-20'}];",ctx);
  assert.equal(vm.runInContext("isBriefIncluded(state.imported[0])",ctx),false);
  vm.runInContext("state.reviewed.push('rss-0123456789abcdef');state.briefIncluded.push('rss-0123456789abcdef');",ctx);
  assert.equal(vm.runInContext("isBriefIncluded(state.imported[0])",ctx),true);
  vm.runInContext("state.briefExcluded.push('rss-0123456789abcdef')",ctx);
  assert.equal(vm.runInContext("isBriefIncluded(state.imported[0])",ctx),false);
});
test('T+1 dates distinguish source publication from 2026 and 2027 milestones',()=>{
  const ctx=context();
  const row=vm.runInContext("SEED.find(x=>x.id==='esma-t1')",ctx);
  assert.equal(row.date,"2026-10-16");
  assert.equal(row.milestoneDate,"2027-10-11");
  assert.match(row.url,/one-year-go-t1-settlement/);
  const early=vm.runInContext("SEED.find(x=>x.id==='esma-t1-allocations')",ctx);
  assert.equal(early.milestoneDate,"2026-12-07");
});
test('direct Irish DPC primary source and post-trade draft RTS recorded',()=>{
  const ctx=context();
  const dpc=vm.runInContext("SEED.find(x=>x.id==='dpc-google')",ctx);
  assert.match(dpc.url,/google-eu403-million/);
  const ptrr=vm.runInContext("SEED.find(x=>x.id==='esma-ptrr')",ctx);
  assert.match(ptrr.summary,/Commission endorsement/);
});
test('review decision and action register fields are present in code and export',()=>{
  assert.match(html,/function setBriefDecision/);
  assert.match(html,/function renderActions/);
  assert.match(html,/function setActionField/);
  assert.match(html,/Action owner/);
  assert.match(html,/state\.actions\[x\.id\]\?\.status/);
  assert.match(html,/lexsignal-sphere-approved\.webp/);
});
test('the presentation shows a real ESMA example and uses approved logo',()=>{
  const landing=fs.readFileSync(path.join(root,'landing.html'),'utf8');
  assert.match(landing,/id="case-example"/);
  assert.match(landing,/one-year-go-t1-settlement/);
  assert.match(landing,/lexsignal-sphere-approved\.webp/);
});
