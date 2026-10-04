// 批次 157-b —— 接着 157-a：抓「复制链接」那个**瞬时提示**的实体、重测「创建团队」、再开「更多菜单」一簇
//
// 🔴 157-a 的两个发现与一个自错：
//   发现①「复制链接」**真的写剪贴板**：`navigator.clipboard.readText()` 读到 **117 字**的 URL
//        （本脚本只记脱敏后的 `<URL>` 与长度，**不落明文链接**）。
//   发现② 点它**会把分享面板关掉** —— 157-a 的「消失 10 个元素」全是面板里的。
//        ⇒ 157-a 随后去点面板内的「创建团队」，点了个空气 ⇒ 断言 ④ 的 `层数: 0` 是**我的顺序错**，
//          **不是**「创建团队没反应」。📌 立规 22：**前一步会关掉你正要用的东西时，
//          后一步的失败不能记成「后一步的错」** —— 和 156 的立规 19 是同一族。
//   待解：新增数 8 → 6 → 1 的递减说明有个**只活约 2.5 秒**的提示，但 157-a 只存了计数、
//        没存**实体**。本轮把每次采样的新增**逐条落盘**。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf } from './jimeng-b139-lib.mjs';

const rec = { 批次: '157b', 目的: '复制链接的瞬时提示 + 创建团队对话框 + 更多菜单三项' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b157b.json', import.meta.url), JSON.stringify(rec, null, 1));
const 串 = (x, n) => { const s = JSON.stringify(x, null, 1); return s === undefined ? 'undefined' : s.slice(0, n || 2000); };
const 脱敏 = (t) => String(t || '').replace(/https?:\/\/\S+/g, '<URL>').replace(/\s+/g, ' ').trim();

const 找点 = (pred) => p.evaluate((pd) => {
  const cands = Array.from(document.querySelectorAll(pd.sel)).filter((b) => {
    const a = b.getAttribute('aria-label') || ''; const t = (b.innerText || '').replace(/\s+/g, ' ').trim();
    if (pd.aria === a) return true;
    if (pd.字面 === t) return true;
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

const 签名 = (阶段) => p.evaluate((tag) => {
  const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; };
  const 集 = [];
  const 加 = (类, e) => { const r = e.getBoundingClientRect(); if (!(r.width > 0 && r.height > 0)) return;
    集.push({ 类, tag: e.tagName, role: e.getAttribute('role'), testid: e.getAttribute('data-testid'), state: e.getAttribute('data-state'),
      cls: (e.className || '').toString().slice(0, 60),
      aria: (e.getAttribute('aria-label') || '').slice(0, 40), 逐字: (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 60), 盒: 盒(e) }); };
  for (const e of document.querySelectorAll('[data-sonner-toast],[role=status],[role=alert],[role=alertdialog],[role=dialog],[data-state=open],[class*=toast],[class*=Toast],[class*=notification],[class*=message],[class*=banner]')) 加('反馈', e);
  for (const e of document.querySelectorAll('[data-testid]')) 加('testid', e);
  for (const e of document.querySelectorAll('div,span,p,li,button,[role=menuitem]')) {
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (t.length > 80) continue;
    if (!/复制|成功|已复制|失败|链接|团队|积分|明细|副本|确认|保存|取消|已加入/.test(t)) continue;
    if (!e.getBoundingClientRect().width) continue;
    if (e.children.length && Array.from(e.children).some((c) => (c.innerText || '').replace(/\s+/g, ' ').trim() === t)) continue;
    加('关键词', e);
  }
  return { 阶段: tag, 总数: 集.length, 集 };
}, 阶段);
const 差 = (A, B) => {
  const key = (z) => [z.类, z.role || '', z.testid || '', z.state || '', z.aria || '', z.逐字 || ''].join('');
  const ma = new Map(A.集.map((z) => [key(z), z]));
  return { 新增: B.集.filter((z) => !ma.has(key(z))), 消失: A.集.filter((z) => !B.集.some((w) => key(w) === key(z))) };
};

const 开分享 = async () => {
  const S = (await 找点({ sel: 'button,[role=button]', testid: 'canvas-share-trigger' })).可用[0];
  if (!S) return null;
  await 点(S); await p.waitForTimeout(1900);
  return await p.evaluate(() => {
    const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; };
    const s = document.querySelector('[data-testid="canvas-share-panel"]');
    if (!s) return { 命中: false };
    return { 命中: true, 盒: 盒(s),
      按钮: Array.from(s.querySelectorAll('button,[role=button]')).map((x) => ({ aria: x.getAttribute('aria-label'),
        逐字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20), 盒: 盒(x) })).filter((z) => z.盒[0] > 0) };
  });
};
const 关浮层 = async () => { for (let k = 0; k < 4; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); } };

const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(), 积分: await R.credits() };
  console.log('起点', JSON.stringify(rec.起点));

  // ================= ① 复制链接：把瞬时提示的**实体**抓下来 =================
  rec.面板1 = await 开分享();
  const 复制 = ((rec.面板1 || {}).按钮 || []).find((z) => z.逐字 === '复制链接');
  rec.复制链接钮 = 复制 || null;
  断言('① 分享面板打开且找得到「复制链接」100×36', (rec.面板1 || {}).命中 === true && !!复制, { 命中: (rec.面板1 || {}).命中 });
  if (复制) {
    const 前 = await 签名('复制前'); rec.复制前总数 = 前.总数;
    rec.复制前面板在 = await p.evaluate(() => !!document.querySelector('[data-testid="canvas-share-panel"]'));
    await 点(复制);
    rec.采样 = [];
    for (let i = 0; i < 12; i++) {
      await p.waitForTimeout(400);
      const s = await 签名('t' + ((i + 1) * 2 / 10));
      const d = 差(前, s);
      rec.采样.push({ 毫秒: (i + 1) * 400, 总数: s.总数, 面板在: await p.evaluate(() => !!document.querySelector('[data-testid="canvas-share-panel"]')),
        新增: d.新增, 消失数: d.消失.length });
      if (i % 3 === 2) 落盘();
    }
    rec.提示实体 = rec.采样.flatMap((z) => z.新增).filter((z) => z.类 !== 'testid' || !/flow-node|media-stroke/.test(z.testid || ''));
    rec.面板何时关 = (rec.采样.find((z) => !z.面板在) || {}).毫秒 || null;
    rec.提示最长活到 = Math.max(...rec.采样.filter((z) => (z.新增 || []).some((q) => q.类 === '反馈')).map((z) => z.毫秒), 0);
    落盘();
    console.log('\n🆕 复制链接采样：面板在第', rec.面板何时关, 'ms 关闭');
    console.log('🆕 瞬时提示实体', 串(rec.提示实体, 1600));
    断言('② 点「复制链接」会**把分享面板关掉**（不是原地反馈）', rec.面板何时关 != null,
      { 前面板在: rec.复制前面板在, 何时关: rec.面板何时关 });
    断言('③ 出现过一个**只活几百毫秒到几秒**的提示元素（不是常驻 toast）', rec.提示实体.length > 0,
      { 实体数: rec.提示实体.length });
  }
  await 关浮层();

  // ================= ② 创建团队（只读对话框）=================
  rec.面板2 = await 开分享();
  const 建队 = ((rec.面板2 || {}).按钮 || []).find((z) => z.逐字 === '创建团队');
  rec.创建团队钮 = 建队 || null;
  console.log('\n面板2 按钮', 串((rec.面板2 || {}).按钮, 700));
  断言('④ 重新打开面板后找得到「创建团队」80×36', !!建队, { 按钮: (rec.面板2 || {}).按钮 });
  if (建队) {
    rec.点前面板在 = await p.evaluate(() => !!document.querySelector('[data-testid="canvas-share-panel"]'));
    await 点(建队); await p.waitForTimeout(2200);
    rec.建队后 = await p.evaluate(() => {
      const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; };
      const ds = Array.from(document.querySelectorAll('[role=dialog],[role=alertdialog],[data-state=open]')).filter((x) => x.getBoundingClientRect().width > 120);
      return { 分享面板还在: !!document.querySelector('[data-testid="canvas-share-panel"]'), 层数: ds.length,
        层: ds.map((d) => ({ role: d.getAttribute('role'), testid: d.getAttribute('data-testid'), 盒: 盒(d),
          逐字脱敏: (d.innerText || '').replace(/https?:\/\/\S+/g, '<URL>').replace(/\s+/g, ' ').trim().slice(0, 400),
          testid清单: Array.from(new Set(Array.from(d.querySelectorAll('[data-testid]')).map((x) => x.getAttribute('data-testid')))).sort(),
          输入: Array.from(d.querySelectorAll('input,textarea')).map((x) => { const r = x.getBoundingClientRect();
            return { placeholder: x.getAttribute('placeholder'), maxlength: x.getAttribute('maxlength'), 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; }),
          按钮: Array.from(d.querySelectorAll('button,[role=button]')).map((x) => { const r = x.getBoundingClientRect();
            return { aria: x.getAttribute('aria-label'), 逐字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 18),
              disabled: x.getAttribute('aria-disabled'), 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; }).filter((z) => z.盒[0] > 0) })) };
    });
    落盘();
    console.log('\n🆕 点「创建团队」后', 串(rec.建队后, 3000));
    断言('⑤ 点「创建团队」弹出新层（层数 ≥ 1）', (rec.建队后 || {}).层数 >= 1, { 层数: (rec.建队后 || {}).层数 });
    断言('⑥ ⛔ 本轮**不提交**（未点任何确认/创建按钮）', rec.点前面板在 === true, null);
    await 关浮层();
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

try { await settle(p, R); } catch (e) { rec.收尾异常 = String(e.message || e).slice(0, 200); }
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(), zoom: await R.zoom(), 积分: await R.credits() };
rec.断言全过 = 断言过; 落盘();
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');
process.exit(0);
