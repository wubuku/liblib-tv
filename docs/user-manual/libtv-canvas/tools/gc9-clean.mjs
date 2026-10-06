import { launch, open, closePromos } from './lib.mjs';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const 名单=()=>page.evaluate(()=>[...document.querySelectorAll('[aria-label^="切换到画布"]')].map(e=>e.getAttribute('aria-label').replace('切换到画布 ','')));
async function 主页(){ await open(page,B); await closePromos(page);
  await page.evaluate(()=>{const b=[...document.querySelectorAll('button')].find(x=>{const r=x.getBoundingClientRect();
    return r.x>160&&r.x<180&&r.y<20&&r.width>40;}); b.click();});
  await page.waitForTimeout(900);
  if(!await page.evaluate(()=>!!document.querySelector('button[aria-label="新建画布"]'))) throw new Error('下拉没开');}
async function 删(目标){
  await 主页();
  const 行=page.locator(`[aria-label="切换到画布 ${目标}"]`).first();
  await 行.scrollIntoViewIfNeeded(); await page.waitForTimeout(400); const rb=await 行.boundingBox();
  await 行.hover(); await page.waitForTimeout(600);
  const mos=await page.evaluate(()=>[...document.querySelectorAll('button[aria-label="更多操作"]')]
    .map(e=>{const b=e.getBoundingClientRect();return {op:getComputedStyle(e).opacity,cx:Math.round(b.x+b.width/2),cy:Math.round(b.y+b.height/2)};}).filter(x=>x.op==='1'));
  if(mos.length!==1){T(`✗ ${目标} 不唯一(${mos.length})`);return false;}
  if(Math.abs(mos[0].cy-(rb.y+rb.height/2))>14){T(`✗ ${目标} 不同高`);return false;}
  await page.mouse.click(mos[0].cx,mos[0].cy); await page.waitForTimeout(800);
  const del=await page.evaluate(()=>[...document.querySelectorAll('div,button,li')]
    .filter(e=>e.innerText.trim()==='删除画布' && e.getBoundingClientRect().width>0)
    .map(e=>{const b=e.getBoundingClientRect();return [b.x+b.width/2,b.y+b.height/2];})[0]);
  if(!del){T(`✗ ${目标} 无删除项`);return false;}
  await page.mouse.click(del[0],del[1]); await page.waitForTimeout(1200);
  const 框=await page.evaluate(()=>{const c=document.querySelector('.mantine-Modal-content');
    return {text:(c.innerText||'').trim(), ok:[...c.querySelectorAll('button')].filter(b=>b.innerText.trim()==='确认')
      .map(b=>{const r=b.getBoundingClientRect();return [Math.round(r.x+r.width/2),Math.round(r.y+r.height/2)];})[0]};});
  if(!框.text.includes(`「${目标}」`)){T(`✗ ${目标} 确认框名字不符，放弃`); await page.keyboard.press('Escape'); return false;}
  await page.mouse.click(框.ok[0],框.ok[1]); await page.waitForTimeout(2500);
  await 主页(); const after=await 名单();
  T(`  ${目标}: ${after.includes(目标)?'❌ 还在':'✅ 已删'}，当前 ${after.length} 项`);
  return !after.includes(目标);
}
try { for (const t of ['GC-取证二','GC-空画布取证']) { T(`--- 删 ${t} ---`); try{await 删(t);}catch(e){T(' 异常:',e.message.slice(0,90));} }
  await 主页(); const m=await 名单();
  T('清理后:', m.length, '前3:', m.slice(0,3), '后2:', m.slice(-2));
  T('残留 GC:', m.filter(n=>n.includes('GC')));
} finally { await browser.close(); }
