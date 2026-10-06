import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const MAIN='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳定(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}
async function 建空画布(名){ await open(page,MAIN); await closePromos(page);
  await page.evaluate(()=>{const b=[...document.querySelectorAll('button')].find(x=>{const r=x.getBoundingClientRect();
    return r.x>160&&r.x<180&&r.y<20&&r.width>40;}); b.click();});
  await page.waitForTimeout(900);
  await page.locator('button[aria-label="新建画布"]').click(); await page.waitForTimeout(900);
  await page.locator('input[aria-label="画布名称"]').fill(名);
  await page.keyboard.press('Enter'); await page.waitForTimeout(3200);
  const pid=await page.evaluate(()=>(location.search.match(/projectId=(\w+)/)||[])[1]);
  // 关抽屉，保证 5 枚都可点
  const 抽=await page.evaluate(()=>!!document.querySelector('.chat-welcome-root'));
  if(抽) await page.locator('button[aria-label="关闭"]').last().click();
  await page.waitForTimeout(1500);
  return {pid, 节点: await 稳定()};
}
const 芯片=(w)=>page.locator('button').filter({hasText:new RegExp(`^${w}$`)}).first();
try {
  const 建 = await 建空画布('GD-取证');
  T('空画布:', 建);
  // 1) 先在**没点任何芯片**时，看芯片排里有没有副标题/描述文字
  const 排=await page.evaluate(()=>{
    const b=[...document.querySelectorAll('button')].find(e=>e.innerText.trim()==='图片生成');
    if(!b) return null;
    const r=b.getBoundingClientRect();
    return {框:[r.x,r.y,r.width,r.height].map(Math.round), 全文:(b.innerText||'').trim(),
      子元素数:b.children.length,
      结构:[...b.children].map(c=>({tag:c.tagName, cls:(c.className||'').toString().slice(0,70),
        t:(c.innerText||'').trim().slice(0,30),
        box:(()=>{const q=c.getBoundingClientRect();return [q.x,q.y,q.width,q.height].map(Math.round);})()}))};
  });
  T('芯片1 结构:', 排);
  // 2) 逐枚点，建出 5 个节点，记录类型和标题
  const 结果=[];
  for (const w of ['图片生成','视频生成','音频生成','剧本生成','智能剪辑']) {
    const b=芯片(w);
    if(await b.count()===0){ T(`${w}: 找不到（芯片可能已消失）`); 结果.push({w, 找不到:true}); break; }
    // 落点自证
    const 证=await b.evaluate(el=>{const r=el.getBoundingClientRect();
      const hit=document.elementFromPoint(Math.round(r.x+r.width/2),Math.round(r.y+r.height/2));
      return {属主:(hit.innerText||hit.tagName).trim().slice(0,20), 是芯片: el.contains(hit)||hit===el};});
    if(!证.是芯片){ T(`✗ ${w} 落点被挡（属主=${证.属主}）`); 结果.push({w, 被挡:true, 证}); continue; }
    await b.click(); await page.waitForTimeout(2600);
    const n=await 稳定();
    const info=await page.evaluate((c)=>{const ns=[...document.querySelectorAll('.react-flow__node')];
      const last=ns[ns.length-1];
      return {总数:ns.length, 最新类型:(last.className||'').match(/react-flow__node-([a-z0-9-]+)/)?.[1],
        最新标题:(last.innerText||'').trim().split('\n')[0], 框:(()=>{const r=last.getBoundingClientRect();return [r.x,r.y,r.width,r.height].map(Math.round);})()};}, n);
    T(`点「${w}」后:`, info);
    结果.push({w, ...info});
  }
  T('汇总:', 结果);
  // 拍全貌：5 个节点都在画布上
  await page.screenshot({path:E('gd1-芯片建出五个节点.png'), clip:{x:140,y:120,width:1160,height:520}});
  console.log('  拍 gd1');
  T('可清理画布: GD-取证', 建.pid);
} finally { await browser.close(); }
