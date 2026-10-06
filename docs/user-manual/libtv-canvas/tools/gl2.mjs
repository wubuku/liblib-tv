import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

// ⭐ 顶栏右侧逐个可点元素：框 + 落点自证 + 祖先链
const 顶栏 = () => {
  const R=(e)=>{const r=e.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
  return [...document.querySelectorAll('button,[role="button"],a,[onclick]')]
    .filter(e=>{const r=e.getBoundingClientRect();
      return r.y<50 && r.x>640 && r.width>4 && r.height>4
        && getComputedStyle(e).pointerEvents!=='none';})
    .map((b,i)=>{const r=b.getBoundingClientRect();
      const h=document.elementFromPoint(Math.round(r.x+r.width/2),Math.round(r.y+r.height/2));
      return {i, 框:R(b), 文字:(b.innerText||'').trim().replace(/\s+/g,' ').slice(0,14),
        aria:b.getAttribute('aria-label'), title:b.getAttribute('title'),
        tag:b.tagName,
        中心是自己:!!(h&&(h===b||b.contains(h))),
        落点:h?((h.innerText||h.getAttribute('aria-label')||h.tagName)||'').trim().slice(0,14):null};});
};

const 面板读 = (标) => {
  const R=(e)=>{const r=e.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
  const 抽屉=[...document.querySelectorAll('.mantine-Drawer-inner,.mantine-Drawer-content')]
    .map(e=>({cls:(e.className||'').toString().slice(0,30), 框:R(e), op:getComputedStyle(e).opacity,
      宽:e.getBoundingClientRect().width,
      文字:(e.innerText||'').trim().replace(/\s+/g,' ').slice(0,60)}))
    .filter(x=>x.宽>50);
  return {标, 抽屉, 尾文:document.body.innerText.replace(/\n{2,}/g,'\n').slice(-200)};
};

try {
  await open(page,B); await closePromos(page); await 稳();
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  const 清单 = await page.evaluate(顶栏);
  T('【顶栏可点元素清单】', JSON.stringify(清单,null,1).slice(0,3000));
  await page.screenshot({path:E('gl2-a-顶栏.png'), clip:{x:640,y:0,width:800,height:50}});
  T('【基准·无面板】', await page.evaluate(面板读,'基准'));

  // 只逐个点「资产管理」和「TV Director」两枚，⛔ 不碰头像/积分
  for (const 目标 of ['资产管理', 'TV Director']) {
    const btn = page.locator(`button:text-is("${目标}")`).first();
    const n = await btn.count();
    T(`按钮「${目标}」命中数:`, n);
    if (n !== 1) continue;
    await btn.click({timeout:5000}).catch(e=>T('  点失败', e.message.slice(0,50)));
    await page.waitForTimeout(2000);
    T(`【点「${目标}」之后】`, await page.evaluate(面板读, 目标));
    await page.screenshot({path:E(`gl2-b-点${目标}.png`)});
    await page.keyboard.press('Escape'); await page.waitForTimeout(1600);
    T(`【Esc 关掉「${目标}」】`, await page.evaluate(面板读, 目标+'后Esc'));
  }
} finally { await browser.close(); }
