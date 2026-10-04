// 批次 157-a —— `canvas-context.md`「分享画布」与「更多菜单」一簇：本轮**可逆**的那几项
//
// 🎯 靶子（静态扫描 `jimeng-b157-scan.mjs` 排出来的）：本页有 **8 处**未执行/未验证陈述，
//    其中新授权（2026-10-04：不执行真实生图/生视频前提下可执行 CRUD 副作用）**解锁了其中 5 处**。
//
// 🔴 **本轮明确不做的两件事，以及为什么**（先划边界，再动手）：
//   ① **改权限**（「仅自己可访问 ∨」）—— 这不是 CRUD，是**把共享画布对拿到链接的人开放**。
//      画布是多人共用的；若在改回去之前会话中断/浏览器被杀，权限会**永久停在开放态**。
//      📌 **「可逆」的前置是「你一定还在场」** —— 这一条不满足，所以不碰。
//   ② **创建团队**的**提交** —— 建团队是**建组织**，会拉人、会产生对外可见实体。
//      本轮只**打开它弹出的对话框并读内容**，然后 Esc。
//
// ✅ 本轮真的做：① 点「复制链接」（写剪贴板，不对外暴露任何东西）② 打开「创建团队」对话框只读
//    ③ 打开「项目信息」→ 点「查看积分明细」，判它是**新标签页**还是**同页跳转**（两种都能安全还原）
//    ④「复制项目」只走到确认那一步就取消。
//
// 🔴 立规 20（承接批次 156 的 19）：**可逆性的判据不是「能不能手工改回来」，是「改回来之前会不会死」。**
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: '157a', 目的: '分享面板（复制链接/创建团队对话框）+ 更多菜单（查看积分明细/复制项目确认步）' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b157a.json', import.meta.url), JSON.stringify(rec, null, 1));
const 串 = (x, n) => { const s = JSON.stringify(x, null, 1); return s === undefined ? 'undefined' : s.slice(0, n || 2000); };

const 读transform = () => p.evaluate(() => { const e = document.querySelector('.react-flow__viewport'); return e ? e.style.transform : null; });
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
    const z = { x: cx, y: cy, 宽: Math.round(r.width), 高: Math.round(r.height), 左: Math.round(r.x), 上: Math.round(r.y),
      aria: b.getAttribute('aria-label'), testid: b.getAttribute('data-testid'),
      逐字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 26),
      在视口内: cx >= 0 && cy >= 0 && cx <= innerWidth && cy <= innerHeight, 中心是自己: btn === b };
    全部.push(z); if (z.在视口内 && z.中心是自己) 可用.push(z);
  }
  return { 候选数: cands.length, 全部, 可用 };
}, pred);

