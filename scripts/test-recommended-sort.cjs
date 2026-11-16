// Run with: node scripts/test-recommended-sort.cjs (Node standard library only).
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
const monsters=JSON.parse(html.match(/<script id="monster-data" type="application\/json">(.*?)<\/script>/s)[1]);
const details=JSON.parse(fs.readFileSync(path.join(root,'data/monsters.json'),'utf8'));
const families=JSON.parse(fs.readFileSync(path.join(root,'data/sort-families.json'),'utf8'));
const context=vm.createContext({sortMode:'recommended'});
const helpers=html.slice(html.indexOf('function compareMonsters('),html.indexOf('const monstersById='));
vm.runInContext(helpers,context);
const area=m=>m.imageWidth*m.imageHeight;
const levelOrder=(a,b)=>a.level-b.level||area(a)-area(b)||Number(a.id)-Number(b.id);
const sizeOrder=(a,b)=>area(a)-area(b)||a.level-b.level||Number(a.id)-Number(b.id);
const anchor=ms=>[...ms].sort(levelOrder)[0];
const family=m=>m.sortFamily||'single:'+m.id;
function blocks(list,key){const result=[],seen=new Set();for(const m of list){const k=key(m);if(result.at(-1)?.key===k)result.at(-1).members.push(m);else{assert.ok(!seen.has(k),'Split block: '+k);seen.add(k);result.push({key:k,members:[m]});}}return result;}
function sorted(ms,order){for(let i=1;i<ms.length;i++)assert.ok(order(ms[i-1],ms[i])<=0,'Unexpected order: '+ms[i-1].name+' / '+ms[i].name);}
function check(input){
 const output=Array.from(context.sortForDisplay([...input]));
 assert.deepEqual(output.map(m=>m.id).sort(),input.map(m=>m.id).sort());
 const familyBlocks=blocks(output,family);sorted(familyBlocks.map(b=>anchor(b.members)),levelOrder);
 for(const block of familyBlocks){
  if(block.members.some(m=>Number.isInteger(m.sortFamilyRank))){
   assert.ok(block.members.every(m=>Number.isInteger(m.sortFamilyRank)),'Incomplete progression metadata');
   sorted(block.members,(a,b)=>a.sortFamilyRank-b.sortFamilyRank);
   continue;
  }
  const count=new Map();
  for(const m of block.members)for(const r of new Set((m.regions||[]).filter(r=>r&&r!=='BOSS')))count.set(r,(count.get(r)||0)+1);
  // Independent membership oracle: the most widely shared eligible source region wins.
  const region=m=>[...new Set((m.regions||[]).filter(r=>r&&r!=='BOSS'))].sort((a,b)=>count.get(b)-count.get(a)||a.localeCompare(b,'ko'))[0]||'';
  const regionBlocks=blocks(block.members,region);
  if(regionBlocks.some(b=>!b.key))assert.equal(regionBlocks.at(-1).key,'');
  sorted(regionBlocks.filter(b=>b.key).map(b=>anchor(b.members)),levelOrder);
  for(const sub of regionBlocks)sorted(sub.members,sizeOrder);
 }
 return output;
}
assert.equal(monsters.length,567);
const detailMap=new Map(details.map(m=>[m.id,m]));
for(const m of monsters)assert.deepEqual(m.regions,detailMap.get(m.id).regions);
const owners=new Set();const galleryMap=new Map(monsters.map(m=>[m.id,m]));
for(const f of families){
 assert.ok(f.monsterIds.length>=2);
 for(const [rank,id] of f.monsterIds.entries()){
  assert.ok(!owners.has(id));owners.add(id);
  for(const m of [detailMap.get(id),galleryMap.get(id)]){
   assert.equal(m.sortFamily,f.id);
   assert.equal(m.sortFamilyRank,f.order==='progression'?rank:undefined);
  }
 }
}
for(const m of monsters)if(!owners.has(m.id)){assert.equal(m.sortFamily,undefined);assert.equal(m.sortFamilyRank,undefined);}
const pair=['8170000','9300028'];assert.equal(detailMap.get(pair[0]).sortFamily,detailMap.get(pair[1]).sortFamily);
let result=check(monsters);const positions=pair.map(id=>result.findIndex(m=>m.id===id));assert.equal(Math.abs(positions[0]-positions[1]),1);
const titles=new Set(monsters.flatMap(m=>m.titles));assert.equal(titles.size,81);
for(const title of titles)check(monsters.filter(m=>m.titles.includes(title)));
// Exact user sequences must survive title filtering, search and missing earlier members.
function sequence(title,ids){
 const list=check(monsters.filter(m=>!title||m.titles.includes(title)));
 const selected=ids.map(id=>detailMap.get(id));assert.ok(selected.every(Boolean));
 assert.equal(new Set(selected.map(m=>m.sortFamily)).size,1,'Requested family membership');
 const positions=ids.map(id=>list.findIndex(m=>m.id===id));
 assert.ok(positions.every((p,i)=>p>=0&&(!i||p===positions[i-1]+1)),'Requested progression: '+ids.join(', '));
 return ids;
}
const snakes=sequence('파충류',['2130103','4230504','4230503','2100105','1150002','9420002']);
sequence('뱀',snakes);
sequence('사람',['9400100','9400101','9400102','9400103','9400110','9400111','9400112','9400113','9400120','9400121','9400408','9400300']);
sequence('사람',['9400593','9400589','9400592','9400590']);
sequence('사람',['9400576','9400577','9400579']);
sequence('사람',['9400260','9400270','9400376','9400289']);
sequence('드래곤',['8180000','8220003']);
sequence('', ['9500390','9500391','9500392']);
sequence('', ['9400263','9400264','9400265']);
sequence('', ['4110302','5110300']);
sequence('', ['8190003','8190004']);
const partial=check(monsters.filter(m=>snakes.slice(3).includes(m.id)));
assert.deepEqual(partial.map(m=>m.id),snakes.slice(3));
// Keep the seven earlier examples contiguous after extending their surrounding visual families.
const idByName=name=>monsters.find(m=>m.name===name).id;
for(const [title,names] of [
 ['사물',['아이언 뮤테','강화된 아이언 뮤테']],['사물',['루모','트리플 루모','루루모']],
 ['사물',['단지','삼단지']],['사물',['통행금지','프리저','과속금지','올리 올리']],
 ['장난감',['티키','틱톡']],['장난감',['브라운테니','핑크테니','팬더테니']],
 ['장난감',['치크세이버','핑크세이버','스카이세이버']]
])sequence(title,names.map(idByName));
for(const query of ['강화','레이스','크로노스','930','없음123'])check(monsters.filter(m=>m.name.includes(query)||m.id.includes(query)));
check([]);
// Region priority overrides size interleaving, and BOSS never connects unrelated places.
const synthetic=(id,regions,size,level=1)=>({id:String(id),name:String(id),sortFamily:'example',regions,imageWidth:size,imageHeight:1,level});
const example=[synthetic(1,['A'],10),synthetic(2,['A','BOSS'],100),synthetic(3,['B'],20),synthetic(4,['B','BOSS'],30),synthetic(5,['BOSS'],1)];
assert.deepEqual(check(example).map(m=>m.id),['1','2','3','4','5']);
const shared=[synthetic(1,['A'],10),synthetic(2,['A','B'],100),synthetic(3,['B'],20),synthetic(4,['B'],30)];
assert.deepEqual(check(shared).map(m=>m.id),['1','3','4','2']);
check([synthetic(1,['A'],20,30),synthetic(2,['A'],20,5)]);
const staged=[{...synthetic(1,['BOSS'],100,180),sortFamilyRank:0},{...synthetic(2,['A'],1,18),sortFamilyRank:1},{...synthetic(3,['B'],10,30),sortFamilyRank:2}];
assert.deepEqual(check(staged).map(m=>m.id),['1','2','3']);
assert.deepEqual(check(staged.slice(1)).map(m=>m.id),['2','3']);
for(const mode of ['size','level']){context.sortMode=mode;const list=Array.from(context.sortForDisplay([...monsters]));sorted(list,mode==='size'?sizeOrder:(a,b)=>a.level-b.level||Number(a.id)-Number(b.id));}
console.log('PASS: 567 monsters, 81 title views, all explicit snake/person/dragon sequences, seven earlier adjacency examples, growth/upgrade/boss progression, filtered sequence stability, region fallback, BOSS exclusion, multi-region overlap, size/level modes and Thanatos/Eregos adjacency.');
