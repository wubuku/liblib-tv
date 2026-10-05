import { launch, open, closePromos } from './lib.mjs';

const MAIN = 'https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
try {
  await open(page, MAIN);
  await closePromos(page);
  await page.getByRole('button', { name: /^画布 \d+$/ }).first().click();
  await page.waitForTimeout(1000);

  // 1) 浮层内部直接子节点树：找滚动容器
  const 树 = await page.evaluate(()=>{
    const pop = document.querySelector('.mantine-Popover-dropdown');
    const walk=(el,d)=>{
      if(d>3) return null;
      return [...el.children].map(c=>{
        const cs=getComputedStyle(c); const b=c.getBoundingClientRect();
        const o={d,tag:c.tagName,cls:(c.className||'').toString().slice(0,110),
          box:[b.x,b.y,b.width,b.height].map(Math.round), sh:c.scrollHeight, ch:c.clientHeight,
          ovY:cs.overflowY, ovX:cs.overflowX, rows:c.querySelectorAll?.('[aria-label^="切换到画布"]').length||0};
        const kid=walk(c,d+1); return kid?{...o,kids:kid}:o;
      });
    };
    return walk(pop,0);
  });
  console.log('浮层子树:'); console.log(JSON.stringify(树,null,1).slice(0,2600));

  // 2) 滚轮能不能滚
  const 读位置 = ()=>page.evaluate(()=>{
    const rows=[...document.querySelectorAll('[aria-label^="切换到画布"]')];
    const r0=rows[0].getBoundingClientRect(), r20=rows[20].getBoundingClientRect(), rl=rows[rows.length-1].getBoundingClientRect();
    return {首行y:Math.round(r0.y), 第21行y:Math.round(r20.y), 末行y:Math.round(rl.y),
      面板: (()=>{const p=document.querySelector('.mantine-Popover-dropdown').getBoundingClientRect();return [p.x,p.y,p.width,p.height].map(Math.round);})(),
      首行可见: r0.top>46 && r0.bottom<320, 末行可见: rl.top>46 && rl.bottom<320};
  });
  T('滚轮前:', await 读位置());
  await page.mouse.move(272, 180);
  for (let i=0;i<6;i++){ await page.mouse.wheel(0, 200); await page.waitForTimeout(120); }
  await page.waitForTimeout(700);
  T('滚 6×200 后:', await 读位置());

  // 3) 键盘：方向键 / End / PageDown
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('ArrowDown');
  await page.waitForTimeout(500);
  T('两次 ArrowDown 后:', await 读位置());
} finally { await browser.close(); }
