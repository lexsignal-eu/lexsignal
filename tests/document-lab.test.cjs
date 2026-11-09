const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const {test}=require('node:test');
const root=path.join(__dirname,'..');
const html=fs.readFileSync(path.join(root,'documents.html'),'utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
const prelaunch=script.split("el('file').addEventListener")[0].replace(/^\s*\(function\(\)\s*\{/,"");

function ctx(){
 const sandbox=vm.createContext({URL,Date,TextDecoder,atob,console});
 vm.runInContext(prelaunch,sandbox);
 return sandbox;
}
test('document lab script parses as JavaScript',()=>new vm.Script(script));
test('official-source URL allowlist rejects attacker and HTTP URLs',()=>{
 const c=ctx();
 assert.equal(vm.runInContext("sourceAllowed('https://www.esma.europa.eu/a')",c),true);
 assert.equal(vm.runInContext("sourceAllowed('https://ec.europa.eu/a')",c),true);
 assert.equal(vm.runInContext("sourceAllowed('https://www.dataprotection.ie/a')",c),true);
 assert.equal(vm.runInContext("sourceAllowed('https://www.esma.europa.eu.evil.com/a')",c),false);
 assert.equal(vm.runInContext("sourceAllowed('http://www.esma.europa.eu/a')",c),false);
});
test('quoted comma and quoted multiline fields work in CSV parser',()=>{
 const c=ctx();
 const s='"Title","Summary","Source","Date"\r\n"MiCA, update","Contains ""quote"" and\nnewline","https://www.esma.europa.eu/news/test","2026-11-09"\r\n';
 c.csv=s;
 const parsed=vm.runInContext("parseCSV(csv)",c);
 assert.equal(parsed.length,1);
 assert.equal(parsed[0].title,'MiCA, update');
 assert.match(parsed[0].summary,/quote/);
 assert.match(parsed[0].summary,/newline/);
});
test('saved plain email exposes subject and body',()=>{
 const c=ctx();
 c.raw='From: analyst@example.org\r\nSubject: MiCA monitoring\r\nDate: Mon, 9 Nov 2026 10:00:00 +0000\r\nContent-Type: text/plain\r\n\r\nSee https://www.esma.europa.eu/test';
 const e=vm.runInContext("emlBody(raw)",c);
 assert.equal(e.subject,'MiCA monitoring');
 assert.match(e.body,/esma/);
});
test('links are deduplicated and restricted to named regulators',()=>{
 const c=ctx();
 c.note='https://www.esma.europa.eu/a https://www.esma.europa.eu/a https://random.org/a';
 const links=vm.runInContext("urlsIn(note)",c);
 assert.equal(links.length,1);
 assert.equal(links[0],'https://www.esma.europa.eu/a');
});
test('document lab promises local processing and avoids fake live OAuth/payment actions',()=>{
 assert.match(html,/processed locally/);
 assert.match(html,/Not connected/);
 assert.match(html,/PDF and Word extraction/);
 assert.match(html,/sourceType:'manual_file'/);
 assert.match(html,/lexsignal-sphere-approved\.webp/);
 assert.doesNotMatch(html,/Stripe\s+checkout/i);
});
