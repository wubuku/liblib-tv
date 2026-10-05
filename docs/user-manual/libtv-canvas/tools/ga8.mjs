import { launch, open, closePromos, shot, shotHighlighted, injectHighlight } from './lib.mjs';
import { resolve, dirname } from 'node:path';
const HERE = resolve('tools');
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve(HERE,'.evidence',n);
async function 拍(clip){ return { clip, path: undefined }; }
const CLIP={x:150,y:38,width:250,height:300};
async function save(name){ await page.screenshot({path:E(name), clip:CLIP}); console.log('  拍',name); }
try {
  await open(page,B); await closePromos(page);
  await page.getByRole('button',{name:/^画布 \d+$/}).first().click(); await page.waitForTimeout(900);

  // 1 面板全貌（未悬停）
  await save('ga8-1-面板全貌.png');

  // 2 悬停第 3 行 → 更多操作显现
  await page.locator('[aria-label^="切换到画布"]').nth(2).hover();
  await page.waitForTimeout(700);
  const mo = await page.evaluate(()=>{
    const mos=[...document.querySelectorAll('button[aria-label="更多操作"]')];
    const on=mos.map((e,i)=>[i,getComputedStyle(e).opacity]).filter(([,o])=>o==='1');
    return {显现的序号: on};
  });
  T('悬停第3行后 opacity=1 的 mo:', mo);
  await save('ga8-2-更多操作显现.png');

  // 3 点加号 → 命名框
  await page.locator('button[aria-label="新建画布"]').click(); await page.waitForTimeout(1000);
  const inp = page.locator('input[aria-label="画布名称"]');
  T('命名框:', await inp.inputValue(), '全选:', await inp.evaluate(e=>e.selectionStart===0&&e.selectionEnd===e.value.length));
  await injectHighlight(page);
  await inp.evaluate(el=>window.canvasUserManualHighlight.show(el,{step:1}));
  await page.waitForTimeout(300);
  await page.screenshot({path:E('ga8-3-命名框.png'), clip:CLIP});
  console.log('  拍 ga8-3-命名框.png');
  await page.evaluate(()=>window.canvasUserManualHighlight.clear());
  // 3b 直接看是不是整行变成输入框
  const 行框 = await page.evaluate(()=>{
    const i=document.querySelector('input[aria-label="画布名称"]');
    const b=i.getBoundingClientRect();
    const row=i.closest('div.bg-canvas-controls-active');
    const rb=row.getBoundingClientRect();
    return {input:[b.x,b.y,b.width,b.height].map(Math.round), 行:[rb.x,rb.y,rb.width,rb.height].map(Math.round),
      同行还有别的元素: row.children.length};
  });
  T('命名框 vs 所在行:', 行框);

  // 4 改名 999 + Enter，再打开看列表
  await inp.fill('999'); await page.keyboard.press('Enter'); await page.waitForTimeout(2500);
  await page.getByRole('button',{name:/^画布 \d+$/}).first().click(); await page.waitForTimeout(900);
  T('列表前5:', await page.evaluate(()=>[...document.querySelectorAll('[aria-label^="切换到画布"]')].slice(0,5).map(e=>e.getAttribute('aria-label'))));
  await save('ga8-4-纯数字名列表.png');
} finally { await browser.close(); }
