// Batch FB-2：⭐⭐⭐ 先把**网格线的真实原点**算对，再问「有没有节点落在网格线上」
//
// FB-1 第一版算错了：它拿「35 的整数倍」当网格线，于是报出
//   导演台 x = -1225.03 离整数倍只有 **0.03**，「像是被吸过」。
// ⛔ 但网格线的原点不是 0 ——
//   DOM 里 `<pattern patternTransform="translate(-8.0258,-8.0258)">`，
//   `patternUnits="userSpaceOnUse"` ⇒ 用户空间就是**画布坐标空间**，
//   于是那个偏移换算成画布单位是 `-8.0258 ÷ 0.458621 = -17.4998 ≈ -17.5`。
//   ⇒ **网格线在 `-17.5 + 35k`，不在 `35k`。**
//
// ⭐⭐ 这正是本项目的老坑「一个数字可能同时对上两个东西」的又一例：
//   用错原点，「0.03」看着像铁证；用对原点，它是**两条网格线的正中**（两边各 17.5）。
//
// 本轮：
//   ① 从 DOM 把网格步长与原点**逐字读出来**，自己换算，不引用上一轮的结论
//   ② 用 `-17.5 + 35k` 重算 11 个节点 22 个坐标到最近网格线的距离
//   ③ 开吸附（这次**自证开关真的翻了**）后做微拖拽实验，看会不会被拉回网格线
//
// ⭐⭐⭐ 复原写在 `finally`；且复原用**整数像素**步进 ——
//   FB-1 的复原卡在 4.875 画布单位，正是因为「1 CSS px ÷ zoom = 2.18 画布单位」
//   这个下限：步进取整到整数像素后，每步都 < 1px，净位移为零。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchFB2.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;

/** ① 网格：步长与原点，全部从 DOM 读 */
const 网格 = () => page.evaluate(() => {
  const v = document.querySelector('.react-flow__viewport');
  const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(v).transform || '');
  const p = m ? m[1].split(',').map(Number) : [1, 0, 0, 1, 0, 0];
  const svg = document.querySelector('svg.react-flow__background') || document.querySelector('.react-flow__background');
  const pat = svg ? svg.querySelector('pattern') : null;
  // ⚠️ 属性真值是 `translate(-8.0258,-8.0258)` —— **没有 px 单位**。
  //    第一版把 `px` 写成必需，结果 null，后面直接空指针崩了。
  const 原串 = pat ? (pat.getAttribute('patternTransform') || '') : '';
  const t = pat && /translate\(\s*(-?[\d.]+)px?\s*,\s*(-?[\d.]+)px?\s*\)/.exec(原串);
  return {
    zoom: p[0],
    pattern宽: pat ? Number(pat.getAttribute('width')) : null,
    pattern偏移px: t ? [Number(t[1]), Number(t[2])] : null,
    patternUnits: pat ? pat.getAttribute('patternUnits') : null,
    patternTransform原串: 原串,
    背景svg: svg ? svg.outerHTML.slice(0, 400) : null,
  };
});

/** ② 22 个坐标到最近网格线的距离（网格线 = 原点 + 35k） */
const 节点距 = (原点, 步长) => page.evaluate(([原, 步]) => {
  const 距 = (val) => {
    const k = (val - 原) / 步;
    return Math.abs(k - Math.round(k)) * 步;
  };
  return [...document.querySelectorAll('.react-flow__node')].map((n) => {
    const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
    if (!t) return null;
    const x = Number(t[1]), y = Number(t[2]);
    const r = n.getBoundingClientRect();
    return {
      id: n.getAttribute('data-id'),
      画布: [x, y],
      x距: Number(距(x).toFixed(4)),
      y距: Number(距(y).toFixed(4)),
      中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)],
      屏: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
    };
  }).filter(Boolean).map((o) => Object.assign(o, { 最小距: Math.min(o.x距, o.y距) }))
    .sort((a, b) => a.最小距 - b.最小距);
}, [原点, 步长]);

/** 底栏按 left 排序定位「网格吸附」（EU/EX 定的规矩，不用名字单条件） */
const 找开关 = () => page.evaluate(() => {
  const out = [];
  for (const b of document.querySelectorAll('button')) {
    const r = b.getBoundingClientRect();
    if (r.top < 740 || r.bottom > 810 || r.left > 340) continue;
    if (b.querySelector('button')) continue;
    out.push({ aria: b.getAttribute('aria-label'), left: Math.round(r.left), pt: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] });
  }
  out.sort((a, b) => a.left - b.left);
  return out;
});

