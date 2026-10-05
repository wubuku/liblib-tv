import { launch, open, closePromos, 读当前zoom } from './lib.mjs';

const MAIN = 'https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const 读 = ()=>page.evaluate(()=>{
  const rows=[...document.querySelectorAll('[aria-label^="切换到画布"]')];
  const sr=document.querySelector('.generator-prompt-scroll-region');
  const rl=rows[rows.length-1].getBoundingClientRect();
  const r0=rows[0].getBoundingClientRect();
  return {行数:rows.length, scrollTop: sr?Math.round(sr.scrollTop):null,
    首行y:Math.round(r0.y), 末行名:rows[rows.length-1].getAttribute('aria-label'),
    末行y:Math.round(rl.y), 末行完全可见: rl.top>=91 && rl.bottom<=311,
    末行部分可见: rl.bottom>91 && rl.top<311};
});
try {
  await open(page, MAIN);
  await closePromos(page);
  await page.getByRole('button', { name: /^画布 \d+$/ }).first().click();
  await page.waitForTimeout(1000);
  const z0 = await 读当前zoom(page);
  T('基线:', await 读()); T('zoom 基线:', z0);

  await page.mouse.move(272, 180);
  // 往下滚到底
  for (let i=0;i<12;i++){ await page.mouse.wheel(0, 400); await page.waitForTimeout(90); }
  await page.waitForTimeout(800);
  T('滚到底(12×400):', await 读());
  T('zoom 滚后:', await 读当前zoom(page));
  // 再往下滚 3 次看有没有边界
  for (let i=0;i<3;i++){ await page.mouse.wheel(0, 400); await page.waitForTimeout(120); }
  await page.waitForTimeout(600);
  T('再滚 3×400:', await 读());
  // 往上滚过头
  for (let i=0;i<15;i++){ await page.mouse.wheel(0, -400); await page.waitForTimeout(70); }
  await page.waitForTimeout(600);
  T('往上滚过头(15×-400):', await 读());

  // ==== 新建命名浮层：只读 + ESC ====
  const before = await page.evaluate(()=>document.querySelectorAll('[aria-label^="切换到画布"]').length);
  await page.locator('button[aria-label="新建画布"]').click();
  await page.waitForTimeout(1200);
  const 浮层 = await page.evaluate(()=>{
    const inp=document.querySelector('input[aria-label="画布名称"]');
    if(!inp) return {err:'没有画布名称 input'};
    // 找浮层根
    let p=inp; const 链=[];
    for(let i=0;i<8&&p;i++){ const b=p.getBoundingClientRect(); const cs=getComputedStyle(p);
      链.push({i,tag:p.tagName,cls:(p.className||'').toString().slice(0,110),
        box:[b.x,b.y,b.width,b.height].map(Math.round), z:cs.zIndex, pos:cs.position, role:p.getAttribute('role')});
      p=p.parentElement; }
    const ib=inp.getBoundingClientRect();
    // 浮层范围内所有可交互元素
    const root=链.find(c=>/Popover|Modal|Dialog|absolute|fixed/.test(c.cls))?.i ?? 3;
    const btns=[...document.querySelectorAll('button')].filter(b=>{
      const bb=b.getBoundingClientRect();
      return bb.width>0&&bb.height>0&&bb.top<400&&bb.left>150&&bb.left<520&&bb.top>0&&bb.top<200
        && /确认|取消|新建|创建|保存|关闭|×/.test((b.getAttribute('aria-label')||'')+(b.innerText||''));
    }).map(b=>{const bb=b.getBoundingClientRect();return {aria:b.getAttribute('aria-label'),t:(b.innerText||'').trim().slice(0,14),box:[bb.x,bb.y,bb.width,bb.height].map(Math.round)};});
    return {input:{value:inp.value, box:[ib.x,ib.y,ib.width,ib.height].map(Math.round),
      全选:inp.selectionStart===0&&inp.selectionEnd===inp.value.length, selS:inp.selectionStart, selE:inp.selectionEnd,
      maxLength:inp.maxLength, placeholder:inp.placeholder, focused:document.activeElement===inp},
      链, 附近按钮:btns};
  });
  console.log('命名浮层:', JSON.stringify(浮层,null,1).slice(0,2200));
  await page.keyboard.press('Escape');
  await page.waitForTimeout(1500);
  const after = await page.evaluate(()=>({
    行数: document.querySelectorAll('[aria-label^="切换到画布"]').length,
    有input: !!document.querySelector('input[aria-label="画布名称"]'),
    顶栏: [...document.querySelectorAll('button')].find(b=>/^画布 \d+$/.test((b.innerText||'').trim()))?.innerText.trim(),
    url: location.search
  }));
  T('ESC 前行数:', before); T('ESC 后:', after);
} finally { await browser.close(); }
