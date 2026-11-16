"""Build all static detail pages from the checked-in MapleNote data snapshot."""
from pathlib import Path
import json,html,re,urllib.parse
ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'data/monsters.json').read_text(encoding='utf-8'))
def esc(value):return html.escape(str(value if value is not None else ''),quote=True)
def fmt(value):
 if value is None or value=='':return '미기재'
 text=str(value)
 if re.fullmatch(r'\d+',text):return f'{int(text):,}'
 return text
def safe_url(url):return url if url and url.startswith('https://') else None
def outgoing(url,label):
 url=safe_url(url)
 return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)}<span class="external-icon" aria-hidden="true">↗</span></a>' if url else f'<span class="map-name">{esc(label)}</span>'
def render(m,index):
 title=f'{m["name"]} · Lv. {m["level"]} | 몬스터 외형 도감'
 tags=''.join(f'<a class="tag" href="../../index.html?title={urllib.parse.quote(t,safe="")}">{esc(t)}</a>' for t in m['titles'])
 desc=esc(m['description']) if m['description'] else ('<span class="empty-text">원본 상세 페이지를 확인할 수 없어 설명을 표시하지 못했습니다.</span>' if m['sourceStatus']=='unavailable' else '<span class="empty-text">메이플노트에 등록된 설명이 없습니다.</span>')
 description_credit=''
 if m.get('descriptionSourceUrl') and m['descriptionSourceUrl']!=m['sourceUrl']:
  description_credit='<p class="source-note">설명 출처: '+outgoing(m['descriptionSourceUrl'],'프랑켄로이드 #'+m['descriptionSourceId']+' 원문')+'</p>'
 notice=''
 if m['sourceStatus']=='unavailable':notice='<p class="notice">메이플노트에서 이 몬스터의 상세 페이지를 찾을 수 없습니다. 지역별 목록에서 확인한 정보만 표시합니다.</p>'
 elif m['sourceStatus']=='cached':notice='<p class="notice">원본 조회가 되지 않아 이전에 수집한 정보를 표시합니다.</p>'
 stats=dict(m['stats'])
 for key in ['HP','MP','EXP','넉백 가능 데미지','물리 데미지','마법 데미지','물리 방어력','마법 방어력','속도','메소','속성관계']:stats.setdefault(key,'')
 stats['체경비']=m['listStats'].get('체경비','')
 if m.get('type'):stats['형태']=m['type'] if m['type']!='Unknown' else '미상'
 stat_html=''.join(f'<div class="stat{" long" if key in ["속성관계","형태"] or "필요 명중" in key else ""}"><dt>{esc(key)}</dt><dd>{esc(fmt(value))}</dd></div>' for key,value in stats.items())
 regions=''.join(f'<span class="region-label">{esc(r)}</span>' for r in m['regions']) or '<p class="empty-text">원본에 지역 분류가 없습니다.</p>'
 spawn=''.join('<li>'+outgoing(a.get('url'),a['name'])+'</li>' for a in m['spawn'])
 maps=f'<ul class="map-list">{spawn}</ul>' if spawn else ('<p>'+esc(m['spawnText'])+'</p>' if m.get('spawnText') else ('<p class="empty-text">원본 상세 페이지를 확인할 수 없어 출현 맵 정보를 표시하지 못했습니다.</p>' if m['sourceStatus']=='unavailable' else '<p class="empty-text">메이플노트에 등록된 출현 맵이 없습니다.</p>'))
 rows=[]
 for drop in m['drops']:
  item_id=drop['url'].rstrip('/').split('/')[-1] if drop.get('url') else ''
  rows.append('<tr><td>'+outgoing(drop.get('url'),drop['name'])+f'</td><td class="item-id">{esc(item_id)}</td><td class="rate">{esc(drop.get("drop_rate") or "미기재")}</td></tr>')
 if rows:
  drops=f'''<div class="drop-toolbar"><label class="drop-search">드롭 아이템 검색<input id="drop-search" type="search" placeholder="아이템 이름 또는 ID" autocomplete="off"></label><span class="drop-count" id="drop-count" aria-live="polite">{len(rows)} / {len(rows)}개</span></div><div class="table-box"><table id="drop-table"><thead><tr><th scope="col">아이템</th><th scope="col">아이템 ID</th><th scope="col" class="rate">드롭 확률</th></tr></thead><tbody>{''.join(rows)}</tbody></table><p class="drop-none" id="drop-no-results" hidden>조건에 맞는 드롭 아이템이 없습니다.</p></div>'''
 else:drops='<div class="table-box"><p class="drop-none">'+('원본 상세 페이지를 확인할 수 없어 드롭 정보를 표시하지 못했습니다.' if m['sourceStatus']=='unavailable' else '메이플노트에 등록된 드롭 정보가 없습니다.')+'</p></div>'
 spawn_count='원본 확인 불가' if m['sourceStatus']=='unavailable' else f'출현 맵 {len(m["spawn"])}개'
 drop_count='원본 확인 불가' if m['sourceStatus']=='unavailable' else f'전체 {len(m["drops"])}개'
 previous=DATA[index-1] if index else None;next_one=DATA[index+1] if index+1<len(DATA) else None
 prev_html=f'<a class="previous" href="../{previous["id"]}/"><small>이전 몬스터 · Lv. {previous["level"]}</small>{esc(previous["name"])}</a>' if previous else '<span></span>'
 next_html=f'<a class="next" href="../{next_one["id"]}/"><small>다음 몬스터 · Lv. {next_one["level"]}</small>{esc(next_one["name"])}</a>' if next_one else '<span></span>'
 return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(m['name'])}의 설명, 스탯, 출현 지역과 드롭 아이템 정보를 확인하세요."><link rel="stylesheet" href="../../assets/detail.css"><script src="../../assets/detail.js" defer></script></head><body><header><div class="wrap topbar"><a class="brand" href="../../index.html?return=1">몬스터 외형 도감</a><a class="back" href="../../index.html?return=1">← 몬스터 목록으로</a></div></header><main class="wrap"><p class="breadcrumb">몬스터 도감 / 상세 정보</p><div class="hero"><figure class="portrait"><img src="../../{esc(m['imagePath'])}" alt="{esc(m['name'])}" width="{m['imageWidth']}" height="{m['imageHeight']}"></figure><div class="intro" id="description"><div class="eyebrow">Lv. {m['level']} · #{m['id']}</div><h1>{esc(m['name'])}</h1><div class="tags" aria-label="외형 타이틀">{tags}</div><p class="description">{desc}</p>{description_credit}{notice}</div></div><nav class="section-nav" aria-label="몬스터 상세 정보"><a href="#description">설명</a><a href="#stats">스탯</a><a href="#regions">출현 지역</a><a href="#drops">드롭 테이블</a></nav><section class="section" id="stats"><div class="section-heading"><h2>스탯</h2><span>레벨 {m['level']}</span></div><dl class="stat-grid">{stat_html}</dl></section><section class="section" id="regions"><div class="section-heading"><h2>출현 지역</h2><span>{spawn_count}</span></div><div class="region-block"><h3>메이플노트 목록 분류</h3><div class="region-labels">{regions}</div><h3>출현 맵</h3>{maps}</div><p class="source-note">맵 이름을 누르면 메이플노트의 맵 정보가 열립니다.</p></section><section class="section" id="drops"><div class="section-heading"><h2>드롭 테이블</h2><span>{drop_count}</span></div>{drops}<p class="source-note">확률은 메이플노트에 게시된 값입니다. 아이템 이름을 누르면 원본 아이템 정보가 열립니다. 과거 버전 데이터이므로 실제 메이플랜드와 다를 수 있습니다.</p></section><nav class="paging" aria-label="다른 몬스터">{prev_html}{next_html}</nav></main><footer class="source-footer"><div class="wrap"><p>자료 출처: {outgoing(m['sourceUrl'],'메이플노트 몬스터 원문')}</p><p>‘미기재’는 원본에 값이 없는 항목이며 0을 뜻하지 않습니다. 이미지와 데이터의 권리는 각 권리자에게 있습니다.</p></div></footer></body></html>'''
for i,m in enumerate(DATA):
 folder=ROOT/'monsters'/m['id'];folder.mkdir(parents=True,exist_ok=True);(folder/'index.html').write_text(render(m,i),encoding='utf-8')
print('Built',len(DATA),'detail pages,',sum(len(m['drops']) for m in DATA),'drop rows.')
