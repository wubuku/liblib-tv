// ⭐⭐⭐ **专用复原脚本** —— Batch EV-6 收尾时把 `a-THmbuJXQj4` 拖歪了。
//
// 根因（先查清再修，别直接拖回去）：
//   EV-6 的复原拖拽**只做了一次**，没校验实际落点。
//   一次拖拽经常因为「按下的那一帧节点矩形还是旧的」而只走完 88% 的行程。
//   日志里能直接看到：`复原后=[-1301,636] 差=[55,36]`，而请求的位移是 `[-464,-301]`。
//   ⭐ 判据缺陷：**「发了一次拖拽」不等于「到位了」，必须读回实际落点再决定要不要重试。**
//
// 本脚本的做法：**循环直到真的到位**。
//   每次：读当前画布坐标 → 算还差多少 → 只拖「还差的那部分」→ 读回校验。
//   差值小于 0.5 才算成功，最多 8 轮。
//
// ⛔ 全程只碰 `a-THmbuJXQj4` 一个节点，不碰别的。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEV7-restore.json';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 步骤: [], 读数: {} };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 目标 = 'a-THmbuJXQj4';
const 基线 = 坐标[目标];

const browser = await launch();
const page = browser.page;

const 读变换 = () => page.evaluate(() => {
  const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(document.querySelector('.react-flow__viewport')).transform);
  const n = m[1].split(',').map(Number);
  return { zoom: n[0] };
});

const 读状态 = (id) => page.evaluate((nid) => {
  const el = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!el) return null;
  const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(el.style.transform || '');
  const r = el.getBoundingClientRect();
  return {
    画布: m ? [parseFloat(m[1]), parseFloat(m[2])] : null,
    中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)],
  };
}, id);

/** 确认吸附是关的 —— 开着吸附拖不回任意坐标 */
const 吸附关着 = async () => {
  const 栏 = await page.evaluate(() => {
    const out = [];
    for (const e of document.querySelectorAll('button')) {
      const r = e.getBoundingClientRect();
      if (r.top < 740 || r.bottom > 810 || r.left > 340) continue;
      if (e.querySelector('button')) continue;
      out.push({ aria: e.getAttribute('aria-label'), box: Math.round(r.left), svg: e.querySelectorAll('svg').length, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] });
    }
    out.sort((a, b) => a.box - b.box);
    return out;
  });
  const 枚 = 栏[4];
  const 认 = !!枚 && 枚.aria === '网格吸附';
  if (!认) return { 认: false, 栏 };
  if (枚.svg === 1) return { 认: true, 开: false, 栏 };
  const [x, y] = 枚.中心;
  const 验 = await page.evaluate(([px, py]) => {
    const b = document.elementFromPoint(px, py)?.closest('button');
    return b ? b.getAttribute('aria-label') : null;
  }, [x, y]);
  await page.mouse.move(x, y); await page.mouse.down(); await page.mouse.up();
  await page.waitForTimeout(1000);
  await page.mouse.move(700, 300); await page.waitForTimeout(400);
  const 栏2 = await page.evaluate(() => {
    const out = [];
    for (const e of document.querySelectorAll('button')) {
      const r = e.getBoundingClientRect();
      if (r.top < 740 || r.bottom > 810 || r.left > 340) continue;
      if (e.querySelector('button')) continue;
      out.push({ aria: e.getAttribute('aria-label'), box: Math.round(r.left), svg: e.querySelectorAll('svg').length });
    }
    out.sort((a, b) => a.box - b.box);
    return out;
  });
  return { 认: true, 开: 栏2[4].svg === 2, 点击自证: 验, 栏: 栏2 };
};

try {
  await open(page, CANVAS_URL);
  await closePromos(page);
  await page.waitForTimeout(4000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);

  const 吸 = await 吸附关着();
  记('吸附状态：' + JSON.stringify({ 认: 吸.认, 开: 吸.开, 点击自证: 吸.点击自证 || '—' }));
  结果.读数.吸附 = 吸;

  const 起 = await 读状态(目标);
  记('起始：' + JSON.stringify(起) + ' 基线=' + JSON.stringify(基线));

  for (let 轮 = 1; 轮 <= 8; 轮++) {
    const 变 = await 读变换();
    const 态 = await 读状态(目标);
    const dx画布 = 基线[0] - 态.画布[0];
    const dy画布 = 基线[1] - 态.画布[1];
    if (Math.abs(dx画布) < 0.5 && Math.abs(dy画布) < 0.5) { 记(`第 ${轮} 轮：已在容差内，停止`); break; }
    const [cx, cy] = 态.中心;
    const 验 = await page.evaluate(([px, py, nid]) => {
      const n = document.elementFromPoint(px, py)?.closest('.react-flow__node');
      return n ? n.getAttribute('data-id') : null;
    }, [cx, cy, 目标]);
    if (验 !== 目标) { 记(`第 ${轮} 轮：落点不是目标（${验}），中止`); break; }
    const dx = Math.round(dx画布 * 变.zoom);
    const dy = Math.round(dy画布 * 变.zoom);
    await page.mouse.move(cx, cy);
    await page.mouse.down();
    for (let i = 1; i <= 12; i++) {
      await page.mouse.move(cx + Math.round((dx * i) / 12), cy + Math.round((dy * i) / 12));
      await page.waitForTimeout(35);
    }
    await page.mouse.up();
    await page.waitForTimeout(900);
    const 后 = await 读状态(目标);
    记(`第 ${轮} 轮：请求画布 [${dx画布.toFixed(2)}, ${dy画布.toFixed(2)}] → 实际 ${JSON.stringify(后.画布)} 差 [${(后.画布[0] - 基线[0]).toFixed(2)}, ${(后.画布[1] - 基线[1]).toFixed(2)}]`);
  }

  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 偏差 = await 核对坐标(page);
  记('⭐⭐ 静置 15s 后坐标复核：' + JSON.stringify(偏差));
  结果.收尾 = { 偏差, 已渲染: Object.keys(await 读全部坐标(page)).length };
  if (偏差.length) throw new Error('仍有偏差，未复原干净');
} catch (e) {
  记('❌ ' + e.message);
  结果.错误 = String((e && e.stack) || e);
} finally {
  落盘(结果);
  await browser.browser.close();
  console.log('\n=== 已写 tools/batchEV7-restore.json ===');
}
