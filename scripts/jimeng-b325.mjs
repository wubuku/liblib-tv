/**
 * 批次 325 · 那个锁到底是**状态**还是**位置**；🔴 而锁住的 `A ≡ 200.000` 随 `safeH` 变不变。
 *
 * ✅ 接批次 324b（`9/9` 臂，`P0` 逐字过）：
 *    命令 `dx` = `0` / `60` / `120` / `240` ⇒ 实测 `.react-flow__viewport` 的 `translate` 变化
 *    = `(0, 0)` / `(0, +10.3)` / `(0, +18.7)` 与 `(0, +19.0)` / `(0, +38.4)` 与 `(0, +37.8)`
 *    ⇒ `A` = `204.838`/`201.846` ｜ `208.400`/`214.771` ｜ 🔴 **`200.000`/`200.000`** ｜ 🔴 **`200.000`/`200.000`**
 *    ⇒ ✅ **实测纵向平移 `≥ 18.7` ⇒ `A` 逐字锁成 `200.000`**（`4/4`）；📌 门槛落在实测 `dy` 的 `10.3` 与 `18.7` 之间。
 *    📌 顺带：**拖动前画布 `translate` 逐字相同**（`9/9` 臂都是 `(−5190.27, −3809.18)`）⇒ 📌 **「画布在哪」已被排除**。
 *    📌 顺带：**横向命令拖出来的却是纵向平移，且只有命令的 `15.6%`–`17.2%`** ⇒ 📌 画布把平移吃掉了一大半。
 *
 * 📌 **本批三问，判据全部测量前写死**：
 *   **P0** 阳性对照 `文本 @1212×720` 必须逐字落 `1.75`；🔴 不中 ⇒ 本批作废。
 *   **P1（状态 vs 位置）**
 *        **甲组「拖回原处」**：先 `+120` 再 `−120`，📌 **逐臂记净 `translate`**。
 *             净位移回到 `0` 附近而 `A` **又散开** ⇒ 📌 **是位置**（阈值型）；
 *             净位移回到 `0` 附近而 `A` **仍是 `200.000`** ⇒ 📌 **是状态**（一次性标志）。
 *        **乙组「反方向拖」**：改成**纵向**命令拖（`dy = +120`），📌 记实测 `translate`。
 *             仍然锁 ⇒ 📌 **方向无关** ⇒ 更加支持「状态」；🔴 不锁 ⇒ 📌 **与方向有关**。
 *   **P2（`200` 随 `safeH` 变吗）** 带上 `+120` 那一拖，把 `h` 扫成 `640 / 680 / 720 / 760 / 800`：
 *        **`A` 极差 `≤ 1.0` ⇒ 画布空间的常数**（预留的是**画布像素**）；
 *        **否则 ⇒ 按 `h=720` 的 `A` 定出斜率，再看逐档偏差 `≤ 5` 是否成立**
 *        ⇒ 成立则是**与 `safeH` 成正比**（固定内容高模型，解出 `T`）；不成立则**两个模型都被否**。
 *        ⚠️ **判据两个分支都要真的验**（立规 205①：`else` 分支不许只是换一种说法）。
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
const OUT = '/tmp/b325.json';
const 放大键 = 'Meta+Equal';
const 闭式 = (w, h, W, H, z0) => Math.min((w - 532) / W, (h - 160) / H, z0);
const VW = 1212;
const H0 = 320;
const h扫 = [640, 680, 720, 760, 800];

const 臂表 = [];
let 序号 = 0;
for (let k = 0; k < 3; k++) { 序号 += 1; 臂表.push({ 键: 'R' + 序号, 组: '甲拖回', kind: '音频', 名: '音频 1', vh: 720, 计划: '往返' }); }
for (let k = 0; k < 3; k++) { 序号 += 1; 臂表.push({ 键: 'V' + 序号, 组: '乙反向', kind: '音频', 名: '音频 1', vh: 720, 计划: '纵向' }); }
for (const h of h扫) { 序号 += 1; 臂表.push({ 键: 'H' + h, 组: '丙h扫', kind: '音频', 名: '音频 1', vh: h, 计划: '正向' }); }
臂表.push({ 键: 'W_1', 组: '对照', kind: '文本', 名: '文本 1', vh: 720, 计划: '无' });

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b325',
  问: '那个锁是状态还是位置？A≡200.000 随 safeH 变吗？',
  接324b: {
    命令dx: '0 / 60 / 120 / 240',
    实测translate变化: '(0,0) / (0,+10.3) / (0,+18.7 与 +19.0) / (0,+38.4 与 +37.8)',
    A: '204.838/201.846 ｜ 208.400/214.771 ｜ 200.000/200.000 ｜ 200.000/200.000',
    结论: '✅ 实测纵向平移 ≥ 18.7 ⇒ A 逐字锁成 200.000（4/4）；门槛落在实测 dy 的 10.3 与 18.7 之间',
    两条已排除: '拖动前 translate 9/9 臂逐字相同 ⇒ 「画布在哪」被排除；横向命令拖出纵向平移、只有命令的 15.6%–17.2%',
  },
  判据: {
    P0: '阳性对照 文本 @1212×720 必须逐字落 1.75，不中即本批作废',
    P1甲: '先 +120 再 −120：净位移回 0 附近而 A 又散开 ⇒ 是位置；净位移回 0 附近而 A 仍 200.000 ⇒ 是状态',
    P1乙: '改成纵向命令拖：仍锁 ⇒ 方向无关；不锁 ⇒ 与方向有关',
    P2: '带 +120 做 h 扫：A 极差 ≤ 1.0 ⇒ 画布空间常数；否则按 h=720 的 A 定斜率，逐档偏差 ≤ 5 才算正比（两个分支都真验）',
  },
  h扫, 臂表, 臂: [], 判定: {},
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

const 拖一次 = async (p, dx, dy, vh) => {
  const 起点 = await p.evaluate(找空白);
  if (!起点) return { 错: '找不到空白起点' };
  const 终x = Math.max(2, Math.min(起点.x + dx, VW - 2));
  const 终y = Math.max(2, Math.min(起点.y + dy, vh - 2));
  await p.mouse.move(起点.x, 起点.y);
  await p.mouse.down();
  await p.mouse.move(终x, 终y, { steps: Math.max(2, Math.round(Math.max(Math.abs(dx), Math.abs(dy)) / 2)) });
  await p.mouse.up();
  await p.waitForTimeout(1400);
  return { 起点, 终x, 终y };
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
  const 记 = { 键: 臂.键, 组: 臂.组, kind: 臂.kind, 名: 臂.名, vw: VW, vh: 臂.vh, 计划: 臂.计划 };
  try {
    br = await chromium.launch({ headless: true });
    const ctx = await br.newContext({ storageState: STATE, viewport: { width: VW, height: 臂.vh } });
    p = await ctx.newPage();
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 60000 });
    await p.waitForTimeout(6000);

    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== VW || 实际.h !== 臂.vh) throw new Error('轴向自检失败：' + 实际.w + 'x' + 实际.h);

    const 找 = await p.evaluate((aria) => {
      const e = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
        .find((x) => x.getAttribute('aria-label') === aria);
      return e ? { id: e.dataset.id, W: e.offsetWidth, H: e.offsetHeight, tf: e.style.transform || '' } : null;
    }, 臂.kind + ' node: ' + 臂.名);
    if (!找) throw new Error('找不到 aria 为「' + (臂.kind + ' node: ' + 臂.名) + '」的节点');
    nid = 找.id;
    记.画布盒 = { W: 找.W, H: 找.H };

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

    // 📌 手势：甲=往返、乙=纵向、丙=正向 120
    记.拖动 = [];
    const 拖 = async (dx, dy) => {
      const 前 = await p.evaluate(读画布);
      const r = await 拖一次(p, dx, dy, 臂.vh);
      const 后 = await p.evaluate(读画布);
      记.拖动.push({ 命令: [dx, dy], 错: r.错 || null, 前, 后, dx实测: (前.x !== null && 后.x !== null) ? +(后.x - 前.x).toFixed(1) : null, dy实测: (前.y !== null && 后.y !== null) ? +(后.y - 前.y).toFixed(1) : null });
    };
    if (臂.计划 === '往返') { await 拖(120, 0); await 拖(-120, 0); }
    else if (臂.计划 === '纵向') { await 拖(0, 120); }
    else if (臂.计划 === '正向') { await 拖(120, 0); }

    const 后节点 = await 读节点();
    记.节点画布坐标未变 = 后节点 ? (后节点.tf === 找.tf) : null;
    记.拖后画布 = await p.evaluate(读画布);
    记.净平移y = (记.拖前画布.y !== null && 记.拖后画布.y !== null) ? +(记.拖后画布.y - 记.拖前画布.y).toFixed(1) : null;
    记.净平移x = (记.拖前画布.x !== null && 记.拖后画布.x !== null) ? +(记.拖后画布.x - 记.拖前画布.x).toFixed(1) : null;

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

    记.闭式预测 = +闭式(VW, 臂.vh, 找.W, 找.H, 记.点之前).toFixed(6);
    记.命中闭式 = Math.abs(记.终点 - 记.闭式预测) < 5e-5;
    if (臂.kind === '文本') 记.命中期望 = Math.abs(记.终点 - 1.75) < 5e-6;
    记.safeH = 臂.vh - 160;
    记.A = 臂.kind === '音频' ? +(记.safeH - H0 * 记.终点).toFixed(3) : 0;
    const 后2 = await 读节点();
    记.落定后节点顶 = 后2 ? 后2.top : null;

    log(臂.键.padEnd(6) + '｜' + String(臂.组).padEnd(6) + '｜' + String(记.vw + 'x' + 记.vh).padEnd(11)
      + '｜净平移(' + String(记.净平移x) + ',' + String(记.净平移y) + ')'
      + '｜落点=' + String(记.终点).padEnd(10) + '｜A=' + String(记.A).padEnd(9)
      + '｜节点未动=' + 记.节点画布坐标未变);
  } catch (e) {
    记.错误 = e.message;
    log(臂.键.padEnd(6) + '🔴 ' + e.message);
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
const 音 = 好.filter((x) => x.kind === '音频');
const 组集 = (g) => 音.filter((x) => x.组 === g);
const 对照 = 取('W_1');
const 判定P0 = 对照 && 对照.命中期望
  ? '✅ P0：阳性对照 `文本 @1212×720` 落 `' + 对照.终点 + '` 逐字等于闭式 `1.75` ⇒ 尺子没漂'
  : '🔴 P0：阳性对照=' + (对照 ? 对照.终点 : '—') + '（期望 1.75）⇒ 本批作废';

const 甲 = 组集('甲拖回');
const 甲集 = 甲.map((x) => x.A);
const 甲判定 = !甲.length ? '（甲组臂不全）'
  : ('📌 P1甲「先 `+120` 再 `−120`」：净平移逐臂 = [' + 甲.map((x) => '(' + x.净平移x + ', ' + x.净平移y + ')').join('、') + ']'
    + '，`A` 逐臂 = [' + 甲集.join(', ') + ']'
    + ' ⇒ ' + (new Set(甲集).size === 1 && 甲集[0] === 200
      ? '✅ **净位移回原处而 `A` 仍是 `200.000`** ⇒ 📌 **是状态（一次性标志），不是位置**'
      : (new Set(甲集).size > 1
        ? '🔴 **净位移回原处而 `A` 又散开** ⇒ 📌 **是位置（阈值型）**，不是状态'
        : '📌 净位移回原处而 A 逐字相同但不是 200.000 ⇒ 需看具体值')));

const 乙 = 组集('乙反向');
const 乙集 = 乙.map((x) => x.A);
const 乙判定 = !乙.length ? '（乙组臂不全）'
  : ('📌 P1乙「改成纵向命令拖 `dy = +120`」：实测平移逐臂 = [' + 乙.map((x) => '(' + x.实测平移x + ', ' + x.实测平移y + ')').join('、') + ']'
    + '，`A` 逐臂 = [' + 乙集.join(', ') + ']'
    + ' ⇒ ' + (乙集.every((a) => a === 200)
      ? '✅ **反方向也锁** ⇒ 📌 **方向无关** ⇒ 与「状态」一致'
      : '🔴 **反方向没锁** ⇒ 📌 **与方向有关**'));

const 丙 = 组集('丙h扫').sort((a, b) => a.safeH - b.safeH);
const 丙A = 丙.map((x) => x.A);
const 丙极差 = 丙A.length >= 3 ? +(Math.max.apply(null, 丙A) - Math.min.apply(null, 丙A)).toFixed(3) : null;
const 基准 = 丙.find((x) => x.safeH === 560);
const 斜率 = 基准 ? +(基准.A / 基准.safeH).toFixed(6) : null;
const 期望 = 斜率 === null ? [] : 丙.map((x) => +(斜率 * x.safeH).toFixed(1));
const 偏差 = 斜率 === null ? [] : 丙.map((x) => +(x.A - 斜率 * x.safeH).toFixed(1));
const 最大偏差 = 偏差.length ? +Math.max.apply(null, 偏差.map(Math.abs)).toFixed(1) : null;
const T解 = (斜率 !== null && 斜率 < 1) ? +(((斜率 * 320) / (1 - 斜率)).toFixed(2)) : null;
const 判定P2 = 丙极差 === null ? '（丙组臂不全）'
  : ('📌 P2：带 `+120` 那一拖做 `h` 扫，`A` 逐档 = ' + 丙.map((x) => '`h=' + (x.safeH + 160) + '`→`' + x.A + '`').join('、')
    + '｜极差 `' + 丙极差 + '`'
    + ' ⇒ ' + (丙极差 <= 1.0
      ? '✅ **`A` 是画布空间的常数**（与 `safeH` 无关）⇒ 📌 预留的是**画布像素**，不是比例'
      : '📌 极差 `> 1.0` ⇒ **不是常数**；📌 再验「是否正比于 `safeH`」：斜率 `' + 斜率 + '` ⇒ 期望 = [' + 期望.join(', ')
        + ']、实测−期望 = [' + 偏差.join(', ') + ']、**最大偏差 `' + 最大偏差 + '`**'
        + ' ⇒ ' + (最大偏差 !== null && 最大偏差 <= 5
          ? '✅ **正比成立** ⇒ 固定内容高模型成立，`T = ' + T解 + '` 画布像素'
          : '🔴 **正比也被否**（最大偏差远超散布）⇒ 📌 两个模型都被否')));

out.判定 = {
  有效臂: 好.length + '/' + 臂表.length,
  判定P0_尺子: 判定P0,
  判定P1甲_状态还是位置: 甲判定,
  判定P1乙_方向: 乙判定,
  判定P2_200随不随safeH: 判定P2,
  甲逐臂: 甲.map((x) => ({ 键: x.键, 净平移: [x.净平移x, x.净平移y], A: x.A, 拖动: x.拖动 })),
  乙逐臂: 乙.map((x) => ({ 键: x.键, A: x.A, 拖动: x.拖动 })),
  丙逐档: 丙.map((x) => ({ 键: x.键, h: x.vh, safeH: x.safeH, A: x.A, 净平移y: x.净平移y, 落点: x.终点 })),
  丙极差, 斜率, 期望, 偏差, 最大偏差, 固定内容高T: T解,
  逐臂: 好.map((x) => ({
    键: x.键, 组: x.组, 计划: x.计划, 视口: x.vw + 'x' + x.vh, z0: x.点之前,
    拖前画布: x.拖前画布, 拖后画布: x.拖后画布, 净平移x: x.净平移x, 净平移y: x.净平移y,
    节点画布坐标未变: x.节点画布坐标未变,
    点后首读: x.点后首读, 读1: x.读1, 读2: x.读2, 读3: x.读3, 落点: x.终点,
    闭式预测: x.闭式预测, 命中闭式: x.命中闭式, safeH: x.safeH, A: x.A, 落定后节点顶: x.落定后节点顶,
  })),
  失效臂: out.臂.filter((x) => x.错误).map((x) => ({ 键: x.键, 错: x.错误 })),
};
log('\n════ 判定 ════\n' + JSON.stringify({
  有效臂: out.判定.有效臂, P0: 判定P0, P1甲: 甲判定, P1乙: 乙判定, P2: 判定P2,
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