const 拖整数像素 = async (id, px_, py_) => {
  const s = await page.evaluate((nid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
    if (!n) return null;
    const r = n.getBoundingClientRect();
    return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
  }, id);
  if (!s) return null;
  const v = await page.evaluate((p) => {
    const e = document.elementFromPoint(p[0], p[1]);
    const n = e ? e.closest('.react-flow__node') : null;
    return n && n.getAttribute('data-id');
  }, s);
  if (v !== id) return { 错: v };
  await page.mouse.move(s[0], s[1]); await page.waitForTimeout(340);
  await page.mouse.down(); await page.waitForTimeout(130);
  await page.mouse.move(s[0] + px_, s[1] + py_); await page.waitForTimeout(240);
  await page.mouse.up(); await page.waitForTimeout(650);
  await page.mouse.move(720, 250); await page.waitForTimeout(300);
  return { 成功: true };
};

let 动过的 = [];
try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));

  // ---------- ① 网格 ----------
  const g = await 网格();
  记('⭐ 网格读数：zoom=' + g.zoom + '｜pattern 宽=' + g.pattern宽 + '｜patternUnits=' + g.patternUnits + '｜patternTransform=' + JSON.stringify(g.pattern偏移px));
  const 步长画布 = g.pattern宽 / g.zoom;
  const 原点画布 = g.pattern偏移px[0] / g.zoom;
  记(`⭐⭐ 换算：步长 = ${g.pattern宽} ÷ ${g.zoom} = **${步长画布.toFixed(4)} 画布单位**`);
  记(`⭐⭐ 换算：原点 = ${g.pattern偏移px[0]} ÷ ${g.zoom} = **${原点画布.toFixed(4)} 画布单位**`);
  记(`⭐⭐⭐ 所以网格线在 **${原点画布.toFixed(2)} + ${步长画布.toFixed(2)}·k**，**不在 35k 上**。`);
  结果.读数.网格 = g; 结果.读数.步长画布 = 步长画布; 结果.读数.原点画布 = 原点画布;

  // ---------- ② 用两个原点各算一遍 ----------
  记('—— ② 两种原点的距离对照 ——');
  const 对 = await 节点距(0, 步长画布);
  const 正 = await 节点距(原点画布, 步长画布);
  记('  【按 35k（错）】最小 ' + Math.min(...对.map((o) => o.最小距)).toFixed(4) + '，<0.5 的有 ' + 对.filter((o) => o.最小距 < 0.5).length + ' 个');
  记('  【按 ' + 原点画布.toFixed(2) + '+35k（对）】最小 ' + Math.min(...正.map((o) => o.最小距)).toFixed(4) + '，<0.5 的有 ' + 正.filter((o) => o.最小距 < 0.5).length + ' 个');
  记('  逐个（正确原点，按最小距排序）：');
  for (const o of 正) 记(`    ${o.id} [${o.画布[0]}, ${o.画布[1]}]｜x 距 ${o.x距}｜y 距 ${o.y距}`);
  结果.读数.按错原点 = 对; 结果.读数.按对原点 = 正;

  // ---------- ③ 开吸附 + 微拖 ----------
  记('—— ③ 开吸附并自证开关真的翻了 ——');
  const 栏 = await 找开关();
  记('  底栏按 left 排序：' + JSON.stringify(栏.map((b) => [b.left, b.aria])));
  const 开关 = 栏.find((b) => (b.aria || '').includes('网格吸附'));
  if (!开关) throw new Error('底栏找不到网格吸附');
  const 前 = 开关.aria;
  await page.mouse.move(开关.pt[0], 开关.pt[1]); await page.waitForTimeout(450);
  await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(1000);
  await page.mouse.move(720, 250); await page.waitForTimeout(500);
  const 栏2 = await 找开关();
  const 后 = (栏2.find((b) => (b.aria || '').includes('网格吸附')) || {}).aria;
  记(`  ⭐ aria：点之前「${前}」→ 点之后「${后}」；翻转了？ ${前 !== 后}`);
  if (前 === 后) {
    记('  ⛔ 第一次点击没翻面，再点一次');
    const p2 = (栏2.find((b) => (b.aria || '').includes('网格吸附')) || {}).pt;
    await page.mouse.move(p2[0], p2[1]); await page.waitForTimeout(450);
    await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(1000);
    await page.mouse.move(720, 250); await page.waitForTimeout(500);
    const 栏3 = await 找开关();
    const 后2 = (栏3.find((b) => (b.aria || '').includes('网格吸附')) || {}).aria;
    记(`  再点之后「${后2}」；翻转了？ ${前 !== 后2}`);
    if (前 === 后2) throw new Error('两次点击都没翻面，本轮到此为止');
  }
  结果.读数.开关 = { 前, 后 };

  // 拿「错原点下最像被吸过」的导演台，和一个普通节点，各做一次整数像素微拖
  for (const id of ['n-56F19pXVB4', 't-UtVx3lZmrV']) {
    const 拖前 = await page.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
      return t ? [Number(t[1]), Number(t[2])] : null;
    }, id);
    const 原位 = [拖前[0], 拖前[1]];
    动过的.push([id, 原位]);
    const r = await 拖整数像素(id, 3, 2);   // 3px 右、2px 下 ≈ 6.5 / 4.4 画布单位
    if (!r || !r.成功) { 记(`  ⛔ ${id} 微拖失败：${JSON.stringify(r)}`); continue; }
    const 拖后 = await page.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
      return t ? [Number(t[1]), Number(t[2])] : null;
    }, id);
    const 位移 = [拖后[0] - 原位[0], 拖后[1] - 原位[1]];
    const 距 = (val, 原, 步) => Math.abs((val - 原) / 步 - Math.round((val - 原) / 步)) * 步;
    记(`  ⭐ ${id}：${JSON.stringify(原位)} → ${JSON.stringify(拖后)}；净位移 ${JSON.stringify(位移.map((v) => Number(v.toFixed(3))))}`);
    记(`     拖前 x 距网格线 ${距(原位[0], 原点画布, 步长画布).toFixed(3)} → 拖后 ${距(拖后[0], 原点画布, 步长画布).toFixed(3)}`);
    记(`     ⭐ 有没有被拉回网格线（距离变小且 < 1）？ ${距(拖后[0], 原点画布, 步长画布) < 1 ? '✅ 是' : '⛔ 否'}`);
    结果.读数[id] = { 原位, 拖后, 位移 };
    await page.screenshot({ path: EVID + `fb2-${id}-微拖之后.png` });
    记(`  已拍 fb2-${id}-微拖之后.png`);
  }

  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 偏差 = await 核对坐标(page);
  记('⭐⭐ 静置 15s 后坐标复核：' + JSON.stringify(偏差));
  结果.收尾 = { 偏差 };
} catch (e) {
  记('❌ ' + e.message);
  结果.错误 = String((e && e.stack) || e);
} finally {
  if (动过的.length) {
    记('—— finally：复原 ——');
    for (const [id, 原位] of 动过的) {
      try {
        for (let 轮 = 1; 轮 <= 24; 轮++) {
          const s = await page.evaluate((nid) => {
            const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
            if (!n) return null;
            const v = document.querySelector('.react-flow__viewport');
            const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(v).transform || '');
            const p = m ? m[1].split(',').map(Number) : [1, 0, 0, 1, 0, 0];
            const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
            const r = n.getBoundingClientRect();
            return { 画布: t ? [Number(t[1]), Number(t[2])] : null, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)], zoom: p[0] };
          }, id);
          if (!s || !s.画布) break;
          const dx = 原位[0] - s.画布[0], dy = 原位[1] - s.画布[1];
          if (Math.hypot(dx, dy) < 0.5) { 记(`  ✅ ${id} 复原到位（轮 ${轮}）`); break; }
          const px_ = Math.max(-8, Math.min(8, Math.round(dx * s.zoom)));
          const py = Math.max(-8, Math.min(8, Math.round(dy * s.zoom)));
          if (px_ === 0 && py === 0) { 记(`  ⛔ ${id} 整数像素已为 0，拖不动（剩余 ${Math.hypot(dx, dy).toFixed(3)}）`); break; }
          const r = await 拖整数像素(id, px_, py);
          if (!r || !r.成功) { 记(`  ⛔ ${id} 复原拖拽失败：${JSON.stringify(r)}`); break; }
        }
      } catch (e2) { 记('  ⛔ 复原抛错：' + e2.message); }
    }
  }
  落盘(结果);
  await 浏览器.browser.close();
  console.log('\n=== 已写 tools/batchFB2.json ===');
}
