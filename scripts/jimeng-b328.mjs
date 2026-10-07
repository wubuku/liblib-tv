/**
 * 批次 328 · 找**第三个 `(R, A)` 点**：上一批的 `R` 普查只认 `node-toolbar` 一个 testid，
 * 而 `时间线` 节点的子 testid 里明明有 `timeline-toolbar` ⇒ 🔴 **探针的 testid 选窄了**
 * （立规 204 的自伤实例：筛窗口 + 筛 testid 同时把真面板挡在门外）。
 *
 * ✅ 接批次 327（`9/9` 臂）：
 *    🔴 **撤回** 327 里「五量和逐字等于 `innerHeight`」这条判据 —— `余量` 是我自己用
 *       `innerHeight − 工具条底边` 定义的，`top+h+gap+R+余量` **恒等于** `innerHeight`，
 *       是**恒等式**不是证据（立规 203：判据里不能出现因变量自己的函数）。
 *    🔴 **间隙不是常数**：`{20, 20.069, 20.078, 20.087}`（音频逐字 `20`，视频随 `h` 单调升）
 *    ✅ **不恒等的真不变量**：`节点顶边 = 80`（仅限高度受限那条分支；图片 `168.75`、时间线 `301.35`）、
 *       `余量 = 56`（三个视口高上逐字恒）、`节点屏高 + 间隙` 落成**整数**（`380/336/376/416`）
 *    🔴 **`(R, A)` 第三档不存在**：`图片`/`外部`/`时间线`/`文本` 在 `node-toolbar` 这个 testid 下都量不到 `R`
 *
 * 📌 **本批测两件事**：
 *   **P1** 按 testid **普查面板**：节点选中后，把页面上**每一个**可见 `[data-testid]` 的
 *        屏矩形都列出来（并标注它在不在选中节点内）⇒ 看时间线/图片/文本的「面板」到底叫什么、
 *        屏高多少、**在节点的上面还是下面**（327 里文本/图片的面板被判成「不存在」，其实是**在节点上方**）。
 *   **P2** 判**面板是否屏固定**：换一个让 `落点` 真的不同的视口高再量同一个面板的屏宽/屏高。
 *        `落点` 变了屏宽跟着变 ⇒ 随落点缩放；纹丝不动 ⇒ 屏固定。
 *        📌 `文本`：盒 `320×320`，`h=720` 落 `1.75`（屏宽实测 `560`）、`h=680` 落 `1.625`、`h=760` 落 `1.875`
 *           ⇒ 若屏宽是 `320×落点` 则是**随落点缩放**；若三档都是 `560` 则是屏固定。
 *        📌 `图片`：盒 `569×320`，`h=720` 落 `1.19531`（面板屏宽实测 `959`）⇒ 另两档同法。
 *
 * ⛔ 本批不做：不平移任何节点（📌 逐臂核对节点画布 `transform` 未变）、不删除、不新建、不触发生成。
 *
 * 前提检查：轴向自检 / 落定自检（三连读，📌 **点完先等 `3200ms`**）/ 点击生效自检 /
 *   `aria` 精确匹配现找现量 / 参数写死 / 每臂独立浏览器 / 盒尺寸逐臂现量 / 平移量逐臂现量。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b328.json';
const 放大键 = 'Meta+Equal';
const 闭式 = (w, h, W, H, z0) => Math.min((w - 532) / W, (h - 160) / H, z0);
const 节 = (x) => (x === undefined || x === null ? null : Math.round(x * 1000) / 1000);
const round6 = (x) => (x === null || x === undefined ? null : +Number(x).toFixed(6));

const 臂表 = [
  { 键: 'W_1', 组: 'P0对照', kind: '文本', 名: '文本 1', vw: 1212, vh: 720, 锁定: false },
  { 键: '音1_720', 组: 'P1尺子', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 锁定: true },
  { 键: '时2_720', 组: 'P2时间线', kind: '时间线', 名: '时间线 2', vw: 1212, vh: 720, 锁定: true },
  { 键: '图_720', 组: 'P3图片', kind: '图片', 名: 'b22-upload', vw: 1212, vh: 720, 锁定: true },
  { 键: '图_680', 组: 'P3图片', kind: '图片', 名: 'b22-upload', vw: 1212, vh: 680, 锁定: true },
  { 键: '图_760', 组: 'P3图片', kind: '图片', 名: 'b22-upload', vw: 1212, vh: 760, 锁定: true },
  { 键: '文1_680', 组: 'P4文本', kind: '文本', 名: '文本 1', vw: 1212, vh: 680, 锁定: true },
  { 键: '文1_720', 组: 'P4文本', kind: '文本', 名: '文本 1', vw: 1212, vh: 720, 锁定: true },
  { 键: '文1_760', 组: 'P4文本', kind: '文本', 名: '文本 1', vw: 1212, vh: 760, 锁定: true },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b328',
  问: '第三档 (R, A) 在哪？—— 327 的 R 普查只认 node-toolbar 一个 testid，时间线节点明明有 timeline-toolbar',
  接327: '撤回「五量和=innerHeight」（恒等式）；间隙非常数 {20, 20.069, 20.078, 20.087}；图片/文本的面板被判成不存在其实在节点上方',
  判据: {
    P0: '阳性对照 文本 @1212×720（不锁定）必须逐字落 1.75',
    P1: '音频 1（锁定）必须逐字落 1.125 ⇒ 尺子没漂',
    P2: '时间线 2（锁定）：普查全部可见 data-testid，找它的面板叫什么、屏高多少、在节点上方还是下方',
    P3: '图片 b22-upload 在 h=680/720/760（锁定）：落点变了面板屏宽跟不跟 ⇒ 判屏固定与否',
    P4: '文本 1 在 h=680/720/760（锁定）：同上',
  },
  臂表, 臂: [], 判定: {},
};

const 读画布 = () => {
  const e = document.querySelector('.react-flow__viewport');
  const t = e ? (e.style.transform || '') : '';
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(t);
  return { x: m ? Number(m[1]) : null, y: m ? Number(m[2]) : null };
};

const 找空白 = () => {
  for (let y = 60; y < innerHeight - 60; y += 40) {
    for (let x = 40; x < innerWidth - 40; x += 40) {
      const e = document.elementFromPoint(x, y);
      if (e && !e.closest('.react-flow__node') && !e.closest('[data-testid="canvas-search-panel"]')) return { x, y };
    }
  }
  return null;
};

const 拖一次 = async (p, dx) => {
  const 起点 = await p.evaluate(找空白);
  if (!起点) return { 错: '找不到空白起点' };
  const 终x = Math.max(2, Math.min(起点.x + dx, 1210));
  await p.mouse.move(起点.x, 起点.y);
  await p.mouse.down();
  await p.mouse.move(终x, 起点.y, { steps: Math.max(2, Math.round(Math.abs(dx) / 2)) });
  await p.mouse.up();
  await p.waitForTimeout(1400);
  return { 起点, 终x };
};

const 备好结果行 = async (p, 词表, 目标id) => {
  const 面板已开 = await p.evaluate(() => !!document.querySelector('[data-testid="canvas-search-panel"] input'));
  if (!面板已开) {
    const 钮 = await p.evaluate(() => {
      const b = document.querySelector('button[aria-label="搜索"]');
      if (!b) return null;
      const r = b.getBoundingClientRect();
      return { 中心: [r.x + r.width / 2, r.y + r.height / 2], 可见: r.width > 0 && r.height > 0 && r.y >= 0 && r.bottom <= innerHeight };
    });
    if (!钮 || !钮.可见) return { 错: '找不到可见的搜索钮' };
    await p.mouse.click(钮.中心[0], 钮.中心[1]);
    await p.waitForTimeout(1600);
  }
  for (const 词 of 词表) {
    const 有输入框 = await p.evaluate(() => {
      const i = document.querySelector('[data-testid="canvas-search-panel"] input');
      if (!i) return false;
      i.focus(); i.select();
      return true;
    });
    if (!有输入框) return { 错: '搜索面板没有输入框' };
    await p.keyboard.type(词, { delay: 80 });
    await p.waitForTimeout(2000);
    const sel = '[data-testid="canvas-search-result-node_' + String(目标id).replace(/^node_/, '') + '"]';
    let r = await p.evaluate((s) => {
      const e = document.querySelector(s);
      if (!e) return null;
      e.scrollIntoView({ block: 'center' });
      const b = e.getBoundingClientRect();
      return { 中心: [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)], 可见: b.width > 0 && b.height > 0 && b.y >= 0 && b.bottom <= innerHeight && b.x >= 0 && b.right <= innerWidth };
    }, sel);
    if (r && !r.可见) {
      await p.waitForTimeout(600);
      r = await p.evaluate((s) => { const e = document.querySelector(s); const b = e.getBoundingClientRect(); return { 中心: [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)], 可见: b.width > 0 && b.height > 0 && b.y >= 0 && b.bottom <= innerHeight && b.x >= 0 && b.right <= innerWidth }; }, sel);
    }
    if (r && r.可见) return { 中心: r.中心 };
  }
  return { 错: '搜不到可见结果行' };
};

// 📌 按 testid **普查**：把页面上每一个可见的 `[data-testid]` 都量一遍屏矩形，
//    并标注它在不在选中节点内、在节点的上方还是下方。
//    📌 立规 204：探针的筛选条件必须真的盖住要判的那一刻 —— 327 用「testid 白名单 + 窗口」两道筛，
//    327 的 `文本`/`图片` 面板都被这两道筛挡掉了（其实它们在节点**上方**）。
//    本批 📌 **不筛 testid**，只按「可见且屏矩形非退化」过滤。
const 普查面板 = (id) => {
  // 📌 `page.evaluate` 会把这个函数**序列化后送进浏览器**执行，模块作用域里的 `节` 它拿不到
  //    （批次 328 第一臂就撞过这个：`ReferenceError: 节 is not defined`，两个臂全部作废）。
  //    ⇒ 所以凡是会在浏览器里跑的函数，用到的每个辅助函数都必须**在函数体内重新定义**。
  const 节 = (x) => (x === undefined || x === null ? null : Math.round(x * 1000) / 1000);
  const 节点e = document.querySelector('.react-flow__node[data-id="' + id + '"]');
  if (!节点e) return { 错: '节点不在 DOM 里' };
  const nb = 节点e.getBoundingClientRect();
  const 节点 = { top: 节(nb.top), bottom: 节(nb.bottom), left: 节(nb.left), right: 节(nb.right), w: 节(nb.width), h: 节(nb.height) };
  const 全 = [];
  const seen = new Set();
  for (const x of document.querySelectorAll('[data-testid]')) {
    const tid = x.getAttribute('data-testid');
    if (!tid || seen.has(tid)) continue;
    const b = x.getBoundingClientRect();
    if (!(b.width > 0 && b.height > 0)) continue;
    seen.add(tid);
    全.push({
      testid: tid, top: 节(b.top), bottom: 节(b.bottom), left: 节(b.left), right: 节(b.right),
      w: 节(b.width), h: 节(b.height),
      在节点内: !!节点e.contains(x),
      相对节点: b.bottom <= nb.top + 0.5 ? '上方' : (b.top >= nb.bottom - 0.5 ? '下方' : '相交'),
      水平中心差: 节(Math.abs((b.left + b.right) / 2 - (nb.left + nb.right) / 2)),
    });
  }
  全.sort((a, b) => (b.w * b.h) - (a.w * a.h));
  return { 节点, innerH: innerHeight, innerW: innerWidth, 全testid: 全 };
};

// ───────── 启动前自检：先在一个一次性浏览器里，把普查逻辑放到**浏览器上下文**真跑一遍 ─────────
// 📌 立规 208（本批新增）：`page.evaluate` 的回调会被**序列化后送进浏览器**执行，
//    模块作用域里的任何标识符（辅助函数、常量）在浏览器里**不存在**。
//    症状是 `ReferenceError: <名字> is not defined`，而且**每个臂报同一句** ——
//    不看头两臂就会误判成「数据全废」，其实是脚本压根没跑起来
//    （批次 328 首次运行：第一臂就 `ReferenceError: 节 is not defined`，两个臂全废）。
{
  let brs = null;
  try {
    brs = await chromium.launch({ headless: true });
    const cs = await brs.newContext({ storageState: STATE, viewport: { width: 1212, height: 720 } });
    const ps = await cs.newPage();
    await ps.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await ps.waitForSelector('.react-flow__node[data-id]', { timeout: 60000 });
    await ps.waitForTimeout(4000);
    // 📌 这里把普查逻辑**原样**再写一遍（而不是引模块里的 `普查面板`）——
    //    目的正是验「这段代码放进浏览器上下文能不能跑」，所以它必须是同一份字面量。
    const 冒烟 = await ps.evaluate(() => {
      const 节 = (x) => (x === undefined || x === null ? null : Math.round(x * 1000) / 1000);
      const 普查面板 = (id) => {
        const 节 = (x) => (x === undefined || x === null ? null : Math.round(x * 1000) / 1000);
        const 节点e = document.querySelector('.react-flow__node[data-id="' + id + '"]');
        if (!节点e) return { 错: '节点不在 DOM 里' };
        const nb = 节点e.getBoundingClientRect();
        const 节点 = { top: 节(nb.top), bottom: 节(nb.bottom), left: 节(nb.left), right: 节(nb.right), w: 节(nb.width), h: 节(nb.height) };
        const 全 = [];
        const seen = new Set();
        for (const x of document.querySelectorAll('[data-testid]')) {
          const tid = x.getAttribute('data-testid');
          if (!tid || seen.has(tid)) continue;
          const b = x.getBoundingClientRect();
          if (!(b.width > 0 && b.height > 0)) continue;
          seen.add(tid);
          全.push({ testid: tid, top: 节(b.top), bottom: 节(b.bottom), left: 节(b.left), right: 节(b.right), w: 节(b.width), h: 节(b.height), 在节点内: !!节点e.contains(x), 相对节点: b.bottom <= nb.top + 0.5 ? '上方' : (b.top >= nb.bottom - 0.5 ? '下方' : '相交'), 水平中心差: 节(Math.abs((b.left + b.right) / 2 - (nb.left + nb.right) / 2)) });
        }
        全.sort((a, b) => (b.w * b.h) - (a.w * a.h));
        return { 节点, innerH: innerHeight, innerW: innerWidth, 全testid: 全 };
      };
      const e = document.querySelector('.react-flow__node[data-id]');
      if (!e) return { 错: '取不到节点' };
      const r = 普查面板(e.dataset.id);
      if (!r.全testid || !r.全testid.length) return { 错: '普查返回空数组' };
      if (typeof r.节点.h !== 'number' || !Number.isFinite(r.节点.h)) return { 错: '节点屏高不是有限数' };
      if (!r.全testid.some((t) => typeof t.testid === 'string' && t.testid)) return { 错: '普查项里没有 testid 字符串' };
      return { 条数: r.全testid.length, 节点h: r.节点.h, 首个testid: r.全testid[0].testid };
    });
    if (冒烟.错) throw new Error(冒烟.错);
    log('✅ 启动前自检通过：普查逻辑在浏览器上下文里跑得通 —— 普查到 ' + 冒烟.条数
      + ' 个 testid（首个 `' + 冒烟.首个testid + '`）、节点屏高 `' + 冒烟.节点h + '`');
  } catch (e) {
    log('🔴 启动前自检失败（脚本跑不起来，先修再跑）：' + e.message);
    process.exit(2);
  } finally {
    try { if (brs) await brs.close(); } catch (e) { /* 忽略 */ }
  }
}

