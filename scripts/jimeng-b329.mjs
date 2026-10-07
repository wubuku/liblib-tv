/**
 * 批次 329 · 三件事，都来自批次 328 自己标的「仍未测」里的前三名。
 *
 * ✅ 接批次 328（`9/9` 臂）：
 *    ✅ 面板的**宽与高是两回事**：文本面板屏宽 `520/560/600` 换算成画布宽度逐字恒 `320`，
 *       屏高三档逐字恒 `40` ⇒ 📌 宽画布固定、高屏固定
 *    📌 `A宽向`：时间线逐字 `0`、图片逐字 `−0.131`、文本 `160/120/80`、音频 `320`
 *    📕 立规 209（两维分判、`else` 不能代替判决）｜📕 立规 210（单向蕴含要用反例撞）
 *
 * 📌 **本批三问**：
 *   **P2/P3 面板屏固定性**（🔴 立规 210 ④ 点名的风险）：📌 批次 328 只在**一个落点**上量过
 *        `音频 1` 的面板屏宽 `680`；📌 批次 327 虽在三个视口高上量过 `视频 1` 的面板屏**高**
 *        （`208 / 208 / 208`），📌 但**屏宽**从没量过 ⇒ 📌 **两维都要在多个落点上重测**，
 *        📌 **而且每维单独判决**（立规 209）。
 *   **P4 图片的 `A宽向 = −0.131`**：📌 那个小数在**三个视口高上逐字相同**，📌 说明它不是高度带来的；
 *        📌 本批换**视口宽**（`w = 1212 / 1250 / 1300`）⇒ 📌 若 `−0.131` 还逐字不变 ⇒ 📌 它是
 *        **宽度预算本身带的小数**；📌 若随 `w` 变 ⇒ 📌 它是别的什么东西。
 *   **P5 间隙的趋势**：📌 批次 327 量到视频的间隙是 `20.069 / 20.078 / 20.087`（`h=680/720/760`），
 *        📌 随 `h` **单调升**；📌 本批补 `h = 640 / 800` 两档 ⇒ 📌 看这条趋势**延伸到哪**。
 *
 * ⛔ 本批不做：不平移任何节点（📌 逐臂核对节点画布 `transform` 未变）、不删除、不新建、不触发生成。
 *
 * 前提检查：**启动前自检**（普查逻辑先在浏览器上下文真跑一遍）/ 轴向自检 / 落定自检（三连读，
 *   📌 **点完先等 `3200ms`**）/ 点击生效自检 / `aria` 精确匹配现找现量 / 参数写死 /
 *   每臂独立浏览器 / 盒尺寸逐臂现量 / 平移量逐臂现量。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b329.json';
const 放大键 = 'Meta+Equal';
const 闭式 = (w, h, W, H, z0) => Math.min((w - 532) / W, (h - 160) / H, z0);
const 节 = (x) => (x === undefined || x === null ? null : Math.round(x * 1000) / 1000);
const round6 = (x) => (x === null || x === undefined ? null : +Number(x).toFixed(6));

const 臂表 = [
  { 键: 'W_1', 组: 'P0对照', kind: '文本', 名: '文本 1', vw: 1212, vh: 720, 锁定: false },
  { 键: '音1_720', 组: 'P1尺子', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 锁定: true },
  { 键: '音1_680', 组: 'P2音频面板', kind: '音频', 名: '音频 1', vw: 1212, vh: 680, 锁定: true },
  { 键: '音1_760', 组: 'P2音频面板', kind: '音频', 名: '音频 1', vw: 1212, vh: 760, 锁定: true },
  { 键: '视1_640', 组: 'P3视频面板', kind: '视频', 名: '视频 1', vw: 1212, vh: 640, 锁定: true },
  { 键: '视1_680', 组: 'P3视频面板', kind: '视频', 名: '视频 1', vw: 1212, vh: 680, 锁定: true },
  { 键: '视1_760', 组: 'P3视频面板', kind: '视频', 名: '视频 1', vw: 1212, vh: 760, 锁定: true },
  { 键: '视1_800', 组: 'P3视频面板', kind: '视频', 名: '视频 1', vw: 1212, vh: 800, 锁定: true },
  { 键: '图_1212', 组: 'P4图片宽向', kind: '图片', 名: 'b22-upload', vw: 1212, vh: 720, 锁定: true },
  { 键: '图_1250', 组: 'P4图片宽向', kind: '图片', 名: 'b22-upload', vw: 1250, vh: 720, 锁定: true },
  { 键: '图_1300', 组: 'P4图片宽向', kind: '图片', 名: 'b22-upload', vw: 1300, vh: 720, 锁定: true },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b329',
  问: '音频/视频面板的屏宽在多个落点上是不是恒；图片那个 −0.131 是不是宽度预算自带的小数；间隙那条趋势延伸到哪',
  接328: '面板两维答案相反（宽画布固定、高屏固定）；A宽向 时间线=0、图片=−0.131；timeline-toolbar 是画布级元素',
  判据: {
    P0: '阳性对照 文本 @1212×720（不锁定）必须逐字落 1.75',
    P1: '音频 1（锁定）必须逐字落 1.125 ⇒ 尺子没漂',
    P2: '音频 1 在 h=680/720/760：面板屏宽、屏高分别判决，**每维单独判**',
    P3: '视频 1 在 h=640/680/720/760/800：面板屏宽、屏高分别判决，**每维单独判**；顺带看间隙趋势',
    P4: '图片 b22-upload 在 w=1212/1250/1300：A宽向 还是不是逐字 −0.131',
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

// 📌 只认**所属节点自己**的那几个 testid，并且用**水平中心差**把画布级元素剔掉。
//    📌 立规 210/批次 328 结果四：`timeline-toolbar` 在**每一臂**都出现（中心差 `704`–`3833`），
//    📌 真面板的中心差是 `0`–`0.009` ⇒ 📌 这里只取 testid 在白名单里**且**中心差 `< 2` 的那些。
const 量自己的面板 = (id) => {
  const 节 = (x) => (x === undefined || x === null ? null : Math.round(x * 1000) / 1000);
  const 白名单 = ['node-toolbar', 'selection-context-toolbar', 'selection-context-toolbar-surface'];
  const 节点e = document.querySelector('.react-flow__node[data-id="' + id + '"]');
  if (!节点e) return { 错: '节点不在 DOM 里' };
  const nb = 节点e.getBoundingClientRect();
  const 节点 = { top: 节(nb.top), bottom: 节(nb.bottom), w: 节(nb.width), h: 节(nb.height), cx: 节((nb.left + nb.right) / 2) };
  const seen = new Set();
  const 全 = [];
  for (const x of document.querySelectorAll('[data-testid]')) {
    const tid = x.getAttribute('data-testid');
    if (!tid || seen.has(tid)) continue;
    const b = x.getBoundingClientRect();
    if (!(b.width > 0 && b.height > 0)) continue;
    seen.add(tid);
    const cx = (b.left + b.right) / 2;
    全.push({ testid: tid, w: 节(b.width), h: 节(b.height), top: 节(b.top), bottom: 节(b.bottom), cx: 节(cx), 中心差: 节(Math.abs(cx - 节点.cx)) });
  }
  const 命中 = 全.filter((t) => 白名单.indexOf(t.testid) >= 0 && t.中心差 !== null && t.中心差 < 2)
    .sort((a, b) => (b.w * b.h) - (a.w * a.h));
  const 出 = { 节点, 候选数: 命中.length, 白名单总数: 全.filter((t) => 白名单.indexOf(t.testid) >= 0).length, 画布级干扰样本: 全.filter((t) => /timeline-toolbar|canvas-fixed-toolbar/.test(t.testid)).map((t) => t.testid + '@' + t.中心差) };
  if (!命中.length) return 出;
  const 主 = 命中[0];
  出.主 = 主;
  出.间隙 = 节(主.top - 节点.bottom);
  出.相对节点 = 主.bottom <= 节点.top + 0.5 ? '上方' : (主.top >= 节点.bottom - 0.5 ? '下方' : '相交');
  return 出;
};

// ───────── 启动前自检（立规 209 ⑤）─────────
{
  let brs = null;
  try {
    brs = await chromium.launch({ headless: true });
    const cs = await brs.newContext({ storageState: STATE, viewport: { width: 1212, height: 720 } });
    const ps = await cs.newPage();
    await ps.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await ps.waitForSelector('.react-flow__node[data-id]', { timeout: 60000 });
    await ps.waitForTimeout(4000);
    const 冒烟 = await ps.evaluate(() => {
      const 节 = (x) => (x === undefined || x === null ? null : Math.round(x * 1000) / 1000);
      const 量自己的面板 = (id) => {
        const 节 = (x) => (x === undefined || x === null ? null : Math.round(x * 1000) / 1000);
        const 白名单 = ['node-toolbar', 'selection-context-toolbar', 'selection-context-toolbar-surface'];
        const 节点e = document.querySelector('.react-flow__node[data-id="' + id + '"]');
        if (!节点e) return { 错: '节点不在 DOM 里' };
        const nb = 节点e.getBoundingClientRect();
        const 节点 = { top: 节(nb.top), bottom: 节(nb.bottom), w: 节(nb.width), h: 节(nb.height), cx: 节((nb.left + nb.right) / 2) };
        const seen = new Set();
        const 全 = [];
        for (const x of document.querySelectorAll('[data-testid]')) {
          const tid = x.getAttribute('data-testid');
          if (!tid || seen.has(tid)) continue;
          const b = x.getBoundingClientRect();
          if (!(b.width > 0 && b.height > 0)) continue;
          seen.add(tid);
          const cx = (b.left + b.right) / 2;
          全.push({ testid: tid, w: 节(b.width), h: 节(b.height), top: 节(b.top), bottom: 节(b.bottom), cx: 节(cx), 中心差: 节(Math.abs(cx - 节点.cx)) });
        }
        const 命中 = 全.filter((t) => 白名单.indexOf(t.testid) >= 0 && t.中心差 !== null && t.中心差 < 2).sort((a, b) => (b.w * b.h) - (a.w * a.h));
        const 出 = { 节点, 候选数: 命中.length };
        if (命中.length) { 出.主 = 命中[0]; 出.间隙 = 节(命中[0].top - 节点.bottom); }
        return 出;
      };
      const e = document.querySelector('.react-flow__node[data-id]');
      if (!e) return { 错: '取不到节点' };
      const r = 量自己的面板(e.dataset.id);
      if (r.错) return { 错: r.错 };
      if (typeof r.节点.h !== 'number' || !Number.isFinite(r.节点.h)) return { 错: '节点屏高不是有限数' };
      return { 节点h: r.节点.h, 候选数: r.候选数, 主宽: r.主 ? r.主.w : null };
    });
    if (冒烟.错) throw new Error(冒烟.错);
    log('✅ 启动前自检通过：普查逻辑在浏览器上下文里跑得通 —— 节点屏高 `' + 冒烟.节点h
      + '`、候选 `' + 冒烟.候选数 + '`、主面板宽 `' + 冒烟.主宽 + '`');
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
    const W0 = 找.W; const H0 = 找.H;

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
    记.面板 = await p.evaluate(量自己的面板, nid);

    记.闭式预测 = round6(闭式(臂.vw, 臂.vh, W0, H0, 记.点之前));
    记.命中闭式 = 记.终点 !== null && Math.abs(记.终点 - 记.闭式预测) < 5e-5;
    记.safeH = 臂.vh - 160;
    记.safeW = 臂.vw - 532;
    记.节点屏高_直接量 = 记.面板 && 记.面板.节点 ? 记.面板.节点.h : null;
    记.A高向 = 记.终点 !== null ? 节(记.safeH - H0 * 记.终点) : null;
    记.A宽向 = 记.终点 !== null ? 节(记.safeW - W0 * 记.终点) : null;
    const 主 = 记.面板 ? 记.面板.主 : null;
    记.面板屏宽 = 主 ? 主.w : null;
    记.面板屏高 = 主 ? 主.h : null;
    记.面板位置 = 记.面板 ? 记.面板.相对节点 : null;
    记.间隙 = 记.面板 ? 记.面板.间隙 : null;
    记.面板画布宽 = (主 && 记.终点) ? 节(主.w / 记.终点) : null;
    记.面板画布高 = (主 && 记.终点) ? 节(主.h / 记.终点) : null;

    log(臂.键.padEnd(9) + '｜' + 臂.名.padEnd(11) + '｜' + String(臂.vw + 'x' + 臂.vh).padEnd(10)
      + '｜落点=' + String(记.终点).padEnd(11)
      + '｜面板屏=' + String(记.面板屏宽).padEnd(6) + 'x' + String(记.面板屏高).padEnd(6)
      + '｜换算画布=' + String(记.面板画布宽).padEnd(9) + 'x' + String(记.面板画布高).padEnd(9)
      + '｜位置=' + String(记.面板位置).padEnd(4)
      + '｜间隙=' + String(记.间隙).padEnd(8)
      + '｜A高向=' + String(记.A高向).padEnd(9)
      + '｜A宽向=' + String(记.A宽向));
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
// 📌 立规 209：每一维**单独判决**，绝不合成一个布尔量。
const 好 = out.臂.filter((x) => !x.错误 && x.点击生效 && x.落定 && x.终点 !== null);
const 取 = (k) => 好.find((x) => x.键 === k);
const 组集 = (g) => 好.filter((x) => x.组 === g);
const 序 = (xs) => xs.slice().sort((a, b) => a.vh - b.vh || a.vw - b.vw);
const 串 = (xs) => 序(xs).map((x) => '`' + x.键 + '`(h=' + x.vh + (x.组 === 'P4图片宽向' ? ',w=' + x.vw : '') + ') 落 `' + x.终点
  + '`、面板屏 `' + x.面板屏宽 + '×' + x.面板屏高 + '`、换算画布 `' + x.面板画布宽 + '×' + x.面板画布高 + '`').join('；');

// 📌 逐维判决函数：**屏宽恒否**、**屏高恒否**、**画布宽恒否**、**画布高恒否**，四项各出一个结论。
const 逐维 = (g, 名) => {
  const xs = 组集(g).filter((x) => x.面板屏宽 !== null && x.面板屏高 !== null);
  if (xs.length < 2) return '（' + g + ' 有效臂不足 2 个）';
  const 屏宽 = Array.from(new Set(xs.map((x) => x.面板屏宽)));
  const 屏高 = Array.from(new Set(xs.map((x) => x.面板屏高)));
  const 画宽 = Array.from(new Set(xs.map((x) => x.面板画布宽)));
  const 画高 = Array.from(new Set(xs.map((x) => x.面板画布高)));
  const 落点集 = Array.from(new Set(xs.map((x) => x.终点)));
  const 自变量真变了 = 落点集.length > 1;
  const 判 = (集) => (集.length === 1 ? '✅ 恒为 `' + 集[0] + '`' : '🔴 在变：' + 集.map((v) => '`' + v + '`').join(' / '));
  return '📌 ' + 名 + ' 的面板逐维判决（' + xs.length + ' 臂，落点集合 ' + 落点集.map((v) => '`' + v + '`').join('、')
    + (自变量真变了 ? '，📌 **落点真的变了**，判据有效' : '，🔴 **落点压根没变**，判据无效') + '）—— ' + 串(xs)
    + '\n　　① 屏**宽**：' + 判(屏宽) + '　⇒ ' + (屏宽.length === 1 ? '屏固定' : '随落点变')
    + '\n　　② 屏**高**：' + 判(屏高) + '　⇒ ' + (屏高.length === 1 ? '屏固定' : '随落点变')
    + '\n　　③ 换算成画布**宽**：' + 判(画宽) + '　⇒ ' + (画宽.length === 1 ? '画布空间固定' : '在画布空间里也在变')
    + '\n　　④ 换算成画布**高**：' + 判(画高) + '　⇒ ' + (画高.length === 1 ? '画布空间固定' : '在画布空间里也在变')
    + '\n　　⇒ 📌 **每一维各判各的，不合成一个结论**（立规 209）';
};

const 对照 = 取('W_1');
const 判定P0 = 对照 && 对照.命中闭式
  ? '✅ P0：阳性对照 `文本 1 @1212×720`（不锁定）落 `' + 对照.终点 + '` 逐字等于闭式 ⇒ 尺子没漂'
  : '🔴 P0：阳性对照=' + (对照 ? 对照.终点 : '—') + '（期望 1.75）⇒ 本批作废';

const 尺子 = 取('音1_720');
const 判定P1 = !尺子 ? '（P1 臂不全）'
  : (尺子.终点 === 1.125
    ? '✅ P1：`音频 1`（锁定）落 `' + 尺子.终点 + '` 逐字复现 ⇒ 尺子没漂'
    : '🔴 P1：`音频 1` 落 `' + 尺子.终点 + '`（期望 `1.125`）⇒ 本批作废');

const 图组 = 组集('P4图片宽向');
const 图A = 图组.filter((x) => x.A宽向 !== null);
const 判定P4 = !图A.length ? '（P4 臂不全）'
  : ('📌 P4：图片那个 `−0.131` 是什么 —— ' + 图A.map((x) => '`w=' + x.vw + '` 落 `' + x.终点 + '`、`A宽向` `' + x.A宽向 + '`').join('；')
    + ' ⇒ ' + (new Set(图A.map((x) => x.A宽向)).size === 1
      ? '✅ **三个视口宽上 `A宽向` 逐字相同（`' + 图A[0].A宽向 + '`）** ⇒ 📌 它**不是视口宽带来的**，📌 是**宽度预算本身自带的小数**（批次 328 那条「三档视口高逐字相同」也一致）'
      : '🔴 `A宽向` 随视口宽变 ⇒ 📌 它不是常数，📌 之前那三档「逐字相同」是因为**视口宽压根没变过**'));

const 视组 = 组集('P3视频面板').filter((x) => x.间隙 !== null);
const 判定P5 = !视组.length ? '（P5 无间隙读数）'
  : ('📌 P5：视频那条间隙趋势延伸到哪 —— '
    + 序(视组).map((x) => '`h=' + x.vh + '` 间隙 `' + x.间隙 + '`').join('、')
    + ' ⇒ 📌 取值集合 `{' + Array.from(new Set(视组.map((x) => x.间隙))).join(', ') + '}`'
    + (new Set(视组.map((x) => x.间隙)).size > 1
      ? ' ⇒ 🔴 **仍在变**，📌 与批次 327 的 `20.069/20.078/20.087` 接得上'
      : ' ⇒ ✅ **在本批这几档上逐字恒**，📌 与批次 327 的读数冲突（📌 需要复核批次 327 那三档）'));

out.判定 = {
  有效臂: 好.length + '/' + 臂表.length,
  判定P0_尺子: 判定P0,
  判定P1_尺子: 判定P1,
  判定P2_音频面板逐维: 逐维('P2音频面板', '音频 1'),
  判定P3_视频面板逐维: 逐维('P3视频面板', '视频 1'),
  判定P4_图片宽向: 判定P4,
  判定P5_间隙趋势: 判定P5,
  逐臂: 好.map((x) => ({
    键: x.键, 组: x.组, kind: x.kind, 名: x.名, 视口: x.vw + 'x' + x.vh, 锁定: x.锁定, 画布盒: x.画布盒,
    拖: x.拖, 节点画布坐标未变: x.节点画布坐标未变,
    z0: x.点之前, 读1: x.读1, 读2: x.读2, 读3: x.读3, 落定: x.落定, 落点: x.终点,
    闭式预测: x.闭式预测, 命中闭式: x.命中闭式, safeH: x.safeH, safeW: x.safeW,
    节点屏高: x.节点屏高_直接量, A高向: x.A高向, A宽向: x.A宽向,
    面板屏宽: x.面板屏宽, 面板屏高: x.面板屏高, 面板画布宽: x.面板画布宽, 面板画布高: x.面板画布高,
    面板位置: x.面板位置, 间隙: x.间隙, 候选数: x.面板 ? x.面板.候选数 : null,
    画布级干扰样本: x.面板 ? x.面板.画布级干扰样本 : null,
  })),
  失效臂: out.臂.filter((x) => x.错误).map((x) => ({ 键: x.键, 错: x.错误 })),
};
log('\n════ 判定 ════\n' + JSON.stringify({
  有效臂: out.判定.有效臂, P0: 判定P0, P1: 判定P1,
  P2: out.判定.判定P2_音频面板逐维, P3: out.判定.判定P3_视频面板逐维,
  P4: 判定P4, P5: 判定P5,
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
