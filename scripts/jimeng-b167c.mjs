// 批次 167-c —— 把 167-b 拿到的机制打成一条**可证伪的定律**，并**订正本批 166 的一个错误推断**。
//
// 🔑 167-b 读到 classList 时，548 在 CSS 里查不到；本轮读 **内联 style** 才真相大白：
//     style="height: 734px; max-height: calc(-32px + 100vh); border-radius: 16px; width: 548px; …"
//   ⇒ ① **548px 是 JS 写死的内联常量**（不是 CSS，也**不是** CSS 变量 ——
//        `--dreamina-geometry-dialog-default-width` 实测是 **480px**，与它无关）；
//      ② **688 根本不是定尺**：声明的高度是 **734**，被 `max-height: calc(-32px + 100vh)`
//        在 720 高的视口上**夹成了 688**。
//   ⇒ 🔴 **手册把这两个数并排记成「契约尺寸 548×688」是错的**：
//      一个是常量、另一个是视口相关的夹取结果，**不是同一族**。
//      （本类错误本册已有同族案例：281×281 是屏上口径而非 canvas 尺寸。）
//
// 📐 由此得到定律并逐档验证：
//   宽 = min(548, 视口宽 − 32)　　门槛 **580 / 579**
//   高 = min(734, 视口高 − 32)　　门槛 **766 / 765**
//   ⚠️ 高度门槛比 720 **高**：要把 734 完整放出来，窗口得比 720 还高 46px。
//
// 🧪 一处方法上的省事：对话框是 `position:fixed`，**开着的时候改视口即可重排**，
//    所以整条阶梯**只开一次对话框**（不必每档重开、不必每档重新找那个节点）。
//    前提是它扛得住 resize —— 这一点本身要断言（每档都核「对话框仍在」）。
//
// ⛔ 只读：只开对话框，不填名称、不点保存；收尾复原缩放与小地图。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';

const 高档 = [[1280, 800], [1280, 766], [1280, 765], [1280, 720], [1280, 700], [1280, 600], [1280, 400]];
const 宽档 = [[1280, 720], [900, 720], [580, 720], [579, 720], [500, 720]];
const rec = { 批次: '167c', 目的: '验证 宽=min(548,100vw−32) 与 高=min(734,100vh−32)，并订正「688 是定尺」的错法' };
let 断言过 = true, 断言数 = 0, 断言预期 = 5;
const 断言 = (名, ok, 详情) => { 断言数++; const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' → ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b167c.json', import.meta.url), JSON.stringify(rec, null, 1));

const 读 = () => {
  const d = document.querySelector('[data-testid="subject-export-confirm-dialog"]');
  if (!d) return { 找到: false, 视口: [innerWidth, innerHeight] };
  const r = d.getBoundingClientRect(), cs = getComputedStyle(d);
  const 子 = Array.from(d.children).map((c) => ({ testid: c.getAttribute('data-testid'), 高: Math.round(c.getBoundingClientRect().height), flex: getComputedStyle(c).flex }));
  return { 找到: true, 视口: [innerWidth, innerHeight],
    盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
    余量: { 左: +r.x.toFixed(1), 右: +(innerWidth - (r.x + r.width)).toFixed(1), 上: +r.y.toFixed(1), 下: +(innerHeight - (r.y + r.height)).toFixed(1) },
    内联: d.getAttribute('style'), 计算: { width: cs.width, height: cs.height, maxHeight: cs.maxHeight, maxWidth: cs.maxWidth },
    子, 子高合计: 子.reduce((s, z) => s + z.高, 0) };
};

const 读共享 = async (p) => p.evaluate(() => ({
  状态行: (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0],
  节点数: document.querySelectorAll('.react-flow__node').length,
  选中: document.querySelectorAll('.react-flow__node.selected').length,
  浮层: Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length,
  积分: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'),
}));

