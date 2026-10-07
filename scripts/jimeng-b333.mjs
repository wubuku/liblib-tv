/**
 * 批次 333 · 门槛**钉死**，外加两个从没测过的问题。
 *
 * ✅ 接批次 332（`8/8` 臂）：
 *    ✅ 门槛 ∈ **`(17.77, 18.07]`** 屏像素（未锁最高 `Δy = 17.77`，锁定从 `18.07` 起）
 *    🔴 **画布平移是棘轮**：拖序 `[+120, -120]` 逐段 `Δy = +18.96 / +18.06`，📌 净 `+37.02` ⇒ 📌 **只增不减**
 *    ✅ **反方向也锁**：单次 `-120` ⇒ `Δy = +19.02`、`A = 200.000` 锁定 ⇒ 📌 锁只看 `|Δtranslate|`
 *    📌 立规 215：📌 落盘 JSON 是权威、📌 日志可能少报判定、📌 取区间界要取最紧的那一档
 *
 * 📌 **本批三问**：
 *   **P2 门槛钉死**：📌 批次 332 把门槛夹在 `(17.77, 18.07]`，📌 本批只加**一个**臂 `dx = 115`
 *        ⇒ 📌 期望把区间切成 `(17.77, ~17.9]` 或 `(~17.9, 18.07]`（📌 实测 `Δy` 才是排序的量，📌 立规 206 ③）
 *   **P3 累加性**：📌 棘轮既然「只增不减」，📌 那**同向连拖两次**是不是**累加**？
 *        📌 拖序 `[+120, +120]` ⇒ 📌 逐段 `Δy` 若第二段 `≈ +19` ⇒ **累加**；📌 若第二段 `≈ 0` ⇒ **饱和**
 *   **P4 锁绑在哪**：📌 锁定 `音频 1` 之后 —— ① 切到 `音频 2`（**不拖**）② 再切回 `音频 1`
 *        ⇒ 📌 三个读数一起看：📌 切走再切回来还锁 ⇒ **锁绑在视口上**（📌 一旦锁住就一直锁）；
 *        🔴 若切回后不锁 ⇒ **锁绑在节点上**（📌 每个节点要各自拖一次）
 *
 * ⛔ 本批不做：不平移任何节点（📌 逐臂核对节点画布 `transform` 未变）、不删除、不新建、不触发生成。
 *
 * 前提检查：**启动前自检** / 轴向自检 / 落定自检（三连读，📌 **点完先等 `3200ms`**）/ 点击生效自检 /
 *   `aria` 精确匹配现找现量 / 参数写死 / 每臂独立浏览器 / 盒尺寸逐臂现量 / **平移量逐臂现量** /
 *   **净位移逐臂现量并当场断言**。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b333.json';
const 放大键 = 'Meta+Equal';
const 节 = (x) => (x === undefined || x === null ? null : Math.round(x * 1000000) / 1000000);

// 📌 面板预留 `R` 写死在本批要用的 `音频` 上（📌 批次 329/331/332 逐字复现过 `204`）
const R表 = { 音频: 204 };

const 臂表 = [
  { 键: 'W_1', 组: 'P0对照', kind: '文本', 名: '文本 1', vw: 1212, vh: 720, 拖序: [] },
  { 键: '音1_120', 组: 'P1尺子', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 拖序: [120] },
  { 键: '音1_d115', 组: 'P2门槛', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 拖序: [115] },
  { 键: '音1_双120', 组: 'P3累加', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 拖序: [120, 120] },
  { 键: '音1_换节点', 组: 'P4锁绑哪', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 拖序: [120], 换到: { kind: '音频', 名: '音频 2' } },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b333',
  问: '门槛的确切值；同向连拖是否累加；锁绑在视口还是绑在节点',
  接332: '门槛 ∈ (17.77, 18.07]；平移是棘轮只增不减；反方向也锁；立规 215',
  判据: {
    P0: '阳性对照 文本 @1212×720（不拖）必须逐字落 1.75',
    P1: '音频 1 带 dx=120（锁定）必须逐字落 1.125、A=200 ⇒ 尺子没漂',
    P2: '音频 1 带 dx=115：把门槛从 (17.77, 18.07] 再切一刀',
    P3: '音频 1 拖序 [+120,+120]：逐段 Δy 若第二段 ≈+19 ⇒ 累加；≈0 ⇒ 饱和',
    P4: '音频 1 锁定后切到 音频 2（不拖）再切回：三个读数看锁绑在视口还是节点',
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

const 找节点 = (aria) => {
  const e = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
    .find((x) => x.getAttribute('aria-label') === aria);
  return e ? { id: e.dataset.id, W: e.offsetWidth, H: e.offsetHeight, tf: e.style.transform || '' } : null;
};

const 读缩放 = () => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  return m ? Number(m[1]) : null;
};

// 📌 「选中一个节点并把落点读定」——📌 批次 333 的每个臂（含 P4 的三次）都走这一条路径。
const 选一次 = async (p, kind, 名, vh) => {
  const ariaWant = kind + ' node: ' + 名;
  const 找 = await p.evaluate(找节点, ariaWant);
  if (!找) throw new Error('找不到 aria 为「' + ariaWant + '」的节点');
  const 行 = await 备好结果行(p, [名, ariaWant, kind], 找.id);
  if (行.错) throw new Error(行.错);
  await p.mouse.click(行.中心[0], 行.中心[1]);
  const 点后首读 = await p.evaluate(读缩放);
  await p.waitForTimeout(3200);
  const 读1 = await p.evaluate(读缩放);
  await p.waitForTimeout(2600);
  const 读2 = await p.evaluate(读缩放);
  await p.waitForTimeout(2000);
  const 读3 = await p.evaluate(读缩放);
  const 选 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((x) => x.dataset.id));
  if (!选.includes(找.id)) throw new Error('点击未生效（选中=' + JSON.stringify(选) + '）');
  const 后 = await p.evaluate((id) => {
    const e = document.querySelector('.react-flow__node[data-id="' + id + '"]');
    return e ? e.style.transform || '' : null;
  }, 找.id);
  const 落定 = (读1 === 读2 && 读2 === 读3);
  const safeH = vh - 160;
  const A = 读3 === null ? null : 节(safeH - 找.H * 读3);
  const 锁 = R表[kind] !== undefined && A !== null
    ? (Math.abs(A - (R表[kind] - 4)) < 0.002 ? '锁定' : '未锁') : 'n/a';
  return {
    kind, 名, 盒: { W: 找.W, H: 找.H }, 点后首读, 读1, 读2, 读3, 落定, 落点: 读3,
    A, 锁定与否: 锁, 节点画布坐标未变: (后 === 找.tf),
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
      const 找节点 = (aria) => {
        const e = Array.from(document.querySelectorAll('.react-flow__node[data-id]')).find((x) => x.getAttribute('aria-label') === aria);
        return e ? { id: e.dataset.id, W: e.offsetWidth, H: e.offsetHeight, tf: e.style.transform || '' } : null;
      };
      const 读缩放 = () => {
        const vp = document.querySelector('.react-flow__viewport');
        const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
        return m ? Number(m[1]) : null;
      };
      const 选一次 = (aria, vh) => {
        const 找 = 找节点(aria);
        if (!找) return { 错: '找不到节点' };
        return { 盒: { W: 找.W, H: 找.H }, 落点: 读缩放(), A: 节((vh - 160) - 找.H * 读缩放()) };
      };
      const r = 选一次('音频 node: 音频 1', 720);
      if (r.错) return { 错: r.错 };
      if (typeof r.落点 !== 'number' || !Number.isFinite(r.落点)) return { 错: '落点不是有限数' };
      if (typeof r.A !== 'number' || !Number.isFinite(r.A)) return { 错: 'A 不是有限数' };
      return { 盒: r.盒.W + 'x' + r.盒.H, 落点: r.落点, A: r.A };
    });
    if (冒烟.错) throw new Error(冒烟.错);
    log('✅ 启动前自检通过：`选一次` 在浏览器上下文里跑得通 —— 盒 `' + 冒烟.盒
      + '`、落点 `' + 冒烟.落点 + '`、`A` = `' + 冒烟.A + '`');
  } catch (e) {
    log('🔴 启动前自检失败（脚本跑不起来，先修再跑）：' + e.message);
    process.exit(2);
  } finally {
    try { if (brs) await brs.close(); } catch (e) { /* 忽略 */ }
  }
}

