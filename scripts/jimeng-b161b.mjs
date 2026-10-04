// 批次 161-b —— 核验「查看积分明细」这个「跳走」型按钮的**目的地**
//
// 🔑 靶子（`canvas-context.md:366-368`）：项目信息对话框「积分消耗」页签里那个
//    `查看积分明细`（BUTTON `94×36@922,573`，无 href / target / aria-label，未禁用，
//    界面右侧带右向箭头 ⇒ 是「跳走」型动作）—— 本手册**未执行**，目的地**未验证**。
//    原文给的不执行理由是「它很可能跳出到积分/充值页，而充值/订阅/积分购买不在范围内」。
//
// 🔴 边界：**只按那一下看它到哪**，**不在落地页点任何充值/订阅/购买按钮**。
//    若它开新页签，只读屏上可见信息 + 拍图，然后关掉并回共享画布。
//
// ⚠️ 纪律：打开模态后**绝不调 settle()**（它会连按 Esc 把刚开的模态关掉）。
//    所以本脚本从头到尾不调用 settle，只用 keyGuard + setZoom 做前置。
import fs from 'node:fs';
import { openCanvas, readers, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf } from './jimeng-b139-lib.mjs';

const rec = { 批次: '161b', 目的: '「查看积分明细」的目的地（只按一下，不在落地页做任何操作）' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b161b.json', import.meta.url), JSON.stringify(rec, null, 1));
const 出图 = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const 画布URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';

const { b, p } = await openCanvas();
const R = readers(p);
let 落地页 = null; let 落地页签 = null;

try {
  await keyGuard(p); await setZoom(p, 60); await p.waitForTimeout(1200);
  const 建前 = await idsOf(p);
  rec.起点 = { 状态行: await R.status(), 节点数: 建前.length, 选中: await selCount(p), 积分: await R.credits() };
  console.log('起点', JSON.stringify(rec.起点));

  // ---- ① 顶栏「更多」 ----
  const 更多落 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('button,[role=button]'))
    .find((x) => (x.getAttribute('aria-label') || '') === '更多'); if (!e) return null;
    const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  rec.更多落 = 更多落;
  断言('⓪ 顶栏找得到「更多」按钮', !!更多落, { 更多落 });
  if (更多落) {
    await p.mouse.click(更多落[0], 更多落[1]);
    await p.waitForTimeout(1300);
    rec.更多菜单 = await p.evaluate(() => { const m = document.querySelector('[role=menu]'); if (!m) return null;
      const r = m.getBoundingClientRect();
      return { 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
        项: Array.from(m.querySelectorAll('[role=menuitem]')).map((i) => (i.innerText || '').trim()) }; });
    console.log('更多菜单 =', JSON.stringify(rec.更多菜单));
    落盘();

    // ---- ② 「项目信息」 ----
    const 项落 = await p.evaluate(() => { const m = document.querySelector('[role=menu]'); if (!m) return null;
      const it = Array.from(m.querySelectorAll('[role=menuitem]')).find((i) => (i.innerText || '').trim() === '项目信息'); if (!it) return null;
      const r = it.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    if (项落) {
      await p.mouse.click(项落[0], 项落[1]);
      await p.waitForTimeout(2200);
      rec.对话框 = await p.evaluate(() => { const d = document.querySelector('[data-testid="workspace-project-info-dialog"]'); if (!d) return { 有: false };
        const r = d.getBoundingClientRect();
        return { 有: true, 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
          逐字: (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 220),
          页签: Array.from(d.querySelectorAll('[role=tab]')).map((t) => ({ 逐字: (t.innerText || '').trim(), 选中: t.getAttribute('aria-selected') })) }; });
      console.log('对话框 =', JSON.stringify(rec.对话框).slice(0, 500));
      落盘();
      断言('① 「项目信息」对话框打开了', rec.对话框.有 === true, rec.对话框);

      // ---- ③ 切到「积分消耗」页签 ----
      const 页签落 = await p.evaluate(() => { const d = document.querySelector('[data-testid="workspace-project-info-dialog"]'); if (!d) return null;
        const t = Array.from(d.querySelectorAll('[role=tab]')).find((x) => (x.innerText || '').trim() === '积分消耗'); if (!t) return null;
        const r = t.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
      if (页签落) {
        await p.mouse.click(页签落[0], 页签落[1]);
        await p.waitForTimeout(1600);
        rec.积分消耗页签 = await p.evaluate(() => { const d = document.querySelector('[data-testid="workspace-project-info-dialog"]'); if (!d) return null;
          const pn = d.querySelector('[role=tabpanel]'); if (!pn) return null; const r = pn.getBoundingClientRect();
          return { 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
            逐字: (pn.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 180) }; });
        console.log('积分消耗页签 =', JSON.stringify(rec.积分消耗页签));
        落盘();

        // ---- ④ 「查看积分明细」按钮的完整属性 ----
        const 钮 = await p.evaluate(() => { const d = document.querySelector('[data-testid="workspace-project-info-dialog"]'); if (!d) return null;
          const btns = Array.from(d.querySelectorAll('button')).map((e) => { const r = e.getBoundingClientRect();
            return { 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20), 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
              href: e.getAttribute('href'), target: e.getAttribute('target'), aria: e.getAttribute('aria-label'),
              testid: e.getAttribute('data-testid'), 禁用: e.disabled || e.getAttribute('aria-disabled') }; });
          return btns; });
        rec.对话框按钮 = 钮;
        const 目标 = (钮 || []).find((z) => /积分明细/.test(z.逐字 || ''));
        rec.目标按钮 = 目标;
        console.log('目标按钮 =', JSON.stringify(目标));
        落盘();
        断言('② 「积分消耗」页签里找得到「查看积分明细」按钮', !!目标, { 按钮: 钮 });

        if (目标) {
          const 落 = [目标.盒[2] + 目标.盒[0] / 2, 目标.盒[3] + 目标.盒[1] / 2];
          rec.点前页签数 = p.context().pages().length;
          rec.点前URL = p.url();
          await p.mouse.click(落[0], 落[1]);
          // 连采，看它是同页跳走还是开新页签
          rec.采样 = [];
          for (let i = 0; i < 10; i++) {
            await p.waitForTimeout(450);
            const 页签列表 = p.context().pages().map((pg) => pg.url());
            rec.采样.push({ 毫秒: (i + 1) * 450, 页签数: 页签列表.length, 页签URL: 页签列表.map((u) => u.slice(0, 130)) });
            if (页签列表.length > rec.点前页签数) break;
          }
          rec.开新页签 = p.context().pages().length > rec.点前页签数;
          rec.点后URL = p.url();
          console.log('开新页签 =', rec.开新页签, '| 点后 URL =', rec.点后URL.slice(0, 130));
          落盘();

          const 目标页 = p.context().pages()[p.context().pages().length - 1];
          if (rec.开新页签) 落地页签 = 目标页;
          await 目标页.waitForTimeout(2600);
          rec.落地 = await 目标页.evaluate(() => ({
            标题: document.title,
            URL: location.href,
            逐字: (document.body.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 800),
            按钮: Array.from(document.querySelectorAll('button,[role=button]')).slice(0, 18).map((e) => {
              const r = e.getBoundingClientRect();
              return { 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 22), 盒: [Math.round(r.width), Math.round(r.height)] }; }),
            testid: Array.from(new Set(Array.from(document.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))).slice(0, 30),
          }));
          console.log('落地 =', JSON.stringify(rec.落地).slice(0, 900));
          await 目标页.screenshot({ path: new URL('./121-credits-detail-destination.png', 出图).pathname });
          rec.图 = 'screenshots/121-credits-detail-destination.png';
          落地页 = 目标页;
          console.log('🖼 已拍 121');
          落盘();
        }
      }
    }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

// ---- 收尾：关掉落地页 / 回画布 / 归位 ----
try {
  if (落地页签) { await 落地页签.close(); rec.已关落地页签 = true; }
  const 页 = p.context().pages();
  for (const pg of 页) { if (pg !== p) { await pg.close().catch(() => {}); } }
} catch (e) { rec.关页异常 = String(e.message || e).slice(0, 200); }
try {
  if (p.url() !== 画布URL) { rec.需回画布 = true; await p.goto(画布URL, { waitUntil: 'domcontentloaded', timeout: 90000 }); await p.waitForTimeout(9000); }
  await keyGuard(p); await setZoom(p, 60); await p.waitForTimeout(1200);
} catch (e) { rec.归位异常 = String((e && e.stack) || e).slice(0, 400); }

rec.收尾 = { 页签数: p.context().pages().length, 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(), zoom: await R.zoom(), 积分: await R.credits() };
rec.断言全过 = 断言过; 落盘();
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');
断言('③ 收尾回到共享画布：1 个页签 / 76 节点 / 0 选中 / 0 浮层 / 60% / 积分不变',
  rec.收尾.页签数 === 1 && rec.收尾.节点数 === 76 && rec.收尾.选中 === 0 && rec.收尾.浮层 === 0 && String(rec.收尾.积分) === String(rec.起点.积分),
  { 起点: rec.起点, 收尾: rec.收尾 });
rec.断言全过 = 断言过; 落盘();
console.log('断言全过 =', rec.断言全过);
process.exit(0);
