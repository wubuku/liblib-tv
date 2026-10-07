/**
 * 批次 332 · 锁定门槛**二分到底** + 🔴 一个**从未干净做过**的实验：「拖回原处会不会解锁」。
 *
 * ✅ 接批次 331（`9/9` 臂）：
 *    ✅ 门槛收窄到 **`(17.45, 19.33]`** 屏像素（`dx = 70/80/90/100/110` 全部未锁，`dx=120` 锁定）
 *    🔴 **未锁区内的 `A` 对 `Δy` 非单调**：`217.200 / 211.0304 / 211.0336 / 209.008 / 212.464`
 *    📌 立规 206 早就写过「平移回原处会不会解锁」这条未测项，📌 **但批次 325 的甲组实测净平移是
 *       `(0,+36.8)`–`(0,+37.8)`、根本没回原处**，📌 所以那条**至今没有被干净地测过一次**
 *
 * 📌 **本批三问**：
 *   **P2 门槛续二分**：📌 批次 331 把门槛夹在 `(17.45, 19.33]`，📌 本批扫 `dx = 112/114/116/118`
 *        ⇒ 📌 期望把 `Δy` 铺在 `17.45`–`19.33` 之间
 *   **P3 回原处**：📌 `+120` 之后再 `-120`，📌 **逐臂验净位移确实回到 `0`**（📌 立规 206 ②：
 *        判据里凡是带「回原处」这种词的，📌 都要把那件事量出来）⇒ 📌 还锁 ⇒ **锁是位移的函数**；
 *        🔴 解锁 ⇒ **锁是「动过」这个状态**
 *   **P4 反方向**：📌 单次 `-120`（往反方向拖）⇒ 📌 锁 ⇒ **锁与方向有关**；🔴 不锁 ⇒ **只看位移大小**
 *
 * ⛔ 本批不做：不平移任何节点（📌 逐臂核对节点画布 `transform` 未变）、不删除、不新建、不触发生成。
 *
 * 前提检查：**启动前自检** / 轴向自检 / 落定自检（三连读，📌 **点完先等 `3200ms`**）/ 点击生效自检 /
 *   `aria` 精确匹配现找现量 / 参数写死 / 每臂独立浏览器 / 盒尺寸逐臂现量 / **平移量逐臂现量** /
 *   **净位移逐臂现量并当场断言**（P3 的命门）。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b332.json';
const 放大键 = 'Meta+Equal';
const 节 = (x) => (x === undefined || x === null ? null : Math.round(x * 1000000) / 1000000);
const round6 = (x) => (x === null || x === undefined ? null : +Number(x).toFixed(6));

// 📌 面板预留 `R` 写死在这一批要用的两类节点上（📌 批次 329 逐字复现过：`204` 与 `208`）
const R表 = { 音频: 204, 视频: 208 };

const 臂表 = [
  { 键: 'W_1', 组: 'P0对照', kind: '文本', 名: '文本 1', vw: 1212, vh: 720, 锁定: false, 拖序: [] },
  { 键: '音1_120', 组: 'P1尺子', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 锁定: true, 拖序: [120] },
  { 键: '音1_d112', 组: 'P2门槛', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 锁定: true, 拖序: [112] },
  { 键: '音1_d114', 组: 'P2门槛', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 锁定: true, 拖序: [114] },
  { 键: '音1_d116', 组: 'P2门槛', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 锁定: true, 拖序: [116] },
  { 键: '音1_d118', 组: 'P2门槛', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 锁定: true, 拖序: [118] },
  { 键: '音1_往返', 组: 'P3回原处', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 锁定: true, 拖序: [120, -120] },
  { 键: '音1_反120', 组: 'P4反方向', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 锁定: true, 拖序: [-120] },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b332',
  问: '锁定门槛的确切值；拖回原处会不会解锁；反方向拖会不会锁',
  接331: '门槛收窄到 (17.45, 19.33]；未锁区 A 对 Δy 非单调；立规 206 的「回原处」至今没干净测过',
  判据: {
    P0: '阳性对照 文本 @1212×720（不拖）必须逐字落 1.75',
    P1: '音频 1 带 dx=120（锁定）必须逐字落 1.125、A=200 ⇒ 尺子没漂、也确认这一拖确实锁住',
    P2: '门槛续二分：dx = 112/114/116/118 逐臂现量实测 Δy 与 A',
    P3: '回原处：+120 之后再 -120，**必须先断言净位移确实回到 0**，再看还锁不锁',
    P4: '反方向：单次 -120，看锁不锁',
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

// 📌 溯源：📌 节点自身 → 祖先链（最多 5 层）→ 直接子元素，📌 逐个查尺寸相关的**全部**属性。
const 溯源 = (id) => {
  const 节 = (x) => (x === undefined || x === null ? null : Math.round(x * 1000000) / 1000000);
  const 属性表 = [
    'width', 'height', 'min-width', 'min-height', 'max-width', 'max-height',
    'aspect-ratio', 'box-sizing', 'padding-top', 'padding-bottom', 'padding-left', 'padding-right',
    'border-top-width', 'border-bottom-width', 'zoom', 'transform', 'display', 'position', 'contain',
  ];
  const 读一个 = (e) => {
    if (!e) return null;
    const cs = getComputedStyle(e);
    const 属 = {};
    for (const k of 属性表) 属[k] = cs.getPropertyValue(k);
    // 📌 把节点/祖先上**所有**自定义属性里名字命中关键词的挑出来
    const 自定义 = {};
    for (let i = 0; i < cs.length; i++) {
      const 名 = cs[i];
      if (typeof 名 !== 'string' || 名.charAt(0) !== '-') continue;
      const 低 = 名.toLowerCase();
      if (低.indexOf('octo') < 0 && 低.indexOf('aspect') < 0 && 低.indexOf('ratio') < 0
        && 低.indexOf('size') < 0 && 低.indexOf('height') < 0 && 低.indexOf('width') < 0) continue;
      自定义[名] = cs.getPropertyValue(名).slice(0, 90);
    }
    return {
      tag: e.tagName.toLowerCase(),
      testid: e.getAttribute('data-testid'),
      cls: (e.getAttribute('class') || '').slice(0, 70),
      style: (e.getAttribute('style') || '').slice(0, 200),
      属,
      自定义,
    };
  };
  const 节点e = document.querySelector('.react-flow__node[data-id="' + id + '"]');
  if (!节点e) return { 错: '节点不在 DOM 里' };
  const 链 = [];
  let cur = 节点e;
  for (let i = 0; i < 6 && cur; i++) { 链.push(读一个(cur)); cur = cur.parentElement; }
  const 子 = Array.from(节点e.children).slice(0, 4).map(读一个);
  return { 链, 子 };
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
      const 溯源 = (id) => {
        const 节 = (x) => (x === undefined || x === null ? null : Math.round(x * 1000000) / 1000000);
        const 属性表 = ['width', 'height', 'max-width', 'max-height', 'aspect-ratio', 'box-sizing', 'padding-top', 'padding-bottom', 'zoom', 'display', 'position', 'contain'];
        const 读一个 = (e) => {
          if (!e) return null;
          const cs = getComputedStyle(e);
          const 属 = {};
          for (const k of 属性表) 属[k] = cs.getPropertyValue(k);
          const 自定义 = {};
          for (let i = 0; i < cs.length; i++) {
            const 名 = cs[i];
            if (typeof 名 !== 'string' || 名.charAt(0) !== '-') continue;
            const 低 = 名.toLowerCase();
            if (低.indexOf('octo') < 0 && 低.indexOf('aspect') < 0 && 低.indexOf('ratio') < 0 && 低.indexOf('size') < 0) continue;
            自定义[名] = cs.getPropertyValue(名).slice(0, 90);
          }
          return { tag: e.tagName.toLowerCase(), testid: e.getAttribute('data-testid'), style: (e.getAttribute('style') || '').slice(0, 200), 属, 自定义 };
        };
        const 节点e = document.querySelector('.react-flow__node[data-id="' + id + '"]');
        if (!节点e) return { 错: '节点不在 DOM 里' };
        const 链 = [];
        let cur = 节点e;
        for (let i = 0; i < 6 && cur; i++) { 链.push(读一个(cur)); cur = cur.parentElement; }
        const 子 = Array.from(节点e.children).slice(0, 4).map(读一个);
        return { 链, 子 };
      };
      const e = document.querySelector('.react-flow__node[data-id]');
      if (!e) return { 错: '取不到节点' };
      const r = 溯源(e.dataset.id);
      if (r.错) return { 错: r.错 };
      if (!Array.isArray(r.链) || r.链.length < 3) return { 错: '祖先链太短' };
      if (typeof r.链[0].属.width !== 'string') return { 错: '宽不是字符串' };
      return { 链长: r.链.length, 子数: r.子.length, 首层宽: r.链[0].属.width, 首层高: r.链[0].属.height, 首层自定义数: Object.keys(r.链[0].自定义).length };
    });
    if (冒烟.错) throw new Error(冒烟.错);
    log('✅ 启动前自检通过：`溯源` 在浏览器上下文里跑得通 —— 祖先链 `' + 冒烟.链长
      + '` 层、子元素 `' + 冒烟.子数 + '` 个、首层宽高 `' + 冒烟.首层宽 + ' / ' + 冒烟.首层高
      + '`、命中自定义属性 `' + 冒烟.首层自定义数 + '` 条');
  } catch (e) {
    log('🔴 启动前自检失败（脚本跑不起来，先修再跑）：' + e.message);
    process.exit(2);
  } finally {
    try { if (brs) await brs.close(); } catch (e) { /* 忽略 */ }
  }
}

