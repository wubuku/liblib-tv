// 批次 174 b 轮：**刷新到底带走了什么** —— 逐项对账。
//
// 手册现状（立规 34 自我降级）：持久化只有零星 4 处（canvas-context.md:622-623
// 「顶栏 已保存 常驻；改动后自动保存；内容跨刷新持久」、30-concepts.md:118-119、
// 90-troubleshooting.md:664 一条排障），**没有任何一处讲「刷新会带走什么」**。
//
// a 轮已经拿到两条**本地**键（都是 `octo.user-preferences.v1.<uid>.*`）：
//   canvas-display = {"minimapVisible":false,"referenceEdgeVisibility":"all"}
//   canvas-panels  = {"openPanelId":null,"placements":{}}
// 🔑 这已经说明：**43 个 localStorage 键里没有任何一个装节点/连线/坐标**
//    ⇒ 画布内容不在本机。但视图偏好在。
//
// ⚠️ 本轮会**真的刷新页面**。这是有意的：刷新是唯一能一次分开
//    「服务端持久 / 本机记忆 / 纯内存」的干净手段（批次 158/159 记过
//    「重载页面」在别处有害，但这里正是要测它 ⇒ 同一动作在不同问题下结论相反）。
//
// 【开跑前先写死预测，测完再对】—— 否则就是事后编故事：
//   | 项 | 预测 | 依据 |
//   | 节点/连线/坐标/画布名 | 活 | 分享链接能给别人访问 ⇒ 服务端 |
//   | 小地图开关           | 活 | localStorage canvas-display.minimapVisible |
//   | 连线显示             | 活 | canvas-display.referenceEdgeVisibility |
//   | 选中态               | 死 | 纯内存 |
//   | 缩放/平移            | 死 | localStorage 里没有对应键 |
//   | 浮层（节点汇总等）    | 死 | 纯内存 |
//   | AI 侧栏开合          | 活 | canvas-panels.openPanelId |
// 🔴 最可能被否的一条：**「AI 侧栏开合」**。a 轮读到 `openPanelId: null`，
//    而此刻侧栏是**开着**的 ⇒ 如果这个键真在记侧栏，值不该是 null。
//    预测它「死」也许才对；也可能这个键记的是**别的**面板（右侧 panel launcher 系）。
//
// 收尾：把小地图、缩放、选中态全部复原；⛔ 不生成、不分享、不新建节点。
import { openCanvas, readers, setZoom, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '174b', 预测: {
  '节点/连线/坐标/画布名': '活（服务端）', '小地图开关': '活（localStorage canvas-display）',
  '连线显示': '活（localStorage）', '选中态': '死（内存）', '缩放/平移': '死（无键）',
  '浮层': '死（内存）', 'AI 侧栏开合': '活（canvas-panels.openPanelId）—— 预判这条最可能被否',
} };

/** 一份完整快照：能拿来逐项 diff 的全部状态。 */
const 快照 = async (标) => {
  const s = await p.evaluate(() => {
    const vp = document.querySelector('.react-flow__viewport');
    const 存 = {};
    for (const k of Object.keys(localStorage)) if (/octo\.user-preferences/.test(k)) 存[k] = localStorage.getItem(k);
    const mm = document.querySelector('[data-testid="canvas-display-toggle-minimap"]');
    const cn = document.querySelector('[data-testid="canvas-display-toggle-connections"]');
    const g = (e) => e && { ariaPressed: e.getAttribute('aria-pressed'), dataState: e.getAttribute('data-state'), text: (e.innerText || '').trim() };
    const 浮层 = Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox],[data-testid$=-popover]'))
      .filter((m) => { const r = m.getBoundingClientRect(); return r.width > 1; })
      .map((m) => { const r = m.getBoundingClientRect(); return (m.getAttribute('data-testid') || m.getAttribute('aria-label') || m.tagName) + `@${Math.round(r.x)},${Math.round(r.y)}`; });
    return {
      url: location.href,
      顶栏文字: (document.querySelector('[data-testid="canvas-top-bar"]')?.innerText || '').replace(/\n/g, ' | '),
      保存状态元素: (() => { const e = document.querySelector('[data-testid="canvas-title-save-status"]');
        return e ? { 标签: e.tagName.toLowerCase(), 文本: (e.textContent || '').trim(), aria: e.getAttribute('aria-label'), live: e.getAttribute('aria-live'), role: e.getAttribute('role') } : null; })(),
      状态行: (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0],
      节点数: document.querySelectorAll('.react-flow__node').length,
      选中: Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')),
      节点指纹: Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
        const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
        const t = n.querySelector('[data-testid="flow-node-title"]');
        return [n.getAttribute('data-id'), t ? (t.innerText || '').trim().split('\n')[0] : '?',
          m ? `${Math.round(parseFloat(m[1]))},${Math.round(parseFloat(m[2]))}` : '?'];
      }).sort((a, b) => String(a[0]).localeCompare(String(b[0]))),
      缩放aria: document.querySelector('[data-testid="canvas-zoom-percent"]')?.getAttribute('aria-label'),
      视口transform: vp ? vp.style.transform : null,
      小地图: g(mm), 连线显示: g(cn),
      侧栏开: !!document.querySelector('[data-testid="canvas-feature-sidecar"]'),
      侧栏text: (document.querySelector('[data-testid="canvas-feature-sidecar"]')?.innerText || '').replace(/\n/g, ' | ').slice(0, 80),
      浮层,
      保存失败锚点存在: !!document.querySelector('[data-testid="canvas-save-failure-anchor"]'),
      localStorage: 存,
    };
  });
  rec[标] = s;
  return s;
};

