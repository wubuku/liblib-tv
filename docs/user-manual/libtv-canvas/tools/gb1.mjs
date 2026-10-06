import { launch, open, closePromos } from './lib.mjs';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const 名单=()=>page.evaluate(()=>[...document.querySelectorAll('[aria-label^="切换到画布"]')].map(e=>e.getAttribute('aria-label').replace('切换到画布 ','')));
async function 主页(){ await open(page,B); await closePromos(page);
  await page.getByRole('button',{name:/^(?:画布 \d+|.*)$/}).first().click(); await page.waitForTimeout(900);
  if(!await page.evaluate(()=>!!document.querySelector('button[aria-label="新建画布"]'))) throw new Error('下拉没开');}
// ⭐ GA-10 的正确判据：opacity:1 的唯一一枚，且中心与目标行中心差 ≤14px
async function 点菜单(目标){
  const 行=page.locator(`[aria-label="切换到画布 ${目标}"]`).first();
  await 行.scrollIntoViewIfNeeded(); await page.waitForTimeout(400);
  const rb=await 行.boundingBox();
  await 行.hover(); await page.waitForTimeout(600);
  const mos=await page.evaluate(()=>[...document.querySelectorAll('button[aria-label="更多操作"]')]
    .map(e=>{const b=e.getBoundingClientRect();return {op:getComputedStyle(e).opacity,cx:Math.round(b.x+b.width/2),cy:Math.round(b.y+b.height/2)};})
    .filter(x=>x.op==='1'));
  if(mos.length!==1){T(`  ✗ opacity=1 的不唯一(${mos.length})`);return false;}
  if(Math.abs(mos[0].cy-(rb.y+rb.height/2))>14){T(`  ✗ 亮的这枚与目标行不同高`);return false;}
  await page.mouse.click(mos[0].cx,mos[0].cy); await page.waitForTimeout(800);
  return true;
}
async function 选菜单(字){ const m=await page.evaluate((z)=>[...document.querySelectorAll('div,button,li')]
    .filter(e=>e.innerText.trim()===z && e.getBoundingClientRect().width>0)
    .map(e=>{const b=e.getBoundingClientRect();return {box:[b.x,b.y,b.width,b.height].map(Math.round)};})
    .sort((a,b)=>a.box[2]*a.box[3]-b.box[2]*b.box[3])[0], 字);
  if(!m){T(`  ✗ 菜单里没有「${字}」`);return false;}
  await page.mouse.click(m.box[0]+m.box[2]/2,m.box[1]+m.box[3]/2); await page.waitForTimeout(900); return true; }
try {
  const net=[]; page.on('request',r=>{const u=r.url(); if(/create-with-space|project\/(create|update|copy)/.test(u)) net.push(r.method()+' '+u.replace('https://api.liblib.tv',''));});
  // 源画布用「手册取证画布」（有内容），先复制两次看序号
  await 主页();
  const 源='手册取证画布';
  T('复制前名单前3:', (await 名单()).slice(0,3));
  for (let i=1;i<=3;i++){
    if(!await 点菜单(源)) break;
    if(!await 选菜单('复制画布')) break;
    await page.waitForTimeout(2500);
    await 主页();
    const m=await 名单();
    T(`第${i}次复制后 前5:`, m.slice(0,5));
    T(`  名单里含「${源}副本」的项:`, m.filter(n=>n.startsWith(源)));
    T(`  网络:`, net.splice(0));
  }
  // 顶栏现在显示什么
  T('顶栏:', await page.evaluate(()=>{const b=[...document.querySelectorAll('button')].find(x=>{const r=x.getBoundingClientRect();
    return r.x>160&&r.x<180&&r.y<20&&r.width>40;}); return b?b.innerText.trim():null;}));
} finally { await browser.close(); }