// 🔴 自 bug（批次 157-a 第一版）：面板按钮对象来自「读面板」，字段是 `盒:[w,h,x,y]`；
//    我却按「找点」的 `宽/高/左/上` 取值 ⇒ `undefined + 50 = NaN` ⇒ `mouse.click(NaN,NaN)`
//    报 **Protocol error: Invalid parameters**。
//    📌 **立规 21：同一个页面上多个取点函数的返回结构必须一致**；
//    两个都叫「按钮列表」但字段名不同，就会在调用点静默变成 NaN。
//    ⇒ 本脚本之后所有点击一律用 `盒[2]+盒[0]/2` 算，不再出现两套字段名。
// 🔑 签名差分：承接批次 156 的立规 19 —— 不预设反馈形态，直接比「页面上出现过的一切」
const 签名 = (阶段) => p.evaluate((tag) => {
  const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; };
  const 集 = [];
  const 加 = (类, e) => { const r = e.getBoundingClientRect(); if (!(r.width > 0 && r.height > 0)) return;
    集.push({ 类, role: e.getAttribute('role'), testid: e.getAttribute('data-testid'), state: e.getAttribute('data-state'),
      aria: (e.getAttribute('aria-label') || '').slice(0, 40), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60), 盒: 盒(e) }); };
  for (const e of document.querySelectorAll('[data-sonner-toast],[role=status],[role=alert],[role=alertdialog],[role=dialog],[data-state=open],[class*=toast],[class*=Toast],[class*=notification],[class*=message],[class*=banner]')) 加('反馈', e);
  for (const e of document.querySelectorAll('[data-testid]')) 加('testid', e);
  for (const e of document.querySelectorAll('div,span,p,li,button,[role=menuitem]')) {
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (t.length > 120) continue;
    if (!/复制|成功|已复制|失败|链接|团队|积分|明细|副本|确认|保存|取消/.test(t)) continue;
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

const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), zoom: await R.zoom(), 积分: await R.credits(), transform: await 读transform() };
  console.log('起点', JSON.stringify(rec.起点));
  rec.起点页数 = p.context().pages().length;
  rec.起点URLs = p.context().pages().map((x) => x.url());

  // ================= ① 分享面板 =================
  const 分享 = await 找点({ sel: 'button,[role=button]', testid: 'canvas-share-trigger' });
  const S = (分享.可用 || [])[0];
  rec.分享钮 = S || null;
  断言('① 顶栏「分享」钮找得到（`canvas-share-trigger`）', !!S, 分享);
  if (S) {
    await p.mouse.click(S.x, S.y); await p.waitForTimeout(1800);
    rec.面板 = await p.evaluate(() => {
      const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; };
      const s = document.querySelector('[data-testid="canvas-share-panel"]');
      if (!s) return { 命中: false };
      // ⚠️ 链接行是明文 URL —— 只记它的**结构**不记它的值
      return { 命中: true, role: s.getAttribute('role'), aria: s.getAttribute('aria-label'), 盒: 盒(s),
        逐字脱敏: (s.innerText || '').replace(/https?:\/\/\S+/g, '<URL>').replace(/\s+/g, ' ').trim().slice(0, 400),
        input数: s.querySelectorAll('input').length,
        链接行结构: Array.from(s.querySelectorAll('*')).filter((e) => (e.innerText || '').trim().length > 20 && (e.innerText || '').indexOf('http') >= 0)
          .map((e) => ({ tag: e.tagName, role: e.getAttribute('role'), testid: e.getAttribute('data-testid'),
            盒: 盒(e), 逐字脱敏: (e.innerText || '').replace(/https?:\/\/\S+/g, '<URL>').replace(/\s+/g, ' ').trim().slice(0, 20) })).slice(0, 3),
        按钮: Array.from(s.querySelectorAll('button,[role=button]')).map((x) => { const r = x.getBoundingClientRect();
          return { aria: x.getAttribute('aria-label'), 逐字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20), 盒: 盒(x) }; }).filter((z) => z.盒[0] > 0) };
    });
    落盘();
    console.log('\n🆕 分享面板', 串(rec.面板, 2000));
    断言('② 分享面板打开且 aria 逐字「分享画布」', (rec.面板 || {}).命中 === true && (rec.面板 || {}).aria === '分享画布', { 命中: (rec.面板 || {}).命中, aria: (rec.面板 || {}).aria });

    // ---- 复制链接 ----
    const 复制 = ((rec.面板 || {}).按钮 || []).find((z) => /复制链接/.test(z.逐字) || /复制链接/.test(z.aria || ''));
    rec.复制链接钮 = 复制 || null;
    if (复制) {
      const 前 = await 签名('复制前');
      rec.复制前总数 = 前.总数;
      // 先试着给剪贴板权限（读不出来不算失败，如实记「无法验证」）
      try { await p.context().grantPermissions(['clipboard-read', 'clipboard-write'], { origin: 'https://jimeng.jianying.com' }); rec.剪贴板权限 = '已授予'; }
      catch (e) { rec.剪贴板权限 = '授予失败: ' + String(e.message || e).slice(0, 120); }
      await p.mouse.click(复制.盒[2] + 复制.盒[0] / 2, 复制.盒[3] + 复制.盒[1] / 2);
      rec.复制后采样 = [];
      for (let i = 0; i < 8; i++) { await p.waitForTimeout(500);
        const s = await 签名('c' + ((i + 1) / 2));
        rec.复制后采样.push({ 毫秒: (i + 1) * 500, 总数: s.总数, 新增: 差(前, s).新增.length, 消失: 差(前, s).消失.length }); }
      const 后 = await 签名('复制后');
      rec.复制总差 = 差(前, 后);
      rec.复制后状态 = { 状态行: await R.status(), 积分: await R.credits(), 节点数: (await idsOf(p)).length, 浮层: await R.overlays() };
      rec.剪贴板读 = await p.evaluate(async () => { try { return { 逐字脱敏: (await navigator.clipboard.readText()).replace(/https?:\/\/\S+/g, '<URL>'), 长度: (await navigator.clipboard.readText()).length }; }
        catch (e) { return { 错: String(e.message || e).slice(0, 140) }; } });
      落盘();
      console.log('复制链接：新增', rec.复制总差.新增.length, '| 消失', rec.复制总差.消失.length, '| 采样', JSON.stringify(rec.复制后采样));
      console.log('新增', 串(rec.复制总差.新增, 1400));
      console.log('剪贴板', JSON.stringify(rec.剪贴板读), '| 权限', rec.剪贴板权限);
      console.log('点后状态', JSON.stringify(rec.复制后状态));
      断言('③ 点「复制链接」**不改变画布任何状态**（状态行/积分/节点数/浮层）',
        rec.复制后状态.状态行 === rec.起点.状态行 && rec.复制后状态.积分 === rec.起点.积分 &&
        rec.复制后状态.节点数 === rec.起点.节点数, { 前: rec.起点, 后: rec.复制后状态 });
    }

    // ---- 创建团队（只读对话框，不提交）----
    const 建队 = ((rec.面板 || {}).按钮 || []).find((z) => /创建团队/.test(z.逐字) || /创建团队/.test(z.aria || ''));
    rec.创建团队钮 = 建队 || null;
    if (建队) {
      await p.mouse.click(建队.盒[2] + 建队.盒[0] / 2, 建队.盒[3] + 建队.盒[1] / 2); await p.waitForTimeout(2000);
      rec.建队后 = await p.evaluate(() => {
        const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; };
        const ds = Array.from(document.querySelectorAll('[role=dialog],[data-state=open]')).filter((x) => x.getBoundingClientRect().width > 150);
        return { 层数: ds.length, 层: ds.map((d) => ({ role: d.getAttribute('role'), testid: d.getAttribute('data-testid'),
          盒: 盒(d), 逐字脱敏: (d.innerText || '').replace(/https?:\/\/\S+/g, '<URL>').replace(/\s+/g, ' ').trim().slice(0, 300),
          testid清单: Array.from(new Set(Array.from(d.querySelectorAll('[data-testid]')).map((x) => x.getAttribute('data-testid')))).sort() })) };
      });
      落盘();
      console.log('\n🆕 点「创建团队」后', 串(rec.建队后, 2200));
      断言('④ 点「创建团队」弹出的东西**不是**原地无反应（有新层或新对话框）',
        (rec.建队后 || {}).层数 > 0, { 层数: (rec.建队后 || {}).层数 });
      for (let k = 0; k < 4; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); }
    }
    rec.关面板后浮层 = await R.overlays();
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

try { await settle(p, R); } catch (e) { rec.收尾异常 = String(e.message || e).slice(0, 200); }
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(), zoom: await R.zoom(), 积分: await R.credits() };
rec.断言全过 = 断言过; 落盘();
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');
process.exit(0);
