// Batch EW-3：⭐⭐ 「新功能：支持真人」归属定位 —— 改用**差分法**，不猜面板长什么样。
//
// EW-2 判据缺陷：用「宽度 200~460 + 贴右缘 + 高 >120」去找参数面板，**读到 0 个**。
//   节点明明选中了（落点自证 `正确: true`），面板却没被找到。
//   ⭐ **读到 0 先怀疑判据** —— 我对「面板长什么样」的几条假设全是我编的。
//
// 本轮做法：**前后差分**。
//   点节点之前先把全页元素的「标签 + 矩形 + 文字」签名存一份，
//   点之后再存一份，**只把新出现的元素列出来**。面板必然在新增列表里，
//   完全不需要我预先知道它的宽度、位置、class。
//
// 然后：找到面板左缘那一列，定位「新功能：支持真人」那个元素，
// 再看它**左邻 / 右邻 / 上下**都有谁 —— 归属就出来了。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEW3.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

/** 全页签名：标签 + 位置 + 文字头。用来做差分。 */
const 签名 = (page) => page.evaluate(() => {
  const o = {};
  let n = 0;
  for (const e of document.querySelectorAll('body *')) {
    const r = e.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    if (r.right < 0 || r.left > innerWidth || r.bottom < 0 || r.top > innerHeight) continue;
    n += 1;
    o['e' + n] = [e.tagName, Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height), (e.innerText || '').trim().slice(0, 40)];
  }
  return { o, n };
});

const browser = await launch();
const page = browser.page;
try {
  await open(page, CANVAS_URL);
  await closePromos(page);
  await page.waitForTimeout(4000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));

  const 前 = await 签名(page);
  记('点之前可见元素数：' + 前.n);

  // ════════ 选中视频节点 ════════
  const 点 = await page.evaluate((id) => {
    const el = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return [Math.round(r.left + r.width / 2), Math.round(r.top + 18)];
  }, 'v-v2hlWY4Br3');
  const 验 = await page.evaluate(([x, y, id]) => {
    const n = document.elementFromPoint(x, y)?.closest('.react-flow__node');
    return n ? n.getAttribute('data-id') : null;
  }, [点[0], 点[1], 'v-v2hlWY4Br3']);
  记('落点自证：' + 验);
  if (验 !== 'v-v2hlWY4Br3') throw new Error('落点不对');
  await page.mouse.click(点[0], 点[1]);
  await page.waitForTimeout(3000);

  const 后 = await 签名(page);
  记('点之后可见元素数：' + 后.n);

  // ════════ 差分：新增的元素 ════════
  const 新增 = [];
  for (const k of Object.keys(后.o)) {
    if (!(k in 前.o)) 新增.push(后.o[k]);
  }
  const 消失 = [];
  for (const k of Object.keys(前.o)) {
    if (!(k in 后.o)) 消失.push(前.o[k]);
  }
  记('⭐ 新增 ' + 新增.length + ' 个 / 消失 ' + 消失.length + ' 个');
  记('新增明细：' + JSON.stringify(新增, null, 1));
  结果.读数.新增 = 新增;
  结果.读数.消失 = 消失;

  // ════════ 找面板：新增里「面积最大、且贴右缘」的那个 ════════
  const 面板候选 = 新增.filter((x) => x[2] >= 140 && x[3] >= 100)
    .sort((a, b) => (b[2] * b[3]) - (a[2] * a[3]));
  记('面板候选（宽>140 高>100 的新增）：' + JSON.stringify(面板候选.slice(0, 8)));
  结果.读数.面板候选 = 面板候选;

  // ════════ ⭐ 直接找「新功能：支持真人」那个元素（面板已开，这次该有了）════════
  const 找字 = await page.evaluate(() => {
    const 命中 = [];
    for (const e of document.querySelectorAll('*')) {
      const t = (e.innerText || '').trim();
      if (!t || t.length > 60) continue;
      if (!/新功能|真人/.test(t)) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) continue;
      if (r.right < 0 || r.left > innerWidth) continue;
      const cs = getComputedStyle(e);
      命中.push({
        标签: e.tagName, 文字: t, 子数: e.children.length,
        cls: String(e.className).slice(0, 110),
        box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        opacity: cs.opacity, pointerEvents: cs.pointerEvents, zIndex: cs.zIndex, position: cs.position,
        祖先链: (() => {
          const a = []; let p = e.parentElement, i = 0;
          while (p && i < 8) {
            const r2 = p.getBoundingClientRect();
            a.push({ t: p.tagName, c: String(p.className).slice(0, 50), box: [Math.round(r2.left), Math.round(r2.top), Math.round(r2.width), Math.round(r2.height)], 子: p.children.length });
            p = p.parentElement; i += 1;
          }
          return a;
        })(),
        兄弟: (() => {
          const 出 = [];
          const par = e.parentElement;
          if (!par) return 出;
          for (const s of par.children) {
            if (s === e) continue;
            const r3 = s.getBoundingClientRect();
            if (r3.width < 2 || r3.height < 2) continue;
            出.push({ t: s.tagName, c: String(s.className).slice(0, 46), 文字: (s.innerText || '').trim().slice(0, 30), box: [Math.round(r3.left), Math.round(r3.top), Math.round(r3.width), Math.round(r3.height)] });
          }
          return 出;
        })(),
        邻居: (() => {
          // ⭐ 按几何找：与它「竖直重叠且水平最近」的元素，最可能是它的触发者/容器
          const r4 = e.getBoundingClientRect();
          const 近 = [];
          for (const s of document.querySelectorAll('body *')) {
            if (s === e) continue;
            const r5 = s.getBoundingClientRect();
            if (r5.width < 6 || r5.height < 6) continue;
            const v重叠 = Math.min(r4.bottom, r5.bottom) - Math.max(r4.top, r5.top);
            if (v重叠 <= 0) continue;
            if (s.contains(e) || e.contains(s)) continue;
            const 水平距 = Math.min(Math.abs(r4.left - r5.right), Math.abs(r5.left - r4.right));
            近.push({ 水平距: Math.round(水平距), t: s.tagName, c: String(s.className).slice(0, 50), 文字: (s.innerText || '').trim().slice(0, 30), box: [Math.round(r5.left), Math.round(r5.top), Math.round(r5.width), Math.round(r5.height)] });
          }
          近.sort((a, b) => a.水平距 - b.水平距);
          return 近.slice(0, 8);
        })(),
      });
    }
    return 命中;
  });
  记('⭐ 含「新功能/真人」的元素：' + JSON.stringify(找字, null, 1));
  结果.读数.找字 = 找字;

  await page.screenshot({ path: EVID + 'ew3-面板左缘.png' });
  记('已拍 ew3-面板左缘.png');

  // ════════ 收尾：取消选中 ════════
  await page.mouse.click(700, 400);
  await page.waitForTimeout(1500);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 偏差 = await 核对坐标(page);
  记('⭐⭐ 静置 15s 后坐标复核：' + JSON.stringify(偏差));
  结果.收尾 = { 偏差, 已渲染: Object.keys(await 读全部坐标(page)).length };
} catch (e) {
  记('❌ ' + e.message);
  结果.错误 = String((e && e.stack) || e);
} finally {
  落盘(结果);
  await browser.browser.close();
  console.log('\n=== 已写 tools/batchEW3.json ===');
}
