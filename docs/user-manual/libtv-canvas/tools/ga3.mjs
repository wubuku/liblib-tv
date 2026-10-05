import { launch, open, closePromos } from './lib.mjs';

const MAIN = 'https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
try {
  await open(page, MAIN);
  await closePromos(page);
  await page.getByRole('button', { name: /^画布 \d+$/ }).first().click();
  await page.waitForTimeout(1000);

  const R = await page.evaluate(() => {
    const nb = document.querySelector('button[aria-label="新建画布"]');
    const sec = nb.closest('section');
    // 往上找第一个真正可滚动的祖先
    const 链=[]; let p=sec;
    for(let i=0;i<6&&p;i++){
      const cs=getComputedStyle(p); const b=p.getBoundingClientRect();
      链.push({i,tag:p.tagName,cls:(p.className||'').toString().slice(0,120),
        box:[b.x,b.y,b.width,b.height].map(Math.round), sh:p.scrollHeight, ch:p.clientHeight,
        ovY:cs.overflowY, maxH:cs.maxHeight, h:cs.height});
      p=p.parentElement;
    }
    // 更多操作按钮的可见性表达：非悬停行也要读
    const mos=[...document.querySelectorAll('button[aria-label="更多操作"]')];
    const 读=(e)=>{const b=e.getBoundingClientRect(); const cs=getComputedStyle(e);
      return {box:[b.x,b.y,b.width,b.height].map(Math.round), op:cs.opacity, vis:cs.visibility,
        disp:cs.display, pe:cs.pointerEvents, cls:(e.className||'').toString().slice(0,90)};};
    const 首 = mos[0], 次 = mos[1];
    return {链, mo总数: mos.length, 首行mo: 读(首), 次行mo: 读(次)};
  });
  console.log('祖先链:'); R.链.forEach(c=>console.log('  ',JSON.stringify(c)));
  console.log('更多操作总数', R.mo总数);
  console.log('首行 mo', JSON.stringify(R.首行mo));
  console.log('次行 mo', JSON.stringify(R.次行mo));

  // 悬停首行后再读一次
  await page.locator('[aria-label^="切换到画布"]').first().hover();
  await page.waitForTimeout(600);
  const H = await page.evaluate(()=>{
    const mo=[...document.querySelectorAll('button[aria-label="更多操作"]')];
    const 读=(e)=>{const cs=getComputedStyle(e);return {op:cs.opacity,vis:cs.visibility,pe:cs.pointerEvents};};
    return {首:读(mo[0]), 次:读(mo[1]), 第三:读(mo[2])};
  });
  console.log('悬停首行后:', JSON.stringify(H));
} finally { await browser.close(); }
