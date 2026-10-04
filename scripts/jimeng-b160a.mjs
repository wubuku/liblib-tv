// 批次 160-a —— 🔴 结清全册**最后一个 ⛔**：`help-and-shortcuts.md` 里「导演台 F ⛔ 未验证」
//
// 原文（`help-and-shortcuts.md:254-262`）写：不按 F 的理由是
//   「**不是「按钮会导航」，而是「按键本身未测会不会导航，未验证，因此不冒险**」。
// ⇒ 这一行是全册快捷键表里**唯一**的 ⛔，也是 `:388` 统计里唯一的「❓ 未验证 1」。
//
// 🔑 边界：本脚本只做**导航判定** —— 按一次 F，看它到不到 3D 工作台。
//    **不点 3D 工作台里的任何生成/发送/确认按钮，不碰任何扣费入口。**
//    若真跳进 3D 工作台，只读屏上可见信息 + 拍一张图，然后**直接导航回共享画布**。
//
// 🔴 建-删护栏：本轮**不新建任何节点**（导演台节点是画布上已有的），
//    所以只需保证「回来之后 76 节点 / 0 选中 / 60% / 小地图开 / 浮层 0」。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf, canvasPos } from './jimeng-b139-lib.mjs';

const rec = { 批次: '160a', 目的: '导演台节点上按 F：到底会不会跳进 3D 工作台' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b160a.json', import.meta.url), JSON.stringify(rec, null, 1));
const 出图 = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const 画布URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';

const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
  const 建前 = await idsOf(p);
  rec.起点 = { URL: p.url(), 状态行: await R.status(), 节点数: 建前.length, 选中: await selCount(p), 积分: await R.credits() };
  console.log('起点', JSON.stringify(rec.起点));

  // ---- ① 找到画布上已有的「导演台」节点 ----
  const 候选 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
    const t = (n.innerText || '').replace(/\s+/g, ' ').trim();
    const r = n.getBoundingClientRect();
    return { id: n.getAttribute('data-id'), 逐字: t.slice(0, 60), 在屏: r.x + r.width > 0 && r.y + r.height > 0 && r.x < innerWidth && r.y < innerHeight,
      中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 盒: [Math.round(r.width), Math.round(r.height)] };
  }).filter((z) => /导演台/.test(z.逐字)));
  rec.导演台候选 = 候选;
  console.log('导演台候选 =', JSON.stringify(候选));
  const SELF = 候选.length === 1 ? 候选[0] : (候选.find((z) => z.在屏) || 候选[0]);
  rec.SELF = SELF ? SELF.id : null;
  断言('⓪ 画布上有且只有一个「导演台」节点', 候选.length === 1, { 候选数: 候选.length });

  if (SELF) {
    // ---- ② 点中它，并记录选中态 ----
    await p.mouse.click(SELF.中心[0], SELF.中心[1]);
    await p.waitForTimeout(1600);
    rec.选中后 = { 选中数: await selCount(p), 逐字: await p.evaluate((id) => {
      const n = document.querySelector('.react-flow__node[data-id="' + id + '"]');
      return n ? (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120) : null; }, SELF.id),
      浮动工具条: await p.evaluate(() => { const t = document.querySelector('[data-testid="node-toolbar"]'); if (!t) return null;
        const r = t.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; }),
      浮层: await R.overlays() };
    console.log('选中后 =', JSON.stringify(rec.选中后));
    落盘();
    断言('① 点中后选中数 = 1', rec.选中后.选中数 === 1, rec.选中后);
    rec.按F前URL = p.url();

    // ---- ③ 按 F，连采 10 次 URL / 浮层 / 对话框 ----
    await p.keyboard.press('f');
    rec.采样 = [];
    let 跳走了 = false;
    for (let i = 0; i < 10; i++) {
      await p.waitForTimeout(450);
      const s = await p.evaluate(() => {
        const 对话框 = Array.from(document.querySelectorAll('[role=dialog],[data-testid$="-dialog"]')).slice(0, 4).map((d) => {
          const r = d.getBoundingClientRect();
          return { testid: d.getAttribute('data-testid'), 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
            逐字: (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160) };
        });
        const 顶层文字 = (document.body.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300);
        return { 标题: document.title, 对话框数: 对话框.length, 对话框, 顶层文字,
          可点: Array.from(document.querySelectorAll('button,[role=button]')).length,
          开浮层: document.querySelectorAll('[data-state=open]').length };
      });
      s.URL = p.url();
      s.采样秒 = (i + 1) * 450;
      if (s.URL !== rec.按F前URL) 跳走了 = true;
      rec.采样.push(s);
      if (跳走了) break;
    }
    rec.跳走 = 跳走了;
    rec.按F后URL = p.url();
    console.log('跳走 =', 跳走了, '| URL =', p.url().slice(0, 120));
    const 末 = rec.采样[rec.采样.length - 1];
    rec.末帧 = { URL: 末.URL, 标题: 末.标题, 对话框数: 末.对话框数, 可点: 末.可点, 开浮层: 末.开浮层 };
    落盘();
    console.log('末帧 =', JSON.stringify(rec.末帧));

    if (跳走了) {
      // ---- ④ 只读记录 3D 工作台，绝不点任何生成/发送/确认/扣费 ----
      await p.waitForTimeout(3500);
      rec.工作台 = await p.evaluate(() => ({
        标题: document.title,
        顶层文字: (document.body.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 900),
        可点数: document.querySelectorAll('button,[role=button]').length,
        testid: Array.from(new Set(Array.from(document.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))).slice(0, 40),
      }));
      rec.工作台URL = p.url();
      console.log('工作台 =', JSON.stringify(rec.工作台).slice(0, 700));
      await p.screenshot({ path: new URL('./120-director-3d-workspace.png', 出图).pathname });
      rec.图 = 'screenshots/120-director-3d-workspace.png';
      console.log('🖼 已拍 120（只读记录，不做任何操作）');
    } else {
      await p.screenshot({ path: new URL('./120-director-f-no-navigation.png', 出图).pathname });
      rec.图 = 'screenshots/120-director-f-no-navigation.png';
      console.log('🖼 已拍 120');
    }
    落盘();
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

// ---- 收尾：无论跳没跳走，都回到共享画布并归位 ----
try {
  if (p.url() !== 画布URL) {
    rec.需回画布 = true;
    await p.goto(画布URL, { waitUntil: 'domcontentloaded', timeout: 90000 });
    await p.waitForTimeout(9000);
  }
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

rec.收尾 = { URL: p.url(), 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(), zoom: await R.zoom(), 积分: await R.credits() };
rec.断言全过 = 断言过; 落盘();
console.log('收尾', JSON.stringify(rec.收尾));
断言('② 收尾回到共享画布：76 节点 / 0 选中 / 0 浮层 / 60% / 积分不变',
  rec.收尾.节点数 === 76 && rec.收尾.选中 === 0 && rec.收尾.浮层 === 0 && String(rec.收尾.积分) === String(rec.起点.积分), { 起点: rec.起点, 收尾: rec.收尾 });
rec.断言全过 = 断言过; 落盘();
console.log('断言全过 =', rec.断言全过);
process.exit(0);
