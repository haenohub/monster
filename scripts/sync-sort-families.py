"""Sync global/title-specific recommendation families and source regions."""
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'index.html';html=p.read_text(encoding='utf-8');match=re.search(r'<script id="monster-data" type="application/json">(.*?)</script>',html,re.S)
if not match:raise ValueError('Gallery data is missing')
gallery=json.loads(match[1]);details=json.loads((ROOT/'data/monsters.json').read_text(encoding='utf-8'));families=json.loads((ROOT/'data/sort-families.json').read_text(encoding='utf-8'));ids={m['id'] for m in gallery}
if ids!={m['id'] for m in details}:raise ValueError('Gallery and detail rosters must match')
details_by_id={m['id']:m for m in details}
for monster in gallery:
 monster['regions']=details_by_id[monster['id']].get('regions',[])
owners={};progression_ranks={};family_ids=set()
for family in families:
 if family['id'] in family_ids:raise ValueError('Duplicate family ID')
 family_ids.add(family['id'])
 if len(family['monsterIds'])<2:raise ValueError('Families need at least two monsters')
 order=family.get('order','region')
 if order not in ['region','progression']:raise ValueError('Unknown family order: '+order)
 for rank,mid in enumerate(family['monsterIds']):
  if mid not in ids:raise ValueError('Unknown monster ID: '+mid)
  if mid in owners:raise ValueError('Monster is assigned to two families: '+mid)
  owners[mid]=family['id']
  if order=='progression':progression_ranks[mid]=rank
title_families=json.loads((ROOT/'data/sort-title-families.json').read_text(encoding='utf-8'))
title_owners={};title_family_ids=set()
for family in title_families:
 title=family['title'];key=(title,family['id'])
 if not title or key in title_family_ids:raise ValueError('Invalid or duplicate title family')
 title_family_ids.add(key)
 if len(family['monsterIds'])<2:raise ValueError('Title families need at least two monsters')
 for rank,mid in enumerate(family['monsterIds']):
  if mid not in ids:raise ValueError('Unknown title-family monster: '+mid)
  if title not in details_by_id[mid]['titles']:raise ValueError('Monster lacks title: '+mid+' / '+title)
  assigned=title_owners.setdefault(mid,{})
  if title in assigned:raise ValueError('Monster is assigned to two families within a title: '+mid)
  assigned[title]={'id':family['id'],'rank':rank}
for collection in [gallery,details]:
 for monster in collection:
  monster.pop('sortFamily',None)
  monster.pop('sortFamilyRank',None)
  monster.pop('sortTitleFamilies',None)
  if monster['id'] in owners:monster['sortFamily']=owners[monster['id']]
  if monster['id'] in progression_ranks:monster['sortFamilyRank']=progression_ranks[monster['id']]
  if monster['id'] in title_owners:monster['sortTitleFamilies']=title_owners[monster['id']]
encoded=json.dumps(gallery,ensure_ascii=False,separators=(',',':')).replace('</','<\\/');p.write_text(html[:match.start(1)]+encoded+html[match.end(1):],encoding='utf-8');(ROOT/'data/monsters.json').write_text(json.dumps(details,ensure_ascii=False,indent=2),encoding='utf-8')
print('Assigned',len(owners),'monsters to',len(families),'families;',len(ids)-len(owners),'single monsters;',len(title_families),'title-specific families.')
