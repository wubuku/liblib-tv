import { launch, open, closePromos } from './lib.mjs';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
try {
  await open(page,B); await closePromos(page);
  T('节点数:', await page.locator('.react-flow__node').count());
  const inp=page.locator('input[aria-label="项目名称"]');
  T('项目名输入框数:', await inp.count());
  if(await inp.count()){
    const b=await inp.boundingBox();
    T('框:', b, '当前值:', JSON.stringify(await inp.inputValue()));
    // ⭐ 按 Enter 提交会发生什么（换个名字）
    const net=[]; page.on('request',r=>{const u=r.url(); if(/project|space/.test(u)) net.push(r.method()+' '+u.replace('https://api.liblib.tv',''));});
    await inp.click({clickCount:3});
    await inp.fill('GF-项目名测试');
    await page.keyboard.press('Enter');
    await page.waitForTimeout(2500);
    T('改后 值:', JSON.stringify(await inp.inputValue()));
    T('网络:', net);
    T('URL:', await page.evaluate(()=>location.search));
    T('切换一张画布看看还在不在');
    await page.evaluate(()=>{const b=[...document.querySelectorAll('button')].find(x=>{const r=x.getBoundingClientRect();
      return r.x>160&&r.x<180&&r.y<20&&r.width>40;}); b.click();});
    await page.waitForTimeout(1000);
    await page.locator('[aria-label="切换到画布 画布 62"]').click(); await page.waitForTimeout(3000);
    T('切到画布62后 项目名:', JSON.stringify(await page.locator('input[aria-label="项目名称"]').inputValue()),
      '画布名:', await page.evaluate(()=>{const b=[...document.querySelectorAll('button')].find(x=>{const r=x.getBoundingClientRect();
      return r.x>160&&r.x<180&&r.y<20&&r.width>40;}); return b?b.innerText.trim():null;}));
  }
} finally { await browser.close(); }
