// 批次 166-b —— 把手册记成「契约尺寸」的对话框，拆成两类：
// **尺寸写死在 CSS 里** 的，与 **尺寸根本不由 CSS 决定（随内容变）** 的。
//
// 🔑 靶子来自 166-a 的静态扫描（它很吵，但其中两条信号很硬）：
//   · `workspace-project-info-dialog` 手册记 **`800×546`**，
//     而 CSS 里有 `.w-workspace-project-info{width:800px}`，**却根本没有 `546px`**；
//   · `subject-export-confirm-dialog` 手册记 **`548×688`**，
//     **548 与 688 在三张样式表里都不存在**（唯一一次 548 是 `153.548px`）。
//   ⇒ 假设：**这几个对话框的高度不是 CSS 常量**，「契约尺寸」这个说法本身过强。
//
// 📐 方法（可推广）：**读运行时的 classList，再把每个类名回查成 CSS 声明**。
//   166-a 已经证明页面内读不到样式表（跨域），但 Node 里能 curl 同一份 CSS ⇒
//   「类名 → 声明」这一步放在 Node 做，「类名 → 元素」放在页面里做，两边一拼就得到机制。
//   ⇒ 这一轮要回答的**不是「多大」**（166 之前的批次早量过），而是
//     **「这个尺寸是写死的，还是内容算出来的」**。
//
// ⛔ 只读：只开对话框读 classList 与计算样式，立刻 Esc。
//    「设置主体」对话框只**开不填不点保存**（它是账号级写入的入口，立规 20）。
import fs from 'node:fs';
import { execSync } from 'node:child_process';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';

const URL_ = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const CSS_URL = 'https://lf3-lv-buz.vlabstatic.com/obj/image-lvweb-buz/ies/lvweb/octo_web/static/css/main.94b57a0e55.css';
const CSS_LOCAL = '/tmp/jimeng-main.94b57a0e55.css';
if (!fs.existsSync(CSS_LOCAL)) execSync(`curl -s -m 40 -o ${CSS_LOCAL} ${CSS_URL}`);
const css = fs.readFileSync(CSS_LOCAL, 'utf8');

const rec = { 批次: '166b', 目的: '把「对话框契约尺寸」拆成「CSS 写死」与「内容算出」两类' };
let 断言过 = true, 断言数 = 0;
const 断言 = (名, ok, 详情) => { 断言数++; const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' → ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b166b.json', import.meta.url), JSON.stringify(rec, null, 1));