const 点 = async (选择器, 说明) => {
  const pt = await p.evaluate((sel) => {
    const e = document.querySelector(sel); if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  }, 选择器);
  if (!pt) { rec.失败 ||= []; rec.失败.push(说明); return false; }
  await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(900); return true;
};

// ------------------------------------------------------------------ ① 原始态
await settle(p, R);
const 原始 = await 快照('原始');
rec.原始.积分 = await R.credits();

// ------------------------------------------ ② 制造受控前置态（每一项都可复原）
// 顺序有讲究：**先改缩放，最后开小地图** —— 批次 134 实测「任何缩放操作都会关掉小地图」。
rec.步骤 = {};
rec.步骤.改缩放到50 = await setZoom(p, 50);
await p.waitForTimeout(600);

// 平移：空白处按下拖动，落到一个特征位置
await p.mouse.move(640, 400); await p.mouse.down();
await p.mouse.move(760, 470, { steps: 12 }); await p.mouse.up();
await p.waitForTimeout(900);

// 选一个节点（点标题行，批次 171 教训：点几何中心可能命中把手热区）
const 选中 = await p.evaluate(() => {
  const t = Array.from(document.querySelectorAll('[data-testid="flow-node-title"]'))
    .find((x) => { const r = x.getBoundingClientRect(); return r.width > 4 && r.x > 200 && r.x < 900 && r.y > 90 && r.y < 600; });
  if (!t) return null; const r = t.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2), (t.innerText || '').trim().split('\n')[0]];
});
if (选中) { await p.mouse.click(选中[0], 选中[1]); await p.waitForTimeout(700); }
rec.步骤.点了哪个节点 = 选中;

// 小地图：点开（复原时要点回关）
rec.步骤.小地图原态 = 原始.小地图;
await 点('[data-testid="canvas-display-toggle-minimap"]', '小地图按钮找不到');
rec.步骤.小地图现态 = await p.evaluate(() => document.querySelector('[data-testid="canvas-display-toggle-minimap"]')?.getAttribute('aria-pressed'));

// 浮层：顶栏「节点 N」汇总
rec.步骤.点了节点汇总 = await 点('[data-testid="canvas-node-summary-trigger"]', '节点汇总按钮找不到');

const 改后 = await 快照('改后');
rec.改后.积分 = await R.credits();

// ------------------------------------------------------------------ ③ 刷新
rec.刷新前URL = p.url();
await p.reload({ waitUntil: 'domcontentloaded' });
await pinViewport(p);
// 等水合：节点数回到基线才算读完（workspace-hydrated-canvas-frame）
const t0 = Date.now();
let n = 0;
while (Date.now() - t0 < 45000) {
  n = await p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  if (n > 0) break;
  await p.waitForTimeout(500);
}
rec.等水合ms = Date.now() - t0; rec.水合后节点数 = n;
await p.waitForTimeout(2500);
const 重载后 = await 快照('重载后');
rec.重载后.积分 = await R.credits();

// ------------------------------------------------------------------ ④ 逐项对账
const 差 = (a, b2) => { try { return JSON.stringify(a) === JSON.stringify(b2) ? null : { 前: a, 后: b2 }; } catch { return { 前: String(a), 后: String(b2) }; } };
rec.对账 = {
  节点数: 差(改后.节点数, 重载后.节点数),
  状态行: 差(改后.状态行, 重载后.状态行),
  保存状态元素: 差(改后.保存状态元素, 重载后.保存状态元素),
  顶栏文字: 差(改后.顶栏文字, 重载后.顶栏文字),
  选中态: 差(改后.选中, 重载后.选中),
  缩放aria: 差(改后.缩放aria, 重载后.缩放aria),
  视口transform: 差(改后.视口transform, 重载后.视口transform),
  小地图: 差(改后.小地图, 重载后.小地图),
  连线显示: 差(改后.连线显示, 重载后.连线显示),
  侧栏开: 差(改后.侧栏开, 重载后.侧栏开),
  浮层: 差(改后.浮层, 重载后.浮层),
  localStorage: 差(改后.localStorage, 重载后.localStorage),
};
// 内容指纹：改后 vs 重载后 必须逐个相同（这是「服务端持久」的直接证据）
const 指纹A = new Map(改后.节点指纹.map((r) => [r[0], r.slice(1).join('|')]));
const 指纹B = new Map(重载后.节点指纹.map((r) => [r[0], r.slice(1).join('|')]));
rec.内容差异 = {
  改后有而重载后无: [...指纹A.keys()].filter((k) => !指纹B.has(k)),
  重载后有而改后无: [...指纹B.keys()].filter((k) => !指纹A.has(k)),
  同id但标题或坐标不同: [...指纹A.keys()].filter((k) => 指纹B.has(k) && 指纹A.get(k) !== 指纹B.get(k))
    .map((k) => ({ id: k, 改后: 指纹A.get(k), 重载后: 指纹B.get(k) })),
};
// 原始 vs 重载后：画布名/顶栏应当一致（除节点数文案）
rec.原始vs重载后_顶栏 = 差(原始.顶栏文字, 重载后.顶栏文字);
console.log(JSON.stringify(rec, null, 1));
process.exit(0);