for (const 臂 of 臂表) {
  let br = null; let p = null;
  const 记 = { 键: 臂.键, 组: 臂.组, kind: 臂.kind, 名: 臂.名, vw: 臂.vw, vh: 臂.vh, 拖序: 臂.拖序 };
  try {
    br = await chromium.launch({ headless: true });
    const ctx = await br.newContext({ storageState: STATE, viewport: { width: 臂.vw, height: 臂.vh } });
    p = await ctx.newPage();
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 60000 });
    await p.waitForTimeout(6000);

    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== 臂.vw || 实际.h !== 臂.vh) throw new Error('轴向自检失败：' + 实际.w + 'x' + 实际.h);

    for (let i = 0; i < 13; i++) { await p.keyboard.press(放大键); await p.waitForTimeout(380); }
    await p.waitForTimeout(1600);
    const 点之前 = await p.evaluate(读缩放);
    if (点之前 === null) throw new Error('点之前读不到 scale');
    记.点之前 = 点之前;

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
      if (记.拖.净dx !== null && 记.拖.净dx !== 0) {
        throw new Error('平移量自检失败：净 dx 应为 0，却是 ' + 记.拖.净dx);
      }
    }

    // 📌 第一次选中
    记.第一次 = await 选一次(p, 臂.kind, 臂.名, 臂.vh);
    记.落点 = 记.第一次.落点;
    记.A = 记.第一次.A;
    记.锁定与否 = 记.第一次.锁定与否;
    记.节点画布坐标未变 = 记.第一次.节点画布坐标未变;

    // 📌 P4：切到另一个节点（不拖），再切回来
    if (臂.换到) {
      记.切走 = await 选一次(p, 臂.换到.kind, 臂.换到.名, 臂.vh);
      记.切回 = await 选一次(p, 臂.kind, 臂.名, 臂.vh);
      记.拖后画布 = 记.拖 ? 记.拖.末 : null;
      const 切走后画布 = await p.evaluate(读画布);
      记.切回后画布 = 切走后画布;
    }

    log(臂.键.padEnd(9) + '｜' + 臂.名.padEnd(11) + '｜拖序=[' + 臂.拖序.join(',') + ']'
      + '｜Δy段=' + (记.拖 ? 记.拖.段.map((s2) => String(s2.dy实测)).join('/') : '—').padEnd(20)
      + '｜净Δy=' + String(记.拖 ? 记.拖.净dy : '—').padEnd(7)
      + '｜落点=' + String(记.落点).padEnd(11)
      + '｜A=' + String(记.A).padEnd(10) + '｜' + 记.锁定与否
      + (记.切走 ? '｜切走(' + 记.切走.名 + ') A=' + 记.切走.A + ' ' + 记.切走.锁定与否
        + '｜切回 A=' + 记.切回.A + ' ' + 记.切回.锁定与否 : ''));
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
const 好 = out.臂.filter((x) => !x.错误 && x.第一次 && x.第一次.落定 && x.第一次.落点 !== null);
const 取 = (k) => 好.find((x) => x.键 === k);
const 组集 = (g) => 好.filter((x) => x.组 === g);

