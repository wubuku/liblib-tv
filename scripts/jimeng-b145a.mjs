// 批次 145 a 轮 —— 纯只读：`*node-empty` 三族在画布上的横向对照。
//
// 📌 选题来源：一次**元审计**（`jimeng-b145-audit.mjs`）发现 §4.49「全灭 testid」分诊表
//   那一行写着「`image-node-empty` 缺前置状态：一个**没有图片**的图片节点；
//   画布上唯一的图片节点**有内容**；`node-empty` 族实测只有 `audio-node-empty` /
//   `video-node-empty`」—— **但 20-reference.md:1733 起明写「2026-10-03 批次 134：
//   按护栏建一个再删掉，验成」**，并给出 `image-node-empty` 的完整契约（`182×182`、
//   aria 逐字 `暂无图片. No resources: 0 ready, 0 processing, 0 failed. Selected.`）。
//   ⇒ **分诊表没跟上批次 134**，是一处漂移。
//
// 本轮只读：画布上**已有**空音频/空视频节点（§4.49 自己说的），
//   把三族的 testid / tag / role / 矩形 / aria 逐字并排读出来，作为复测 `image-node-empty` 的对照基线。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { idsOf, selCount, 组数 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 145, 轮: 'a', 目的: 'node-empty 三族横向对照（纯只读）' };

const 读一族 = (testid) => p.evaluate((t) => {
  const els = Array.from(document.querySelectorAll(`[data-testid="${t}"]`));
  return { testid: t, 实例数: els.length,
    逐项: els.slice(0, 3).map((e) => { const r = e.getBoundingClientRect();
      const n = e.closest('.react-flow__node');
      return { tag: e.tagName, role: e.getAttribute('role'),
        盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10],
        canvas: [e.offsetWidth, e.offsetHeight],
        aria: e.getAttribute('aria-label'),
        逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60),
        cls: String(e.className || '').slice(0, 80),
        所属节点: n ? n.getAttribute('data-id') : null,
        所属节点aria: n ? n.getAttribute('aria-label') : null,
        节点选中: n ? n.classList.contains('selected') : null }; }) };
}, testid);

const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p);
  await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p),
    zoom: await R.zoom(), minimap: await R.minimap(), 积分: await R.credits() };

  // ---- 三族并排
  rec.三族 = {};
  for (const t of ['image-node-empty', 'video-node-empty', 'audio-node-empty']) {
    rec.三族[t] = await 读一族(t);
  }
  // ---- 全部 `*-node-empty` 族成员（看还有没有第四族）
  rec.empty族 = await p.evaluate(() => {
    const s = new Set();
    for (const e of document.querySelectorAll('[data-testid$="-node-empty"]')) s.add(e.getAttribute('data-testid'));
    return [...s].sort();
  });
  // ---- 画布上各类节点的数量分布（确认哪些是空节点）
  rec.节点类型分布 = await p.evaluate(() => {
    const c = {};
    for (const n of document.querySelectorAll('.react-flow__node')) {
      const cls = String(n.className || '');
      const m = /react-flow__node-([a-z]+)/.exec(cls);
      const k = m ? m[1] : '其他';
      c[k] = (c[k] || 0) + 1;
    }
    return c;
  });
  // ---- 图片节点（有内容的那个）作为对照
  rec.有内容的图片节点 = await p.evaluate(() => {
    const out = [];
    for (const n of document.querySelectorAll('.react-flow__node')) {
      if (!/react-flow__node-image/.test(String(n.className || ''))) continue;
      out.push({ id: n.getAttribute('data-id'),
        testid: Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')).sort(),
        aria: n.getAttribute('aria-label') });
    }
    return out;
  });
  // ---- 静态 testid 清单（收尾比对用）
  rec.静态testid = await R.testids();
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); }

await settle(p, R);
const 末 = await idsOf(p);
rec.收尾 = { 状态行: await R.status(), 节点数: 末.length, 组数: await 组数(p), 选中: await selCount(p),
  浮层: await R.overlays(), zoom: await R.zoom(), minimap: await R.minimap(), 积分: await R.credits() };
fs.writeFileSync(new URL('./_tmp-b145a.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify({ 起点: rec.起点, 三族: rec.三族, empty族: rec.empty族,
  节点类型分布: rec.节点类型分布, 有内容的图片节点: rec.有内容的图片节点, 收尾: rec.收尾, 异常: rec.异常 }, null, 1));
await b.close();
