const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const {test}=require('node:test');

const root=path.join(__dirname,'..');
const page=fs.readFileSync(path.join(root,'research-brief.html'),'utf8');
const script=page.match(/<script>([\s\S]*?)<\/script>/)[1];

test('synthetic research page syntax, visible workflow and publish entrypoint',()=>{
  new vm.Script(script);
  assert.match(page,/id="profile"/);
  assert.match(page,/id="export"/);
  assert.match(page,/Download reviewed draft/);
  assert.match(page,/I have checked the original source/);
  assert.match(page,/link rel="icon" type="image\/webp" href="brand\/lexsignal-sphere-approved\.webp"/);
  assert.match(page,/data\/example_research\.json/);
  const builder=fs.readFileSync(path.join(root,'build_site.py'),'utf8');
  assert.match(builder,/"research-brief\.html"/);
  assert.match(builder,/data\/example_research\.json/);
  const library=fs.readFileSync(path.join(root,'regulatory-library.html'),'utf8');
  assert.match(library,/href="research-brief\.html"/);
});

test('research worksheet rejects spoofed URLs, unsourced claims and malformed profiles',()=>{
  const start=script.indexOf('function validWorksheet(');
  const end=script.indexOf('function currentProfile(',start);
  assert.ok(start>0&&end>start);
  const ctx=vm.createContext({URL,APPROVED:'https://'});
  vm.runInContext(script.slice(start,end),ctx);
  const item={
    actId:'gdpr',shortName:'GDPR',name:'General Data Protection Regulation',
    sourceUrl:'https://eur-lex.europa.eu/eli/reg/2016/679/oj',
    evidenceStatus:'reference_only_provision_not_verified',
    applicabilityStatus:'not_assessed',humanReviewRequired:true,
    verificationQuestion:'Determine controller role'
  };
  const valid={schema:'lexsignal-example-research-v1',
    profiles:[{id:'demo',items:[item]}]};
  ctx.doc=valid;
  assert.equal(vm.runInContext('validWorksheet(doc)',ctx),true);
  for(const bad of [
    {...item,sourceUrl:'https://eur-lex.europa.eu.attacker.example/act'},
    {...item,sourceUrl:'javascript:alert(1)'},
    {...item,evidenceStatus:'verified_and_binding'},
    {...item,applicabilityStatus:'confirmed'},
    {...item,humanReviewRequired:false}
  ]){
    ctx.doc={...valid,profiles:[{id:'demo',items:[bad]}]};
    assert.equal(vm.runInContext('validWorksheet(doc)',ctx),false);
  }
});

test('research markdown includes citation and unanswered questions but asserts no legal obligations',()=>{
  const start=script.indexOf('function buildMarkdown(');
  const end=script.indexOf("el('profile').addEventListener",start);
  assert.ok(start>0&&end>start);
  const ctx=vm.createContext({});
  vm.runInContext(script.slice(start,end),ctx);
  ctx.profile={id:'demo',name:'Synthetic Test',jurisdiction:'EU',
    assumptions:['Software company'],limitations:'Illustrative only'};
  ctx.rows=[{shortName:'GDPR',name:'General Data Protection Regulation',
    citation:'Regulation (EU) 2016/679',
    sourceUrl:'https://eur-lex.europa.eu/eli/reg/2016/679/oj',
    screeningRationale:'Data processing merits research',
    verificationQuestion:'Confirm covered processing',
    milestones:[]}];
  const out=vm.runInContext('buildMarkdown(profile,rows,"2026-11-10T12:00:00Z")',ctx);
  assert.match(out,/Source:|Original source:/);
  assert.match(out,/NO DETERMINATION OF LEGAL APPLICABILITY/);
  assert.match(out,/Confirm covered processing/);
  assert.match(out,/https:\/\/eur-lex\.europa\.eu\/eli\/reg\/2016\/679\/oj/);
});
