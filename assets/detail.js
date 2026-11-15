'use strict';
const input=document.getElementById('drop-search');
if(input){
 const rows=[...document.querySelectorAll('#drop-table tbody tr')];
 const count=document.getElementById('drop-count');
 const empty=document.getElementById('drop-no-results');
 input.addEventListener('input',()=>{
  const query=input.value.trim().toLocaleLowerCase();let visible=0;
  for(const row of rows){const match=row.textContent.toLocaleLowerCase().includes(query);row.hidden=!match;if(match)visible++;}
  count.textContent=visible+' / '+rows.length+'개';empty.hidden=visible>0;
 });
}