const { b, p } = await openCanvas();
const R = readers(p);
let 起始缩放 = null, s2 = null;
try {
  await keyGuard(p); await settle(p, R); await p.waitForTimeout(1200);
  rec.起点 = { 状态行: await R.status(), 节点数: (await R.ids()).length, 积分: await R.credits(), 缩放: await R.zoom() };
  const m = /(\d+)%/.exec(rec.起点.缩放 || ''); 起始缩放 = m ? parseInt(m[1], 10) : 60;
  await setZoom(p, 20); await p.waitForTimeout(1400);
  const t = await p.evaluate(() => { const x = Array.from(document.querySelectorAll('.react-flow__node')).find((n) => /b22-upload/.test(n.innerText || ''));
    if (!x) return null; const r = x.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  断言('⓪ 找到 b22-upload 并可右键', !!t, { t });
  await p.mouse.click(t[0], t[1]); await p.waitForTimeout(1000);
  await p.mouse.click(t[0], t[1], { button: 'right' }); await p.waitForTimeout(1700);
  const it = await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"] [role=menuitem]')).find((x) => /保存到主体库/.test(x.innerText || ''));
    if (!m) return null; const r = m.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  断言('① 右键菜单里有「保存到主体库」', !!it, { it });
  await p.mouse.click(it[0], it[1]); await p.waitForTimeout(2800);
  const 开 = await p.evaluate(读);
  断言('② 对话框已打开且基线读数 = 548×688（手册原记的那个数）', 开.找到 && 开.盒[0] === 548 && 开.盒[1] === 688, 开.盒);
  rec.内联样式 = 开.内联;
  落盘();

  // ---- 关键前提：开着改视口，它扛不扛得住 ----
  s2 = await p.context().newCDPSession(p);
  rec.高度档 = [];
  for (const [w, h] of 高档) {
    await s2.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
    await p.waitForTimeout(1300);
    const 读数 = await p.evaluate(读);
    rec.高度档.push(读数);
    console.log(`  [高 ${w}×${h}] 盒 ${JSON.stringify(读数.盒)} maxH ${读数.计算.maxHeight} 子合计 ${读数.子高合计}`);
  }
  rec.宽度档 = [];
  for (const [w, h] of 宽档) {
    await s2.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
    await p.waitForTimeout(1300);
    const 读数 = await p.evaluate(读);
    rec.宽度档.push(读数);
    console.log(`  [宽 ${w}×${h}] 盒 ${JSON.stringify(读数.盒)} maxW ${读数.计算.maxWidth}`);
  }
  const 预测高 = (h) => Math.min(734, h - 32);
  const 预测宽 = (w) => Math.min(548, w - 32);
  rec.预测 = { 高: 高档.map(([, h]) => 预测高(h)), 高实测: rec.高度档.map((z) => z.盒 && z.盒[1]),
    宽: 宽档.map(([w]) => 预测宽(w)), 宽实测: rec.宽度档.map((z) => z.盒 && z.盒[0]) };
  断言('③ 十二档（7 高 + 5 宽）**全程对话框都没被 resize 关掉**，且与 min(定尺, 视口−32) 逐档相同',
    rec.高度档.every((z, i) => z.找到 && z.盒[1] === 预测高(高档[i][1])) &&
    rec.宽度档.every((z, i) => z.找到 && z.盒[0] === 预测宽(宽档[i][0])), rec.预测);
  断言('④ 高度门槛在 766/765：766 档读出 734（声明高度首次完整），765 档读出 733',
    rec.高度档.find((z) => z.视口[1] === 766).盒[1] === 734 &&
    rec.高度档.find((z) => z.视口[1] === 765).盒[1] === 733, rec.预测);
  断言('⑤ 三段高度（52 头 / 552 体 / 84 脚）之和逐档等于对话框高',
    rec.高度档.filter((z) => z.找到).every((z) => z.子高合计 === z.盒[1]),
    rec.高度档.map((z) => ({ 视口高: z.视口 && z.视口[1], 盒高: z.盒 && z.盒[1], 子合计: z.子高合计 })));
  断言('⑥ 720 档读出的是**夹取结果 688**，而声明高度是 734（两者不是同一族数）',
    rec.内联样式 && /height:\s*734px/.test(rec.内联样式) &&
    rec.高度档.find((z) => z.视口[1] === 720).盒[1] === 688,
    { 内联: rec.内联样式 });
  落盘();
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); console.log('异常', rec.异常); 断言过 = false; }
finally {
  for (let k = 0; k < 4; k++) { try { await p.keyboard.press('Escape'); await p.waitForTimeout(700); } catch (e) {} }
  // 🔴 本轮收尾断言当场抓到一处真泄漏：`Emulation.clearDeviceMetricsOverride`
  //   **只是撤掉覆盖、并不会把视口钉回 1280×720** —— 撤掉之后读出的是**窗口真实尺寸 1282×759**。
  //   ⇒ 撤销的正解是**显式 `pinViewport()`**（批次 165/166 用的就是它）。
  //   📌 这也解释了为什么 165-a 之后共享页签会掉到 800×873：那次是先 clear、后没钉。
  try { if (s2) await s2.send('Emulation.clearDeviceMetricsOverride'); } catch (e) {}
  try { const { pinViewport } = await import('./jimeng-safe-keys.mjs'); rec.钉回 = await pinViewport(p); } catch (e) { rec.钉回异常 = String(e).slice(0, 200); }
  try { if (起始缩放) { rec.复原缩放 = await setZoom(p, 起始缩放); } } catch (e) {}
  try { await settle(p, R); } catch (e) {}
  try {
    const mm = await R.minimap();
    if (!mm || mm.ariaPressed !== 'true') { const t = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-display-toggle-minimap"]'); if (!e) return null;
      const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
      if (t) { await p.mouse.click(t[0], t[1]); await p.waitForTimeout(1300); } rec.小地图已重开 = true; }
  } catch (e) {}
  try { const { pinViewport } = await import('./jimeng-safe-keys.mjs'); await pinViewport(p); } catch (e) {}
  rec.收尾 = { 状态行: await R.status(), 节点数: (await R.ids()).length, 选中: await R.selCount(), 浮层: await R.overlays(),
    视口: await p.evaluate(() => [innerWidth, innerHeight]), 缩放: await R.zoom(), 积分: await R.credits() };
  console.log('收尾', JSON.stringify(rec.收尾));
  断言('⛔ 收尾回到基线（76 节点 / 0 选中 / 浮层 0 / 视口与缩放复原 / 积分不变，无持久写入）',
    rec.收尾.节点数 === 76 && rec.收尾.选中 === 0 && rec.收尾.浮层 === 0 &&
    String(rec.收尾.积分) === String(rec.起点.积分) && rec.收尾.视口[0] === 1280 && rec.收尾.视口[1] === 720,
    { 起点: rec.起点, 收尾: rec.收尾 });
  if (断言数 < 断言预期) { console.log(`⛔ 断言只跑了 ${断言数}/${断言预期} 条 —— 中途崩了`); 断言过 = false; }
  rec.断言执行数 = 断言数; rec.断言预期数 = 断言预期; rec.断言全过 = 断言过; 落盘();
  console.log('\n断言全过 =', 断言过);
}
process.exit(0);
