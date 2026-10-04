// Batch EW-2：⭐⭐ 定位「新功能：支持真人」到底属于哪枚控件。
//
// EW-1 的两条路都没走通：
//   ① `aria-describedby` 归属链 —— 页面上只有 1 个气泡且**没有 id**，
//      Mantine 新版用 floating-ui，**不再用 aria-describedby 关联** ⇒ 这条路作废。
//   ② 全文搜「新功能 / 真人」⇒ **0 个命中**。不是判据错，是**参数面板没开** ——
//      ET 当时是开着面板读的。⇒ 先选中节点开面板，再搜。
//
// 本轮做法：**按几何位置反查**。
//   ET 记的是「横坐标 = 参数面板 left − 58px，纵坐标随面板上下移动，114×27，常驻」。
//   既然它跟着面板走，就去扫**面板左缘那条竖带**，把带里每一个元素全量倾倒，
//   再看谁在它旁边、谁可能是触发者。**不按文字找，按位置找。**
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEW2.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const browser = await launch();
const page = browser.page;
try {
  await open(page, CANVAS_URL);
  await closePromos(page);
  await page.waitForTimeout(4000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));

  // ════════ ① 选中视频节点 v-v2hlWY4Br3，打开参数面板 ════════
  const 点 = await page.evaluate((id) => {
    const el = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return [Math.round(r.left + r.width / 2), Math.round(r.top + 18)];
  }, 'v-v2hlWY4Br3');
  记('节点中心附近点击点：' + JSON.stringify(点));
  const 验 = await page.evaluate(([x, y, id]) => {
    const e = document.elementFromPoint(x, y);
    const n = e ? e.closest('.react-flow__node') : null;
    return { 落点: n ? n.getAttribute('data-id') : null, 正确: !!(n && n.getAttribute('data-id') === id) };
  }, [点[0], 点[1], 'v-v2hlWY4Br3']);
  记('落点自证：' + JSON.stringify(验));
  if (!验.正确) throw new Error('落点不对，中止');
  await page.mouse.click(点[0], 点[1]);
  await page.waitForTimeout(2500);

  // ════════ ② 找参数面板（用宽 + 右侧贴边找，不按 class 猜）════════
  const 面板 = await page.evaluate(() => {
    const 出 = [];
    for (const e of document.querySelectorAll('div')) {
      const r = e.getBoundingClientRect();
      if (r.width < 200 || r.width > 460) continue;
      if (r.height < 120) continue;
      if (r.right < innerWidth - 8) continue;      // 贴右缘
      if (r.top < 50) continue;
      const cs = getComputedStyle(e);
      出.push({
        标签: e.tagName, cls: String(e.className).slice(0, 90),
        box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        position: cs.position, zIndex: cs.zIndex, 子数: e.children.length,
        文字头: (e.innerText || '').trim().slice(0, 60),
      });
    }
    出.sort((a, b) => (b.box[2] * b.box[3]) - (a.box[2] * a.box[3]));
    return 出.slice(0, 6);
  });
  记('候选面板：' + JSON.stringify(面板, null, 1));
  结果.读数.候选面板 = 面板;

  const P = 面板[0];
  if (!P) throw new Error('没找到参数面板');

  // ════════ ③ ⭐ 扫面板左缘那条竖带：全量倾倒 ════════
  const 竖带 = await page.evaluate(([L, T, R, B]) => {
    const 出 = [];
    for (const e of document.querySelectorAll('*')) {
      const r = e.getBoundingClientRect();
      if (r.width < 3 || r.height < 3) continue;
      if (r.right < L || r.left > R) continue;
      if (r.bottom < T || r.top > B) continue;
      const cs = getComputedStyle(e);
      出.push({
        标签: e.tagName,
        文字: (e.innerText || '').trim().slice(0, 50),
        cls: String(e.className).slice(0, 100),
        box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        距面板左: Math.round(r.left - L),
        opacity: cs.opacity, pointerEvents: cs.pointerEvents, position: cs.position, zIndex: cs.zIndex,
        子数: e.children.length,
      });
    }
    // 只留「真正压在面板左边那一列」的：右边界不超过 面板左 + 20
    return 出.filter((x) => x.box[0] + x.box[2] <= L + 20).sort((a, b) => a.box[1] - b.box[1]);
  }, [P.box[0], 40, P.box[0] + 20, 810]);

  记('⭐ 面板左缘竖带（' + P.box[0] + ' 左边那一列）命中 ' + 竖带.length + ' 个：');
  记(JSON.stringify(竖带, null, 1));
  结果.读数.竖带 = 竖带;

  // ════════ ④ 全文搜「新功能 / 真人」（这次面板开着）════════
  const 找字 = await page.evaluate(() => {
    const 命中 = [];
    for (const e of document.querySelectorAll('*')) {
      const t = (e.innerText || '').trim();
      if (!t || t.length > 60) continue;
      if (!/新功能|真人/.test(t)) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) continue;
      const cs = getComputedStyle(e);
      命中.push({
        标签: e.tagName, 文字: t, 子数: e.children.length,
        cls: String(e.className).slice(0, 100),
        box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        opacity: cs.opacity, pointerEvents: cs.pointerEvents, zIndex: cs.zIndex,
        祖先链: (() => {
          const a = []; let p = e.parentElement, i = 0;
          while (p && i < 7) { const r2 = p.getBoundingClientRect(); a.push({ t: p.tagName, c: String(p.className).slice(0, 46), box: [Math.round(r2.left), Math.round(r2.top), Math.round(r2.width), Math.round(r2.height)] }); p = p.parentElement; i++; }
          return a;
        })(),
      });
    }
    return 命中;
  });
  记('含「新功能/真人」的元素：' + JSON.stringify(找字, null, 1));
  结果.读数.找字 = 找字;

  await page.screenshot({ path: EVID + 'ew2-面板左缘.png' });
  记('已拍 ew2-面板左缘.png');

  // ════════ 收尾：取消选中 ════════
  await page.mouse.click(60, 700);
  await page.waitForTimeout(1200);
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
  console.log('\n=== 已写 tools/batchEW2.json ===');
}
