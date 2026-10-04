// 批次 157-c —— 「更多菜单」一簇：复制项目的确认步 + 「查看积分明细」到底是新标签页还是同页跳转
//
// 🆕 157-b 刚拿到的关键读数（决定了本轮哪些能碰、哪些不能碰）：
//   点「创建团队」**不是**弹出「建团队」对话框，而是跳到**整屏团队会员付费页**
//   （`1280×720`、逐字「限时惊喜 积分加赠 超级年卡 …… 高级团队会员-12个月 ¥263 席位/月 ¥549
//     席位 合计 ¥6312 7700 积分/席位/每月 **购买团队会员**」`438×44@166,737`，席位可增减）。
//   ⇒ 📌 **「创建团队」是付费入口，不是免费建组织。** 本轮**没有点**「购买团队会员」，
//      也没有碰席位加减。这一条把手册原写的「属对外产出动作」升级成「**属扣费**」——
//      也就是说，它此前被排除在外的**真正理由**一直是扣费，只是没人点开看过。
//
// ✅ 本轮做：① 「复制项目」只走到**确认那一步**就取消（若它先弹确认框）
//    ② 「查看积分明细」点下去，判它是**新标签页**还是**同页跳转**，读落地页，然后还原
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf } from './jimeng-b139-lib.mjs';

const rec = { 批次: '157c', 目的: '复制项目的确认步 + 查看积分明细的落地形态' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b157c.json', import.meta.url), JSON.stringify(rec, null, 1));
const 串 = (x, n) => { const s = JSON.stringify(x, null, 1); return s === undefined ? 'undefined' : s.slice(0, n || 2000); };
const 找点 = (pred) => p.evaluate((pd) => {
  const cands = Array.from(document.querySelectorAll(pd.sel)).filter((b) => {
    const a = b.getAttribute('aria-label') || ''; const t = (b.innerText || '').replace(/\s+/g, ' ').trim();
    if (pd.aria === a) return true;
    if (pd.字面 === t) return true;
    if (pd.文字Includes && t.indexOf(pd.文字Includes) >= 0) return true;
    if (pd.testid === b.getAttribute('data-testid')) return true;
    return false;
  });
  const 全部 = [], 可用 = [];
  for (const b of cands) {
    const r = b.getBoundingClientRect(); if (!(r.width > 0 && r.height > 0)) continue;
    const cx = Math.round(r.x + r.width / 2); const cy = Math.round(r.y + r.height / 2);
    const h = document.elementFromPoint(cx, cy); const btn = h && h.closest(pd.sel);
    const z = { x: cx, y: cy, 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
      aria: b.getAttribute('aria-label'), testid: b.getAttribute('data-testid'),
      逐字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 26),
      在视口内: cx >= 0 && cy >= 0 && cx <= innerWidth && cy <= innerHeight, 中心是自己: btn === b };
    全部.push(z); if (z.在视口内 && z.中心是自己) 可用.push(z);
  }
  return { 候选数: cands.length, 全部, 可用 };
}, pred);
const 点 = async (btn) => { await p.mouse.click(btn.盒[2] + btn.盒[0] / 2, btn.盒[3] + btn.盒[1] / 2); };
// 🔴 自 bug（批次 157-c 第一版）：evaluate 的回调体跑在**页面上下文**里，
//    拿不到宿主的 `脱敏` ⇒ `ReferenceError: 脱敏 is not defined`。
//    📌 立规 22b：**跨 `page.evaluate` 边界只能传可序列化的数据与页面内定义的函数**；
//    宿主里的工具函数要么在页面内重写一遍，要么先取值再脱敏。
const 层快照 = (阶段) => p.evaluate((tag) => {
  const 脱敏 = (t) => String(t || '').replace(/https?:\/\/\S+/g, '<URL>').replace(/\s+/g, ' ').trim();
  const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; };
  const ds = Array.from(document.querySelectorAll('[role=dialog],[role=alertdialog],[role=menu],[data-state=open]')).filter((x) => x.getBoundingClientRect().width > 60);
  return { 阶段: tag, 层数: ds.length, 层: ds.map((d) => ({ role: d.getAttribute('role'), testid: d.getAttribute('data-testid'),
    aria: d.getAttribute('aria-label'), 盒: 盒(d),
    逐字脱敏: 脱敏(d.innerText).slice(0, 400),
    testid清单: Array.from(new Set(Array.from(d.querySelectorAll('[data-testid]')).map((x) => x.getAttribute('data-testid')))).sort(),
    按钮: Array.from(d.querySelectorAll('button,[role=button]')).map((x) => { const r = x.getBoundingClientRect();
      return { aria: x.getAttribute('aria-label'), 逐字: 脱敏(x.innerText).slice(0, 18), disabled: x.getAttribute('aria-disabled'),
        盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; }).filter((z) => z.盒[0] > 0) })) };
}, 阶段);
const 读页 = (page) => page.evaluate(() => ({
  URL: location.href, 标题: document.title,
  正文前: (document.body.innerText || '').replace(/https?:\/\/\S+/g, '<URL>').replace(/\s+/g, ' ').trim().slice(0, 400),
  testid样本: Array.from(new Set(Array.from(document.querySelectorAll('[data-testid]')).map((x) => x.getAttribute('data-testid')))).sort().slice(0, 30),
}));

