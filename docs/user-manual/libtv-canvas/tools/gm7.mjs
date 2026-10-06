// GM-7：只截图，不拖任何东西 —— 两态底栏按钮对照 + 常驻提示条。
import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}
const 态 = () => page.evaluate(()=>{
  const b=document.querySelector('button[aria-label="移动"],button[aria-label="抓手工具"]');
  return b?{aria:b.getAttribute('aria-label'), 背景:getComputedStyle(b).backgroundColor}:null;});
try {
  await open(page,B); await closePromos(page); T('节点数', await 稳());
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);

  // 亮态：点一下按钮
  await page.locator('button[aria-label="移动"]').first().click(); await page.waitForTimeout(1600);
  T('亮态:', await 态());
  await page.screenshot({path:E('gm7-a-亮态底栏条.png'), clip:{x:556,y:652,width:300,height:88}});   // 提示条两行
  await page.screenshot({path:E('gm7-b-亮态底栏按钮.png'), clip:{x:556,y:744,width:300,height:56}}); // 底栏七枚

  // 灭态：按 H
  await page.keyboard.press('h'); await page.waitForTimeout(1500);
  T('灭态:', await 态());
  await page.screenshot({path:E('gm7-c-灭态底栏条.png'), clip:{x:556,y:652,width:300,height:88}});
  await page.screenshot({path:E('gm7-d-灭态底栏按钮.png'), clip:{x:556,y:744,width:300,height:56}});
  T('收尾节点数（必须 12）:', await page.locator('.react-flow__node').count());
} finally { await browser.close(); }
