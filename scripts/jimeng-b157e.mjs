// 批次 157-e —— 找「删除项目副本」的入口（157-d 的下拉层没被选择器命中，本轮放宽）
//
// 🔴 背景：157-c 点「复制项目」**无确认框**、一步到位地造出了项目副本
//    `f43b795d-…-c899db06fb07`（标题「测试项目5」，76 节点）。现在要在共享帐号上把它删掉。
//    157-d 的探针要求浮层 `width>120 && height>60`，而项目下拉很可能更窄或结构不同 ⇒ 一个都没命中。
//    ⇒ 📌 立规 23：**「没找到」和「找错了」在日志上同形**；
//        探针失败时第一反应应该是**把选择器放宽、把 class 一起 dump 出来**，而不是改判据。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';

const rec = { 批次: '157e', 目的: '放宽探针：把项目下拉的真实结构与删除入口 dump 出来' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b157e.json', import.meta.url), JSON.stringify(rec, null, 1));
const 串 = (x, n) => { const s = JSON.stringify(x, null, 1); return s === undefined ? 'undefined' : s.slice(0, n || 2000); };

const { b, p } = await openCanvas();
const R = readers(p);
const dump = (tag) => p.evaluate((t) => {
  const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; };
  const 可见 = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const 层 = Array.from(document.querySelectorAll('[data-state=open],[role=menu],[role=listbox],[role=dialog],[role=alertdialog],[data-radix-popper-content-wrapper]'))
    .filter(可见).map((e) => ({ tag: e.tagName, role: e.getAttribute('role'), testid: e.getAttribute('data-testid'),
      state: e.getAttribute('data-state'), cls: (e.className || '').toString().slice(0, 70), 盒: 盒(e),
      逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300) }));
  // 所有含「删除 / 移除 / 管理 / 更多」字样的可见元素
  const 危险 = Array.from(document.querySelectorAll('button,a,[role=button],[role=menuitem],[role=option],li,div,span'))
    .filter((e) => { const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
      if (t.length > 24 || !t) return false;
      if (!/删除|移除|管理|Delete|Remove|更多|设置|重命名/.test(t)) return false;
      if (!可见(e)) return false;
      if (e.children.length && Array.from(e.children).some((c) => (c.innerText || '').replace(/\s+/g, ' ').trim() === t)) return false;
      return true; })
    .map((e) => ({ tag: e.tagName, role: e.getAttribute('role'), testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
      cls: (e.className || '').toString().slice(0, 60), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim(), 盒: 盒(e) }));
  // 所有可见链接（项目切换器多半是 <a href>）
  const 链接 = Array.from(document.querySelectorAll('a[href]')).filter(可见)
    .map((e) => ({ href: e.getAttribute('href'), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30), 盒: 盒(e) }));
  return { 阶段: t, 层, 危险, 链接 };
}, tag);

try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1000);
  rec.起点 = { URL: p.url(), 状态行: await R.status(), 积分: await R.credits() };
  rec.点前 = await dump('点前');
  console.log('点前 可见层', (rec.点前.层 || []).length, '| 链接', (rec.点前.链接 || []).length, '| 危险词', (rec.点前.危险 || []).length);
  console.log('点前 链接', 串(rec.点前.链接, 1200));

  const t = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-project-trigger"]'); if (!e) return null;
    const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  rec.触发点 = t;
  if (t) { await p.mouse.click(t[0], t[1]); await p.waitForTimeout(2200); }
  rec.点后 = await dump('点后');
  落盘();
  console.log('\n点后 可见层', (rec.点后.层 || []).length);
  console.log('层', 串(rec.点后.层, 2400));
  console.log('链接', 串(rec.点后.链接, 2400));
  console.log('危险词', 串(rec.点后.危险, 1200));
  断言('① 点「项目」后有可见浮层出现', (rec.点后.层 || []).length > (rec.点前.层 || []).length,
    { 前: (rec.点前.层 || []).length, 后: (rec.点后.层 || []).length });
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }
try { await settle(p, R); } catch (e) { rec.收尾异常 = String(e.message || e).slice(0, 200); }
rec.收尾 = { URL: p.url(), 浮层: await R.overlays(), 积分: await R.credits() };
rec.断言全过 = 断言过; 落盘();
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');
process.exit(0);
