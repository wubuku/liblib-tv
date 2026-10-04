// 批次 160-b —— 结清「导演台 F」：先把**在视口外**的节点平移进视口，再点选、再按 F
//
// 🔴 160-a 踩到的坑（立规 16 的又一次）：导演台节点 `node_pxvkay973v` 的中心在
//    **`[-131,-180]`——视口外**。于是点击落空、选中数 0，
//    后面那 10 次采样测的其实是「**什么都没选**时按 F」，
//    而那一条手册里**早就写过了** ⇒ 整个实验作废。
//    ⇒ 本轮先把节点**平移进视口**，确认「选中数 = 1」之后才按 F。
//
// 🔑 平移怎么算：react-flow 里 `屏幕坐标 = 画布坐标 × 缩放 + translate`，
//    拖拽 (dx,dy) 就让 translate 加 (dx,dy) ⇒ 要把节点从 [-131,-180] 挪到画面中心
//    (640,360)，需要 **(+771, +540)**。
//    起点必须落在 `.react-flow__pane` 的空白处（不能压在别的节点上）。
//
// 🔴 边界不变：只做**导航判定**；若真跳进 3D 工作台，只读屏上信息 + 拍图，然后回画布。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf } from './jimeng-b139-lib.mjs';

const rec = { 批次: '160b', 目的: '把视口外的导演台节点平移进视口 → 点选 → 按 F 判导航' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b160b.json', import.meta.url), JSON.stringify(rec, null, 1));
const 出图 = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const 画布URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';

const { b, p } = await openCanvas();
const R = readers(p);

const 读节点 = (id) => p.evaluate((i) => {
  const n = document.querySelector('.react-flow__node[data-id="' + i + '"]');
  if (!n) return null;
  const r = n.getBoundingClientRect();
  return { 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 盒: [Math.round(r.width), Math.round(r.height)],
    在屏: r.x + r.width > 0 && r.y + r.height > 0 && r.x < innerWidth && r.y < innerHeight,
    逐字: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 90) };
}, id);

const 找空白 = () => p.evaluate(() => {
  const 在节点上 = (x, y) => !!document.elementFromPoint(x, y)?.closest('.react-flow__node');
  for (const pt of [[200, 150], [150, 620], [1100, 150], [640, 640], [120, 350]]) if (!在节点上(pt[0], pt[1])) return pt;
  return null;
});

try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
  const 建前 = await idsOf(p);
  rec.起点 = { 状态行: await R.status(), 节点数: 建前.length, 选中: await selCount(p), 积分: await R.credits() };
  console.log('起点', JSON.stringify(rec.起点));

  const 候选 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => ({
    id: n.getAttribute('data-id'), 逐字: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40) })).filter((z) => /导演台/.test(z.逐字)));
  const SELF = 候选[0]?.id || null;
  rec.SELF = SELF;
  断言('⓪ 画布上有且只有一个「导演台」节点', 候选.length === 1, { 候选 });

  if (SELF) {
    rec.平移前 = await 读节点(SELF);
    console.log('平移前 =', JSON.stringify(rec.平移前));

    // ---- ① 平移：最多试 3 次，每次按实测差值补 ----
    rec.平移 = [];
    for (let k = 0; k < 3; k++) {
      const cur = await 读节点(SELF);
      if (cur && cur.在屏) { rec.平移.push({ 轮: k, 已进屏: true }); break; }
      const dx = Math.round(640 - cur.中心[0]);
      const dy = Math.round(360 - cur.中心[1]);
      const 起 = await 找空白();
      if (!起) { rec.平移.push({ 轮: k, 错: '找不到空白起点' }); break; }
      const 终 = [Math.min(1270, Math.max(10, 起[0] + dx)), Math.min(710, Math.max(10, 起[1] + dy))];
      const 实拖 = [终[0] - 起[0], 终[1] - 起[1]];
      await p.mouse.move(起[0], 起[1]);
      await p.mouse.down();
      await p.mouse.move(起[0] + 实拖[0] / 2, 起[1] + 实拖[1] / 2, { steps: 6 });
      await p.mouse.move(终[0], 终[1], { steps: 6 });
      await p.mouse.up();
      await p.waitForTimeout(1400);
      const after = await 读节点(SELF);
      rec.平移.push({ 轮: k, 起点: 起, 拖了: 实拖, 之后中心: after ? after.中心 : null, 之后在屏: after ? after.在屏 : null });
      console.log('  平移', k, JSON.stringify(rec.平移[rec.平移.length - 1]));
    }
    const 到位 = await 读节点(SELF);
    rec.平移后 = 到位;
    落盘();
    断言('① 导演台节点已进视口', !!到位 && 到位.在屏, 到位);

    if (到位 && 到位.在屏) {
      // ---- ② 点中它 ----
      await p.mouse.click(到位.中心[0], 到位.中心[1]);
      await p.waitForTimeout(1700);
      rec.选中后 = { 选中数: await selCount(p), 逐字: await 读节点(SELF),
        浮动工具条: await p.evaluate(() => { const t = document.querySelector('[data-testid="node-toolbar"]'); if (!t) return null;
          const r = t.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; }),
        浮层: await R.overlays() };
      console.log('选中后 =', JSON.stringify(rec.选中后).slice(0, 400));
      落盘();
      断言('② **选中数 = 1**（这一步对了才谈得上按 F）', rec.选中后.选中数 === 1, rec.选中后);

      // ---- ③ 按 F ----
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
            顶层文字: (document.body.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 260) };
        });
        s.URL = p.url(); s.毫秒 = (i + 1) * 450;
        if (s.URL !== rec.按F前URL) 跳走 = true;
        rec.采样.push(s);
        if (跳走) break;
      }
      rec.跳走 = 跳走;
      rec.按F后URL = p.url();
      const 末 = rec.采样[rec.采样.length - 1];
      rec.末帧 = { URL: 末.URL, 标题: 末.标题, 对话框数: 末.对话框.length, 对话框: 末.对话框, 不可用提示盒: 末.不可用提示盒, 开浮层: 末.开浮层 };
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

try {
  if (p.url() !== 画布URL) { rec.需回画布 = true; await p.goto(画布URL, { waitUntil: 'domcontentloaded', timeout: 90000 }); await p.waitForTimeout(9000); }
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
} catch (e) { rec.归位异常 = String((e && e.stack) || e).slice(0, 400); }
try {
  const mm = await R.minimap();
  if (!mm || mm.ariaPressed !== 'true') {
    const t = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-display-toggle-minimap"]'); if (!e) return null;
      const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    if (t) { await p.mouse.click(t[0], t[1]); await p.waitForTimeout(1400); }
  }
} catch (e) {}

rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(), zoom: await R.zoom(), 积分: await R.credits() };
rec.断言全过 = 断言过; 落盘();
console.log('收尾', JSON.stringify(rec.收尾));
断言('③ 收尾回到基线：76 节点 / 0 选中 / 0 浮层 / 60% / 积分不变',
  rec.收尾.节点数 === 76 && rec.收尾.选中 === 0 && rec.收尾.浮层 === 0 && String(rec.收尾.积分) === String(rec.起点.积分), { 起点: rec.起点, 收尾: rec.收尾 });
rec.断言全过 = 断言过; 落盘();
console.log('断言全过 =', rec.断言全过);
process.exit(0);
