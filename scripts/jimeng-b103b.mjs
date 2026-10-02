// 批次 103 · b 轮：左栏入口改用「**查容器后代**」重取。
//
// 🔴 **本轮自己踩了批次 99 已经立过规的坑**：a 轮用坐标粗筛
//   （`x < 容器宽+40` 且 `y` 落在容器纵向范围内）取左栏按钮，
//   结果**多捞进 6 个不属于左栏的项**：
//     · `添加素材到时间线`（`1113×84`，超宽，横跨整块画布，x 恰好 < 200）
//     · 底部 dock 的 4 个：`选择工具` / `小地图` / `显示连线` / `Zoom options, 100%`
//       （它们 y=672，落在「容器顶 72 + 容器高 632 = 704」之内，x 也 < 200）
//   判据失败，却**读数看着还挺整齐**（步长 42/42/…/56/42）——
//   **差一点就当成「复核通过」了**。
//
// 📌 批次 99 的原文教训：「判断某面板有几个控件要查**容器后代**，别按坐标筛」。
//   坐标筛的致命处在于：**越界的元素照样能被框进来**，
//   而读数不会因此变乱 ⇒ 假阴性极难发现。
//   正路：`container.querySelectorAll('button,[role=button]')`，
//   再按「有 aria + 宽高非零 + 中心点在容器矩形内」过滤（中心点而不是左上角，更抗超宽元素）。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };

// 先找出左栏容器本身：批次 99 记 `canvas-navigation-shell`，本轮重新确认
out.containers = await p.evaluate(() => Array.from(document.querySelectorAll('aside,nav,section,div'))
  .map((e) => { const r = e.getBoundingClientRect();
    return { tag: e.tagName, tid: e.getAttribute('data-testid'), id: e.id, aria: e.getAttribute('aria-label'),
      rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
      nBtn: e.querySelectorAll('button,[role=button]').length }; })
  .filter((x) => /^12,72 /.test(x.rect) || (x.tid && /navigation|rail|left/i.test(x.tid))));
log('候选左栏容器：', JSON.stringify(out.containers, null, 1));

out.rail = await p.evaluate(() => {
  // 正路：先按**矩形**挑出左栏容器（x≈12、宽≈160、高 > 500），再查它的**后代**
  const cands = Array.from(document.querySelectorAll('*')).filter((e) => {
    const r = e.getBoundingClientRect();
    return Math.abs(r.x - 12) < 3 && Math.abs(r.width - 160) < 4 && r.height > 500; });
  const box = cands.sort((a, b) => a.querySelectorAll('*').length - b.querySelectorAll('*').length)[0];
  if (!box) return { noBox: true };
  const br = box.getBoundingClientRect();
  const items = Array.from(box.querySelectorAll('button,[role=button]')).map((e) => {
      const r = e.getBoundingClientRect();
      const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
      const inside = cx >= br.x && cx <= br.x + br.width && cy >= br.y && cy <= br.y + br.height;
      const el = document.elementFromPoint(Math.round(cx), Math.round(cy));
      return { aria: e.getAttribute('aria-label'), tid: e.getAttribute('data-testid'),
        y: Math.round(r.y), x: Math.round(r.x), w: Math.round(r.width), h: Math.round(r.height),
        insideByCenter: inside, hitSelf: !!(el && (el === e || e.contains(el) || e.contains(el.parentElement || e))) }; })
    .filter((x) => x.aria && x.w > 0 && x.h > 0 && x.insideByCenter);
  return { boxTag: box.tagName, boxTid: box.getAttribute('data-testid'), boxId: box.id,
    boxRect: `${Math.round(br.x)},${Math.round(br.y)} ${Math.round(br.width)}×${Math.round(br.height)}`,
    nDescendantBtns: box.querySelectorAll('button,[role=button]').length,
    count: items.length, testidNull: items.filter((i) => !i.tid).length,
    items, ys: items.map((i) => i.y), steps: items.slice(1).map((i, k) => i.y - items[k].y) };
});
log('\n=== 左栏（容器后代口径）===');
log(JSON.stringify(out.rail, null, 1));

// 交叉验证：容器里到底有几个「有 aria 且宽高非零」的按钮
out.cross = await p.evaluate(() => {
  const cands = Array.from(document.querySelectorAll('*')).filter((e) => {
    const r = e.getBoundingClientRect();
    return Math.abs(r.x - 12) < 3 && Math.abs(r.width - 160) < 4 && r.height > 500; });
  const box = cands.sort((a, b) => a.querySelectorAll('*').length - b.querySelectorAll('*').length)[0];
  if (!box) return null;
  const all = Array.from(box.querySelectorAll('button,[role=button]'));
  return { all: all.length,
    withAria: all.filter((e) => e.getAttribute('aria-label')).length,
    nonZero: all.filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; }).length,
    both: all.filter((e) => { const r = e.getBoundingClientRect();
      return e.getAttribute('aria-label') && r.width > 0 && r.height > 0; }).length,
    dropped: all.filter((e) => { const r = e.getBoundingClientRect();
      return !(e.getAttribute('aria-label') && r.width > 0 && r.height > 0); })
      .map((e) => ({ tag: e.tagName, tid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
        w: Math.round(e.getBoundingClientRect().width), h: Math.round(e.getBoundingClientRect().height) })) };
});
log('\n=== 交叉验证：容器内按钮总数 ===');
log(JSON.stringify(out.cross, null, 1));

out.end = { scale: await p.evaluate(() => { const e = document.querySelector('.react-flow__viewport');
  const m = e && /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return m ? Number(m[1]) : null; }) };
writeFileSync(new URL('./_tmp-b103b.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
