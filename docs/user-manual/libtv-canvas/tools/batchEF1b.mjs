// Batch EF-1b：EF-1 的「当前使用」命中是 <body>（无文本、box 铺满视口）—— 那是假阳性。
//
// ⭐ EF-1 的判据缺陷：向上找「第一个有背景色的祖先」爬得太高，一路爬到 <body>
//    （body 有背景色 rgb(20,20,20)）⇒ 任何页面都能「命中」，等于没判据。
//    正确做法：**只认文本节点自身的直接父级**，且要求它**尺寸小、真的在某个节点卡里**。
//
// 本步：精确定位「当前使用」在页面里的**真实位置**，
//   区分「真徽标」vs「藏在 i18n 注水数据里的文案」。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchEF1b.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));

const 结果 = {};

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6000 });
  await closePromos(page);
  await page.waitForTimeout(1000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1600);

  // ⭐ 只认「文本节点的直接父级」，不往上爬
  const 精确定位 = await page.evaluate(() => {
    const out = [];
    const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = w.nextNode())) {
      const txt = (n.nodeValue || '').trim();
      if (!txt.includes('当前使用')) continue;
      const p = n.parentElement;
      const r = p.getBoundingClientRect();
      const cs = getComputedStyle(p);
      // ⭐ 祖先链上有没有 .react-flow__node / 大编辑器容器
      const inNode = !!p.closest('.react-flow__node');
      const inModal = !!p.closest('.mantine-Modal-content, .mantine-Drawer-content');
      // 祖先链上有没有 hidden / style=display:none
      const chain = [];
      for (let e = p; e && e !== document.body; e = e.parentElement) {
        const s = e.getAttribute && e.getAttribute('style');
        if (e.hasAttribute && e.hasAttribute('hidden')) chain.push(`${e.tagName}[hidden]`);
        if (s && /display:\s*none/.test(s)) chain.push(`${e.tagName}{display:none}`);
        if (e.className && typeof e.className === 'string' && /hidden|invisible/.test(e.className))
          chain.push(`${e.tagName}.hidden`);
      }
      out.push({
        文本: txt,
        片段: txt.length > 60 ? txt.slice(0, 60) + '…' : txt,
        tag: p.tagName,
        className: p.className.toString().slice(0, 80),
        box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        在节点卡里: inNode, 在模态里: inModal,
        被隐藏的祖先: chain,
        祖先链: (() => {
          const c = []; for (let e = p; e && e !== document.body; e = e.parentElement) c.push(e.tagName + '.' + (typeof e.className === 'string' ? e.className.split(' ')[0] : ''));
          return c.slice(0, 8);
        })(),
      });
    }
    return out;
  });
  结果.精确命中 = 精确定位;
  console.log('═══ 「当前使用」精确命中', 精确定位.length, '处 ═══');
  for (const h of 精确定位) {
    console.log(`\n  文本片段: ${JSON.stringify(h.片段)}`);
    console.log(`  tag=${h.tag} cls=${h.className}`);
    console.log(`  box=${JSON.stringify(h.box)}  在节点卡里=${h.在节点卡里}  在模态里=${h.在模态里}`);
    console.log(`  被隐藏的祖先=${JSON.stringify(h.被隐藏的祖先)}`);
    console.log(`  祖先链=${JSON.stringify(h.祖先链)}`);
  }
  落盘(结果);

  // ⭐ 阳性对照：找一个**确实可见**的界面文案，确认这套定位方法本身有效
  const 阳性 = await page.evaluate(() => {
    const out = [];
    for (const kw of ['资产管理', '适合屏幕', '视频节点', '图片节点']) {
      const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      let n, 找到 = null;
      while ((n = w.nextNode())) {
        const t = (n.nodeValue || '').trim();
        if (t !== kw) continue;
        const p = n.parentElement, r = p.getBoundingClientRect();
        if (r.width > 0 && r.height > 0) { 找到 = { kw, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] }; break; }
      }
      out.push(找到 || { kw, 找到: false });
    }
    return out;
  });
  结果.阳性对照 = 阳性;
  console.log('\n═══ ⭐ 阳性对照（确认定位方法有效）═══');
  for (const p of 阳性) console.log('  ', JSON.stringify(p));
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEF1b.json ===');
}