for (const 臂 of 臂表) {
  let br = null; let p = null; let nid = null;
  const 记 = { 键: 臂.键, 组: 臂.组, kind: 臂.kind, 名: 臂.名, vw: 臂.vw, vh: 臂.vh, 锁定: 臂.锁定, dx: 臂.dx };
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
    记.拖序 = 臂.拖序.slice();
    if (臂.拖序.length > 0) {
      const 起 = await p.evaluate(读画布);
      记.拖 = { 起, 段: [], 错: [] };
      for (const d of 臂.拖序) {
        const 前 = await p.evaluate(读画布);
        const r = await 拖一次(p, d);
        if (r.错) 记.拖.错.push(r.错);
        const 后 = await p.evaluate(读画布);
        const 段 = {
          命令: d,
          dx实测: (前.x !== null && 后.x !== null) ? +(后.x - 前.x).toFixed(2) : null,
          dy实测: (前.y !== null && 后.y !== null) ? +(后.y - 前.y).toFixed(2) : null,
        };
        if (段.dx实测 !== null && 段.dx实测 !== 0) {
          throw new Error('平移量自检失败：横向命令拖的 dx 实测应为 0，却是 ' + 段.dx实测);
        }
        记.拖.段.push(段);
      }
      const 末 = await p.evaluate(读画布);
      记.拖.末 = 末;
      记.拖.净dy = (起.y !== null && 末.y !== null) ? +(末.y - 起.y).toFixed(2) : null;
      记.拖.净dx = (起.x !== null && 末.x !== null) ? +(末.x - 起.x).toFixed(2) : null;
      记.拖.总dy = 记.拖.段.reduce((q, s) => q + (s.dy实测 || 0), 0);
      if (记.拖.净dx !== null && 记.拖.净dx !== 0) {
        throw new Error('平移量自检失败：往返之后净 dx 应为 0，却是 ' + 记.拖.净dx);
      }
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
    if (臂.组 === 'P2溯源') 记.溯源 = await p.evaluate(溯源, nid);

    const z = 记.终点;
    记.safeH = 臂.vh - 160;
    记.A = z !== null ? 节(记.safeH - H0 * z) : null;
    记.锁定与否 = R表[臂.kind] !== undefined && 记.A !== null
      ? (Math.abs(记.A - (R表[臂.kind] - 4)) < 0.002 ? '锁定' : '未锁') : 'n/a';

    log(臂.键.padEnd(9) + '｜' + 臂.名.padEnd(11) + '｜拖序=[' + 臂.拖序.join(',') + ']'
      + '｜Δy段=' + (记.拖 ? 记.拖.段.map((s2) => String(s2.dy实测)).join('/') : '—').padEnd(22)
      + '｜净Δy=' + String(记.拖 ? 记.拖.净dy : '—').padEnd(7)
      + '｜落点=' + String(z).padEnd(11)
      + '｜A=' + String(记.A).padEnd(10)
      + '｜' + 记.锁定与否);
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

const 对照 = 取('W_1');
const 判定P0 = 对照
  ? (对照.终点 === 1.75 ? '✅ P0：阳性对照 `文本 1 @1212×720`（不拖）落 `1.75` ⇒ 尺子没漂' : '🔴 P0：阳性对照落 `' + 对照.终点 + '`（期望 1.75）⇒ 本批作废')
  : '🔴 P0：对照臂无效';

const 尺子 = 取('音1_120');
const 判定P1 = !尺子 ? '（P1 臂不全）'
  : (尺子.终点 === 1.125 && Math.abs(尺子.A - 200) < 0.002
    ? '✅ P1：`音频 1` 带 `dx=120` 落 `1.125`、`A` = `' + 尺子.A + '` ⇒ **尺子没漂，且这一拖确实锁住**'
    : '🔴 P1：落 `' + 尺子.终点 + '`、`A` = `' + 尺子.A + '`（期望 `1.125`/`200`）⇒ 本批作废');

// 📌 门槛：📌 把批次 331 与 332 的**全部**未锁/锁臂按实测 Δy 排好，📌 找「未锁 → 锁定」的第一处分界。
const 门槛组 = 组集('P2门槛').filter((x) => x.拖 && x.拖.净dy !== null);
const 判定P2 = !门槛组.length ? '（P2 臂不全）'
  : '📌 P2：门槛续二分（`音频 1`，`h=720`，期望干净值 `A = 200`）—— '
    + 门槛组.slice().sort((a, b) => Math.abs(a.拖.净dy) - Math.abs(b.拖.净dy))
      .map((x) => '命令 `' + x.拖序[0] + '` ⇒ 实测 `净Δy=' + x.拖.净dy + '` ⇒ `A` = `' + x.A + '` **' + x.锁定与否 + '**').join('；')
    + '\n　　⇒ 📌 `净Δx` 逐臂实测都是 `0`（📌 与批次 331、325 结果四一致）'
    + '\n　　⇒ ' + (() => {
      const 尺 = 取('音1_120');
      const 锁集 = 门槛组.filter((x) => x.锁定与否 === '锁定' && x.拖.净dy !== null)
        .concat(尺 && 尺.锁定与否 === '锁定' && 尺.拖.净dy !== null ? [尺] : [])
        .sort((a, b) => Math.abs(a.拖.净dy) - Math.abs(b.拖.净dy));
      const xs = 门槛组.filter((x) => x.锁定与否 === '未锁').sort((a, b) => Math.abs(a.拖.净dy) - Math.abs(b.拖.净dy));
      if (!锁集.length) return '🔴 没有任何一个锁定档 ⇒ 整组读数不可解释';
      // 📌 立规 205 ①：📌 取**最窄的那个锁定档**当界上界，📌 **不是**随手拿尺子那一档
      //    （第一版正是拿尺子的 19.33 当界，📌 那会把区间报成 `(17.77, 19.33]` 而虚胖 `1.56` 像素）
      const hi = 锁集[0];
      const 门槛 = Math.abs(hi.拖.净dy);
      if (!xs.length) return '📌 本批这几档**全部锁定** ⇒ 📌 只报读数，不下「分界在哪」的结论（立规 205 ①）';
      const lo = xs[xs.length - 1];
      return '✅ **未锁的最高档 `净Δy=' + lo.拖.净dy + '`（`A=' + lo.A + '`，未锁）；**最窄的**锁定档 `净Δy=' + hi.拖.净dy + '`（`A=' + hi.A + '`，臂 `' + hi.键 + '`）**'
        + '\n　　⇒ 📌 **门槛 ∈ (' + Math.abs(lo.拖.净dy) + ', ' + 门槛 + '] 屏像素**，📌 宽度约 `' + (门槛 - Math.abs(lo.拖.净dy)).toFixed(2) + '` 像素'
        + '\n　　⇒ 📌 批次 331 给的 `(17.45, 19.33]`（宽 `1.88`）⇒ 📌 **本批收窄到 `' + (门槛 - Math.abs(lo.拖.净dy)).toFixed(2) + '` 像素宽**';
    })();

// 📌 P3 回原处：📌 **先验净位移确实回到 0**（立规 206 ②），📌 再看还锁不锁。
const 往返 = 取('音1_往返');
const 判定P3 = !往返 ? '（P3 臂不全）'
  : '📌 P3：拖回原处会不会解锁 —— '
    + '拖序 `[' + 往返.拖序.join(', ') + ']`，📌 逐段实测 `Δy` = `' + 往返.拖.段.map((s) => String(s.dy实测)).join('` / `') + '`'
    + '，📌 **净 `Δx` = `' + 往返.拖.净dx + '`、净 `Δy` = `' + 往返.拖.净dy + '`**'
    + ' ⇒ 📌 ' + (往返.拖.净dx === 0 && Math.abs(往返.拖.净dy) < 0.01
      ? '✅ **净位移确实回到 `0`**（📌 立规 206 ② 要求的「回原处」这次是真的量到了，📌 批次 325 那次不是）'
      : '🔴 **净位移没回到 `0`** ⇒ 📌 这个臂测的不是「回原处」，作废')
    + '；落点 `' + 往返.终点 + '`、`A` = `' + 往返.A + '` **' + 往返.锁定与否 + '**'
    + '\n　　⇒ ' + (往返.拖.净dx === 0 && Math.abs(往返.拖.净dy) < 0.01
      ? (往返.锁定与否 === '锁定'
        ? '✅ **回到原处之后仍然锁定** ⇒ 📌 **锁是「净位移大小」的函数，不是「动过没有」这个状态**（立规 206 ① 终于有了一次干净读数）'
        : '🔴 **回到原处之后解锁了** ⇒ 📌 **锁是「动过」这个状态，不是位移大小** ⇒ 📌 批次 325 那句「门槛是 `|Δtranslate|` 的门槛」🔴 **不成立**，📌 要改写成「门槛是『有没有动过』」')
      : '📌 因净位移没回零，本臂不下结论');

const 反 = 取('音1_反120');
const 判定P4 = !反 ? '（P4 臂不全）'
  : '📌 P4：反方向单拖 —— 拖序 `[' + 反.拖序.join(', ') + ']`，实测 `净Δy` = `' + 反.拖.净dy + '`、净 `Δx` = `' + 反.拖.净dx + '`'
    + ' ⇒ 落点 `' + 反.终点 + '`、`A` = `' + 反.A + '` **' + 反.锁定与否 + '**'
    + '\n　　⇒ ' + (反.锁定与否 === '锁定'
      ? '✅ **往反方向拖也锁住** ⇒ 📌 锁**只看位移大小、不看方向**'
      : '🔴 **反方向不锁** ⇒ 📌 锁**与方向有关**');

out.判定 = {
  有效臂: 好.length + '/' + 臂表.length,
  判定P0_尺子: 判定P0,
  判定P1_尺子: 判定P1,
  判定P2_门槛续二分: 判定P2,
  判定P3_回原处: 判定P3,
  判定P4_反方向: 判定P4,
  逐臂: 好.map((x) => ({
    键: x.键, 组: x.组, kind: x.kind, 名: x.名, 视口: x.vw + 'x' + x.vh, 锁定: x.锁定, 拖序: x.拖序,
    画布盒offset: x.画布盒offset, 拖: x.拖, 节点画布坐标未变: x.节点画布坐标未变,
    z0: x.点之前, 读1: x.读1, 读2: x.读2, 读3: x.读3, 落定: x.落定, 落点: x.终点,
    A: x.A, 锁定与否: x.锁定与否,
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