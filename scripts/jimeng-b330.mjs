/**
 * 批次 330 · 盒尺寸的「`offsetX` 与真实值」全画布普查 —— 📌 顺带找出 `568.875` 与 `568.889` 的**来源**。
 *
 * ✅ 接批次 329（`11/11` 臂）：
 *    🔴 `视频 1` 的**真实画布盒高是 `568.875`**，而 `offsetHeight` 报 `569` ⇒ 📌 落点拿 `569` 算、
 *       画出来 `568.875` ⇒ 间隙 = `20 + 0.125 × 落点`（`5/5` 臂残差 `≤ 0.00042`）
 *    🔴 `图片` 的 `A宽向` = `−0.131 / −0.141 / −0.150`（随视口宽变），📌 批次 329 判「成因仍未测」
 *       ⇒ 📌 **本批先用已有读数反推一个候选**：`屏差 ÷ 落点` = `0.109930 / 0.111401 / 0.111111`
 *       ⇒ 📌 **≈ `1/9`**，📌 即图片节点真实画布宽可能是 **`568.889 = 569 − 1/9`**
 *       ⇒ 📌 代入 `(w − 532)/568.889` 得 `1.195312267 / 1.262109128 / 1.349999736`
 *       ⇒ 📌 与三个实测落点 `1.195310 / 1.262110 / 1.35` **逐字吻合** ⇒ 📌 **同一现象**
 *
 * 📌 **本批两问**：
 *   **P2** 反推验证：📌 每臂把「节点屏矩形 ÷ 落点」算成**真实画布盒**，📌 与 `offsetWidth/Height`
 *        对照 ⇒ 📌 哪些节点的 `offsetX` 与真实值**不一致**、差多少、是否与落点无关。
 *   **P3** 来源定位：📌 把节点的**内联 `style` 全文**、**`getComputedStyle` 的 `width`/`height`**、
 *        **直接子元素的 testid 与它们的屏矩形**全部倒出来 ⇒ 📌 看那个分数是**写死在 style 里**的，
 *        还是**布局算出来的**（📌 比如按比例、按 `aspect-ratio`、按父容器百分比）。
 *
 * ⛔ 本批不做：不平移任何节点（📌 逐臂核对节点画布 `transform` 未变）、不删除、不新建、不触发生成。
 *
 * 前提检查：**启动前自检** / 轴向自检 / 落定自检（三连读，📌 **点完先等 `3200ms`**）/ 点击生效自检 /
 *   `aria` 精确匹配现找现量 / 参数写死 / 每臂独立浏览器 / 盒尺寸逐臂现量 / 平移量逐臂现量。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b330.json';
const 放大键 = 'Meta+Equal';
const 闭式 = (w, h, W, H, z0) => Math.min((w - 532) / W, (h - 160) / H, z0);
const 节 = (x) => (x === undefined || x === null ? null : Math.round(x * 1000000) / 1000000);

const 臂表 = [
  { 键: 'W_1', 组: 'P0对照', kind: '文本', 名: '文本 1', vw: 1212, vh: 720, 锁定: false },
  { 键: '音1_720', 组: 'P1尺子', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 锁定: true },
  { 键: '音1_680', 组: 'P2反推', kind: '音频', 名: '音频 1', vw: 1212, vh: 680, 锁定: true },
  { 键: '音1_760', 组: 'P2反推', kind: '音频', 名: '音频 1', vw: 1212, vh: 760, 锁定: true },
  { 键: '视1_640', 组: 'P2反推', kind: '视频', 名: '视频 1', vw: 1212, vh: 640, 锁定: true },
  { 键: '视1_720', 组: 'P2反推', kind: '视频', 名: '视频 1', vw: 1212, vh: 720, 锁定: true },
  { 键: '视1_800', 组: 'P2反推', kind: '视频', 名: '视频 1', vw: 1212, vh: 800, 锁定: true },
  { 键: '图_1212', 组: 'P4图片宽', kind: '图片', 名: 'b22-upload', vw: 1212, vh: 720, 锁定: true },
  { 键: '图_1250', 组: 'P4图片宽', kind: '图片', 名: 'b22-upload', vw: 1250, vh: 720, 锁定: true },
  { 键: '图_1300', 组: 'P4图片宽', kind: '图片', 名: 'b22-upload', vw: 1300, vh: 720, 锁定: true },
  { 键: '时2_720', 组: 'P5时间线', kind: '时间线', 名: '时间线 2', vw: 1212, vh: 720, 锁定: true },
  { 键: '导_720', 组: 'P6外部', kind: '外部', 名: '导演台', vw: 1212, vh: 720, 锁定: true },
  { 键: '文3_720', 组: 'P7文本变体', kind: '文本', 名: '文本 3', vw: 1212, vh: 720, 锁定: true },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b330',
  问: '哪些节点的 offsetX 与真实画布盒不一致、差多少；那个分数是写死在 style 里还是布局算出来的',
  接329: '视频真实画布高 568.875（offsetHeight 报 569）；图片 A宽向 随视口宽变、成因未测；候选 568.889 = 569 − 1/9',
  判据: {
    P0: '阳性对照 文本 @1212×720（不锁定）必须逐字落 1.75',
    P1: '音频 1（锁定）必须逐字落 1.125 ⇒ 尺子没漂',
    P2: '反推：真实画布盒 = 节点屏矩形 ÷ 落点；与 offsetWidth/offsetHeight 对照',
    P3: '来源：内联 style 全文 + getComputedStyle 的 width/height + 直接子元素 testid 与屏矩形',
    P4: '图片在 w=1212/1250/1300：真实画布宽是不是 568.889',
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

// 📌 把「这个节点到底是什么盒子」一次性倒出来：📌 内联 style、computed 宽高、直接子元素。
const 拆盒 = (id) => {
  const 节 = (x) => (x === undefined || x === null ? null : Math.round(x * 1000000) / 1000000);
  const e = document.querySelector('.react-flow__node[data-id="' + id + '"]');
  if (!e) return { 错: '节点不在 DOM 里' };
  const b = e.getBoundingClientRect();
  const cs = getComputedStyle(e);
  const 子 = Array.from(e.children).slice(0, 8).map((x) => {
    const cb = x.getBoundingClientRect();
    const ccs = getComputedStyle(x);
    return {
      tag: x.tagName.toLowerCase(),
      testid: x.getAttribute('data-testid'),
      cls: (x.getAttribute('class') || '').slice(0, 60),
      style: (x.getAttribute('style') || '').slice(0, 160),
      屏宽: 节(cb.width), 屏高: 节(cb.height),
      计算宽: ccs.width, 计算高: ccs.height,
    };
  });
  return {
    屏宽: 节(b.width), 屏高: 节(b.height),
    offset宽: e.offsetWidth, offset高: e.offsetHeight,
    计算宽: cs.width, 计算高: cs.height,
    内联style: e.getAttribute('style'),
    transform: e.style.transform || '',
    子,
  };
};

// ───────── 启动前自检 ─────────
{
  let brs = null;
  try {
    brs = await chromium.launch({ headless: true });
    const cs2 = await brs.newContext({ storageState: STATE, viewport: { width: 1212, height: 720 } });
    const ps = await cs2.newPage();
    await ps.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await ps.waitForSelector('.react-flow__node[data-id]', { timeout: 60000 });
    await ps.waitForTimeout(4000);
    const 冒烟 = await ps.evaluate(() => {
      const 节 = (x) => (x === undefined || x === null ? null : Math.round(x * 1000000) / 1000000);
      const 拆盒 = (id) => {
        const 节 = (x) => (x === undefined || x === null ? null : Math.round(x * 1000000) / 1000000);
        const e = document.querySelector('.react-flow__node[data-id="' + id + '"]');
        if (!e) return { 错: '节点不在 DOM 里' };
        const b = e.getBoundingClientRect();
        const cs = getComputedStyle(e);
        const 子 = Array.from(e.children).slice(0, 8).map((x) => {
          const cb = x.getBoundingClientRect();
          const ccs = getComputedStyle(x);
          return { tag: x.tagName.toLowerCase(), testid: x.getAttribute('data-testid'), cls: (x.getAttribute('class') || '').slice(0, 60), style: (x.getAttribute('style') || '').slice(0, 160), 屏宽: 节(cb.width), 屏高: 节(cb.height), 计算宽: ccs.width, 计算高: ccs.height };
        });
        return { 屏宽: 节(b.width), 屏高: 节(b.height), offset宽: e.offsetWidth, offset高: e.offsetHeight, 计算宽: cs.width, 计算高: cs.height, 内联style: e.getAttribute('style'), transform: e.style.transform || '', 子 };
      };
      const e = document.querySelector('.react-flow__node[data-id]');
      if (!e) return { 错: '取不到节点' };
      const r = 拆盒(e.dataset.id);
      if (r.错) return { 错: r.错 };
      if (typeof r.屏宽 !== 'number' || !Number.isFinite(r.屏宽)) return { 错: '屏宽不是有限数' };
      if (!Array.isArray(r.子)) return { 错: '子元素列表不是数组' };
      return { 屏宽: r.屏宽, 屏高: r.屏高, offset宽: r.offset宽, 子数: r.子.length, 计算宽: r.计算宽 };
    });
    if (冒烟.错) throw new Error(冒烟.错);
    log('✅ 启动前自检通过：`拆盒` 在浏览器上下文里跑得通 —— 屏 `'
      + 冒烟.屏宽 + '×' + 冒烟.屏高 + '`、offset `' + 冒烟.offset宽 + '`、计算宽 `' + 冒烟.计算宽 + '`、子元素 `' + 冒烟.子数 + '` 个');
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
    记.画布盒offset = { W: 找.W, H: 找.H };
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
      记.拖 = { 命令: 120, 错: r.错 || null, dx实测: (前.x !== null && 后.x !== null) ? +(后.x - 前.x).toFixed(1) : null, dy实测: (前.y !== null && 后.y !== null) ? +(后.y - 后.y).toFixed(1) : null };
      记.拖.dy实测 = (前.y !== null && 后.y !== null) ? +(后.y - 前.y).toFixed(1) : null;
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

    await p.waitForTimeout(1500);
    记.盒 = await p.evaluate(拆盒, nid);

    const z = 记.终点;
    记.真实画布宽 = (记.盒 && z) ? 节(记.盒.屏宽 / z) : null;
    记.真实画布高 = (记.盒 && z) ? 节(记.盒.屏高 / z) : null;
    记.宽差 = (记.真实画布宽 !== null) ? 节(W0 - 记.真实画布宽) : null;
    记.高差 = (记.真实画布高 !== null) ? 节(H0 - 记.真实画布高) : null;
    记.safeH = 臂.vh - 160;
    记.safeW = 臂.vw - 532;
    记.A高向 = z !== null ? 节(记.safeH - H0 * z) : null;
    记.A宽向 = z !== null ? 节(记.safeW - W0 * z) : null;
    记.闭式预测 = z !== null ? Math.round(闭式(臂.vw, 臂.vh, W0, H0, 记.点之前) * 1e6) / 1e6 : null;
    记.命中闭式 = z !== null && Math.abs(z - 记.闭式预测) < 5e-5;

    log(臂.键.padEnd(9) + '｜' + 臂.名.padEnd(11) + '｜' + String(臂.vw + 'x' + 臂.vh).padEnd(10)
      + '｜落点=' + String(z).padEnd(11)
      + '｜offset=' + String(W0 + 'x' + H0).padEnd(9)
      + '｜真实画布=' + String(记.真实画布宽).padEnd(11) + 'x' + String(记.真实画布高).padEnd(11)
      + '｜差=' + String(记.宽差).padEnd(9) + '/' + String(记.高差).padEnd(9)
      + '｜计算宽高=' + String(记.盒 ? 记.盒.计算宽 : '—') + '/' + String(记.盒 ? 记.盒.计算高 : '—'));
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
const 序 = (xs) => xs.slice().sort((a, b) => a.vh - b.vh || a.vw - b.vw);

const 对照 = 取('W_1');
const 判定P0 = 对照 && 对照.命中闭式
  ? '✅ P0：阳性对照 `文本 1 @1212×720`（不锁定）落 `' + 对照.终点 + '` 逐字等于闭式 ⇒ 尺子没漂'
  : '🔴 P0：阳性对照=' + (对照 ? 对照.终点 : '—') + '（期望 1.75）⇒ 本批作废';

const 尺子 = 取('音1_720');
const 判定P1 = !尺子 ? '（P1 臂不全）'
  : (尺子.终点 === 1.125
    ? '✅ P1：`音频 1`（锁定）落 `' + 尺子.终点 + '` 逐字复现 ⇒ 尺子没漂'
    : '🔴 P1：`音频 1` 落 `' + 尺子.终点 + '`（期望 `1.125`）⇒ 本批作废');

// 📌 按 kind 归组，每组报「真实画布盒取值集合」与「offset 与真实值的差」。
const 按类 = {};
for (const x of 好) {
  const k = x.kind + ' ' + x.名;
  if (!按类[k]) 按类[k] = [];
  按类[k].push(x);
}
const 类集 = Object.keys(按类).sort();
const 判定P2 = '📌 P2：全画布盒尺寸普查（真实画布盒 ≟ 节点屏矩形 ÷ 落点）\n'
  + 类集.map((k) => {
    const xs = 序(按类[k]);
    const 真宽 = Array.from(new Set(xs.map((x) => x.真实画布宽)));
    const 真高 = Array.from(new Set(xs.map((x) => x.真实画布高)));
    const 差宽 = Array.from(new Set(xs.map((x) => x.宽差)));
    const 差高 = Array.from(new Set(xs.map((x) => x.高差)));
    return '　📌 `' + k + '`（' + xs.length + ' 臂）offset `' + xs[0].画布盒offset.W + '×' + xs[0].画布盒offset.H + '`'
      + '｜真实画布宽 `{' + 真宽.join(', ') + '}`｜真实画布高 `{' + 真高.join(', ') + '}`'
      + '｜宽差 `{' + 差宽.join(', ') + '}`｜高差 `{' + 差高.join(', ') + '}`'
      + '⇒ ' + (差宽.every((d) => Math.abs(d) < 1e-6) && 差高.every((d) => Math.abs(d) < 1e-6)
        ? '✅ `offsetX` 与真实值逐字一致'
        : '🔴 **`offsetX` 与真实值不一致**');
  }).join('\n');

const 图组 = 组集('P4图片宽');
const 图真宽 = Array.from(new Set(图组.filter((x) => x.真实画布宽 !== null).map((x) => x.真实画布宽)));
const 判定P4 = !图组.length ? '（P4 臂不全）'
  : '📌 P4：图片的真实画布宽是不是 `568.889` —— '
    + 序(图组).map((x) => '`w=' + x.vw + '` 落 `' + x.终点 + '`、真实画布宽 `' + x.真实画布宽 + '`、offset `' + x.画布盒offset.W + '`、宽差 `' + x.宽差 + '`').join('；')
    + ' ⇒ 📌 取值集合 `{' + 图真宽.join(', ') + '}`'
    + ' ⇒ ' + (图真宽.length === 1 ? '✅ **三档视口宽上真实画布宽逐字恒**，📌 与候选 `568.889` ' + (Math.abs(图真宽[0] - 568.889) < 0.01 ? '**吻合**' : '**不吻合**（实测 `' + 图真宽[0] + '`）') : '🔴 真实画布宽随视口宽变');

const 判定P3 = '📌 P3：那个分数是**写死在 style 里**还是**布局算出来的** ——\n'
  + 序(好).map((x) => {
    const b = x.盒;
    if (!b) return '　📌 `' + x.键 + '`：没读到盒';
    return '　📌 `' + x.键 + '`（`' + x.kind + ' ' + x.名 + '`）内联 `style` = `' + String(b.内联style) + '`'
      + '｜`getComputedStyle` 宽/高 = `' + b.计算宽 + ' / ' + b.计算高 + '`'
      + '｜直接子元素：' + (b.子.length ? b.子.map((c) => '`' + (c.testid || c.tag) + '` 内联 `' + String(c.style) + '` 计算 `' + c.计算宽 + '×' + c.计算高 + '`').join(' ｜ ') : '（无）');
  }).join('\n');

out.判定 = {
  有效臂: 好.length + '/' + 臂表.length,
  判定P0_尺子: 判定P0,
  判定P1_尺子: 判定P1,
  判定P2_全画布盒普查: 判定P2,
  判定P3_分数来源: 判定P3,
  判定P4_图片真实画布宽: 判定P4,
  逐臂: 好.map((x) => ({
    键: x.键, 组: x.组, kind: x.kind, 名: x.名, 视口: x.vw + 'x' + x.vh, 锁定: x.锁定,
    画布盒offset: x.画布盒offset, 真实画布宽: x.真实画布宽, 真实画布高: x.真实画布高, 宽差: x.宽差, 高差: x.高差,
    盒: x.盒,
    拖: x.拖, 节点画布坐标未变: x.节点画布坐标未变,
    z0: x.点之前, 读1: x.读1, 读2: x.读2, 读3: x.读3, 落定: x.落定, 落点: x.终点,
    A高向: x.A高向, A宽向: x.A宽向,
  })),
  失效臂: out.臂.filter((x) => x.错误).map((x) => ({ 键: x.键, 错: x.错误 })),
};
log('\n════ 判定 ════\n' + JSON.stringify({
  有效臂: out.判定.有效臂, P0: 判定P0, P1: 判定P1, P2: 判定P2, P3: 判定P3, P4: 判定P4,
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
