// 批次 64 探测：点左栏「上传」**到底弹了什么**？
// 我假设「点上传 = 直接开系统文件选择器」，8 秒内 `filechooser` 事件没来。
// 🔑 又一次「阴性结果先问前置条件」：不是「上传坏了」，是**我对入口的假设没验证过**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const OUT = new URL('./_tmp-b64-probe.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const statusLine=()=>p.evaluate(()=>(document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/)||['?'])[0]);
const credit=()=>p.evaluate(()=>{const m=document.body.innerText.match(/(\d[\d,]*)\s*基础会员/);return m?m[1]:null;});
const snapshot=()=>p.evaluate(()=>{
  const vis=(e)=>{const r=e.getBoundingClientRect();return r.width>1&&r.height>1;};
  const pops=Array.from(document.querySelectorAll('[role="dialog"],[role="listbox"],[role="menu"],[data-testid*="upload"],[data-testid*="picker"],[data-testid*="menu"]'))
    .filter(vis).map(e=>{const r=e.getBoundingClientRect();
      return{tid:e.getAttribute('data-testid'),role:e.getAttribute('role'),box:`${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
        text:(e.innerText||'').replace(/\s+/g,' ').trim().slice(0,200),
        items:Array.from(e.querySelectorAll('[role="menuitem"],[role="option"],li,button')).filter(vis)
          .map(x=>{const q=x.getBoundingClientRect();return{aria:x.getAttribute('aria-label'),text:(x.innerText||'').replace(/\s+/g,' ').trim().slice(0,24),box:`${Math.round(q.width)}x${Math.round(q.height)}@${Math.round(q.x)},${Math.round(q.y)}`};}).slice(0,10)};});
  const inputs=Array.from(document.querySelectorAll('input[type=file]')).map(e=>{
    const r=e.getBoundingClientRect();return{cls:String(e.className||'').slice(0,30),box:`${Math.round(r.width)}x${Math.round(r.height)}`,multiple:e.multiple,accept:e.accept,vis:vis(e)};});
  const newTids=Array.from(new Set(Array.from(document.querySelectorAll('[data-testid]')).map(e=>e.getAttribute('data-testid'))))
    .filter(t=>/upload|import|file|drop|drag/i.test(t));
  return{pops,inputs,newTids,bodyHasUpload:/\u4e0a\u4f20|upload/i.test(document.body.innerText.slice(0,4000))};
});
const clickAt=async(x,y)=>{await p.mouse.click(x,y);};
console.log('=== 点「上传」前后对照 ===');
console.log('点前:', JSON.stringify(await snapshot(), null, 1).slice(0, 1200));
await clickAt(36, 563);
await p.waitForTimeout(2000);
const s1=await snapshot();
console.log('\n点后(2s):', JSON.stringify(s1, null, 1).slice(0, 2000));
console.log('\n状态:', await statusLine(), '| 积分', await credit());
// 如果弹了菜单，列出可点项并逐个试
if (s1.pops.length) {
  const items=s1.pops.flatMap(x=>x.items);
  console.log('\n弹层里的可点项:', JSON.stringify(items,null,1));
  for (const it of items) {
    const mm=it.box.match(/(\d+)x(\d+)@(-?\d+),(-?\d+)/);
    const w=Number(mm[1]),h=Number(mm[2]),ox=Number(mm[3]),oy=Number(mm[4]);
    const x=Math.round(ox+w/2),y=Math.round(oy+h/2);
    const land=await p.evaluate(([x,y])=>{const t=document.elementFromPoint(x,y);const o=t&&t.closest('button,[role="menuitem"],[role="option"]');
      return{tag:t&&t.tagName,aria:o&&o.getAttribute('aria-label'),text:o&&(o.innerText||'').trim().slice(0,20),ok:!!o};},[x,y]);
    console.log(`\n  点「${it.text||it.aria}」@(${x},${y}) 落点=${JSON.stringify(land)}`);
    const fc=p.waitForEvent('filechooser',{timeout:4000}).catch(()=>null);
    await clickAt(x,y);
    const ch=await fc;
    if (ch) { console.log('    ✅ filechooser 触发 | multiple =', ch.isMultiple()); break; }
    await p.waitForTimeout(1500);
    const s2=await snapshot();
    console.log('    未触发 filechooser；新弹层:', JSON.stringify(s2.pops.map(z=>({tid:z.tid,role:z.role,box:z.box,text:z.text.slice(0,120)}))));
    if (!s2.pops.length) { console.log('    弹层都没了'); break; }
  }
}
await p.keyboard.press('Escape'); await p.waitForTimeout(900);
for(let i=0;i<3;i++){await p.keyboard.press('Escape');await p.waitForTimeout(300);}
writeFileSync(OUT, JSON.stringify(await snapshot(),null,1));
console.log('\n终态:', await statusLine(), '| 积分', await credit());
console.log('写入', OUT.pathname);
await b.close();
