// 批次 156-l —— **只读**：账号级「Dreamina Subjects」有没有管理入口（决定敢不敢真存一个主体）
//
// 156-k 已经把「保存到主体库」的前半程（弹设置主体对话框 → 必填名称 → 保存转可用）测完了。
// 剩下唯一未知的半程是「点保存之后写到哪、能不能删」。
// 🔴 **写共享数据前必须先确认清得掉** —— 这是本项目的硬规矩，不因为「已经授权」就豁免。
//    所以本轮**一个写入动作都不做**，只把全局 chrome 里的入口翻一遍。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf } from './jimeng-b139-lib.mjs';

const rec = { 批次: '156l', 目的: '只读：找账号级主体库（Dreamina Subjects）的管理入口' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b156l.json', import.meta.url), JSON.stringify(rec, null, 1));
const 串 = (x, n) => { const s = JSON.stringify(x, null, 1); return s === undefined ? 'undefined' : s.slice(0, n || 2000); };

const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1000);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 积分: await R.credits() };
  console.log('起点', JSON.stringify(rec.起点));

  // ===== ① 全局 chrome：画布节点之外的可见可点物 =====
  rec.chrome = await p.evaluate(() => {
    const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; };
    return Array.from(document.querySelectorAll('button,a,[role=button],[role=tab],[role=menuitem],[role=link]'))
      .filter((e) => { if (e.closest('.react-flow__node')) return false;
        if (e.closest('[data-testid="node-toolbar"]')) return false;
        const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
      .map((e) => ({ tag: e.tagName, role: e.getAttribute('role'), testid: e.getAttribute('data-testid'),
        aria: (e.getAttribute('aria-label') || '').slice(0, 70),
        href: e.getAttribute('href'),
        逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 26), 盒: 盒(e) }));
  });
  rec.chrome数 = rec.chrome.length;
  console.log('chrome 可点数', rec.chrome数);
  console.log('chrome 清单', 串(rec.chrome, 3000));
  rec.命中主体 = rec.chrome.filter((z) => /主体|账号|账户|个人|设置|资料|我的|Subject|Account|Profile|Settings/i.test((z.aria || '') + z.逐字 + (z.testid || '')));
  落盘();
  console.log('\n🆕 主体/账号相关', 串(rec.命中主体, 1400));
  断言('① 全局 chrome 里存在「主体库 / 账号」类入口（可判定清得掉）', rec.命中主体.length > 0, { 命中: rec.命中主体 });

  // ===== ② 顶栏 testid 全量（找没 aria 的纯图标入口）=====
  rec.顶栏 = await p.evaluate(() => {
    const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; };
    return Array.from(document.querySelectorAll('[data-testid]'))
      .filter((e) => !e.closest('.react-flow__node') && e.getBoundingClientRect().y < 120)
      .map((e) => ({ testid: e.getAttribute('data-testid'), tag: e.tagName, role: e.getAttribute('role'),
        aria: (e.getAttribute('aria-label') || '').slice(0, 50), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30), 盒: 盒(e) }))
      .filter((z) => z.盒[0] > 0);
  });
  console.log('\n顶栏 testid', 串(rec.顶栏, 2200));

  // ===== ③ 左栏 / 侧栏全量（找纯 testid 入口）=====
  rec.左栏 = await p.evaluate(() => {
    const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; };
    return Array.from(document.querySelectorAll('[data-testid]'))
      .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && r.x < 80 && r.y > 100; })
      .map((e) => ({ testid: e.getAttribute('data-testid'), aria: (e.getAttribute('aria-label') || '').slice(0, 40),
        逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20), 盒: 盒(e) }));
  });
  console.log('\n左栏 testid', 串(rec.左栏, 1600));

  // ===== ④ 主体节点里的「导入主体」模态 —— 那里可能有「去管理」入口 =====
  const 主节点 = await p.evaluate(() => {
    const n = Array.from(document.querySelectorAll('.react-flow__node')).find((e) => /subject/i.test(e.className || '') || (e.innerText || '').indexOf('主体') >= 0);
    if (!n) return null; const r = n.getBoundingClientRect();
    return { cls: (n.className || '').toString().slice(0, 80), id: n.getAttribute('data-id'),
      逐字: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160), 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] };
  });
  rec.主体节点 = 主节点;
  console.log('\n主体节点', JSON.stringify(主节点));
  落盘();
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

await settle(p, R);
const mm = await R.minimap();
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(),
  zoom: await R.zoom(), 积分: await R.credits() };
rec.断言全过 = 断言过; 落盘();
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');
await b.close();