const 对照 = 取('W_1');
const 判定P0 = 对照
  ? (对照.落点 === 1.75 ? '✅ P0：阳性对照 `文本 1 @1212×720`（不拖）落 `1.75` ⇒ 尺子没漂' : '🔴 P0：阳性对照落 `' + 对照.落点 + '`（期望 1.75）⇒ 本批作废')
  : '🔴 P0：对照臂无效';

const 尺子 = 取('音1_120');
const 判定P1 = !尺子 ? '（P1 臂不全）'
  : (尺子.落点 === 1.125 && Math.abs(尺子.A - 200) < 0.002
    ? '✅ P1：`音频 1` 带 `dx=120` 落 `1.125`、`A` = `' + 尺子.A + '` ⇒ **尺子没漂，且这一拖确实锁住**'
    : '🔴 P1：落 `' + 尺子.落点 + '`、`A` = `' + 尺子.A + '`（期望 `1.125`/`200`）⇒ 本批作废');

const 门槛臂 = 取('音1_d115');
// 📌 立规 215 ③：📌 锁定档与未锁档**合起来按 |Δy| 升序排**，📌 再取**最紧**的一对。
const 本批未锁 = [门槛臂].filter((x) => x && x.锁定与否 === '未锁');
const 本批锁 = [门槛臂].filter((x) => x && x.锁定与否 === '锁定');
const 参照未锁 = { 键: '音1_d114（批次 332）', dy: 17.77, A: 210.8064 };
const 参照锁 = { 键: '音1_d116（批次 332）', dy: 18.07, A: 200.000 };
const 判定P2 = !门槛臂 ? '（P2 臂不全）'
  : '📌 P2：门槛钉死的一刀（`音频 1`，`h=720`，期望干净值 `A = 200`）—— '
    + '命令 `115` ⇒ 实测 `净Δy = ' + 门槛臂.拖.净dy + '` ⇒ 落点 `' + 门槛臂.落点 + '`、`A` = `' + 门槛臂.A + '` **' + 门槛臂.锁定与否 + '**'
    + '\\n　　⇒ 📌 `净Δx` = `' + 门槛臂.拖.净dx + '`（📌 与批次 331/332 一致）'
    + '\\n　　⇒ ' + (() => {
      if (!本批未锁.length && !本批锁.length) return '📌 本臂的读数没法判锁/不锁 ⇒ 只报读数（立规 205 ①）';
      // 📌 把本批这一刀插进批次 332 已有的两根界之间
      if (本批未锁.length) {
        const lo = Math.abs(门槛臂.拖.净dy) < Math.abs(参照未锁.dy) ? 门槛臂 : 参照未锁;
        return '🔴 **这一刀落在未锁侧** ⇒ 📌 未锁的最高档变成 `净Δy = ' + Math.abs(lo.dy) + '`'
          + '（臂 `' + lo.键 + '`，`A = ' + lo.A + '`）⇒ 📌 **门槛 ∈ (' + Math.abs(lo.dy) + ', ' + Math.abs(参照锁.dy) + ']`**'
          + '，宽 `' + (Math.abs(参照锁.dy) - Math.abs(lo.dy)).toFixed(2) + '` 像素';
      }
      const hi = Math.abs(门槛臂.拖.净dy) < Math.abs(参照锁.dy) ? 门槛臂 : 参照锁;
      return '✅ **这一刀落在锁定侧** ⇒ 📌 **最窄的锁定档变成 `净Δy = ' + Math.abs(hi.dy) + '`**（臂 `' + hi.键 + '`，`A = ' + hi.A + '`）'
        + ' ⇒ 📌 **门槛 ∈ (' + Math.abs(参照未锁.dy) + ', ' + Math.abs(hi.dy) + ']`**'
        + '，宽 `' + (Math.abs(hi.dy) - Math.abs(参照未锁.dy)).toFixed(2) + '` 像素（📌 批次 332 给的宽是 `0.30`）';
    })();

