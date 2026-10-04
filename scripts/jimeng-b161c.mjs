// 批次 161-c —— 把「查看积分明细」钉死：它是**关掉对话框**，还是**打开了什么**
//
// 161-b 的读数：点下去 **URL 不变**、**没开新页签**，而点后 `body.innerText` 里
// **不再有「查看积分明细」** ⇒ 那一瞬间**对话框被关掉了**。
// 但收尾 `浮层 = 1` ⇒ 又有什么东西开着。本轮把「开着的到底是什么」读出来。
import fs from 'node:fs';
import { openCanvas, readers, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf } from './jimeng-b139-lib.mjs';

const rec = { 批次: '161c', 目的: '钉死「查看积分明细」按下后的真实效果' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b161c.json', import.meta.url), JSON.stringify(rec, null, 1));
const 出图 = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const 画布URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';

const { b, p } = await openCanvas();
const R = readers(p);

const 场景 = () => p.evaluate(() => {
  const d = document.querySelector('[data-testid="workspace-project-info-dialog"]');
  const 开 = Array.from(document.querySelectorAll('[data-state=open]')).map((e) => ({
    testid: e.getAttribute('data-testid'), tag: e.tagName, role: e.getAttribute('role'),
    逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 90) }));
  const toast = Array.from(document.querySelectorAll('[data-sonner-toast],[role=status],[role=alert],li'))
    .filter((e) => { const t = (e.innerText || '').trim(); return t && t.length < 80 && !/节点/.test(t); })
    .slice(0, 6).map((e) => ({ tag: e.tagName, testid: e.getAttribute('data-testid'), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 70) }));
  return { 对话框在: !!d,
    对话框逐字: d ? (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160) : null,
    开浮层: 开, toast,
    顶层浮层框: Array.from(document.querySelectorAll('body > div')).map((e) => { const r = e.getBoundingClientRect();
      return { 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)], dataState: e.getAttribute('data-state'),
        子数: e.children.length, 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60) }; }),
    URL: location.href, 标题: document.title };
});

