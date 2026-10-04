// 批次 160-e —— 把两条冒出来的新事实钉死：
//   ① 导演台**被选中时到底有没有浮动工具条**（手册写「无」，本轮读到 `680×204`）
//   ② 按 F 的静默是**真静默**还是采样太稀（音频那行是 8 次 / 3000ms）
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf } from './jimeng-b139-lib.mjs';

const rec = { 批次: '160e', 目的: '钉死「导演台有没有浮动工具条」与「按 F 是不是真静默」' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b160e.json', import.meta.url), JSON.stringify(rec, null, 1));
const 出图 = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const 画布URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';

const { b, p } = await openCanvas();
const R = readers(p);
const 读节点 = (id) => p.evaluate((i) => {
  const n = document.querySelector('.react-flow__node[data-id="' + i + '"]');
  if (!n) return null;
  const r = n.getBoundingClientRect();
  return { 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
    中心在屏: r.x + r.width / 2 > 40 && r.x + r.width / 2 < innerWidth - 40 && r.y + r.height / 2 > 40 && r.y + r.height / 2 < innerHeight - 40 };
}, id);
const 工具态 = () => p.evaluate(() => { const t = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]'); if (!t) return null;
  const r = t.getBoundingClientRect(); return { aria: t.getAttribute('aria-label'), 落点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; });
const 切抓手 = async () => { const t = await 工具态(); if (t && !/抓手/.test(t.aria || '')) { await p.mouse.click(t.落点[0], t.落点[1]); await p.waitForTimeout(800); } };
const 切选择 = async () => { const t = await 工具态(); if (t && !/选择/.test(t.aria || '')) { await p.mouse.click(t.落点[0], t.落点[1]); await p.waitForTimeout(800); } };

try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1000);
  const 建前 = await idsOf(p);
  rec.起点 = { 状态行: await R.status(), 节点数: 建前.length, 选中: await selCount(p), 积分: await R.credits() };
  console.log('起点', JSON.stringify(rec.起点));

  const 候选 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => ({
    id: n.getAttribute('data-id'), 逐字: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40) })).filter((z) => /导演台/.test(z.逐字)));
  const SELF = 候选[0]?.id || null;
  rec.SELF = SELF;
  断言('⓪ 画布上有且只有一个「导演台」节点', 候选.length === 1, { 候选 });

  if (SELF) {
    // ---- ① 平移到中心在视口内 ----
    await 切抓手();
    for (let k = 0; k < 8; k++) {
      const cur = await 读节点(SELF);
      if (cur && cur.中心在屏) break;
      const dx = Math.round(640 - cur.中心[0]), dy = Math.round(360 - cur.中心[1]);
      const 起 = [1150, 660], 终 = [Math.min(1272, 起[0] + dx), Math.min(712, 起[1] + dy)];
      if (终[0] === 起[0] && 终[1] === 起[1]) break;
      await p.mouse.move(起[0], 起[1]); await p.mouse.down();
      await p.mouse.move(终[0], 终[1], { steps: 12 }); await p.mouse.up();
      await p.waitForTimeout(1100);
    }
    await 切选择();
    const 到位 = await 读节点(SELF);
    落盘();
    断言('① 节点中心已进视口', !!到位 && 到位.中心在屏, 到位);

    // ---- ② 对照：**没选中**时有没有浮动工具条 ----
    rec.未选中时工具条 = await p.evaluate(() => { const t = document.querySelector('[data-testid="node-toolbar"]');
      if (!t) return null; const r = t.getBoundingClientRect();
      return { 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)], 父: t.parentElement?.getAttribute('data-testid') || null,
        同级数: t.parentElement ? t.parentElement.children.length : null }; });
    console.log('未选中时工具条 =', JSON.stringify(rec.未选中时工具条));

    // ---- ③ 选中后读工具条全部内容 ----
    await p.mouse.click(到位.中心[0], 到位.中心[1]);
    await p.waitForTimeout(1800);
    rec.选中数 = await selCount(p);
    rec.选中后工具条 = await p.evaluate(() => {
      const t = document.querySelector('[data-testid="node-toolbar"]');
      if (!t) return { 有: false };
      const r = t.getBoundingClientRect();
      const 节点 = t.closest('.react-flow__node');
      const nr = 节点 ? 节点.getBoundingClientRect() : null;
      return { 有: true, 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
        挂在: 节点 ? 节点.getAttribute('data-id') : null,
        节点盒: nr ? [Math.round(nr.width), Math.round(nr.height), Math.round(nr.x), Math.round(nr.y)] : null,
        中心dx: nr ? Math.round((r.x + r.width / 2) - (nr.x + nr.width / 2)) : null,
        底到顶: nr ? Math.round(nr.y - (r.y + r.height)) : null,
        按钮: Array.from(t.querySelectorAll('button,[role=button]')).map((e) => {
          const q = e.getBoundingClientRect();
          return { value: e.getAttribute('data-toolbar-value'), aria: e.getAttribute('aria-label'), title: e.getAttribute('title'),
            逐字: (e.innerText || '').trim().slice(0, 18), 盒: [Math.round(q.width), Math.round(q.height)] };
        }),
        逐字: (t.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160) };
    });
    console.log('选中数 =', rec.选中数, '| 工具条 =', JSON.stringify(rec.选中后工具条).slice(0, 800));
    落盘();
    断言('② 选中数 = 1', rec.选中数 === 1, { 选中数: rec.选中数 });
    断言('③ 选中后**确实存在**浮动工具条', rec.选中后工具条.有 === true, rec.选中后工具条);
    if (rec.选中后工具条.有 && rec.选中后工具条.挂在 === SELF) {
      await p.evaluate(() => { const t = document.querySelector('[data-testid="node-toolbar"]'); if (!t) return false;
        const r = t.getBoundingClientRect(); const ov = document.createElement('div'); ov.id = '__hl__';
        ov.style.cssText = 'position:fixed;pointer-events:none;z-index:2147483647;border:3px solid rgb(255,146,48);border-radius:10px;box-sizing:border-box;left:' + (r.x - 4) + 'px;top:' + (r.y - 4) + 'px;width:' + (r.width + 8) + 'px;height:' + (r.height + 8) + 'px;';
        document.body.appendChild(ov); return true; });
      await p.waitForTimeout(600);
      await p.screenshot({ path: new URL('./120-director-selected-toolbar.png', 出图).pathname });
      rec.图 = 'screenshots/120-director-selected-toolbar.png';
      await p.evaluate(() => { const e = document.getElementById('__hl__'); if (e) e.remove(); return true; });
      console.log('🖼 已拍 120');
    }

    // ---- ④ 按 F，**密集采样 16 × 300ms** ----
    const 取景 = async () => p.evaluate((id) => {
      const n = document.querySelector('.react-flow__node[data-id="' + id + '"]');
      const 开 = Array.from(document.querySelectorAll('[data-state=open]')).map((d) => d.getAttribute('data-testid') || d.getAttribute('data-radix-popper-content-wrapper') || d.tagName);
      const 对话 = Array.from(document.querySelectorAll('[role=dialog]')).map((d) => (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60));
      const 提示 = Array.from(document.querySelectorAll('div')).filter((d) => d.children.length === 0 && /此快捷键当前不可用/.test(d.innerText || '')).length;
      const toast = Array.from(document.querySelectorAll('[data-sonner-toast],[data-radix-toast],li')).filter((d) => /不可用|失败|已/.test(d.innerText || '')).length;
      return { 节点逐字: n ? (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 110) : null,
        选中: !!document.querySelector('.react-flow__node.selected'), 开浮层: 开.length, 对话框: 对话, 不可用提示: 提示, toast,
        选中工具条: !!document.querySelector('[data-testid="node-toolbar"]'),
        全局可见元素: document.querySelectorAll('body *').length };
    }, SELF);
    rec.按F前 = await 取景();
    rec.采样 = [];
    await p.keyboard.press('f');
    for (let i = 0; i < 16; i++) {
      await p.waitForTimeout(300);
      const s = await 取景(); s.毫秒 = (i + 1) * 300; s.URL = p.url();
      rec.采样.push(s);
    }
    rec.跳走 = rec.采样.some((z) => z.URL !== rec.按F前URL);
    rec.与前不同的帧 = rec.采样.map((s, i) => {
      const a = rec.按F前, 变 = [];
      if (s.节点逐字 !== a.节点逐字) 变.push('节点逐字');
      if (s.开浮层 !== a.开浮层) 变.push('开浮层');
      if (s.对话框.length !== a.对话框.length) 变.push('对话框');
      if (s.不可用提示 !== a.不可用提示) 变.push('不可用提示');
      if (s.选中工具条 !== a.选中工具条) 变.push('选中工具条');
      if (s.全局可见元素 !== a.全局可见元素) 变.push('全局元素数');
      return 变.length ? { 毫秒: s.毫秒, 变 } : null;
    }).filter(Boolean);
    rec.结论_全程无变化 = rec.与前不同的帧.length === 0;
    落盘();
    console.log('按 F 前 =', JSON.stringify(rec.按F前));
    console.log('与按 F 前不同的帧 =', JSON.stringify(rec.与前不同的帧));
    断言('④ **按 F 全程零变化**（16 × 300ms，无导航、无对话框、无提示、无浮层）', rec.结论_全程无变化 && !rec.跳走, { 跳走: rec.跳走, 变过的帧: rec.与前不同的帧 });
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

try { await 切选择(); } catch (e) {}
try {
  if (p.url() !== 画布URL) { await p.goto(画布URL, { waitUntil: 'domcontentloaded', timeout: 90000 }); await p.waitForTimeout(9000); }
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
} catch (e) {}
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
断言('⑤ 收尾回到基线', rec.收尾.节点数 === 76 && rec.收尾.选中 === 0 && rec.收尾.浮层 === 0 && /选择/.test(String(rec.收尾.工具?.aria || '')) && String(rec.收尾.积分) === String(rec.起点.积分), { 起点: rec.起点, 收尾: rec.收尾 });
rec.断言全过 = 断言过; 落盘();
console.log('断言全过 =', rec.断言全过);
process.exit(0);