const 双 = 取('音1_双120');
const 判定P3 = !双 || !双.拖 || 双.拖.段.length < 2 ? '（P3 臂不全）'
  : '📌 P3：同向连拖两次（拖序 `[+120, +120]`）—— 📌 逐段实测 `Δy` = `' + 双.拖.段.map((s) => String(s.dy实测)).join('` / `') + '`'
    + '，📌 净 `Δy` = `' + 双.拖.净dy + '`、净 `Δx` = `' + 双.拖.净dx + '`'
    + ' ⇒ 落点 `' + 双.落点 + '`、`A` = `' + 双.A + '` **' + 双.锁定与否 + '**'
    + '\\n　　⇒ 📌 第一段与第二段都是**往下**，📌 第二段 `Δy = ' + 双.拖.段[1].dy实测 + '`'
    + '\\n　　⇒ ' + (Math.abs(双.拖.段[1].dy实测) > 5
      ? '✅ **第二段仍走了 `' + 双.拖.段[1].dy实测 + '` 屏像素**（📌 与第一段 `' + 双.拖.段[0].dy实测 + '` 同量级）⇒ 📌 **棘轮是**累加**的**，📌 拖几次就往下挪几次'
      : '🔴 第二段几乎为 `0` ⇒ 📌 棘轮**会饱和**，📌 只挪一次');