// ---- Node 侧：类名 → CSS 声明 ----
const 解转义 = (s) => s.replace(/\\2c\s?/g, ',').replace(/\\\]/g, ']').replace(/\\\[/g, '[').replace(/\\\(/g, '(').replace(/\\\)/g, ')').replace(/\\\//g, '/').replace(/\\%/g, '%').replace(/\\\./g, '.');
const 类到声明 = new Map();
for (const m of css.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
  for (const sel of m[1].split(',')) {
    const s = sel.trim();
    if (!/^\.[\w\\]/.test(s)) continue;
    const key = '.' + 解转义(s.slice(1));
    if (!类到声明.has(key)) 类到声明.set(key, []);
    类到声明.get(key).push(m[2].trim());
  }
}
const 解析类 = (cls) => {
  const out = [];
  for (const c of cls) {
    const d = 类到声明.get('.' + c);
    if (d) for (const decl of d) {
      const 尺寸 = decl.split(';').filter((x) => /^(?:max-|min-)?(?:width|height)\s*:/.test(x.trim()));
      if (尺寸.length) out.push({ 类: c, 尺寸声明: 尺寸.map((x) => x.trim()) });
    }
  }
  return out;
};

// ---- 页面内：读元素的几何 + classList + 计算样式 ----
const 读元素 = (选择器) => {
  const e = document.querySelector(选择器);
  if (!e) return { 找到: false };
  const r = e.getBoundingClientRect(), cs = getComputedStyle(e);
  const 子 = Array.from(e.children).slice(0, 6).map((c) => {
    const q = c.getBoundingClientRect(), s = getComputedStyle(c);
    return { cls: (typeof c.className === 'string' ? c.className : '').slice(0, 60), testid: c.getAttribute('data-testid'),
      盒: [Math.round(q.width), Math.round(q.height)],
      尺寸声明: ['width', 'height', 'max-height', 'flex', 'flex-grow'].map((k) => k + '=' + s[k]).filter((z) => !/=(auto|none|0px)/.test(z)) };
  });
  return { 找到: true, 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
    classList: (typeof e.className === 'string' ? e.className : '').split(/\s+/).filter(Boolean),
    计算: { width: cs.width, height: cs.height, maxHeight: cs.maxHeight, maxWidth: cs.maxWidth, minHeight: cs.minHeight,
      display: cs.display, flexDirection: cs.flexDirection, overflow: cs.overflow, flex: cs.flex },
    直接子: 子, 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120) };
};

const 读共享 = async (p) => p.evaluate(() => ({
  视口: [innerWidth, innerHeight],
  状态行: (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0],
  节点数: document.querySelectorAll('.react-flow__node').length,
  选中: document.querySelectorAll('.react-flow__node.selected').length,
  浮层: Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length,
  积分: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'),
}));

const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p); await settle(p, R); await p.waitForTimeout(1000);
  rec.起点 = { 状态行: await R.status(), 节点数: (await R.ids()).length, 积分: await R.credits(), 缩放: await R.zoom() };
  console.log('起点', JSON.stringify(rec.起点));
  rec.对话框 = {};

  // ---------- ① 项目信息对话框：顶栏「更多」→ 查看项目信息 ----------
  const 更多 = await p.evaluate(() => {
    const 候选 = Array.from(document.querySelectorAll('button,[role=button]'));
    const e = 候选.find((x) => (x.getAttribute('aria-label') || '') === '更多') ||
             候选.find((x) => (x.getAttribute('aria-label') || '').includes('更多')) ||
             候选.find((x) => (x.innerText || '').trim() === '···' || (x.innerText || '').trim() === '…');
    if (!e) return null;
    const r = e.getBoundingClientRect(); return { 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], aria: e.getAttribute('aria-label') };
  });
  rec.更多钮 = 更多;
  断言('⓪ 顶栏找得到「更多」按钮', !!更多, { 更多 });
  if (更多) {
    await p.mouse.click(更多.点[0], 更多.点[1]); await p.waitForTimeout(1500);
    const 项 = await p.evaluate(() => {
      const it = Array.from(document.querySelectorAll('[role=menuitem],button')).find((x) => (x.innerText || '').trim() === '项目信息');
      if (!it) return null;
      const r = it.getBoundingClientRect(); return { 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 逐字: (it.innerText || '').trim() };
    });
    rec.项目信息项 = 项;
    if (项) {
      await p.mouse.click(项.点[0], 项.点[1]);
      await p.waitForTimeout(2600);
      const 读 = await p.evaluate(读元素, '[data-testid="workspace-project-info-dialog"]');
      if (读.找到) {
        读.解析 = 解析类(读.classList);
        rec.对话框.项目信息 = 读;
        console.log('项目信息 classList =', JSON.stringify(读.classList));
        console.log('  解析到的尺寸声明 =', JSON.stringify(读.解析));
        console.log('  直接子 =', JSON.stringify(读.直接子));
        await p.screenshot({ path: new URL('../docs/user-manual/jimeng-canvas/screenshots/124-project-info-dialog-548-546-check.png', import.meta.url).pathname });
        rec.图 = 'screenshots/124-project-info-dialog-548-546-check.png';
      } else {
        const 有啥 = await p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog]')).map((d) => d.getAttribute('data-testid') || d.className.slice(0, 40)));
        rec.项目信息未找到 = { 现存对话框: 有啥 };
        console.log('⛔ 没读到项目信息对话框；现存 role=dialog =', JSON.stringify(有啥));
      }
      for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); }
    } else { await p.keyboard.press('Escape'); await p.waitForTimeout(700); }
  }
  落盘();

  // ---------- ② 资产库对话框作为对照（已知真值：801×620 写死） ----------
  const 资产钮 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('button,[role=button]'))
    .find((x) => (x.getAttribute('aria-label') || '') === '资产库'); if (!e) return null;
    const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (资产钮) {
    await p.mouse.click(资产钮[0], 资产钮[1]); await p.waitForTimeout(2600);
    const 读 = await p.evaluate(读元素, '[data-testid="canvas-asset-library-dialog"]');
    if (读.找到) { 读.解析 = 解析类(读.classList); rec.对话框.资产库 = 读;
      console.log('\n资产库 classList =', JSON.stringify(读.classList));
      console.log('  解析到的尺寸声明 =', JSON.stringify(读.解析));
      console.log('  直接子 =', JSON.stringify(读.直接子)); }
    await p.keyboard.press('Escape'); await p.waitForTimeout(1200);
  }
  落盘();
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); console.log('异常', rec.异常); }
finally {
  for (let k = 0; k < 3; k++) { try { await p.keyboard.press('Escape'); await p.waitForTimeout(600); } catch (e) {} }
  try { await settle(p, R); } catch (e) {}
  rec.收尾 = { 状态行: await R.status(), 节点数: (await R.ids()).length, 选中: await R.selCount(), 浮层: await R.overlays(), 积分: await R.credits() };
  console.log('收尾', JSON.stringify(rec.收尾));
  断言('⑨ 收尾回到基线（76 节点 / 0 选中 / 浮层 0 / 积分不变）',
    rec.收尾.节点数 === 76 && rec.收尾.选中 === 0 && rec.收尾.浮层 === 0 && String(rec.收尾.积分) === String(rec.起点.积分), { 起点: rec.起点, 收尾: rec.收尾 });
  rec.断言执行数 = 断言数; rec.断言预期数 = 2; rec.断言全过 = 断言过 && 断言数 >= 2; 落盘();
  console.log(`断言执行 ${断言数} ／ 断言全过 =`, rec.断言全过);
}
process.exit(0);
