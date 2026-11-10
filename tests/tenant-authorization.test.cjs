/* M4 policy checks against a D1-shaped in-memory test double. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { test } = require('node:test');
const { pathToFileURL } = require('node:url');
const modulePromise = import(pathToFileURL(path.join(__dirname, '../backend/access_control.mjs')).href);

function fakeD1(memberships, records = {}) {
  const calls = [];
  const db = {
    calls,
    prepare(sql) {
      return {
        bind(...params) {
          calls.push({ sql, params });
          return {
            async first() {
              if (sql.includes('FROM memberships')) {
                const row = memberships.find(m => m.organizationId === params[0] &&
                  m.userId === params[1]);
                return row ? { role: row.role } : null;
              }
              const match = sql.match(/^SELECT id, organization_id FROM ([a-z_]+) WHERE id =/);
              if (!match) throw Error('Unexpected test query');
              const row = (records[match[1]] || []).find(r => r.id === params[0] &&
                r.organization_id === params[1]);
              return row || null;
            }
          };
        }
      };
    }
  };
  return db;
}

test('membership is fetched from server database, never from client role', async () => {
  const {requireOrganizationAccess} = await modulePromise;
  const db = fakeD1([{ organizationId:'org-a', userId:'alice', role:'reader' }]);
  const session = {verified:true,userId:'alice',role:'admin'};
  const ctx = await requireOrganizationAccess(db, session, 'org-a', 'research:read');
  assert.equal(ctx.role, 'reader');
  assert.equal(db.calls[0].params.join(','), 'org-a,alice');
  await assert.rejects(() => requireOrganizationAccess(db,session,'org-a','billing:manage'),
    {status:403,code:'permission_denied'});
});

test('unknown, unverified or cross-organization principal is denied', async () => {
  const {requireOrganizationAccess} = await modulePromise;
  const db=fakeD1([{organizationId:'org-b',userId:'alice',role:'admin'}]);
  await assert.rejects(() => requireOrganizationAccess(db,{userId:'alice',verified:false},'org-b','research:read'),
    {status:401});
  await assert.rejects(() => requireOrganizationAccess(db,{userId:'alice',verified:true},'org-a','research:read'),
    {status:404,code:'organization_not_found'});
  await assert.rejects(() => requireOrganizationAccess(db,{userId:'alice',verified:true},'org-a;DROP','research:read'),
    {status:400});
  assert.equal(db.calls.length,1);
});

test('analyst can review; reader cannot write; admin manages connectors', async () => {
  const {requireOrganizationAccess} = await modulePromise;
  const db=fakeD1([
    {organizationId:'org-a',userId:'reader',role:'reader'},
    {organizationId:'org-a',userId:'analyst',role:'analyst'},
    {organizationId:'org-a',userId:'admin',role:'admin'}
  ]);
  await assert.rejects(() => requireOrganizationAccess(db,{verified:true,userId:'reader'},'org-a','review:write'),{status:403});
  await requireOrganizationAccess(db,{verified:true,userId:'analyst'},'org-a','review:write');
  await assert.rejects(() => requireOrganizationAccess(db,{verified:true,userId:'analyst'},'org-a','connector:manage'),{status:403});
  const ctx=await requireOrganizationAccess(db,{verified:true,userId:'admin'},'org-a','connector:manage');
  assert.equal(ctx.permission,'connector:manage');
});

test('cross-tenant records cannot be fetched even when their ID is known', async () => {
  const {requireOrganizationAccess,requireTenantRecord}=await modulePromise;
  const db=fakeD1(
    [{organizationId:'org-a',userId:'alice',role:'analyst'}],
    {review_decisions:[
      {id:'review-1',organization_id:'org-b'},
      {id:'review-2',organization_id:'org-a'}
    ]}
  );
  const ctx=await requireOrganizationAccess(db,{verified:true,userId:'alice'},'org-a','research:read');
  await assert.rejects(()=>requireTenantRecord(db,ctx,'review_decisions','review-1'),
    {status:404,code:'record_not_found'});
  const record=await requireTenantRecord(db,ctx,'review_decisions','review-2');
  assert.equal(record.organizationId,'org-a');
  assert.deepEqual(db.calls[1].params,['review-1','org-a']);
});

test('a forged context, table, or permission cannot bypass the scoped query', async () => {
  const {requireOrganizationAccess,requireTenantRecord}=await modulePromise;
  const db=fakeD1([{organizationId:'org-a',userId:'admin',role:'admin'}],{
    connector_accounts:[{id:'con-1',organization_id:'org-a'}]
  });
  await assert.rejects(() => requireTenantRecord(db,
    {organizationId:'org-a',actorUserId:'admin',permission:'connector:manage'},
    'connector_accounts','con-1'),{status:403});
  const ctx=await requireOrganizationAccess(db,{verified:true,userId:'admin'},'org-a','connector:manage');
  await assert.rejects(() => requireTenantRecord(db,ctx,'memberships','con-1'),/Unapproved/);
  assert.equal((await requireTenantRecord(db,ctx,'connector_accounts','con-1')).id,'con-1');
});

test('membership revocation takes effect on the next authorization request', async () => {
  const {requireOrganizationAccess}=await modulePromise;
  const members=[{organizationId:'org-a',userId:'alice',role:'analyst'}];
  const db=fakeD1(members);
  await requireOrganizationAccess(db,{verified:true,userId:'alice'},'org-a','review:write');
  members.length=0;
  await assert.rejects(()=>requireOrganizationAccess(db,{verified:true,userId:'alice'},'org-a','review:write'),{status:404});
});

test('private backend code does not ship in the static Pages release', () => {
  const builder=fs.readFileSync(path.join(__dirname,'../build_site.py'),'utf8');
  assert.doesNotMatch(builder,/copytree\(.*backend/);
  assert.match(builder,/PAGES =/);
});