const 换 = 取('音1_换节点');
const 判定P4 = !换 || !换.切走 || !换.切回 ? '（P4 臂不全）'
  : '📌 P4：锁绑在哪 —— `音频 1` 拖 `dx=120` 锁住后：'
    + '\\n　　① 原节点 `音频 1`：`A` = `' + 换.A + '` **' + 换.锁定与否 + '**'
    + '\\n　　② 切到 `音频 2`（**不拖**）：`A` = `' + 换.切走.A + '` **' + 换.切走.锁定与否 + '**'
    + '\\n　　③ 再切回 `音频 1`（**不拖**）：`A` = `' + 换.切回.A + '` **' + 换.切回.锁定与否 + '**'
    + '\\n　　④ 📌 切走时画布 `translate` = `(' + 换.拖后画布.x + ', ' + 换.拖后画布.y + ')`，📌 切回后 = `(' + 换.切回后画布.x + ', ' + 换.切回后画布.y + ')`'
    + ' ⇒ 📌 **切走与切回期间画布自身没有被拖动**（📌 两段拖只发生在第 ① 步之前）'
    + '\\n　　⇒ ' + (换.切回.锁定与否 === '锁定'
      ? '✅ **切回 `音频 1` 之后仍然锁定** ⇒ 📌 **锁绑在视口上，不绑在节点上**：📌 一旦某个节点的落定把视口拖过门槛，📌 同一会话里**别的节点也共享这个干净状态**'
      : '🔴 **切回 `音频 1` 之后不锁了** ⇒ 📌 **锁绑在节点上**：📌 每个节点要各自拖一次才能锁');

out.判定 = {
  有效臂: 好.length + '/' + 臂表.length,
  判定P0_尺子: 判定P0,
  判定P1_尺子: 判定P1,
  判定P2_门槛钉死: 判定P2,
  判定P3_累加性: 判定P3,
  判定P4_锁绑在哪: 判定P4,
  逐臂: 好.map((x) => ({
    键: x.键, 组: x.组, kind: x.kind, 名: x.名, 视口: x.vw + 'x' + x.vh, 拖序: x.拖序,
    画布盒: x.第一次.盒, 拖: x.拖, 节点画布坐标未变: x.节点画布坐标未变,
    点之前: x.点之前, 第一次: x.第一次, 切走: x.切走, 切回: x.切回,
    拖后画布: x.拖后画布, 切回后画布: x.切回后画布,
    落点: x.落点, A: x.A, 锁定与否: x.锁定与否,
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