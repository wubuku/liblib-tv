/**
 * 批次 324 · 平移那一拖把散布锁成了 `A ≡ 200.000` —— 🔴 **那这个「干净值」是什么？它随 `safeH` 变吗？**
 *
 * ✅ **接批次 323c 的实测（`10/10` 臂数据全在，只是判定器自己判废了）**：
 *    `dx = 0`（不干预）三臂：`A` = **`212.038` / `209.699` / `208.000`**
 *    `dx = −120` 三臂：`A` = **`200.000` / `200.000` / `200.000`**
 *    `dx = +120` 三臂：`A` = **`200.000` / `200.000` / `200.000`**
 *    📌 而两组的**实测平移量只有 `4.3`–`4.9` 屏像素**（`120` 像素的拖几乎没生效）⇒ 📌 **不是「平移多远」，是「有没有这么一拖」**。
 *    📌 并且会话内重复 fit 在 `dx = 0` 与两个平移组里都**逐字不变**（`212.038`×3、`200.000`×3）⇒ 📌 **每次会话内 fit 是确定的**。
 *
 * 🔴 **本批要修的一处自己的错**：批次 323c 在 `p.mouse.click` 之后**立刻**读第一次缩放，
 *    ⇒ 🔴 `读1` 读到的是动画中途（`2.779` / `2.20068` / `2.53814` …）⇒ 🔴 `落定 = 读1===读2===读3` 永远为假
 *    ⇒ 🔴 **判定器把 `10/10` 臂全判废了**（`有效臂 0/10`、`P0 对照=—`），📌 而 `读2` 与 `读3` **逐字相同**、数据是好的。
 *    ⇒ 📌 **修法：点完先等 `3200ms` 再开始三连读**；📌 **落定只用「等过之后」的三连读判**，
 *    📌 而点完立刻那一次读数**另存为 `点后首读`**，它是动画起点，📌 **不参与落定判定**。
 *
 * 📌 **两个问题，判据全部测量前写死**：
 *   **P1（哪个手势能拿到干净值）** 在点击前做**不同的无副作用手势**，各 `1`–`3` 臂：
 *        `无干预` / `空白处单击` / `拖 5px` / `拖 40px` / `复现 4.6px` / `缩放出一次再进一次` / `窗口宽 resize 1px 再改回` / `开搜索面板再按 Esc`
 *        ⇒ 判据：**出现逐字相同的 `A` 的手势 ⇒ ✅ 「干净值」可复现**；📌 **全都在散布里 ⇒ 🔴 那一拖带来的不是「干净」而是别的东西**。
 *   **P2（干净值随 `safeH` 变吗）** 带上「那一拖」，把 `h` 扫成 `640 / 680 / 720 / 760 / 800`：
 *        ⇒ **`A` 的极差 `≤ 1.0` ⇒ 画布空间的常数**（`A` 是预留的画布像素）；
 *        ⇒ **`A` 与 `safeH` 成正比 ⇒ 固定内容高模型**（`s = safeH/(H₀+T)`，由 `h=720` 的 `A=200` 解出 `T = 177.78`）。
 *
 * 📌 **P0** 阳性对照 `文本 @1212×720` 必须逐字落 `1.75`；🔴 不中 ⇒ 本批作废。
 *
 * ⛔ 本批不做：不平移任何节点、不删除、不新建、不触发生成；resize 只改浏览器视口、不改画布内容。
 *
 * 前提检查：轴向自检 / 落定自检（三连读，点完先等） / 点击生效自检 /
 *   `aria` 精确匹配现找现量 / 参数写死 / 每臂独立浏览器 / 盒尺寸逐臂现量 / 手势效果逐臂现量。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b324.json';
const 放大键 = 'Meta+Equal';
const 缩小键 = 'Meta+Minus';
const 闭式 = (w, h, W, H, z0) => Math.min((w - 532) / W, (h - 160) / H, z0);
const H0 = 320;

const 手势表 = [
  { 名: '无干预', 拖: 0, 特殊: null, 组: 'P1' },
  { 名: '空白单击', 拖: 0, 特殊: '单击', 组: 'P1' },
  { 名: '拖5', 拖: 5, 特殊: null, 组: 'P1' },
  { 名: '拖40', 拖: 40, 特殊: null, 组: 'P1' },
  { 名: '拖4.6', 拖: 4.6, 特殊: null, 组: 'P1' },
  { 名: '缩放往返', 拖: 0, 特殊: '缩放往返', 组: 'P1' },
  { 名: '窗口往返', 拖: 0, 特殊: '窗口往返', 组: 'P1' },
  { 名: '面板开关', 拖: 0, 特殊: '面板开关', 组: 'P1' },
];
const h扫 = [640, 680, 720, 760, 800];

const 臂表 = [];
let 序号 = 0;
for (const g of 手势表) {
  const n = g.名 === '无干预' ? 3 : 2;
  for (let k = 0; k < n; k++) {
    序号 += 1;
    臂表.push({ 键: 'G' + 序号, 组: 'P1', 手势: g.名, kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 拖: g.拖, 特殊: g.特殊 });
  }
}
for (const h of h扫) {
  序号 += 1;
  臂表.push({ 键: 'H' + h, 组: 'P2', 手势: '拖4.6', kind: '音频', 名: '音频 1', vw: 1212, vh: h, 拖: 4.6, 特殊: null });
}
臂表.push({ 键: 'W_1', 组: '对照', kind: '文本', 名: '文本 1', vw: 1212, vh: 720, 拖: 0, 特殊: null, 期望: 1.75 });

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b324',
  问: '平移那一拖把散布锁成 A≡200.000 —— 哪个手势能拿到干净值？干净值随 safeH 变吗？',
  接323c: {
    'dx=0': 'A = 212.038 / 209.699 / 208.000',
    'dx=-120': 'A = 200.000 / 200.000 / 200.000',
    'dx=+120': 'A = 200.000 / 200.000 / 200.000',
    实测平移量: '只有 4.3–4.9 屏像素（120 像素的拖几乎没生效）⇒ 不是「平移多远」，是「有没有这么一拖」',
    会话内: '逐字不变（212.038×3、200.000×3）⇒ 每次会话内 fit 是确定的',
  },
  本批修的错: {
    错: '323c 点完立刻读第一次缩放 ⇒ 读到动画中途 ⇒ 落定判据永远为假 ⇒ 判定器把 10/10 臂全判废（而 读2===读3，数据是好的）',
    修法: '点完先等 3200ms 再开始三连读；点完立刻那一次另存为「点后首读」，不参与落定判定',
  },
  判据: {
    P0: '阳性对照 文本 @1212×720 必须逐字落 1.75，不中即本批作废',
    P1: '不同手势后 A 逐字相同 ⇒ 干净值可复现；全都在散布里 ⇒ 那一拖带来的不是「干净」',
    P2: '带那一拖做 h 扫：A 极差 ≤ 1.0 ⇒ 画布空间常数；A 与 safeH 成正比 ⇒ 固定内容高模型（T=177.78 由 A=200@safeH=560 解出）',
  },
  臂表, 臂: [], 判定: {},
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
  const 记 = { 键: 臂.键, 组: 臂.组, 手势: 臂.手势, kind: 臂.kind, 名: 臂.名, vw: 臂.vw, vh: 臂.vh, 拖: 臂.拖, 特殊: 臂.特殊 };
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
    记.手势前画布tf = 找.tf;

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
      return { top: Math.round(b.top * 10) / 10, h: Math.round(b.height * 10) / 10, tf: e.style.transform || '' };
    }, nid);
    记.点之前 = await 读缩放();
    if (记.点之前 === null) throw new Error('点之前读不到 scale');
    const 手势前 = await 读节点();

    // 📌 手势：全部在空白处做，逐臂现量它到底改变了什么
    // 🔴 修：原来这里叫 `记.手势`，而 `记.手势` 在建 记 时已经是**字符串**（手势名），
    //    这里用对象把它**覆盖**掉了 ⇒ P1 分组拿对象比字符串、永远为空，对照臂更直接抛 `padEnd`。
    //    ⇒ 现在细节对象改名 `手势详情`，`手势` 始终是字符串。
    记.手势详情 = { 名: String(臂.手势 || '（对照）'), 拖: 臂.拖, 特殊: 臂.特殊, 起手: null, 实测位移: null, 点之前变化: null };
    if (臂.拖 || 臂.特殊 === '单击') {
      const 起点 = await p.evaluate(() => {
        for (let y = 60; y < innerHeight - 60; y += 40) {
          for (let x = 40; x < innerWidth - 40; x += 40) {
            const e = document.elementFromPoint(x, y);
            if (e && !e.closest('.react-flow__node') && !e.closest('[data-testid="canvas-search-panel"]')) return { x, y };
          }
        }
        return null;
      });
      记.手势详情.起手 = 起点;
      if (!起点) throw new Error('找不到空白起点');
      if (臂.特殊 === '单击') {
        await p.mouse.click(起点.x, 起点.y);
      } else {
        await p.mouse.move(起点.x, 起点.y);
        await p.mouse.down();
        await p.mouse.move(起点.x + 臂.拖, 起点.y, { steps: Math.max(2, Math.round(臂.拖 / 2)) });
        await p.mouse.up();
      }
      await p.waitForTimeout(1400);
    } else if (臂.特殊 === '缩放往返') {
      const 前 = 记.点之前;
      await p.keyboard.press(缩小键);
      await p.waitForTimeout(700);
      await p.keyboard.press(放大键);
      await p.waitForTimeout(1400);
      记.手势详情.点之前变化 = { 前, 后: await 读缩放() };
    } else if (臂.特殊 === '窗口往返') {
      await p.setViewportSize({ width: 臂.vw + 1, height: 臂.vh });
      await p.waitForTimeout(900);
      await p.setViewportSize({ width: 臂.vw, height: 臂.vh });
      await p.waitForTimeout(1400);
    } else if (臂.特殊 === '面板开关') {
      const 钮 = await p.evaluate(() => {
        const b = document.querySelector('button[aria-label="搜索"]');
        if (!b) return null;
        const r = b.getBoundingClientRect();
        return { 中心: [r.x + r.width / 2, r.y + r.height / 2] };
      });
      if (钮) {
        await p.mouse.click(钮.中心[0], 钮.中心[1]);
        await p.waitForTimeout(1500);
        await p.keyboard.press('Escape');
        await p.waitForTimeout(1200);
      }
    }
    const 手势后 = await 读节点();
    记.手势详情.实测位移 = 手势前 && 手势后 ? +(手势后.top - 手势前.top).toFixed(1) : null;
    记.手势后点之前 = await 读缩放();
    记.节点画布坐标未变 = 手势后 ? (手势后.tf === 记.手势前画布tf) : null;

    const ariaWant = 臂.kind + ' node: ' + 臂.名;
    const 行 = await 备好结果行(p, [臂.名, ariaWant, 臂.kind], nid);
    if (行.错) throw new Error(行.错);
    await p.mouse.click(行.中心[0], 行.中心[1]);
    // 📌 修法：点完**立刻**读一次，但只作为「点后首读」存起来；落定判定从等过之后开始
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

    记.闭式预测 = +闭式(臂.vw, 臂.vh, 找.W, 找.H, 记.点之前).toFixed(6);
    记.命中闭式 = Math.abs(记.终点 - 记.闭式预测) < 5e-5;
    if (臂.期望 !== undefined) 记.命中期望 = Math.abs(记.终点 - 臂.期望) < 5e-6;
    记.safeH = 臂.vh - 160;
    记.A = 臂.kind === '音频' ? +(记.safeH - H0 * 记.终点).toFixed(3) : 0;
    const 后 = await 读节点();
    记.落定后节点顶 = 后 ? 后.top : null;
    记.工具条屏高 = await p.evaluate(() => {
      const es = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'))
        .map((x) => x.getBoundingClientRect()).filter((r) => r.width > 0 && r.height > 0);
      if (!es.length) return null;
      const b = es.reduce((q, r) => (r.width * r.height > q.width * q.height ? r : q));
      return Math.round(b.height * 100) / 100;
    });

    log(臂.键.padEnd(6) + '｜' + String(臂.手势 || '对照').padEnd(7) + '｜' + String(臂.vw + 'x' + 臂.vh).padEnd(10)
      + '｜落点=' + String(记.终点).padEnd(10)
      + '｜A=' + String(记.A).padEnd(9)
      + '｜首读=' + String(记.点后首读).padEnd(9)
      + '｜手势位移=' + String(记.手势详情.实测位移).padEnd(7)
      + '｜工具条屏高=' + 记.工具条屏高);
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
const 对照 = 取('W_1');
const 判定P0 = 对照 && 对照.命中期望
  ? '✅ P0：阳性对照 `文本 @1212×720` 落 `' + 对照.终点 + '` 逐字等于闭式 `1.75` ⇒ 尺子没漂'
  : '🔴 P0：阳性对照=' + (对照 ? 对照.终点 : '—') + '（期望 1.75）⇒ 本批作废';

const P1 = [];
for (const g of 手势表) {
  const 组 = 好.filter((x) => x.组 === 'P1' && x.手势 === g.名);
  const 集 = 组.map((x) => x.A);
  P1.push({ 手势: g.名, n: 集.length, A: 集, 逐字相同: 集.length > 1 && new Set(集).size === 1 });
}
const 锁定 = P1.filter((x) => x.逐字相同);
const 基线 = P1.find((x) => x.手势 === '无干预');
const 判定P1 = '📌 P1：各手势后 `A` 逐臂 = ' + P1.map((x) => '`' + x.手势 + '`→[' + x.A.join(', ') + ']').join('、')
  + '｜**逐字相同的手势** = ' + (锁定.length ? 锁定.map((x) => '`' + x.手势 + '`').join('、') : '无')
  + (基线 ? '｜基线「无干预」极差 = ' + (Math.max.apply(null, 基线.A) - Math.min.apply(null, 基线.A)).toFixed(3) : '')
  + ' ⇒ ' + (锁定.length
    ? '✅ **「干净值」可复现** ⇒ 📌 拿到它的手势 = ' + 锁定.map((x) => '`' + x.手势 + '`（值 `' + x.A[0] + '`）').join('、')
    : '🔴 **所有手势的 `A` 都在散布里** ⇒ 📌 批次 323c 那一拖带来的不是「干净」，另有解释');

const P2 = 好.filter((x) => x.组 === 'P2');
const P2A = P2.map((x) => ({ 键: x.键, safeH: x.safeH, A: x.A, 落点: x.终点 }));
const P2极差 = P2A.length >= 3 ? +(Math.max.apply(null, P2A.map((x) => x.A)) - Math.min.apply(null, P2A.map((x) => x.A))).toFixed(3) : null;
const 基准 = P2A.find((x) => x.safeH === 560);
const T解 = 基准 ? +(((基准.A / 基准.safeH) * 320) / (1 - 基准.A / 基准.safeH)).toFixed(2) : null;
const 判定P2 = (P2极差 === null)
  ? '（P2 臂不全）'
  : ('📌 P2：带那一拖做 `h` 扫，`A` 逐档 = ' + P2A.map((x) => '`h=' + (x.safeH + 160) + '`→`' + x.A + '`').join('、')
    + '｜极差 `' + P2极差 + '`'
    + ' ⇒ ' + (P2极差 <= 1.0
      ? '✅ **`A` 是画布空间的常数**（与 `safeH` 无关）⇒ 📌 预留的是**画布像素**，不是比例'
      : (() => {
          // 🔴 修：原来的 else 分支直接写「A 与 safeH 成正比 ⇒ 模型成立」——
          //    🔴 而极差大**只说明不是常数**，**不说明正比**（本批实测就是反例：非单调）。
          //    ⇒ 现在真的去比「按正比模型算的期望值」。
          const 斜率 = 基准 ? 基准.A / 基准.safeH : null;
          const 期望 = 斜率 === null ? [] : P2A.map((x) => +(斜率 * x.safeH).toFixed(1));
          const 偏差 = 斜率 === null ? [] : P2A.map((x) => +(x.A - 斜率 * x.safeH).toFixed(1));
          const 最大偏差 = 偏差.length ? Math.max.apply(null, 偏差.map(Math.abs)) : null;
          return '📌 极差 `> 1.0` ⇒ **不是常数**；📌 再检验「是否正比于 `safeH`」：'
            + '按 `h=720` 的 `A=' + (基准 ? 基准.A : '—') + '` 定出斜率 `' + (斜率 === null ? '—' : 斜率.toFixed(6))
            + '` ⇒ 期望值 = [' + 期望.join(', ') + ']、实测−期望 = [' + 偏差.join(', ') + ']，**最大偏差 `' + 最大偏差 + '`**'
            + ' ⇒ ' + (最大偏差 !== null && 最大偏差 <= 5
              ? '✅ **正比成立** ⇒ 固定内容高模型成立，`T = ' + T解 + '` 画布像素'
              : '🔴 **正比也被否**（偏差远超散布）⇒ 📌 这一组**仍在散布态**（带的手势没锁住），'
                + '它复现的是批次 322 的结论：`A` 与 `safeH` **无趋势**，极差与同视口重跑的散布同量级');
        })()));

out.判定 = {
  有效臂: 好.length + '/' + 臂表.length,
  判定P0_尺子: 判定P0,
  判定P1_哪个手势锁住: 判定P1,
  判定P2_干净值随不随safeH: 判定P2,
  P1汇总: P1, P2逐档: P2A, P2极差, 固定内容高T: T解,
  逐臂: 好.map((x) => ({
    键: x.键, 组: x.组, 手势: x.手势, 视口: x.vw + 'x' + x.vh, z0: x.点之前,
    手势后点之前: x.手势后点之前, 手势位移: x.手势详情.实测位移, 节点画布坐标未变: x.节点画布坐标未变,
    点后首读: x.点后首读, 读1: x.读1, 读2: x.读2, 读3: x.读3, 落点: x.终点,
    闭式预测: x.闭式预测, 命中闭式: x.命中闭式, safeH: x.safeH, A: x.A,
    落定后节点顶: x.落定后节点顶, 工具条屏高: x.工具条屏高,
  })),
  失效臂: out.臂.filter((x) => x.错误).map((x) => ({ 键: x.键, 错: x.错误 })),
};
log('\n════ 判定 ════\n' + JSON.stringify({
  有效臂: out.判定.有效臂, P0: 判定P0, P1: 判定P1, P2: 判定P2, P2极差, 固定内容高T: T解,
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
