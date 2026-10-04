// Batch EF-11：EF-10 证实整张卡的 innerText 里**含「当前使用」**（栈[4][5] 都读到了），
// 但探针落点偏到了卡名那行，没取到徽标本身。
//
// 本步最简单可靠：**在广场里枚举所有含「当前使用」的元素**，
// 不管它是什么标签、不管背景色，把全部读数打出来。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchEF11.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));

const 结果 = { 读数: {} };
const 目标ID = 'i-sODTbgLUm1';

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6500 });
  await closePromos(page);
  await page.waitForTimeout(1200);
  await page.evaluate(() => { for (const b of document.querySelectorAll('button')) if ((b.innerText || '').trim() === '知道了') { b.click(); return; } });
  await page.waitForTimeout(600);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1500);

  const 标题 = await page.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    const t = [...n.querySelectorAll('*')].find(e => /图片节点/.test(e.innerText || '') && e.children.length === 0);
    const r = (t || n).getBoundingClientRect();
    return [r.left + r.width / 2, r.top + r.height / 2];
  }, 目标ID);
  await page.mouse.click(标题[0], 标题[1]);
  await page.waitForTimeout(1500);
  await page.evaluate(() => {
    const 编辑器 = [...document.querySelectorAll('div')].find(e => {
      const r = e.getBoundingClientRect(); const t = e.innerText || '';
      if (r.width < 250 || r.height < 150) return false;
      if (!/参考/.test(t) || !/Lib Image/.test(t)) return false;
      for (const c of e.children) { const cr = c.getBoundingClientRect(); if (cr.width >= 250 && cr.height >= 150 && /参考/.test(c.innerText || '')) return false; }
      return true;
    });
    if (!编辑器) return;
    for (const 文 of ['替换', '风格']) {
      const el = [...编辑器.querySelectorAll('*')].find(e => e.children.length === 0 && (e.innerText || '').trim() === 文);
      if (el) { el.click(); return; }
    }
  });
  await page.waitForTimeout(3000);

  // ⭐ 广场里所有 innerText 含「当前使用」的元素，从外到内全列
  const 全部 = await page.evaluate(() => {
    const 广场 = [...document.querySelectorAll('.mantine-Modal-content, .mantine-Drawer-content')]
      .find(e => /风格广场|我的收藏|最近使用/.test(e.innerText || ''));
    if (!广场) return { 错: '广场没开' };
    const out = [];
    for (const e of 广场.querySelectorAll('*')) {
      const t = (e.innerText || '');
      if (!t.includes('当前使用')) continue;
      const r = e.getBoundingClientRect();
      const cs = getComputedStyle(e);
      const 卡 = e.closest('[class*="group"]');
      out.push({
        tag: e.tagName,
        自身文字: e.children.length === 0 ? t.trim() : `(${e.children.length} 个子元素)`,
        bg: cs.backgroundColor, color: cs.color, fontSize: cs.fontSize,
        圆角: cs.borderRadius, padding: cs.padding, 边框: cs.boxShadow.slice(0, 40),
        box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        在卡内: !!卡,
        卡名: (卡?.innerText || '').split('\n').filter(Boolean).slice(0, 2).join(' / '),
        cls: e.className.toString().slice(0, 140),
        html: e.outerHTML.slice(0, 320),
      });
    }
    return { 命中数: out.length, 全部: out };
  });
  结果.读数.全部 = 全部;

  if (全部.错) { console.log('  ', 全部.错); }
  else {
    console.log('═══ 广场里含「当前使用」的元素:', 全部.命中数, '个 ═══');
    // ⭐ 从最小的开始 —— 最小那个才是徽标本身
    const 按大小 = [...全部.全部].sort((a, b) => (a.box[2] * a.box[3]) - (b.box[2] * b.box[3]));
    for (const e of 按大小.slice(0, 5)) {
      console.log(`\n  <${e.tag}> 自身="${e.自身文字}"`);
      console.log(`    bg=${e.bg} color=${e.color} 字号=${e.fontSize}`);
      console.log(`    圆角=${e.圆角} padding=${e.padding} box=${JSON.stringify(e.box)}`);
      console.log(`    卡名=${e.卡名.slice(0, 40)}`);
      console.log(`    cls=${e.cls}`);
      console.log(`    html=${e.html.slice(0, 260)}`);
    }
  }
  await page.screenshot({ path: '.evidence/batchEF11-当前使用徽标最终读数.png' });
  落盘(结果);
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEF11.json ===');
}