for (const 臂 of 臂表) {
  let br = null; let p = null; let nid = null;
  const 记 = { 键: 臂.键, 组: 臂.组, kind: 臂.kind, 名: 臂.名, vw: 臂.vw, vh: 臂.vh, 锁定: 臂.锁定 };
  try {
    br = await chromium.launch({ headless: true });
    const ctx = await br.newContext({ storageState: STATE, viewport: { width: 臂.vw, height: 臂.vh } });
    p = await ctx.newPage();
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 60000 });
    await p.waitForTimeout(6000);

    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== 臂.vw || 实际.h !== 臂.vh) throw new Error('轴向自检失败：' + 实际.w + 'x' + 实际.h);

    const 找 = await p.evaluate((aria) => {
      const e = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
        .find((x) => x.getAttribute('aria-label') === aria);
      return e ? { id: e.dataset.id, W: e.offsetWidth, H: e.offsetHeight, tf: e.style.transform || '' } : null;
    }, 臂.kind + ' node: ' + 臂.名);
    if (!找) throw new Error('找不到 aria 为「' + (臂.kind + ' node: ' + 臂.名) + '」的节点');
    nid = 找.id;
    记.画布盒 = { W: 找.W, H: 找.H };
    const H0 = 找.H;
    const W0 = 找.W;

    for (let i = 0; i < 13; i++) { await p.keyboard.press(放大键); await p.waitForTimeout(380); }
    await p.waitForTimeout(1600);
    const 读缩放 = () => p.evaluate(() => {
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      return m ? Number(m[1]) : null;
    });
    记.点之前 = await 读缩放();
    if (记.点之前 === null) throw new Error('点之前读不到 scale');

    记.拖 = null;
    if (臂.锁定) {
      const 前 = await p.evaluate(读画布);
      const r = await 拖一次(p, 120);
      const 后 = await p.evaluate(读画布);
      记.拖 = { 命令: 120, 错: r.错 || null, dx实测: (前.x !== null && 后.x !== null) ? +(后.x - 前.x).toFixed(1) : null, dy实测: (前.y !== null && 后.y !== null) ? +(后.y - 前.y).toFixed(1) : null };
    }

    const ariaWant = 臂.kind + ' node: ' + 臂.名;
    const 行 = await 备好结果行(p, [臂.名, ariaWant, 臂.kind], nid);
    if (行.错) throw new Error(行.错);
    await p.mouse.click(行.中心[0], 行.中心[1]);
    记.点后首读 = await 读缩放();
    await p.waitForTimeout(3200);
    const 读1 = await 读缩放();
    await p.waitForTimeout(2600);
    const 读2 = await 读缩放();
    await p.waitForTimeout(2000);
    const 读3 = await 读缩放();
    记.读1 = 读1; 记.读2 = 读2; 记.读3 = 读3;
    记.落定 = (读1 === 读2 && 读2 === 读3);
    记.终点 = 读3;

    const 选 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((x) => x.dataset.id));
    记.点击生效 = 选.includes(nid);
    if (!记.点击生效) throw new Error('点击未生效（选中=' + JSON.stringify(选) + '）');

    const 后 = await p.evaluate((id) => {
      const e = document.querySelector('.react-flow__node[data-id="' + id + '"]');
      return e ? e.style.transform || '' : null;
    }, nid);
    记.节点画布坐标未变 = (后 === 找.tf);

    await p.waitForTimeout(1800);
    记.普查 = await p.evaluate(普查面板, nid);

    记.闭式预测 = round6(闭式(臂.vw, 臂.vh, 找.W, H0, 记.点之前));
    记.命中闭式 = 记.终点 !== null && Math.abs(记.终点 - 记.闭式预测) < 5e-5;
    记.safeH = 臂.vh - 160;
    记.节点屏高_直接量 = 记.普查.节点 ? 记.普查.节点.h : null;
    记.节点屏宽_直接量 = 记.普查.节点 ? 记.普查.节点.w : null;
    记.A = 记.终点 !== null ? Math.round((记.safeH - H0 * 记.终点) * 1000) / 1000 : null;
    记.A宽向 = 记.终点 !== null ? Math.round((臂.vw - 532 - W0 * 记.终点) * 1000) / 1000 : null;

    const 面板候选 = (记.普查.全testid || []).filter((t) => /toolbar|panel|bar-host|feature-host/.test(t.testid));
    记.面板候选 = 面板候选;
    const 主 = 面板候选.find((t) => t.testid === 'node-toolbar') || 面板候选[0] || null;
    记.主面板 = 主;
    if (主) {
      记.主面板屏高 = 主.h;
      记.主面板屏宽 = 主.w;
      记.主面板位置 = 主.相对节点;
      记.主面板画布宽 = 节(主.w / 记.终点);
      记.主面板画布高 = 节(主.h / 记.终点);
      记.主面板屏宽除节点盒宽 = 节(主.w / W0);
      记.主面板屏宽除落点 = 节(主.w / 记.终点);
    }

    log(臂.键.padEnd(9) + '｜' + 臂.名.padEnd(11) + '｜' + String(臂.vw + 'x' + 臂.vh).padEnd(10)
      + '｜盒=' + String(W0 + 'x' + H0).padEnd(9)
      + '｜落点=' + String(记.终点).padEnd(11)
      + '｜A高向=' + String(记.A).padEnd(10)
      + '｜A宽向=' + String(记.A宽向).padEnd(10)
      + '｜主面板=' + String(主 ? 主.testid : '—').padEnd(24)
      + (主 ? '屏' + String(主.w) + 'x' + String(主.h) + ' ' + 主.相对节点 + ' 内' + (主.在节点内 ? 'Y' : 'N')
             + ' 画布' + String(记.主面板画布宽) + 'x' + String(记.主面板画布高) : '')
      + '｜面板候选数=' + 面板候选.length);
  } catch (e) {
    记.错误 = e.message;
    log(臂.键.padEnd(9) + '🔴 ' + e.message);
  } finally {
    try { if (p) await p.close(); } catch (e) { /* 忽略 */ }
    try { if (br) await br.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

// ───────── 判定 ─────────
const 好 = out.臂.filter((x) => !x.错误 && x.点击生效 && x.落定 && x.终点 !== null);
const 取 = (k) => 好.find((x) => x.键 === k);
const 组集 = (g) => 好.filter((x) => x.组 === g);
const 面板串 = (xs) => xs.map((x) => '`' + x.键 + '`(h=' + x.vh + ') 落 `' + x.终点 + '`、`A`高向 `' + x.A + '`、`A`宽向 `' + x.A宽向
  + (x.主面板 ? '、面板 `' + x.主面板.testid + '` 屏 `' + x.主面板屏宽 + '×' + x.主面板屏高 + '` 在节点**' + x.主面板位置 + '**'
      + '、换算成画布是 `' + x.主面板画布宽 + '×' + x.主面板画布高 + '`' : '、**面板没普查到**')).join('；');

const 对照 = 取('W_1');
const 判定P0 = 对照 && 对照.命中闭式
  ? '✅ P0：阳性对照 `文本 1 @1212×720`（不锁定）落 `' + 对照.终点 + '` 逐字等于闭式 ⇒ 尺子没漂'
  : '🔴 P0：阳性对照=' + (对照 ? 对照.终点 : '—') + '（期望 1.75）⇒ 本批作废';

const 尺子 = 取('音1_720');
const 判定P1 = !尺子 ? '（P1 臂不全）'
  : (尺子.终点 === 1.125
    ? '✅ P1：`音频 1`（锁定）落 `' + 尺子.终点 + '` 逐字复现 ⇒ 尺子没漂'
    : '🔴 P1：`音频 1` 落 `' + 尺子.终点 + '`（期望 `1.125`）⇒ 本批作废');

const 时组 = 组集('P2时间线');
const 判定P2 = !时组.length ? '（P2 臂不全）'
  : '📌 P2：时间线的面板叫什么 —— ' + 面板串(时组)
    + ' ⇒ ' + (时组[0].主面板
      ? '📌 **找到了 `' + 时组[0].主面板.testid + '` 这个 testid**（327 的普查只认 `node-toolbar`，把它挡在门外了）'
      : '📌 时间线节点上**任何** testid 都没匹配到面板 ⇒ 它是真的没有屏固定面板');

const 判定屏固定 = (g, 名) => {
  const xs = 组集(g);
  if (xs.length < 2) return '（' + g + ' 臂不足 2 个）';
  const 面板集 = xs.filter((x) => x.主面板);
  if (!面板集.length) return '📌 ' + 名 + '：**没有普查到面板**，判不了屏固定';
  const 屏宽集 = Array.from(new Set(面板集.map((x) => x.主面板屏宽)));
  const 屏高集 = Array.from(new Set(面板集.map((x) => x.主面板屏高)));
  const 画布宽集 = Array.from(new Set(面板集.map((x) => x.主面板画布宽)));
  const 画布高集 = Array.from(new Set(面板集.map((x) => x.主面板画布高)));
  return '📌 ' + 名 + ' 的屏固定性 —— ' + 面板集.map((x) => '`h=' + x.vh + '` 落 `' + x.终点 + '` 面板屏 `' + x.主面板屏宽 + '×' + x.主面板屏高
      + '` 换算画布 `' + x.主面板画布宽 + '×' + x.主面板画布高 + '`').join('；')
    + ' ⇒ 📌 屏宽取值集合 `{' + 屏宽集.join(', ') + '}`、屏高取值集合 `{' + 屏高集.join(', ') + '}`'
    + '、**换算成画布后**宽 `{' + 画布宽集.join(', ') + '}` 高 `{' + 画布高集.join(', ') + '}`'
    + ' ⇒ ' + (画布宽集.length === 1 && 画布高集.length === 1
      ? '✅ **换算成画布后两维都逐字不变 ⇒ 面板是画布空间固定的**，只是随落点缩放'
      : (屏宽集.length === 1 && 屏高集.length === 1
        ? '✅ **屏两维都逐字不变 ⇒ 面板是屏固定的**'
        : '📌 **屏两维都变了** ⇒ 面板既不是屏固定也不是画布固定（换算成画布后仍变）'));
};

out.判定 = {
  有效臂: 好.length + '/' + 臂表.length,
  判定P0_尺子: 判定P0,
  判定P1_尺子: 判定P1,
  判定P2_时间线面板: 判定P2,
  判定P3_图片屏固定性: 判定屏固定('P3图片', '图片 b22-upload'),
  判定P4_文本屏固定性: 判定屏固定('P4文本', '文本 1'),
  逐臂: 好.map((x) => ({
    键: x.键, 组: x.组, kind: x.kind, 名: x.名, 视口: x.vw + 'x' + x.vh, 锁定: x.锁定, 画布盒: x.画布盒,
    拖: x.拖, 节点画布坐标未变: x.节点画布坐标未变,
    z0: x.点之前, 读1: x.读1, 读2: x.读2, 读3: x.读3, 落定: x.落定, 落点: x.终点,
    闭式预测: x.闭式预测, 命中闭式: x.命中闭式, safeH: x.safeH,
    节点屏高: x.节点屏高_直接量, 节点屏宽: x.节点屏宽_直接量,
    A高向: x.A, A宽向: x.A宽向,
    主面板: x.主面板, 面板候选: x.面板候选,
    全testid: x.普查 ? x.普查.全testid : null,
  })),
  失效臂: out.臂.filter((x) => x.错误).map((x) => ({ 键: x.键, 错: x.错误 })),
};
log('\n════ 判定 ════\n' + JSON.stringify({
  有效臂: out.判定.有效臂, P0: 判定P0, P1: 判定P1, P2: 判定P2,
  P3: out.判定.判定P3_图片屏固定性, P4: out.判定.判定P4_文本屏固定性,
}, null, 1));

const brz = await chromium.launch({ headless: true });
const ctxz = await brz.newContext({ storageState: STATE, viewport: { width: 1280, height: 720 } });
const pz = await ctxz.newPage();
try {
  await pz.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await pz.waitForSelector('.react-flow__node', { timeout: 60000 });
  await pz.waitForTimeout(6000);
  out.末态 = await pz.evaluate(() => ({
    节点数: document.querySelectorAll('.react-flow__node').length,
    状态行: (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null,
    积分: (document.querySelector('[data-testid="canvas-commerce-entry"]') || {}).textContent || null,
  }));
  log('末态独立复查：' + JSON.stringify(out.末态));
} finally { try { await pz.close(); await brz.close(); } catch (e) { /* 忽略 */ } }

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
process.exit(0);
