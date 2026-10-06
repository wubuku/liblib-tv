import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const MAIN='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
const 建过的=[];
async function 稳定(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}
async function 新空画布(名){ await open(page,MAIN); await closePromos(page);
  await page.evaluate(()=>{const b=[...document.querySelectorAll('button')].find(x=>{const r=x.getBoundingClientRect();
    return r.x>160&&r.x<180&&r.y<20&&r.width>40;}); b.click();});
  await page.waitForTimeout(900);
  await page.locator('button[aria-label="新建画布"]').click(); await page.waitForTimeout(900);
  await page.locator('input[aria-label="画布名称"]').fill(名);
  await page.keyboard.press('Enter'); await page.waitForTimeout(3200);
  const pid=await page.evaluate(()=>(location.search.match(/projectId=(\w+)/)||[])[1]);
  建过的.push({名, pid});
  // ⭐ 只关**看得见**的那枚关闭键（DOM 里还有不可见的同 aria 按钮，缺陷 507 同族）
  const 关掉了 = await page.evaluate(()=>{
    const bs=[...document.querySelectorAll('button[aria-label="关闭"]')]
      .filter(b=>{const r=b.getBoundingClientRect(); return r.width>0&&r.height>0;});
    if(!bs.length) return false; bs[bs.length-1].click(); return true; });
  T('  抽屉可见=', await page.evaluate(()=>{const d=document.querySelector('.chat-welcome-root');
    return d?(()=>{const q=d.getBoundingClientRect();return q.width>0&&q.height>0;})():null;}),
    '点了关闭=', 关掉了);
  await page.waitForTimeout(1600);
  await 稳定();
  return pid;}
try {
  const 结果=[];
  for (const w of ['图片生成','视频生成','音频生成','剧本生成','智能剪辑']) {
    await 新空画布(`GD-${w}`);
    const b=page.locator('button').filter({hasText:new RegExp(`^${w}$`)}).first();
    if(await b.count()===0){ T(`${w}: 芯片不存在`); continue; }
    const 证=await b.evaluate(el=>{const r=el.getBoundingClientRect();
      const hit=document.elementFromPoint(Math.round(r.x+r.width/2),Math.round(r.y+r.height/2));
      return {属主:(hit.innerText||hit.tagName).trim().slice(0,16), 是芯片: el.contains(hit)||hit===el};});
    T(`${w} 落点:`, 证);
    if(!证.是芯片){ 结果.push({w, 被挡:true, 证}); continue; }
    await b.click(); await page.waitForTimeout(2800);
    const n=await 稳定();
    const info=await page.evaluate(()=>{const ns=[...document.querySelectorAll('.react-flow__node')];
      const last=ns[ns.length-1];
      return {总数:ns.length, 类型:(last.className||'').match(/react-flow__node-([a-z0-9-]+)/)?.[1],
        标题:(last.innerText||'').trim().split('\n')[0],
        框:(()=>{const r=last.getBoundingClientRect();return [r.x,r.y,r.width,r.height].map(Math.round);})()};});
    T(`  → 建出:`, info);
    结果.push({w, ...info});
    // 第 1、4 枚拍图
    if(w==='视频生成'||w==='剧本生成'){
      await page.screenshot({path:E(`gd2-${w}.png`), clip:{x:Math.max(0,info.框[0]-60),y:Math.max(0,info.框[1]-60),
        width:Math.min(700,info.框[2]+120),height:Math.min(470,info.框[3]+120)}});
      console.log(`  拍 gd2-${w}`);
    }
  }
  T('⭐ 汇总:', 结果);
  T('⭐ 建过的画布（待清理）:', 建过的.map(x=>x.名));
} finally { await browser.close(); }
