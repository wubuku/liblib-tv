import { launch, open, closePromos } from './lib.mjs';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const 名单=()=>page.evaluate(()=>[...document.querySelectorAll('[aria-label^="切换到画布"]')].map(e=>e.getAttribute('aria-label').replace('切换到画布 ','')));
async function 主页(){ await open(page,B); await closePromos(page);
  await page.getByRole('button').filter({hasText:/^(?:画布|手册|.*副本\d*$)/}).first().click(); await page.waitForTimeout(900);
  if(!await page.evaluate(()=>!!document.querySelector('button[aria-label="新建画布"]'))) throw new Error('下拉没开');}
async function 点菜单(目标){ const 行=page.locator(`[aria-label="切换到画布 ${目标}"]`).first();
  await 行.scrollIntoViewIfNeeded(); await page.waitForTimeout(400); const rb=await 行.boundingBox();
  await 行.hover(); await page.waitForTimeout(600);
  const mos=await page.evaluate(()=>[...document.querySelectorAll('button[aria-label="更多操作"]')]
    .map(e=>{const b=e.getBoundingClientRect();return {op:getComputedStyle(e).opacity,cx:Math.round(b.x+b.width/2),cy:Math.round(b.y+b.height/2)};}).filter(x=>x.op==='1'));
  if(mos.length!==1){T(`  ✗ 不唯一(${mos.length})`);return false;}
  if(Math.abs(mos[0].cy-(rb.y+rb.height/2))>14){T('  ✗ 不同高');return false;}
  await page.mouse.click(mos[0].cx,mos[0].cy); await page.waitForTimeout(800); return true;}
async function 选菜单(字){ const m=await page.evaluate((z)=>[...document.querySelectorAll('div,button,li')]
    .filter(e=>e.innerText.trim()===z && e.getBoundingClientRect().width>0)
    .map(e=>{const b=e.getBoundingClientRect();return {box:[b.x,b.y,b.width,b.height].map(Math.round)};})
    .sort((a,b)=>a.box[2]*a.box[3]-b.box[2]*b.box[3])[0], 字);
  if(!m){T(`  ✗ 无「${字}」`);return false;}
  await page.mouse.click(m.box[0]+m.box[2]/2,m.box[1]+m.box[3]/2); await page.waitForTimeout(900); return true;}
// ⭐ 重命名边界：先测空名能不能提交
async function 改名(目标,新名){
  if(!await 点菜单(目标)) return null;
  if(!await 选菜单('重命名画布')) return null;
  const inp=page.locator('input[aria-label="画布名称"]');
  if(await inp.count()===0){ T('  ✗ 重命名后没有输入框'); return null; }
  await inp.fill(新名);
  if (新名==='') await page.keyboard.press('Enter'); else await page.keyboard.press('Enter');
  await page.waitForTimeout(2200);
  await 主页();
  return await 名单();
}
try {
  const net=[]; page.on('request',r=>{const u=r.url(); if(/project\/(update|copy|create)/.test(u)) net.push(r.method()+' '+u.replace('https://api.liblib.tv',''));});
  await 主页();
  // 1) 重命名为空
  T('--- 重命名为空 ---');
  let m = await 改名('手册取证画布副本1','');
  T('结果 名单前4:', m?m.slice(0,4):null, '网络:', net.splice(0));
  // 2) 重命名为纯空格
  T('--- 重命名为纯空格 ---');
  m = await 改名('手册取证画布副本1','   ');
  T('结果 名单前4:', m?m.slice(0,4):null, '网络:', net.splice(0));
  // 3) 复制一张副本本身，看名字怎么叠
  T('--- 复制「副本3」 ---');
  await 点菜单('手册取证画布副本3'); await 选菜单('复制画布'); await page.waitForTimeout(2500); await 主页();
  T('名单前6:', (await 名单()).slice(0,6)); T('网络:', net.splice(0));
} finally { await browser.close(); }
