// 批次 160-c —— 用**抓手工具**平移，把导演台节点拖进视口，再点选、再按 F
//
// 🔴 160-b 踩到的两个坑：
//   ① 在**选择工具**下拖拽空白 = **框选**，不是平移 —— 节点 x 坐标三轮都没动，
//      反而在共享画布上留下 **33 个选中**，收尾断言直接红。
//      ⇒ 立规 30：**「拖拽」在两种工具下是两件事** —— 选择工具拖 = 框选，
//        抓手工具拖 = 平移。想平移**必须先切抓手**，用完切回。
//   ② 收尾的 `settle()` 按 Esc **清不掉框选** ⇒ 选中数要单独清、单独断言。
//
// 本轮顺序：① 清选中 → ② 切抓手 → ③ 拖到节点进视口 → ④ 切回选择工具
//          → ⑤ 点中节点确认「选中数 = 1」→ ⑥ 按 F 判导航 → ⑦ 切回选择工具并归位
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf } from './jimeng-b139-lib.mjs';

const rec = { 批次: '160c', 目的: '抓手工具平移 → 点选 → 按 F 判导航' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b160c.json', import.meta.url), JSON.stringify(rec, null, 1));
const 出图 = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const 画布URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';

const { b, p } = await openCanvas();
const R = readers(p);

const 读节点 = (id) => p.evaluate((i) => {
  const n = document.querySelector('.react-flow__node[data-id="' + i + '"]');
  if (!n) return null;
  const r = n.getBoundingClientRect();
  return { 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 盒: [Math.round(r.width), Math.round(r.height)],
    在屏: r.x + r.width > 0 && r.y + r.height > 0 && r.x < innerWidth && r.y < innerHeight };
}, id);

const 工具态 = () => p.evaluate(() => { const t = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  if (!t) return null; const r = t.getBoundingClientRect();
  return { aria: t.getAttribute('aria-label'), 落点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; });
const 切抓手 = async () => { const t = await 工具态(); if (!t) return null;
  if (!/抓手/.test(t.aria || '')) { await p.mouse.click(t.落点[0], t.落点[1]); await p.waitForTimeout(900); }
  return await 工具态(); };
const 切选择 = async () => { const t = await 工具态(); if (!t) return null;
  if (!/选择/.test(t.aria || '')) { await p.mouse.click(t.落点[0], t.落点[1]); await p.waitForTimeout(900); }
  return await 工具态(); };
const 清选中 = async () => { for (let k = 0; k < 3; k++) { if (await selCount(p) === 0) return true;
    const e = await p.evaluate(() => { const pane = document.querySelector('.react-flow__pane');
      if (!pane) return null; const r = pane.getBoundingClientRect();
      for (const pt of [[r.x + 8, r.y + r.height - 8], [r.x + 12, r.y + 12], [r.x + r.width / 2, r.y + r.height - 10]])
        if (!document.elementFromPoint(pt[0], pt[1])?.closest('.react-flow__node')) return pt;
      return null; });
    if (e) { await p.mouse.click(e[0], e[1]); await p.waitForTimeout(800); } } return await selCount(p) === 0; };

try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1000);
  const 建前 = await idsOf(p);
  rec.起点 = { 状态行: await R.status(), 节点数: 建前.length, 选中: await selCount(p), 积分: await R.credits() };
  console.log('起点', JSON.stringify(rec.起点));

  // ---- ① 先把上一轮遗留的框选清掉 ----
  rec.清理前选中 = await selCount(p);
  rec.清理成功 = await 清选中();
  console.log('清理：', rec.清理前选中, '→', await selCount(p));
  落盘();
  断言('⓪ 先把框选残留清干净', rec.清理成功, { 前: rec.清理前选中, 后: await selCount(p) });

  const 候选 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => ({
    id: n.getAttribute('data-id'), 逐字: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40) })).filter((z) => /导演台/.test(z.逐字)));
  const SELF = 候选[0]?.id || null;
  rec.SELF = SELF;
  断言('① 画布上有且只有一个「导演台」节点', 候选.length === 1, { 候选 });

  if (SELF) {
    rec.平移前 = await 读节点(SELF);
    console.log('平移前 =', JSON.stringify(rec.平移前));

    // ---- ② 切抓手 → 拖 → 切回选择 ----
    rec.工具_抓手前 = await 工具态();
    rec.工具_切抓手后 = await 切抓手();
    console.log('抓手工具 =', JSON.stringify(rec.工具_切抓手后));

    rec.平移 = [];
    for (let k = 0; k < 4; k++) {
      const cur = await 读节点(SELF);
      if (cur && cur.在屏) { rec.平移.push({ 轮: k, 已进屏: true }); break; }
      const dx = Math.round(640 - cur.中心[0]);
      const dy = Math.round(360 - cur.中心[1]);
      const 起 = [1100, 620], 终 = [Math.min(1270, 起[0] + dx), Math.min(710, 起[1] + dy)];
      await p.mouse.move(起[0], 起[1]);
      await p.mouse.down();
      await p.mouse.move(终[0], 终[1], { steps: 12 });
      await p.mouse.up();
      await p.waitForTimeout(1200);
      const after = await 读节点(SELF);
      rec.平移.push({ 轮: k, 起, 终, 拖了: [终[0] - 起[0], 终[1] - 起[1]], 之后中心: after?.中心, 之后在屏: after?.在屏, 之后选中: await selCount(p) });
      console.log('  平移', k, JSON.stringify(rec.平移[rec.平移.length - 1]));
      落盘();
    }
    rec.工具_切回选择 = await 切选择();
    const 到位 = await 读节点(SELF);
    rec.平移后 = 到位;
    rec.平移后选中 = await selCount(p);
    console.log('平移后 =', JSON.stringify(到位), '| 工具 =', JSON.stringify(rec.工具_切回选择));
    落盘();
    断言('② 导演台节点已进视口', !!到位 && 到位.在屏, 到位);
    断言('③ 切回选择工具', /选择/.test(String(rec.工具_切回选择?.aria || '')), rec.工具_切回选择);

    if (到位 && 到位.在屏) {
      await p.mouse.click(到位.中心[0], 到位.中心[1]);
      await p.waitForTimeout(1700);
      rec.选中后 = { 选中数: await selCount(p), 逐字: await p.evaluate((id) => {
        const n = document.querySelector('.react-flow__node[data-id="' + id + '"]');
        return n ? (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 110) : null; }, SELF),
        浮动工具条: await p.evaluate(() => { const t = document.querySelector('[data-testid="node-toolbar"]'); if (!t) return null;
          const r = t.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; }),
        浮层: await R.overlays() };
      console.log('选中后 =', JSON.stringify(rec.选中后).slice(0, 400));
      落盘();
      断言('④ **选中数 = 1**（这一步对了才谈得上按 F）', rec.选中后.选中数 === 1, rec.选中后);

      rec.按F前URL = p.url();
      await p.keyboard.press('f');
      rec.采样 = [];
      let 跳走 = false;
      for (let i = 0; i < 12; i++) {
        await p.waitForTimeout(450);
        const s = await p.evaluate(() => {
          const 对话框 = Array.from(document.querySelectorAll('[role=dialog],[data-testid$="-dialog"]')).slice(0, 4).map((d) => {
            const r = d.getBoundingClientRect();
            return { testid: d.getAttribute('data-testid'), 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
              逐字: (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160) };
          });
          const 提示 = Array.from(document.querySelectorAll('div')).filter((d) => /此快捷键当前不可用/.test(d.innerText || '') && d.children.length === 0)
            .map((d) => { const r = d.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; });
          return { 标题: document.title, 对话框, 不可用提示盒: 提示, 开浮层: document.querySelectorAll('[data-state=open]').length,
            顶层文字: (document.body.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 240) };
        });
        s.URL = p.url(); s.毫秒 = (i + 1) * 450;
        if (s.URL !== rec.按F前URL) 跳走 = true;
        rec.采样.push(s);
        if (跳走) break;
      }
      rec.跳走 = 跳走;
      rec.按F后URL = p.url();
      const 末 = rec.采样[rec.采样.length - 1];
      rec.末帧 = { URL: 末.URL, 标题: 末.标题, 对话框: 末.对话框, 不可用提示盒: 末.不可用提示盒, 开浮层: 末.开浮层 };
      落盘();
      console.log('跳走 =', 跳走, '| 末帧 =', JSON.stringify(rec.末帧).slice(0, 500));

      if (跳走) {
        await p.waitForTimeout(4000);
        rec.工作台 = await p.evaluate(() => ({
          标题: document.title,
          顶层文字: (document.body.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 900),
          可点数: document.querySelectorAll('button,[role=button]').length,
          testid: Array.from(new Set(Array.from(document.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))).slice(0, 40),
        }));
        rec.工作台URL = p.url();
        console.log('工作台 =', JSON.stringify(rec.工作台).slice(0, 800));
        await p.screenshot({ path: new URL('./120-director-3d-workspace.png', 出图).pathname });
        rec.图 = 'screenshots/120-director-3d-workspace.png';
      } else {
        await p.screenshot({ path: new URL('./120-director-f-on-canvas.png', 出图).pathname });
        rec.图 = 'screenshots/120-director-f-on-canvas.png';
      }
      console.log('🖼 已拍 120');
      落盘();
    }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

try { await 切选择(); } catch (e) { rec.切回异常 = String(e.message || e).slice(0, 200); }
try {
  if (p.url() !== 画布URL) { rec.需回画布 = true; await p.goto(画布URL, { waitUntil: 'domcontentloaded', timeout: 90000 }); await p.waitForTimeout(9000); }
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
} catch (e) { rec.归位异常 = String((e && e.stack) || e).slice(0, 400); }
try { await 清选中(); } catch (e) {}
try {
  const mm = await R.minimap();
  if (!mm || mm.ariaPressed !== 'true') {
    const t = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-display-toggle-minimap"]'); if (!e) return null;
      const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    if (t) { await p.mouse.click(t[0], t[1]); await p.waitForTimeout(1400); }
  }
} catch (e) {}

rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(), zoom: await R.zoom(), 积分: await R.credits(), 工具: await 工具态() };
rec.断言全过 = 断言过; 落盘();
console.log('收尾', JSON.stringify(rec.收尾));
断言('⑤ 收尾回到基线：76 节点 / 0 选中 / 0 浮层 / 60% / 选择工具 / 积分不变',
  rec.收尾.节点数 === 76 && rec.收尾.选中 === 0 && rec.收尾.浮层 === 0
  && /选择/.test(String(rec.收尾.工具?.aria || '')) && String(rec.收尾.积分) === String(rec.起点.积分),
  { 起点: rec.起点, 收尾: rec.收尾 });
rec.断言全过 = 断言过; 落盘();
console.log('断言全过 =', rec.断言全过);
process.exit(0);
