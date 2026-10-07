/**
 * 批次 327 · 通式 `A = R − 4` 找**第三个不同的 `R`**，并把屏空间式 `节点屏高 = h − 156 − R` 从「反推」升级成「直接量」。
 *
 * ✅ 接批次 326（`9/9` 臂）：音频 `R=204 ⇒ A=200`，视频 `R=208 ⇒ A=204`
 *    ⇒ 📌 通式 **`A = 面板屏高 R − 4`**，📌 闭式 `落点 = (safeH − (R−4))/H₀`
 *    ⇒ 📌 等价的**屏空间式** `节点屏高 = h − 156 − R`（`156 = 顶边 80 + 间隙 20 + 余量 56`）
 *
 * 📌 **本批换个测法**：批次 326 的 `节点屏高` 是从 `落点` **反推**的（`H₀ × 落点`），
 *    那是**推论**。本批**落地直接量**五个屏空间量并逐字求和：
 *    `顶边 + 节点屏高 + 间隙 + R + 余量 ≟ innerHeight`
 *    ⇒ 命中 ⇒ 屏空间式不再是推论而是读数；不命中 ⇒ 那个「恒 664 / 恒 80 / 恒 20 / 恒 56」里有虚的。
 *
 * 🔴 **本批主问题：`(R, A)` 只有 `(204,200)` `(208,204)` 两点**，两点永远定不了一条直线外加一个偏移。
 *    画布上还有 `图片 b22-upload`(`569×320`)、`外部 导演台`(`320×320`)、`时间线 2`(`1200×207`) 未测过面板屏高
 *    ⇒ 📌 若其中任何一个给出**第三档 `R`**，且 `A = R − 4` 仍逐字成立 ⇒ 通式坐实；
 *    🔴 若它们压根没有屏固定面板（`R` 缺测）⇒ 那就如实记成「第三点不存在」，**不拿两点硬说三点**（立规 207）。
 *
 * 📌 臂表：
 *   **P0 对照** `文本 1 @1212×720` **不锁定** 必须逐字落 `1.75` ⇒ 尺子没漂。
 *   **P1 尺子** `音频 1 @1212×720` 锁定必须逐字落 `1.125`、`R=204`、`A=200` ⇒ 本批的 `R` 仍量得到 204。
 *   **P2 R普查** `图片 b22-upload` 锁定 ⇒ 它的 `R` 是多少、`A` 是多少。
 *   **P3 R普查** `外部 导演台` 锁定 ⇒ 同上。
 *   **P4 R普查** `时间线 2` 锁定 ⇒ 同上。
 *   **P5 文本变体** `文本 3` 锁定 ⇒ 文本那条「不屏固定 ⇒ `A≡0`」在**另一个**文本节点上也成立吗。
 *   **P6/P7/P8 屏空间式** `视频 1` 在 `h=680/760/720` 锁定 ⇒ 预测落点逐字 `0.555361 / 0.695957 / 0.625659`
 *        （= `(h − 156 − 208)/569`），且五量和**逐字等于 `innerHeight`**。
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
const OUT = '/tmp/b327.json';
const 放大键 = 'Meta+Equal';
const 闭式 = (w, h, W, H, z0) => Math.min((w - 532) / W, (h - 160) / H, z0);

// 📌 屏空间式：`A = R − 4` ⇒ `节点屏高 = (h − 160) − (R − 4) = h − 156 − R`
const 屏空间闭式 = (vh, R) => (vh - 156 - R) / 569;
const round6 = (x) => (x === null || x === undefined ? null : +Number(x).toFixed(6));

const 臂表 = [
  { 键: 'W_1', 组: 'P0对照', kind: '文本', 名: '文本 1', vw: 1212, vh: 720, 锁定: false },
  { 键: '音1_720', 组: 'P1尺子', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 锁定: true },
  { 键: '图_720', 组: 'P2R普查', kind: '图片', 名: 'b22-upload', vw: 1212, vh: 720, 锁定: true },
  { 键: '导_720', 组: 'P3R普查', kind: '外部', 名: '导演台', vw: 1212, vh: 720, 锁定: true },
  { 键: '时2_720', 组: 'P4R普查', kind: '时间线', 名: '时间线 2', vw: 1212, vh: 720, 锁定: true },
  { 键: '文3_锁', 组: 'P5文本变体', kind: '文本', 名: '文本 3', vw: 1212, vh: 720, 锁定: true },
  { 键: '视1_680', 组: 'P6屏空间', kind: '视频', 名: '视频 1', vw: 1212, vh: 680, 锁定: true },
  { 键: '视1_720', 组: 'P6屏空间', kind: '视频', 名: '视频 1', vw: 1212, vh: 720, 锁定: true },
  { 键: '视1_760', 组: 'P6屏空间', kind: '视频', 名: '视频 1', vw: 1212, vh: 760, 锁定: true },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b327',
  问: '通式 A = R − 4 只有 (204,200) (208,204) 两点；屏空间式 节点屏高 = h − 156 − R 能否落地直接量',
  接326: '音频 R=204⇒A=200；视频 R=208⇒A=204；(560−208+4)/569=0.625659 逐字命中',
  测法升级: '不再从 落点 反推 节点屏高，直接量 顶边/节点屏高/间隙/R/余量 五个屏空间量并逐字求和 ≟ innerHeight',
  判据: {
    P0: '阳性对照 文本 @1212×720（不锁定）必须逐字落 1.75',
    P1: '音频 1（锁定）必须逐字落 1.125、R=204、A=200 ⇒ 本批的 R 仍量得到 204',
    P2: '图片 b22-upload（锁定）：量它的面板屏高 R 与 A',
    P3: '外部 导演台（锁定）：量它的面板屏高 R 与 A',
    P4: '时间线 2（锁定）：量它的面板屏高 R 与 A',
    P5: '文本 3（锁定）：文本那条「不屏固定 ⇒ A≡0」在另一个文本节点上也成立吗',
    P6: '视频 1 在 h=680/720/760（锁定）：落点必须逐字 (h−156−208)/569 = 0.555361/0.625659/0.695957',
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

// 📌 屏空间五量的直接测量：把**所有**可见工具条的屏矩形都列出来（不预设只会有一个），
//    再按「水平中心最贴近选中节点、且顶边落在节点底边上下 240 内」筛出属于它的那个。
//    📌 立规 204：探针的窗口必须真的盖住要判的那一刻 —— 所以这里**不**只量最大的那个。
const 量屏空间 = (id) => {
  const 节 = (x) => (x === undefined ? null : Math.round(x * 1000) / 1000);
  const 节点e = document.querySelector('.react-flow__node[data-id="' + id + '"]');
  if (!节点e) return { 错: '节点不在 DOM 里' };
  const nb = 节点e.getBoundingClientRect();
  const 节点 = { top: 节(nb.top), bottom: 节(nb.bottom), left: 节(nb.left), right: 节(nb.right), w: 节(nb.width), h: 节(nb.height) };
  const 全部工具条 = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'))
    .map((x) => { const b = x.getBoundingClientRect(); return { top: 节(b.top), bottom: 节(b.bottom), left: 节(b.left), right: 节(b.right), w: 节(b.width), h: 节(b.height), 面积: 节(b.width * b.height) }; })
    .filter((r) => r.w > 0 && r.h > 0);
  const 候选 = 全部工具条
    .map((r) => ({ r, dx: Math.abs((r.left + r.right) / 2 - (节点.left + 节点.right) / 2) }))
    .filter((z) => z.dx <= 节点.w / 2 + 80 && z.r.top >= 节点.bottom - 240 && z.r.top <= 节点.bottom + 240)
    .sort((a, b) => a.dx - b.dx);
  const 命中 = 候选.length ? 候选[0].r : null;
  const 出 = {
    节点, 工具条总数: 全部工具条.length, 候选数: 候选.length,
    工具条: 命中,
    全部工具条屏矩形: 全部工具条,
    innerH: innerHeight,
  };
  if (!命中) return 出;
  出.间隙 = 节(命中.top - 节点.bottom);
  出.余量 = 节(innerHeight - 命中.bottom);
  出.簇底边 = 节(命中.bottom);
  出.五量和 = 节(节点.top + 节点.h + 出.间隙 + 命中.h + 出.余量);
  出.五量和等于innerH = Math.abs(出.五量和 - innerHeight) < 0.0011;
  return 出;
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

    // 📌 落定后再等一拍，确保工具条已挂载（立规 204：窗口要真的盖住要判的那一刻）
    await p.waitForTimeout(1800);
    记.屏空间 = await p.evaluate(量屏空间, nid);

    记.闭式预测 = round6(闭式(臂.vw, 臂.vh, 找.W, H0, 记.点之前));
    记.命中闭式 = 记.终点 !== null && Math.abs(记.终点 - 记.闭式预测) < 5e-5;
    记.safeH = 臂.vh - 160;

    const sp = 记.屏空间;
    const R = sp && sp.工具条 ? sp.工具条.h : null;
    记.R = R;
    记.节点屏高_直接量 = sp && sp.节点 ? sp.节点.h : null;
    记.节点屏高_反推 = 记.终点 !== null ? Math.round(H0 * 记.终点 * 1000) / 1000 : null;
    记.两法一致 = (记.节点屏高_直接量 !== null && 记.节点屏高_反推 !== null)
      ? Math.abs(记.节点屏高_直接量 - 记.节点屏高_反推) < 0.5 : null;
    记.A = 记.终点 !== null ? Math.round((记.safeH - H0 * 记.终点) * 1000) / 1000 : null;
    记.R减4 = R === null ? null : Math.round((R - 4) * 1000) / 1000;
    记.命中A等于R减4 = (记.A !== null && 记.R减4 !== null) ? Math.abs(记.A - 记.R减4) < 0.0011 : null;
    if (R !== null) {
      记.屏空间闭式预测 = round6(屏空间闭式(臂.vh, R));
      记.命中屏空间闭式 = Math.abs(记.终点 - 记.屏空间闭式预测) < 5e-6;
    } else {
      记.屏空间闭式预测 = null; 记.命中屏空间闭式 = null;
    }

    log(臂.键.padEnd(9) + '｜' + 臂.名.padEnd(11) + '｜' + String(臂.vw + 'x' + 臂.vh).padEnd(10)
      + '｜盒高=' + String(H0).padEnd(5)
      + '｜落点=' + String(记.终点).padEnd(11)
      + '｜节点屏高(量/推)=' + String(记.节点屏高_直接量).padEnd(8) + '/' + String(记.节点屏高_反推).padEnd(8)
      + '｜R=' + String(R).padEnd(7)
      + '｜间隙=' + String(sp ? sp.间隙 : '—').padEnd(7)
      + '｜余量=' + String(sp ? sp.余量 : '—').padEnd(7)
      + '｜A=' + String(记.A).padEnd(9)
      + '｜A=R−4:' + (记.命中A等于R减4 === null ? 'n/a' : 记.命中A等于R减4 ? '✅' : '🔴')
      + '｜五量和=' + String(sp ? sp.五量和 : '—').padEnd(9)
      + '｜=innerH:' + (sp && sp.五量和等于innerH !== undefined ? (sp.五量和等于innerH ? '✅' : '🔴') : 'n/a'));
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
const 好 = out.臂.filter((x) => !x.错误 && x.点击生效 && x.落定 && x.终点 !== undefined && x.终点 !== null);
const 取 = (k) => 好.find((x) => x.键 === k);
const 组集 = (g) => 好.filter((x) => x.组 === g);
const 点串 = (xs) => xs.map((x) => '`' + x.键 + '`(`' + x.kind + ' ' + x.名 + '`) 落点 `' + x.终点 + '`、`R`=' + (x.R === null ? '—' : x.R) + '、`A`=' + x.A).join('；');

const 对照 = 取('W_1');
const 判定P0 = 对照 && 对照.命中闭式
  ? '✅ P0：阳性对照 `文本 1 @1212×720`（不锁定）落 `' + 对照.终点 + '` 逐字等于闭式 ⇒ 尺子没漂'
  : '🔴 P0：阳性对照=' + (对照 ? 对照.终点 : '—') + '（期望 1.75）⇒ 本批作废';

const 尺子 = 取('音1_720');
const 判定P1 = !尺子 ? '（P1 臂不全）'
  : (尺子.终点 === 1.125 && 尺子.R === 204 && 尺子.A === 200
    ? '✅ P1：`音频 1`（锁定）落 `' + 尺子.终点 + '`、`R`=`' + 尺子.R + '`、`A`=`' + 尺子.A + '` 逐字复现批次 326 ⇒ 本批的 `R` 仍量得到 `204`'
    : '🔴 P1：`音频 1`（锁定）落 `' + 尺子.终点 + '`、`R`=`' + 尺子.R + '`、`A`=`' + 尺子.A + '`（期望 `1.125`/`204`/`200`）⇒ 本批作废');

// 📌 立规 203：穷尽分类，不写「不是 A 就是 B」的 else。R 普查这一组的每个臂按它**实际有没有量到 R** 三分。
const 普查组 = 组集('P2R普查').concat(组集('P3R普查')).concat(组集('P4R普查'));
const 有R = 普查组.filter((x) => x.R !== null && x.R !== undefined);
const 无R = 普查组.filter((x) => x.R === null || x.R === undefined);
const 新R档 = 有R.filter((x) => x.R !== 204 && x.R !== 208);
const 判定P2 = '📌 P2–P4 `R` 普查（锁定）—— ' + 点串(普查组)
  + ' ⇒ 📌 **量到 `R` 的臂 ' + 有R.length + '/' + 普查组.length + ' 个**，取值集合 `{' + Array.from(new Set(有R.map((x) => x.R))).join(', ') + '}`'
  + '；量不到 `R` 的 ' + 无R.length + ' 个：' + (无R.length ? 无R.map((x) => '`' + x.键 + '`').join('、') : '—')
  + ' ⇒ ' + (无R.length === 0
    ? (新R档.length
      ? (新R档.every((x) => x.命中A等于R减4)
        ? '✅ **出现第三档 `R`=`' + 新R档.map((x) => x.R).join('/') + '`，且 `A = R − 4` 在它上面逐字成立** ⇒ 📌 通式 `A = R − 4` 从两点升到三点'
        : '🔴 出现新 `R` 但 `A = R − 4` 不成立 ⇒ 通式被否')
      : '📌 **量到的 `R` 全是已知的 `204`/`208`，没有第三档** ⇒ 📌 画布上现成的节点给不出第三个 `R`（立规 207：不拿两点硬说三点）')
    : '📌 **有臂压根量不到 `R`（面板不是屏固定或压根没有 `node-toolbar`）** ⇒ 这些臂**不能**用来验 `A = R − 4`')
  + '；📌 在**量得到 `R` 的臂**上 `A = R − 4` ' + (有R.every((x) => x.命中A等于R减4) ? '✅ 逐字全成立' : '🔴 有臂不成立');

const 文本变 = 取('文3_锁');
const 判定P5 = !文本变 ? '（P5 臂不全）'
  : '📌 P5：文本那条「面板不屏固定 ⇒ `A≡0`」的第二个证据 —— `文本 3`（锁定）落 `' + 文本变.终点
    + '`、`A`=`' + 文本变.A + '`、`R`=' + (文本变.R === null ? '—' : 文本变.R)
    + '、`间隙`=' + (文本变.屏空间 ? 文本变.屏空间.间隙 : '—')
    + ' ⇒ ' + (文本变.A === 0
      ? '✅ **`A` 逐字 `0`**，与 `文本 1` 一致 ⇒ 📌 文本这一类上「面板不屏固定就不预留」在**另一个**节点上复现'
      : '🔴 `文本 3` 的 `A` 不为 `0` ⇒ 「文本 `A≡0`」不是文本类的性质，要重查');

const 屏组 = 组集('P6屏空间');
const 屏预期 = { 视1_680: 0.555361, 视1_720: 0.625659, 视1_760: 0.695957 };
const 判定P6 = !屏组.length ? '（P6 臂不全）'
  : ('📌 P6：屏空间式 `节点屏高 = h − 156 − R` 在**多个视口高**上（锁定，`视频 1`，`R=208`）—— '
    + 屏组.map((x) => '`h=' + x.vh + '` 预测 `' + 屏预期[x.键] + '` 实测 `' + x.终点 + '`'
      + (x.命中屏空间闭式 ? '✅' : '🔴')
      + '｜五量和 `' + (x.屏空间 ? x.屏空间.五量和 : '—') + '` ≟ `innerHeight=' + x.vh + '`'
      + (x.屏空间 && x.屏空间.五量和等于innerH !== undefined ? (x.屏空间.五量和等于innerH ? '✅' : '🔴') : 'n/a')).join('；')
    + ' ⇒ ' + (屏组.every((x) => x.命中屏空间闭式) ? '✅ **三档视口高全部逐字命中屏空间闭式**' : '🔴 有档不命中')
    + '；' + (屏组.every((x) => x.屏空间 && x.屏空间.五量和等于innerH) ? '✅ **五量和逐字等于 `innerHeight`** ⇒ 📌 屏空间式不再是「从落点反推的推论」，是**落地直接量**' : '🔴 有档五和不等于 `innerHeight`'));

const 五和集 = 好.filter((x) => x.屏空间 && x.屏空间.工具条);
const 间隙集 = Array.from(new Set(五和集.map((x) => x.屏空间.间隙)));
const 余量集 = Array.from(new Set(五和集.map((x) => x.屏空间.余量)));
const 顶边集 = Array.from(new Set(五和集.map((x) => x.屏空间.节点.top)));

out.判定 = {
  有效臂: 好.length + '/' + 臂表.length,
  判定P0_尺子: 判定P0,
  判定P1_尺子: 判定P1,
  判定P2_R普查: 判定P2,
  判定P5_文本变体: 判定P5,
  判定P6_屏空间式: 判定P6,
  屏空间常数: { 间隙取值集合: 间隙集, 余量取值集合: 余量集, 节点顶边取值集合: 顶边集 },
  逐臂: 好.map((x) => ({
    键: x.键, 组: x.组, kind: x.kind, 名: x.名, 视口: x.vw + 'x' + x.vh, 锁定: x.锁定, 画布盒: x.画布盒,
    拖: x.拖, 节点画布坐标未变: x.节点画布坐标未变,
    z0: x.点之前, 点后首读: x.点后首读, 读1: x.读1, 读2: x.读2, 读3: x.读3, 落定: x.落定, 落点: x.终点,
    闭式预测: x.闭式预测, 命中闭式: x.命中闭式, safeH: x.safeH,
    R: x.R, 节点屏高_直接量: x.节点屏高_直接量, 节点屏高_反推: x.节点屏高_反推, 两法一致: x.两法一致,
    间隙: x.屏空间 ? x.屏空间.间隙 : null, 余量: x.屏空间 ? x.屏空间.余量 : null,
    簇底边: x.屏空间 ? x.屏空间.簇底边 : null,
    五量和: x.屏空间 ? x.屏空间.五量和 : null, 五量和等于innerH: x.屏空间 ? x.屏空间.五量和等于innerH : null,
    工具条总数: x.屏空间 ? x.屏空间.工具条总数 : null, 候选数: x.屏空间 ? x.屏空间.候选数 : null,
    A: x.A, R减4: x.R减4, 命中A等于R减4: x.命中A等于R减4,
    屏空间闭式预测: x.屏空间闭式预测, 命中屏空间闭式: x.命中屏空间闭式,
  })),
  失效臂: out.臂.filter((x) => x.错误).map((x) => ({ 键: x.键, 错: x.错误 })),
};
log('\n════ 判定 ════\n' + JSON.stringify({
  有效臂: out.判定.有效臂, P0: 判定P0, P1: 判定P1, P2: 判定P2, P5: 判定P5, P6: 判定P6,
  屏空间常数: out.判定.屏空间常数,
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
