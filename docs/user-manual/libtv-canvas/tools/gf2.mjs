import { launch, open, closePromos } from './lib.mjs';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
try {
  await open(page,B); await closePromos(page);
  const inp=page.locator('input[aria-label="项目名称"]');
  T('刷新后 项目名:', JSON.stringify(await inp.inputValue()));
  T('标签页标题:', await page.title());
  T('节点数:', await page.locator('.react-flow__node').count());
  // 查清这个输入框到底是什么：读它的所有属性
  const 属性=await page.evaluate(()=>{
    const i=document.querySelector('input[aria-label="项目名称"]');
    if(!i) return null;
    const r=i.getBoundingClientRect();
    return {type:i.type, value:i.value, placeholder:i.placeholder, maxLength:i.maxLength,
      readOnly:i.readOnly, disabled:i.disabled, name:i.name, id:i.id,
      box:[r.x,r.y,r.width,r.height].map(Math.round),
      祖先:(()=>{let p=i, out=[]; for(let k=0;k<4&&p;k++){
        const cs=getComputedStyle(p); out.push({tag:p.tagName, cls:(p.className||'').toString().slice(0,90),
          contenteditable:p.getAttribute&&p.getAttribute('contenteditable')}); p=p.parentElement;} return out;})()};
  });
  T('输入框属性:', 属性);
  // ⭐ 试着改回去 —— 先试 fill（不带 clickCount:3）
  const net=[]; page.on('request',r=>{const u=r.url(); if(/api\/canvas\/project\/(update|rename)/.test(u)) net.push(r.method()+' '+u.replace('https://api.liblib.tv',''));});
  await inp.fill('未命名工作区');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(2500);
  T('改回后 值:', JSON.stringify(await inp.inputValue()));
  T('改名请求:', net);
  T('刷新复核…');
  await page.reload({waitUntil:'domcontentloaded'}); await page.waitForTimeout(3000); await closePromos(page);
  T('刷新后 项目名:', JSON.stringify(await page.locator('input[aria-label="项目名称"]').inputValue()));
} finally { await browser.close(); }