const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(), 积分: await R.credits() };
  rec.起点页数 = p.context().pages().length;
  rec.起点页 = await 读页(p);
  console.log('起点', JSON.stringify(rec.起点), '| 页数', rec.起点页数);

  // ================= ① 更多菜单 → 复制项目 =================
  const 更多 = (await 找点({ sel: 'button,[role=button]', aria: '更多' })).可用[0];
  rec.更多钮 = 更多 || null;
  断言('① 顶栏「更多」钮找得到（aria 逐字「更多」，**顶栏唯一无 testid 的按钮**）', !!更多, 更多);
  if (更多) {
    await 点(更多); await p.waitForTimeout(1700);
    rec.更多菜单 = await p.evaluate(() => {
      const ms = Array.from(document.querySelectorAll('[role=menu]')).filter((x) => x.getBoundingClientRect().width > 60);
      if (!ms.length) return { 命中: false };
      const m = ms[ms.length - 1]; const r = m.getBoundingClientRect();
      return { 命中: true, 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
        testid: m.getAttribute('data-testid'), aria: m.getAttribute('aria-label'),
        逐字: (m.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120),
        项: Array.from(m.querySelectorAll('[role=menuitem]')).map((x) => { const ir = x.getBoundingClientRect();
          return { 逐字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20), aria: x.getAttribute('aria-label'),
            盒: [Math.round(ir.width), Math.round(ir.height), Math.round(ir.x), Math.round(ir.y)] }; }) };
    });
    落盘();
    console.log('\n🆕 更多菜单', 串(rec.更多菜单, 1200));
    断言('② 更多菜单逐字复现「项目信息 / 复制项目」两项', (rec.更多菜单 || {}).命中 === true &&
      ((rec.更多菜单 || {}).项 || []).length === 2, rec.更多菜单);

    const 复制项目 = ((rec.更多菜单 || {}).项 || []).find((z) => z.逐字 === '复制项目');
    rec.复制项目项 = 复制项目 || null;
    if (复制项目) {
      const 前页数 = p.context().pages().length;
      rec.复制项目前页数 = 前页数;
      const 前 = await 层快照('复制前');
      await p.mouse.click(复制项目.盒[2] + 复制项目.盒[0] / 2, 复制项目.盒[3] + 复制项目.盒[1] / 2);
      await p.waitForTimeout(2400);
      rec.复制项目后 = await 层快照('复制后');
      rec.复制项目后页数 = p.context().pages().length;
      rec.复制项目后页 = await 读页(p);
      rec.复制项目后状态 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 积分: await R.credits() };
      落盘();
      console.log('\n🆕 点「复制项目」后', 串(rec.复制项目后, 2200));
      console.log('页数', 前页数, '→', rec.复制项目后页数, '| 状态', JSON.stringify(rec.复制项目后状态));
      断言('③ 点「复制项目」**先弹一层确认**（不是直接复制完）', (rec.复制项目后 || {}).层数 > (前 || {}).层数,
        { 前: (前 || {}).层数, 后: (rec.复制项目后 || {}).层数 });
    }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }
try { await settle(p, R); } catch (e) { rec.收尾异常 = String(e.message || e).slice(0, 200); }
rec.收尾1 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 浮层: await R.overlays(), 页数: p.context().pages().length };
console.log('第一段收尾', JSON.stringify(rec.收尾1));
rec.断言全过 = 断言过; 落盘();
process.exit(0);
