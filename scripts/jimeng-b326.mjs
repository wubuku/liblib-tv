/**
 * 批次 326 · `A ≡ 200` 是**画布级**的，还是与节点、与视口宽有关？
 *
 * ✅ 接批次 325（`12/12` 臂，`P0` 逐字过）：
 *    带 `+120` 那一拖（实测净平移 `(0, +18.7)`）做 `h` 扫 `640/680/720/760/800`
 *    ⇒ 落点逐字 `0.875000 / 1.000000 / 1.125000 / 1.250000 / 1.375000`，`A` **五档逐字 `200.000`、极差 `0`**
 *    ⇒ 📌 **闭式 `落点 = (safeH − 200)/320` 逐字成立**，📌 几何自洽 `320 × 落点 + 200 = safeH`
 *    ⇒ 📌 **而 `320` 是 `音频 1` 的画布盒高** ⇒ 🔴 **这个 `200` 到底是画布级的常数，还是「对 `320` 那个盒子的比例」？**
 *
 * 📌 **本批全部在锁定态下测**（📌 每臂都带 `+120` 那一拖，并**逐臂现量实测平移**）：
 *   **P0** 阳性对照 `文本 @1212×720`（**不锁定**）必须逐字落 `1.75`。
 *   **P1** `音频 1`（锁定）必须逐字落 `1.125`（= `(560 − 200)/320`）⇒ **本批的尺子没漂**。
 *   **P2** 节点维度：`音频 2`、`音频 68` 锁定后 `A` 必须**逐字 `200.000`** ⇒ 排掉「随节点变」。
 *   **P3** 🔴 **盒高度维度**：`视频 1` 的画布盒是 `320×569` ⇒ 📌 **若 `200` 是画布级常数，落点应是 `(560 − 200)/569 = 0.632688`**
 *        ⇒ 逐字命中 ⇒ ✅ **`200` 与节点盒高无关**；🔴 若给别的数 ⇒ `200` 与盒高有关（比例或 `320` 的函数）。
 *   **P4** `文本 1` **锁定**后：📌 若仍逐字落 `1.75` ⇒ 📌 **锁定不改变文本那条路径**（文本本来就不预留）；
 *        🔴 若变了 ⇒ 📌 锁定对文本也有影响。
 *   **P5** 视口宽维度：`音频 1` 在 `w = 1216 / 1250` 锁定后 `A` 必须逐字 `200.000` ⇒ 排掉「随 `safeW` 变」。
 *
 * 📌 **盒高逐臂现量**：📌 `H₀` 一律取该臂节点自己的 `offsetHeight`（📌 不写死 `320`/`569`），
 *    📌 `A = safeH − H₀ · 落点`，📌 闭式预测 `= (safeH − 200) / H₀`。
 *
 * ⛔ 本批不做：不平移任何节点（📌 逐臂核对节点画布 `transform` 未变）、不删除、不新建、不触发生成。
 *
 * 前提检查：轴向自检 / 落定自检（三连读，📌 **点完先等 `3200ms`**，📌「点后首读」单存不参与判定）/
 *   点击生效自检 / `aria` 精确匹配现找现量 / 参数写死 / 每臂独立浏览器 / 盒尺寸逐臂现量 / 平移量逐臂现量。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b326.json';
const 放大键 = 'Meta+Equal';
const 闭式 = (w, h, W, H, z0) => Math.min((w - 532) / W, (h - 160) / H, z0);
const 预留 = 200;

const 臂表 = [
  { 键: '音1_720', 组: 'P1尺子', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 锁定: true },
  { 键: '音2_720', 组: 'P2节点', kind: '音频', 名: '音频 2', vw: 1212, vh: 720, 锁定: true },
  { 键: '音68_720', 组: 'P2节点', kind: '音频', 名: '音频 68', vw: 1212, vh: 720, 锁定: true },
  { 键: '视1_720', 组: 'P3盒高', kind: '视频', 名: '视频 1', vw: 1212, vh: 720, 锁定: true },
  { 键: '文1_锁', 组: 'P4文本', kind: '文本', 名: '文本 1', vw: 1212, vh: 720, 锁定: true },
  { 键: '时1_锁', 组: 'P4文本', kind: '时间线', 名: '时间线 1', vw: 1212, vh: 720, 锁定: true },
  { 键: '音1_1216', 组: 'P5视口宽', kind: '音频', 名: '音频 1', vw: 1216, vh: 720, 锁定: true },
  { 键: '音1_1250', 组: 'P5视口宽', kind: '音频', 名: '音频 1', vw: 1250, vh: 720, 锁定: true },
  { 键: 'W_1', 组: 'P0对照', kind: '文本', 名: '文本 1', vw: 1212, vh: 720, 锁定: false },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b326',
  问: 'A ≡ 200 是画布级的常数，还是与节点盒高、与视口宽有关？',
  接325: '带 +120 那一拖做 h 扫，落点逐字 0.875/1.000/1.125/1.250/1.375，A 五档逐字 200.000、极差 0',
  但: '🔴 那个 320 是 音频 1 的画布盒高 ⇒ 200 到底是画布级常数，还是对 320 的比例？',
  判据: {
    P0: '阳性对照 文本 @1212×720（不锁定）必须逐字落 1.75',
    P1: '音频 1（锁定）必须逐字落 1.125（= (560−200)/320）⇒ 本批尺子没漂',
    P2: '音频 2 / 音频 68 锁定后 A 必须逐字 200.000 ⇒ 排掉「随节点变」',
    P3: '视频 1 盒高 569：若 200 是画布级常数，落点应是 (560−200)/569 = 0.632688；给别的数则 200 与盒高有关',
    P4: '文本 1 / 时间线 1 锁定后：仍落 1.75 则锁定不改变文本那条路径',
    P5: '音频 1 在 w=1216/1250 锁定后 A 必须逐字 200.000 ⇒ 排掉「随 safeW 变」',
  },
  预留常数: 预留,
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

const 拖一次 = async (p, dx, vh) => {
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

    for (let i = 0; i < 13; i++) { await p.keyboard.press(放大键); await p.waitForTimeout(380); }
    await p.waitForTimeout(1600);
    const 读缩放 = () => p.evaluate(() => {
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      return m ? Number(m[1]) : null;
    });
    const 读节点 = () => p.evaluate((id) => {
      const e = document.querySelector('.react-flow__node[data-id="' + id + '"]');
      if (!e) return null;
      const b = e.getBoundingClientRect();
      return { top: Math.round(b.top * 10) / 10, tf: e.style.transform || '' };
    }, nid);
    记.点之前 = await 读缩放();
    if (记.点之前 === null) throw new Error('点之前读不到 scale');
    记.拖前画布 = await p.evaluate(读画布);

    记.拖 = null;
    if (臂.锁定) {
      const 前 = await p.evaluate(读画布);
      const r = await 拖一次(p, 120, 臂.vh);
      const 后 = await p.evaluate(读画布);
      记.拖 = { 命令: 120, 错: r.错 || null, dx实测: (前.x !== null && 后.x !== null) ? +(后.x - 前.x).toFixed(1) : null, dy实测: (前.y !== null && 后.y !== null) ? +(后.y - 前.y).toFixed(1) : null };
    }
    const 后节点 = await 读节点();
    记.节点画布坐标未变 = 后节点 ? (后节点.tf === 找.tf) : null;

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

    记.闭式预测 = +闭式(臂.vw, 臂.vh, 找.W, H0, 记.点之前).toFixed(6);
    记.命中闭式 = Math.abs(记.终点 - 记.闭式预测) < 5e-5;
    记.safeH = 臂.vh - 160;
    记.A = +(记.safeH - H0 * 记.终点).toFixed(3);
    记.预留式预测 = +((记.safeH - 预留) / H0).toFixed(6);
    记.命中预留式 = Math.abs(记.终点 - 记.预留式预测) < 5e-6;
    const 后2 = await 读节点();
    记.落定后节点顶 = 后2 ? 后2.top : null;
    记.工具条屏高 = await p.evaluate(() => {
      const es = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'))
        .map((x) => x.getBoundingClientRect()).filter((r) => r.width > 0 && r.height > 0);
      if (!es.length) return null;
      const b = es.reduce((q, r) => (r.width * r.height > q.width * q.height ? r : q));
      return Math.round(b.height * 100) / 100;
    });

    log(臂.键.padEnd(9) + '｜' + 臂.名.padEnd(7) + '｜' + String(记.vw + 'x' + 记.vh).padEnd(10)
      + '｜盒高=' + String(H0).padEnd(5)
      + '｜拖dy=' + String(记.拖 ? 记.拖.dy实测 : '未锁').padEnd(7)
      + '｜落点=' + String(记.终点).padEnd(11)
      + '｜预留式预测=' + String(记.预留式预测).padEnd(11)
      + '｜A=' + String(记.A).padEnd(10)
      + (记.命中预留式 ? '｜✅命中预留式' : '｜🔴不中'));
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
const 好 = out.臂.filter((x) => !x.错误 && x.点击生效 && x.落定 && x.终点 !== undefined);
const 取 = (k) => 好.find((x) => x.键 === k);
const 组集 = (g) => 好.filter((x) => x.组 === g);
const 拼 = (g) => 组集(g).map((x) => '`' + x.键 + '` 落点 `' + x.终点 + '`、`A` = `' + x.A + '`').join('；');

const 对照 = 取('W_1');
const 判定P0 = 对照 && 对照.命中闭式
  ? '✅ P0：阳性对照 `文本 @1212×720`（不锁定）落 `' + 对照.终点 + '` 逐字等于闭式 ⇒ 尺子没漂'
  : '🔴 P0：阳性对照=' + (对照 ? 对照.终点 : '—') + '（期望 1.75）⇒ 本批作废';

const 尺子 = 取('音1_720');
const 判定P1 = !尺子 ? '（P1 臂不全）'
  : (尺子.A === 200 && 尺子.命中预留式
    ? '✅ P1：`音频 1`（锁定）落 `' + 尺子.终点 + '` 逐字等于 `(560 − 200)/320 = 1.125` ⇒ 本批尺子没漂'
    : '🔴 P1：`音频 1`（锁定）落 `' + 尺子.终点 + '`、`A` = `' + 尺子.A + '`（期望 `1.125` / `200.000`）⇒ 本批作废');

const 节点组 = 组集('P2节点');
const 判定P2 = !节点组.length ? '（P2 臂不全）'
  : ('📌 P2：节点维度（锁定）—— ' + 拼('P2节点')
    + ' ⇒ ' + (节点组.every((x) => x.A === 200) ? '✅ **三个音频节点上 `A` 逐字 `200.000`** ⇒ 排掉「随节点变」' : '🔴 有节点不逐字 200'));

const 视 = 取('视1_720');
const 判定P3 = !视 ? '（P3 臂不全）'
  : ('📌 P3：盒高维度（锁定）—— `视频 1` 的画布盒是 `320×' + (视.画布盒 ? 视.画布盒.H : '?') + '`'
    + ' ⇒ 落点 `' + 视.终点 + '`，预留式预测 `(560 − 200)/' + (视.画布盒 ? 视.画布盒.H : '?') + '` = `' + 视.预留式预测 + '`，`A` = `' + 视.A + '`'
    + ' ⇒ ' + (视.命中预留式 && 视.A === 200
      ? '✅ **逐字命中** ⇒ **`200` 与节点盒高无关**（`320` 与 `569` 两种盒高都预留 `200`）⇒ 📌 **`200` 是画布级常数**'
      : '🔴 **不命中** ⇒ `200` 与盒高有关（可能是对 `320` 的比例，或是别的函数）'));

const 文本组 = 组集('P4文本');
const 判定P4 = !文本组.length ? '（P4 臂不全）'
  : ('📌 P4：锁定对文本那条路径的影响 —— ' + 拼('P4文本')
    + ' ⇒ ' + (文本组.every((x) => x.命中闭式)
      ? '✅ **锁定后文本仍逐字命中闭式** ⇒ 📌 **锁定不改变文本那条路径**（文本本来就不预留）'
      : '🔴 锁定改变了文本的落点 ⇒ 与「文本 `A` 恒为 0」的说法冲突，需要重查'));

const 宽组 = 组集('P5视口宽');
const 判定P5 = !宽组.length ? '（P5 臂不全）'
  : ('📌 P5：视口宽维度（锁定）—— ' + 拼('P5视口宽')
    + ' ⇒ ' + (宽组.every((x) => x.A === 200) ? '✅ **不同 `safeW` 上 `A` 逐字 `200.000`** ⇒ 排掉「随 `safeW` 变」' : '🔴 有宽度档不逐字 200'));

out.判定 = {
  有效臂: 好.length + '/' + 臂表.length,
  判定P0_尺子: 判定P0,
  判定P1_锁定有没有生效: 判定P1,
  判定P2_节点维度: 判定P2,
  判定P3_盒高维度: 判定P3,
  判定P4_文本路径: 判定P4,
  判定P5_视口宽维度: 判定P5,
  逐臂: 好.map((x) => ({
    键: x.键, 组: x.组, 名: x.名, 视口: x.vw + 'x' + x.vh, 锁定: x.锁定, 画布盒: x.画布盒,
    拖: x.拖, 节点画布坐标未变: x.节点画布坐标未变,
    z0: x.点之前, 点后首读: x.点后首读, 读1: x.读1, 读2: x.读2, 读3: x.读3, 落点: x.终点,
    闭式预测: x.闭式预测, 命中闭式: x.命中闭式, safeH: x.safeH, A: x.A,
    预留式预测: x.预留式预测, 命中预留式: x.命中预留式,
    落定后节点顶: x.落定后节点顶, 工具条屏高: x.工具条屏高,
  })),
  失效臂: out.臂.filter((x) => x.错误).map((x) => ({ 键: x.键, 错: x.错误 })),
};
log('\n════ 判定 ════\n' + JSON.stringify({
  有效臂: out.判定.有效臂, P0: 判定P0, P1: 判定P1, P2: 判定P2, P3: 判定P3, P4: 判定P4, P5: 判定P5,
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
