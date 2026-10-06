import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
try {
  await open(page,B); await closePromos(page);
  const 读=async()=>({项目名: await page.evaluate(()=>document.querySelector('input[aria-label="项目名称"]')?.value),
    标题: await page.title(), 节点: await page.locator('.react-flow__node').count()});
  T('基线:', await 读());
  // 抓改名请求：这次只按方法+路径过滤
  const net=[]; page.on('request',r=>{const u=new URL(r.url());
    if(u.host.includes('api.liblib.tv') && /project|space/.test(u.pathname)) net.push(r.method()+' '+u.pathname);});
  const inp=page.locator('input[aria-label="项目名称"]');
  await inp.fill('GF-标题验证');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(2500);
  T('改后:', await 读());
  T('请求:', net);
  await page.screenshot({path:E('gf1-顶栏项目名已改.png'), clip:{x:0,y:0,width:520,height:44}});
  console.log('  拍 gf1');
  // 改回去
  net.splice(0);
  await inp.fill('未命名工作区');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(2500);
  T('改回后:', await 读());
  T('请求:', net);
  // ⭐ 测一下 blur（点别处）会不会提交
  net.splice(0);
  await inp.fill('GF-失焦测试');
  await page.mouse.click(700, 500);
  await page.waitForTimeout(2500);
  T('失焦后:', await 读());
  T('请求:', net);
  // 再改回去
  await inp.fill('未命名工作区');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(2500);
  T('最终:', await 读());
} finally { await browser.close(); }
