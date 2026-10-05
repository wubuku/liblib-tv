import { launch, open, closePromos } from './lib.mjs';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const 行名 = ()=>page.evaluate(()=>[...document.querySelectorAll('[aria-label^="切换到画布"]')].map(e=>e.getAttribute('aria-label').replace('切换到画布 ','')));
try {
  await open(page,B); await closePromos(page);
  await page.getByRole('button',{name:/^(?:画布 \d+|999|GA-[^0-9]*)$/}).first().click(); await page.waitForTimeout(1000);
  const before = await 行名();
  T('清理前总数:', before.length, '前6:', before.slice(0,6));
  const target='画布 64';
  const i = before.indexOf(target);
  T('目标索引', i);
  const 行 = page.locator(`[aria-label="切换到画布 ${target}"]`).first();
  await 行.scrollIntoViewIfNeeded(); await page.waitForTimeout(400);
  const rb = await 行.boundingBox(); T('行框', [rb.x,rb.y,rb.width,rb.height].map(Math.round));
  await 行.hover(); await page.waitForTimeout(700);
  // ⭐ 只认**唯一** opacity=1 的那一枚，且必须与目标行同高
  const mos = await page.evaluate((y)=>[...document.querySelectorAll('button[aria-label="更多操作"]')]
    .map((e,i)=>{const b=e.getBoundingClientRect();return {i, op:getComputedStyle(e).opacity,
      cx:Math.round(b.x+b.width/2), cy:Math.round(b.y+b.height/2), y:Math.round(b.y)};})
    .filter(x=>x.op==='1'), rb.y);
  T('opacity=1 的 mo:', mos);
  if(mos.length!==1){ T('✗ opacity=1 的不唯一，中止'); process.exit(1); }
  const m=mos[0];
  if(Math.abs(m.cy-(rb.y+rb.height/2))>14){ T(`✗ 亮的这枚与目标行不同高：mo.cy=${m.cy} 行心=${rb.y+rb.height/2}，中止`); process.exit(1); }
  const 属主 = await page.evaluate(([x,y])=>{const e=document.elementFromPoint(x,y);return e?(e.getAttribute('aria-label')||e.tagName):null;},[m.cx,m.cy]);
  T('落点自证 =', 属主);
  if(属主!=='更多操作'){ T('✗ 落点不对，中止'); process.exit(1); }
  await page.mouse.click(m.cx, m.cy);   // ⭐ 只走这一条，不再有 nth(0) fallback
  await page.waitForTimeout(900);
  const 菜单 = await page.evaluate(()=>[...document.querySelectorAll('div,button,li')].filter(e=>
      /^(在新窗口打开|重命名画布|复制画布|删除画布)$/.test((e.innerText||'').trim()) && e.getBoundingClientRect().width>0)
    .map(e=>{const b=e.getBoundingClientRect();return {t:e.innerText.trim(),box:[b.x,b.y,b.width,b.height].map(Math.round)};})
    .sort((a,b)=>a.box[2]*a.box[3]-b.box[2]*b.box[3]).slice(0,4));
  T('菜单:', 菜单);
  const del=菜单.find(x=>x.t==='删除画布');
  await page.mouse.click(del.box[0]+del.box[2]/2, del.box[1]+del.box[3]/2);
  await page.waitForTimeout(1300);
  const 框 = await page.evaluate(()=>{const c=document.querySelector('.mantine-Modal-content');
    return {text:(c.innerText||'').trim(), btns:[...c.querySelectorAll('button')].map(e=>{const r=e.getBoundingClientRect();
      return {t:e.innerText.trim(),box:[r.x,r.y,r.width,r.height].map(Math.round)};})};});
  T('确认框:', 框);
  T('⭐ 确认框名字是否就是目标：', 框.text.includes(`「${target}」`) ? '✅ 是' : `❌ 不是（框里写的是别的名字）`);
  const ok=框.btns.find(x=>x.t==='确认');
  const cxp=ok.box[0]+ok.box[2]/2, cyp=ok.box[1]+ok.box[3]/2;
  const 自证=await page.evaluate(([x,y])=>{const e=document.elementFromPoint(x,y);return e?(e.innerText||'').trim():null;},[cxp,cyp]);
  T('确认落点自证 =', 自证);
  await page.mouse.click(cxp,cyp); await page.waitForTimeout(2500);
  await open(page,B); await closePromos(page);
  await page.getByRole('button',{name:/^(?:画布 \d+|999)$/}).first().click(); await page.waitForTimeout(900);
  const after=await 行名();
  T('删除后总数:', after.length, '前5:', after.slice(0,5), '后3:', after.slice(-3));
} finally { await browser.close(); }