try {
  await keyGuard(p); await setZoom(p, 60); await p.waitForTimeout(1200);
  const 建前 = await idsOf(p);
  rec.起点 = { 状态行: await R.status(), 节点数: 建前.length, 选中: await selCount(p), 积分: await R.credits(), 浮层: await R.overlays() };
  console.log('起点', JSON.stringify(rec.起点));

  // ① 更多 → 项目信息 → 积分消耗
  const 更多 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('button,[role=button]')).find((x) => (x.getAttribute('aria-label') || '') === '更多');
    if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  await p.mouse.click(更多[0], 更多[1]); await p.waitForTimeout(1300);
  const 项 = await p.evaluate(() => { const it = Array.from(document.querySelectorAll('[role=menuitem]')).find((i) => (i.innerText || '').trim() === '项目信息'); if (!it) return null;
    const r = it.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  await p.mouse.click(项[0], 项[1]); await p.waitForTimeout(2200);
  const 页签 = await p.evaluate(() => { const t = Array.from(document.querySelectorAll('[role=tab]')).find((x) => (x.innerText || '').trim() === '积分消耗'); if (!t) return null;
    const r = t.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  await p.mouse.click(页签[0], 页签[1]); await p.waitForTimeout(1600);
  断言('⓪ 对话框停在「积分消耗」页签', await p.evaluate(() => !!document.querySelector('[data-testid="workspace-project-info-dialog"]')), {});

  const 钮 = await p.evaluate(() => { const d = document.querySelector('[data-testid="workspace-project-info-dialog"]'); if (!d) return null;
    const e = Array.from(d.querySelectorAll('button')).find((x) => /积分明细/.test(x.innerText || '')); if (!e) return null;
    const r = e.getBoundingClientRect();
    return { 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
      禁用: !!(e.disabled || e.getAttribute('aria-disabled') === 'true'),
      外层盒: (() => { const q = e.parentElement; if (!q) return null; const s = q.getBoundingClientRect(); return [Math.round(s.width), Math.round(s.height), Math.round(s.x), Math.round(s.y)]; })(),
      逐字: (e.innerText || '').replace(/\s+/g, ' ').trim() }; });
  rec.按钮 = 钮;
  console.log('按钮 =', JSON.stringify(钮));
  落盘();

  rec.按前 = await 场景();
  落盘();
  console.log('按前 =', JSON.stringify({ 对话框在: rec.按前.对话框在, 开浮层: rec.按前.开浮层.length, 顶层: rec.按前.顶层浮层框.length }));

  // ② 点它，密集采样 14 × 400ms
  await p.mouse.click(钮.盒[2] + 钮.盒[0] / 2, 钮.盒[3] + 钮.盒[1] / 2);
  rec.采样 = [];
  for (let i = 0; i < 14; i++) {
    await p.waitForTimeout(400);
    const s = await 场景(); s.毫秒 = (i + 1) * 400;
    rec.采样.push({ 毫秒: s.毫秒, 对话框在: s.对话框在, 开浮层数: s.开浮层.length, 开浮层: s.开浮层,
      toast: s.toast, 顶层浮层框: s.顶层浮层框, URL变了吗: s.URL !== rec.按前.URL });
    落盘();
  }
  rec.URL变过 = rec.采样.some((z) => z.URL变了吗);
  rec.对话框消失帧 = rec.采样.find((z) => !z.对话框在);
  rec.浮层快照 = [...new Set(rec.采样.flatMap((z) => z.开浮层.map((o) => o.testid || o.tag + ':' + o.逐字.slice(0, 30))))];
  rec.toast全集 = [...new Set(rec.采样.flatMap((z) => z.toast.map((t) => t.逐字)))];
  rec.结论 = {
    URL是否变过: rec.URL变过,
    对话框是否被关掉: !!rec.对话框消失帧,
    关掉发生在第几帧: rec.对话框消失帧 ? rec.对话框消失帧.毫秒 : null,
    按下后仍开着的浮层: rec.浮层快照,
    出现的toast: rec.toast全集,
  };
  落盘();
  console.log('结论 =', JSON.stringify(rec.结论, null, 1));
  断言('① URL 全程不变、**没开新页签**（不是跳走型）', !rec.URL变过 && p.context().pages().length === 1, rec.结论);

  await p.screenshot({ path: new URL('./121-credits-detail-destination.png', 出图).pathname });
  rec.图 = 'screenshots/121-credits-detail-destination.png';
  console.log('🖼 已拍 121');
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

// ③ 收尾：把可能残留的浮层关干净
try {
  for (let k = 0; k < 4; k++) {
    const n = await p.evaluate(() => document.querySelectorAll('[data-state=open]').length);
    if (n <= 1) break;
    await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  }
  const 还 = await p.evaluate(() => document.querySelectorAll('[data-state=open]').length);
  if (还 > 1) { await p.mouse.click(640, 690); await p.waitForTimeout(1000); }
} catch (e) { rec.清浮层异常 = String(e.message || e).slice(0, 200); }

try {
  if (p.url() !== 画布URL) { await p.goto(画布URL, { waitUntil: 'domcontentloaded', timeout: 90000 }); await p.waitForTimeout(9000); }
  await keyGuard(p); await setZoom(p, 60); await p.waitForTimeout(1200);
} catch (e) {}
try {
  const mm = await R.minimap();
  if (!mm || mm.ariaPressed !== 'true') {
    const t = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-display-toggle-minimap"]'); if (!e) return null;
      const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    if (t) { await p.mouse.click(t[0], t[1]); await p.waitForTimeout(1400); }
  }
} catch (e) {}
rec.收尾 = { 页签数: p.context().pages().length, 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(), zoom: await R.zoom(), 积分: await R.credits() };
rec.断言全过 = 断言过; 落盘();
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');
断言('② 收尾回到共享画布：1 页签 / 76 节点 / 0 选中 / 0 浮层 / 60% / 积分不变',
  rec.收尾.页签数 === 1 && rec.收尾.节点数 === 76 && rec.收尾.选中 === 0 && rec.收尾.浮层 === 0 && String(rec.收尾.积分) === String((rec.起点 || {}).积分),
  { 起点: rec.起点 || null, 收尾: rec.收尾 });
rec.断言全过 = 断言过; 落盘();
console.log('断言全过 =', rec.断言全过);
process.exit(0);
