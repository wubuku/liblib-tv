/**
 * 批次 331 · 两件事：📌 溯源 `568.889` 到底是**谁**算出来的；📌 把锁定门槛**二分**出来。
 *
 * ✅ 接批次 330（`13/13` 臂）：
 *    📌 同一个尺寸在 DOM 里有**三份**：内联 `style` 声明 **`568.889px`** ｜ `getComputedStyle`
 *       布局值 **`568.875px`** ｜ `offsetX` **`569`**；📌 图片宽度项用 `568.889`、视频高度项用 `569`
 *
 * 📌 **本批起意之前先算了一遍**（📌 立规 212 ④：候选值要先算出来再验证）：
 *    `320 × 16/9 = 568.888888…` ⇒ 📌 **这就是一个 9:16 的宽高比**
 *    声明值   `568.889`  =  `320 × 16/9` **四舍五入到三位小数**
 *    布局值   `568.875`  =  `⌊568.888889 × 8⌋ / 8` = `⌊4551.111⌋ / 8` = **`4551 / 8`** ⇒ 📌 **向下取到 1/8 像素栅格**
 *    `offsetX` `569`     =  `round(568.888889)`
 *    ⇒ 📌 **三份是同一个值的三级取整**，📌 原始值是 `320 × 16/9`
 *
 * 📌 **本批两问**：
 *   **P2/P3 溯源**：📌 把节点**自身、祖先链、直接子元素**的 `aspect-ratio` / `width` / `height` /
 *        `max-*` / `padding-*` / `box-sizing` / `zoom` 全查一遍，📌 外加节点上**所有** `--octo-*`
 *        与名字里带 `aspect`/`ratio`/`height`/`width` 的自定义属性
 *        ⇒ 📌 找得到 `aspect-ratio: 16 / 9` 之类 ⇒ ✅ **有直接 DOM 证据**；🔴 找不到 ⇒ 📌 **只敢说
 *        「三个数是同一个值的三级取整」，不能说「是谁算的」**（立规 212 ②）
 *   **P4 门槛二分**：📌 批次 325 只知道门槛落在实测纵向平移 `10.3` 与 `18.7` 之间；📌 平移约为命令的
 *        `15.6%`–`17.2%` ⇒ 📌 命令 `70/80/90/100/110` 应当把 `Δy` 铺进那个区间 ⇒ 📌 二分出确切门槛
 *
 * ⛔ 本批不做：不平移任何节点（📌 逐臂核对节点画布 `transform` 未变）、不删除、不新建、不触发生成。
 *
 * 前提检查：**启动前自检** / 轴向自检 / 落定自检（三连读，📌 **点完先等 `3200ms`**）/ 点击生效自检 /
 *   `aria` 精确匹配现找现量 / 参数写死 / 每臂独立浏览器 / 盒尺寸逐臂现量 / **平移量逐臂现量**。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b331.json';
const 放大键 = 'Meta+Equal';
const 节 = (x) => (x === undefined || x === null ? null : Math.round(x * 1000000) / 1000000);
const round6 = (x) => (x === null || x === undefined ? null : +Number(x).toFixed(6));

// 📌 面板预留 `R` 写死在这一批要用的两类节点上（📌 批次 329 逐字复现过：`204` 与 `208`）
const R表 = { 音频: 204, 视频: 208 };

const 臂表 = [
  { 键: 'W_1', 组: 'P0对照', kind: '文本', 名: '文本 1', vw: 1212, vh: 720, 锁定: false, dx: 0 },
  { 键: '音1_120', 组: 'P1尺子', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 锁定: true, dx: 120 },
  { 键: '视1_720', 组: 'P2溯源', kind: '视频', 名: '视频 1', vw: 1212, vh: 720, 锁定: true, dx: 120 },
  { 键: '图_720', 组: 'P2溯源', kind: '图片', 名: 'b22-upload', vw: 1212, vh: 720, 锁定: true, dx: 120 },
  { 键: '音1_d70', 组: 'P4门槛', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 锁定: true, dx: 70 },
  { 键: '音1_d80', 组: 'P4门槛', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 锁定: true, dx: 80 },
  { 键: '音1_d90', 组: 'P4门槛', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 锁定: true, dx: 90 },
  { 键: '音1_d100', 组: 'P4门槛', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 锁定: true, dx: 100 },
  { 键: '音1_d110', 组: 'P4门槛', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 锁定: true, dx: 110 },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b331',
  问: '568.889 是谁算出来的；锁定门槛落在 10.3 与 18.7 之间的哪一点',
  接330: '同一个尺寸三份：内联 568.889px / getComputedStyle 568.875px / offsetX 569',
  起意前先算: '320 × 16/9 = 568.888889；声明=四舍五入三位；布局=⌊568.888889×8⌋/8=4551/8=568.875；offsetX=round=569',
  判据: {
    P0: '阳性对照 文本 @1212×720（不锁定）必须逐字落 1.75',
    P1: '音频 1 带 dx=120（锁定）必须逐字落 1.125、A=200 ⇒ 尺子没漂、也确认这一拖确实锁住',
    P2: '视频 1 / 图片 b22-upload 的溯源：查 aspect-ratio / 宽高 / max-* / padding / box-sizing / zoom + 祖先链 + 全部 --octo-* 自定义属性',
    P4: '门槛二分：dx = 70/80/90/100/110 逐臂现量实测 Δy 与 A，找锁/不锁的分界',
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
    if (臂.dx > 0) {
      const 前 = await p.evaluate(读画布);
      const r = await 拖一次(p, 臂.dx);
      const 后 = await p.evaluate(读画布);
      记.拖 = {
        命令: 臂.dx, 错: r.错 || null,
        dx实测: (前.x !== null && 后.x !== null) ? +(后.x - 前.x).toFixed(2) : null,
        dy实测: (前.y !== null && 后.y !== null) ? +(后.y - 前.y).toFixed(2) : null,
      };
      if (记.拖.dx实测 !== null && 记.拖.dx实测 !== 0) {
        throw new Error('平移量自检失败：横向命令拖的 dx 实测应为 0，却是 ' + 记.拖.dx实测);
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

    log(臂.键.padEnd(9) + '｜' + 臂.名.padEnd(11) + '｜dx=' + String(臂.dx).padEnd(4)
      + '｜拖=' + (记.拖 ? ('Δx=' + String(记.拖.dx实测).padEnd(5) + ' Δy=' + String(记.拖.dy实测).padEnd(7)) : '未拖 '.padEnd(18))
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
  ? (对照.终点 === 1.75 ? '✅ P0：阳性对照 `文本 1 @1212×720`（不锁定）落 `1.75` ⇒ 尺子没漂' : '🔴 P0：阳性对照落 `' + 对照.终点 + '`（期望 1.75）⇒ 本批作废')
  : '🔴 P0：对照臂无效';

const 尺子 = 取('音1_120');
const 判定P1 = !尺子 ? '（P1 臂不全）'
  : (尺子.终点 === 1.125 && Math.abs(尺子.A - 200) < 0.002
    ? '✅ P1：`音频 1` 带 `dx=120` 落 `1.125`、`A` = `' + 尺子.A + '` ⇒ **尺子没漂，且这一拖确实锁住**'
    : '🔴 P1：落 `' + 尺子.终点 + '`、`A` = `' + 尺子.A + '`（期望 `1.125`/`200`）⇒ 本批作废');

// 📌 P2：📌 逐臂把祖先链里**每一层**的尺寸属性与自定义属性列出来，📌 找有没有 `aspect-ratio`。
const 溯源组 = 组集('P2溯源');
const 判定P2 = !溯源组.length ? '（P2 臂不全）'
  : 溯源组.map((x) => {
    const 行 = (x.溯源 && x.溯源.链 ? x.溯源.链 : []).map((n, i) => {
      if (!n) return '　　第' + i + '层：（空）';
      const a = n.属;
      const 自定义键 = Object.keys(n.自定义 || {});
      const 命中 = 自定义键.filter((k) => /aspect|ratio/i.test(k));
      return '　　第' + i + '层 `<' + n.tag + (n.testid ? ' data-testid=' + n.testid : '') + '>`'
        + '｜`aspect-ratio`=`' + a['aspect-ratio'] + '`'
        + '｜`width`=`' + a.width + '` `height`=`' + a.height + '`'
        + '｜`max-*`=`' + a['max-width'] + ' / ' + a['max-height'] + '`'
        + '｜`padding-top`=`' + a['padding-top'] + '` `padding-bottom`=`' + a['padding-bottom'] + '`'
        + '｜`box-sizing`=`' + a['box-sizing'] + '` `zoom`=`' + a.zoom + '` `contain`=`' + a.contain + '`'
        + (自定义键.length ? '｜自定义 `' + 自定义键.length + '` 条' + (命中.length ? '（含 aspect/ratio：`' + 命中.join('`、`') + '`）' : '（**无** aspect/ratio 相关）') : '')
        + '\n　　　内联 `style` = `' + n.style + '`';
    }).join('\n');
    const 子行 = (x.溯源 && x.溯源.子 ? x.溯源.子 : []).map((n) => n
      ? '　　子 `<' + n.tag + (n.testid ? ' data-testid=' + n.testid : '') + '>`｜`aspect-ratio`=`' + n.属['aspect-ratio']
        + '`｜`width`=`' + n.属.width + '` `height`=`' + n.属.height + '`｜内联 `' + n.style + '`'
      : null).filter(Boolean).join('\n');
    return '📌 `' + x.键 + '`（`' + x.kind + ' ' + x.名 + '`，offset `' + x.画布盒offset.W + '×' + x.画布盒offset.H + '`）\n' + 行 + '\n' + 子行;
  }).join('\n\n');

const 门槛组 = 组集('P4门槛').filter((x) => x.拖 && x.拖.dy实测 !== null);
const 判定P4 = !门槛组.length ? '（P4 臂不全）'
  : '📌 P4：锁定门槛二分（`音频 1`，`h=720`，期望干净值 `A = 200`）—— '
    + 门槛组.slice().sort((a, b) => a.拖.dy实测 - b.拖.dy实测)
      .map((x) => '命令 `' + x.dx + '` ⇒ 实测 `Δx=' + x.拖.dx实测 + '`、`Δy=' + x.拖.dy实测 + '` ⇒ `A` = `' + x.A + '` **' + x.锁定与否 + '**').join('；')
    + '\n　　⇒ 📌 `Δx` **逐臂实测都是 `0`**（📌 与批次 325 结果四一致）'
    + '\n　　⇒ ' + (() => {
      const xs = 门槛组.slice().sort((a, b) => a.拖.dy实测 - b.拖.dy实测);
      let 分界 = null;
      for (let i = 0; i + 1 < xs.length; i++) {
        if (xs[i].锁定与否 === '未锁' && xs[i + 1].锁定与否 === '锁定') { 分界 = [xs[i], xs[i + 1]]; break; }
      }
      if (!分界) return '🔴 **本批这几档没有出现「未锁 → 锁定」的分界** ⇒ 📌 报告每一档的读数，不下结论（立规 205 ①）';
      const lo = 分界[0]; const hi = 分界[1];
      return '✅ **分界落在这两档之间：实测 `Δy=' + lo.拖.dy实测 + '`（`A=' + lo.A + '`，未锁）与 `Δy=' + hi.拖.dy实测 + '`（`A=' + hi.A + '`，锁定）**'
        + '\n　　⇒ 📌 **门槛 ∈ (' + lo.拖.dy实测 + ', ' + hi.拖.dy实测 + '] 屏像素**，📌 比批次 325 的「`10.3` 与 `18.7` 之间」**收窄到约 `' + (hi.拖.dy实测 - lo.拖.dy实测) + '` 像素宽**';
    })();

out.判定 = {
  有效臂: 好.length + '/' + 臂表.length,
  判定P0_尺子: 判定P0,
  判定P1_尺子: 判定P1,
  判定P2_溯源: 判定P2,
  判定P4_门槛二分: 判定P4,
  逐臂: 好.map((x) => ({
    键: x.键, 组: x.组, kind: x.kind, 名: x.名, 视口: x.vw + 'x' + x.vh, 锁定: x.锁定, dx: x.dx,
    画布盒offset: x.画布盒offset, 拖: x.拖, 节点画布坐标未变: x.节点画布坐标未变,
    z0: x.点之前, 读1: x.读1, 读2: x.读2, 读3: x.读3, 落定: x.落定, 落点: x.终点,
    A: x.A, 锁定与否: x.锁定与否, 溯源: x.溯源,
  })),
  失效臂: out.臂.filter((x) => x.错误).map((x) => ({ 键: x.键, 错: x.错误 })),
};
log('\n════ 判定 ════\n' + JSON.stringify({
  有效臂: out.判定.有效臂, P0: 判定P0, P1: 判定P1, P2: 判定P2, P4: 判定P4,
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