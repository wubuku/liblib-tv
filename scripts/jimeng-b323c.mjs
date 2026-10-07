/**
 * 批次 323c · 两件事：① 修 P2 那个「搜索面板开关」；② **把线索做成因果检验** —— 故意平移画布，看 `A` 跟不跟着动。
 *
 * 📌 **线索（零成本复算，n=4）**：批次 323b 的密集采样里，📌 **节点在「工具条挂载那一帧」的屏顶**逐臂是
 *    `−2167.53 / −2159.81 / −2146.57 / −2226.54`（📌 极差 `80` 屏像素），📌 而同臂的 `A` 是
 *    `211.491 / 203.872 / 203.725 / 210.797` ⇒ 📌 `corr(挂载时节点顶, A) = −0.671`。
 *    🔴 **`n = 4` 撑不起任何结论**（立规 201 的同款：**先算出来的相关性只是线索，不是判决**）
 *    ⇒ 📌 **本批改成因果检验：自己动手改那个自变量，看因变量动不动。**
 *
 * 🔴 **P2 又挂了一次（如实记）**：批次 323b 的「搜不到可见结果行」根因是
 *    📌 **第一次搜索后面板还开着，而 `备好结果行` 又去点了一次「搜索」钮 —— 那是「关闭」**，
 *    ⇒ 🔴 面板一关，`input` 没了，键盘输入打到页面上，结果行自然永远找不到。
 *    ⇒ 📌 **修法：先看 `[data-testid="canvas-search-panel"] input` 在不在，在就不点那个钮。**
 *
 * 📌 **判据（测量前写死）**：
 *   **P0** 阳性对照 `文本 @1212×720` 必须逐字落 `1.75`；🔴 不中 ⇒ 本批作废。
 *   **P2** 同一会话内再做 `2` 次 fit（点走 `文本 1` 再点回 `音频 1`）：
 *        逐臂 `A` 极差 `< 0.5` 画布像素 ⇒ 📌 **噪声是「每次加载」级的**；不小于 ⇒ 📌 **是「每次点击」级的**。
 *   **P3（因果）** 点击前把画布**平移 `0 / −120 / +120` 屏像素**（在空白处拖，📌 并逐臂核对「节点画布坐标没被拖动」），
 *        每档 `3` 臂 ⇒ 判据：**三组的 `A` 均值两两之差 `> 3 × 组内标准差`** ⇒ ✅ **`A` 由点击前的位置决定**；
 *        否则 🔴 **点击前的位置不是因**（⇒ 散布另有来源）。
 *
 * ⛔ 本批不做：不平移任何节点、不删除、不新建、不触发生成。
 *
 * 前提检查：轴向自检 / 落定自检（三连读）/ 点击生效自检 /
 *   `aria` 精确匹配现找现量 / 参数写死 / 每臂独立浏览器 / 盒尺寸逐臂现量 / 平移落点逐臂现量。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b323c.json';
const 放大键 = 'Meta+Equal';
const 闭式 = (w, h, W, H, z0) => Math.min((w - 532) / W, (h - 160) / H, z0);
const VW = 1212;
const VH = 720;
const SAFE_H = VH - 160;
const H0 = 320;
const 平移档 = [0, -120, 120];
const 每档臂数 = 3;

const 臂表 = [];
let 序号 = 0;
for (const dx of 平移档) {
  for (let k = 0; k < 每档臂数; k++) {
    序号 += 1;
    臂表.push({ 键: 'M' + 序号, 组: '平移dx' + dx, kind: '音频', 名: '音频 1', dx, 同时做P2: k === 0 });
  }
}
臂表.push({ 键: 'W_1', 组: '对照', kind: '文本', 名: '文本 1', dx: 0, 期望: 1.75 });

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b323c',
  问: 'A 由点击前的位置决定吗？（因果平移）+ 噪声是每次加载级还是每次点击级？',
  线索: {
    来源: '批次 323b 密集采样的零成本复算，n=4',
    挂载时节点屏顶: '−2167.53 / −2159.81 / −2146.57 / −2226.54（极差 80 屏像素）',
    同臂A: '211.491 / 203.872 / 203.725 / 210.797',
    相关系数: 'corr = −0.671',
    但: '🔴 n=4 撑不起结论 ⇒ 本批改因果检验：自己改自变量，看因变量动不动',
  },
  本批修的错: {
    P2为什么又挂: '第一次搜索后面板还开着，而备好结果行又去点了一次「搜索」钮 —— 那是「关闭」；面板一关 input 没了，键盘输入打到页面上',
    修法: '先看 [data-testid="canvas-search-panel"] input 在不在，在就不点那个钮',
  },
  判据: {
    P0: '阳性对照 文本 @1212×720 必须逐字落 1.75，不中即本批作废',
    P2: '同一会话内再做 2 次 fit；逐臂 A 极差 < 0.5 画布像素 ⇒ 噪声是每次加载级；否则是每次点击级',
    P3: '点击前平移 0 / −120 / +120 屏像素，每档 3 臂；三组 A 均值两两之差 > 3×组内标准差 ⇒ A 由点击前位置决定；否则不是因',
  },
  臂表, 臂: [], 判定: {},
};

/** 📌 修好之后的「备好结果行」：面板已开着就不要再点那个钮（那一下是「关闭」）。 */
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

const 搜并点 = async (p, 词表, 目标id) => {
  const r = await 备好结果行(p, 词表, 目标id);
  if (r.错) return r.错;
  await p.mouse.click(r.中心[0], r.中心[1]);
  await p.waitForTimeout(3200);
  return null;
};

/** 📌 在**空白处**拖动画布平移 `dx` 屏像素，并逐臂核对「节点的画布坐标没被拖动」。 */
const 平移 = async (p, dx) => {
  if (!dx) return { 生效: true, 实测dx: 0, 起点: null };
  const 起点 = await p.evaluate(() => {
    for (let y = 60; y < innerHeight - 60; y += 40) {
      for (let x = 40; x < innerWidth - 40; x += 40) {
        const e = document.elementFromPoint(x, y);
        if (e && !e.closest('.react-flow__node') && !e.closest('[data-testid="canvas-search-panel"]')) return { x, y };
      }
    }
    return null;
  });
  if (!起点) return { 生效: false, 实测dx: 0, 起点: null };
  await p.mouse.move(起点.x, 起点.y);
  await p.mouse.down();
  await p.mouse.move(起点.x + dx, 起点.y, { steps: 14 });
  await p.mouse.up();
  await p.waitForTimeout(1200);
  return { 生效: true, 实测dx: dx, 起点 };
};

for (const 臂 of 臂表) {
  let br = null; let p = null; let nid = null; let 文id = null;
  const 记 = { 键: 臂.键, 组: 臂.组, kind: 臂.kind, 名: 臂.名, vw: VW, vh: VH, dx: 臂.dx };
  try {
    br = await chromium.launch({ headless: true });
    const ctx = await br.newContext({ storageState: STATE, viewport: { width: VW, height: VH } });
    p = await ctx.newPage();
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 60000 });
    await p.waitForTimeout(6000);

    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== VW || 实际.h !== VH) throw new Error('轴向自检失败：' + 实际.w + 'x' + 实际.h);

    const 找 = await p.evaluate((aria) => {
      const e = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
        .find((x) => x.getAttribute('aria-label') === aria);
      return e ? { id: e.dataset.id, W: e.offsetWidth, H: e.offsetHeight, tf: e.style.transform || '' } : null;
    }, 臂.kind + ' node: ' + 臂.名);
    if (!找) throw new Error('找不到 aria 为「' + (臂.kind + ' node: ' + 臂.名) + '」的节点');
    nid = 找.id;
    记.画布盒 = { W: 找.W, H: 找.H };
    记.平移前画布tf = 找.tf;
    const t = await p.evaluate((aria) => {
      const e = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
        .find((x) => x.getAttribute('aria-label') === aria);
      return e ? e.dataset.id : null;
    }, '文本 node: 文本 1');
    文id = t;

    for (let i = 0; i < 13; i++) { await p.keyboard.press(放大键); await p.waitForTimeout(380); }
    await p.waitForTimeout(1600);
    const 读缩放 = () => p.evaluate(() => {
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      return m ? Number(m[1]) : null;
    });
    const 读节点屏顶 = () => p.evaluate((id) => {
      const e = document.querySelector('.react-flow__node[data-id="' + id + '"]');
      if (!e) return null;
      const b = e.getBoundingClientRect();
      return { top: Math.round(b.top * 10) / 10, h: Math.round(b.height * 10) / 10, tf: e.style.transform || '' };
    }, nid);
    记.点之前 = await 读缩放();
    if (记.点之前 === null) throw new Error('点之前读不到 scale');
    const 平移前顶 = await 读节点屏顶();

    记.平移 = await 平移(p, 臂.dx);
    const 平移后顶 = await 读节点屏顶();
    记.平移前节点顶 = 平移前顶 ? 平移前顶.top : null;
    记.平移后节点顶 = 平移后顶 ? 平移后顶.top : null;
    记.平移实测屏像素 = 平移前顶 && 平移后顶 ? +(平移后顶.top - 平移前顶.top).toFixed(1) : null;
    记.节点画布坐标未变 = 平移后顶 ? (平移后顶.tf === 记.平移前画布tf) : null;
    if (记.平移实测屏像素 === null) throw new Error('读不到节点屏顶');
    if (臂.dx && Math.abs(记.平移实测屏像素 - 臂.dx) > 12) 记.平移没到位 = true;

    const ariaWant = 臂.kind + ' node: ' + 臂.名;
    const 行 = await 备好结果行(p, [臂.名, ariaWant, 臂.kind], nid);
    if (行.错) throw new Error(行.错);
    记.点击前节点顶 = (await 读节点屏顶()).top;
    await p.mouse.click(行.中心[0], 行.中心[1]);

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

    记.闭式预测 = +闭式(VW, VH, 找.W, 找.H, 记.点之前).toFixed(6);
    记.命中闭式 = Math.abs(记.终点 - 记.闭式预测) < 5e-5;
    if (臂.期望 !== undefined) 记.命中期望 = Math.abs(记.终点 - 臂.期望) < 5e-6;
    记.A = 臂.kind === '音频' ? +(SAFE_H - H0 * 记.终点).toFixed(3) : 0;
    const 后顶 = await 读节点屏顶();
    记.落定后节点顶 = 后顶 ? 后顶.top : null;

    记.会话内 = [];
    if (臂.同时做P2 && 文id) {
      for (let k = 0; k < 2; k++) {
        const e2 = await 搜并点(p, ['文本 1', '文本 node: 文本 1'], 文id);
        if (e2) { 记.会话内.push({ 轮: k, 错: e2 }); break; }
        const e3 = await 搜并点(p, [臂.名, ariaWant, 臂.kind], nid);
        if (e3) { 记.会话内.push({ 轮: k, 错: e3 }); break; }
        const a = await 读缩放();
        await p.waitForTimeout(2600);
        const b = await 读缩放();
        await p.waitForTimeout(1800);
        const c = await 读缩放();
        记.会话内.push({ 轮: k, a, b, c, 落定: a === b && b === c, 落点: c, A: +(SAFE_H - H0 * c).toFixed(3) });
      }
    }

    log(臂.键.padEnd(4) + '｜' + 臂.组.padEnd(10) + '｜落点=' + String(记.终点).padEnd(10)
      + '｜A=' + String(记.A).padEnd(9)
      + '｜平移实测=' + String(记.平移实测屏像素).padEnd(8)
      + '｜节点画布坐标未变=' + String(记.节点画布坐标未变).padEnd(6)
      + '｜点击前顶=' + String(记.点击前节点顶).padEnd(11)
      + '｜落定后顶=' + String(记.落定后节点顶).padEnd(7)
      + '｜会话内=' + JSON.stringify(记.会话内.map((x) => (x.错 ? 'ERR:' + x.错 : x.A))));
  } catch (e) {
    记.错误 = e.message;
    log(臂.键.padEnd(4) + '🔴 ' + e.message);
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
const 对照 = 取('W_1');
const 判定P0 = 对照 && 对照.命中期望
  ? '✅ P0：阳性对照 `文本 @1212×720` 落 `' + 对照.终点 + '` 逐字等于闭式 `1.75` ⇒ 尺子没漂'
  : '🔴 P0：阳性对照=' + (对照 ? 对照.终点 : '—') + '（期望 1.75）⇒ 本批作废';

const 有会话内 = 音.filter((x) => (x.会话内 || []).length && (x.会话内 || []).every((y) => y.落点 !== undefined));
const 会话内差 = 有会话内.map((a) => {
  const 集 = (a.会话内.map((y) => y.A)).concat([a.A]);
  return +(Math.max.apply(null, 集) - Math.min.apply(null, 集)).toFixed(3);
});
const 判定P2 = !会话内差.length
  ? '（P2 臂不全或仍报错：' + JSON.stringify(音.map((a) => (a.会话内 || []).map((y) => y.错).filter(Boolean))) + '）'
  : ('📌 P2：做了会话内重复的 `n = ' + 有会话内.length + '` 臂，`A` 极差逐臂 = [' + 会话内差.join(', ') + ']（画布像素）'
    + ' ⇒ ' + (Math.max.apply(null, 会话内差) < 0.5
      ? '✅ **会话内完全不动** ⇒ 📌 **噪声是「每次加载」级的，不是「每次点击」级的**'
      : '✅ **会话内也抖** ⇒ 📌 **噪声是「每次点击」级的**'));

const 组统计 = 平移档.map((dx) => {
  const g = 音.filter((x) => x.组 === '平移dx' + dx);
  const 集 = g.map((x) => x.A);
  const n = 集.length;
  const m = n ? 集.reduce((a, b) => a + b, 0) / n : null;
  const sd = n > 1 ? Math.sqrt(集.reduce((a, b) => a + (b - m) * (b - m), 0) / (n - 1)) : null;
  return { dx, n, 均值: m === null ? null : +m.toFixed(3), 标准差: sd === null ? null : +sd.toFixed(3), 集: 集.slice().sort((a, b) => a - b) };
});
const 有效组 = 组统计.filter((x) => x.n >= 2 && x.标准差 !== null);
const 最大组内sd = 有效组.length ? Math.max.apply(null, 有效组.map((x) => x.标准差)) : null;
const 两两差 = [];
for (let i = 0; i < 组统计.length; i++) {
  for (let j = i + 1; j < 组统计.length; j++) {
    if (组统计[i].均值 === null || 组统计[j].均值 === null) continue;
    两两差.push({ 对: 'dx' + 组统计[i].dx + ' vs dx' + 组统计[j].dx, 差均值: +(组统计[j].均值 - 组统计[i].均值).toFixed(3) });
  }
}
const 判定P3 = (有效组.length < 3 || 最大组内sd === null)
  ? '（P3 臂不全：' + JSON.stringify(组统计) + '）'
  : ('📌 P3：点击前平移 `0 / −120 / +120` 屏像素，每档 `n = ' + 每档臂数 + '` ⇒ `A` 均值 = '
    + 组统计.map((x) => '`' + x.dx + '`→`' + x.均值 + '`（组内 sd ' + x.标准差 + '）').join('、')
    + '｜两两均值差 = ' + 两两差.map((x) => x.对 + ' `' + x.差均值 + '`').join('、')
    + ' ⇒ ' + (Math.max.apply(null, 两两差.map((x) => Math.abs(x.差均值))) > 3 * 最大组内sd
      ? '✅ **`A` 由点击前的位置决定** ⇒ 📌 **散布的来源找到了：搜索把节点滚到哪一点，是随run变的**'
      : '🔴 **点击前的位置不是因**（两两均值差都没超过 `3 × 组内 sd = ' + (3 * 最大组内sd).toFixed(3) + '`）⇒ 📌 散布另有来源'));

out.判定 = {
  有效臂: 好.length + '/' + 臂表.length,
  判定P0_尺子: 判定P0,
  判定P2_会话内还是跨会话: 判定P2,
  判定P3_平移因果: 判定P3,
  平移组统计: 组统计,
  两两均值差: 两两差,
  组内最大sd: 最大组内sd,
  逐臂: 好.map((x) => ({
    键: x.键, 组: x.组, dx: x.dx, z0: x.点之前, 落点: x.终点, 闭式预测: x.闭式预测, 命中闭式: x.命中闭式, A: x.A,
    平移实测屏像素: x.平移实测屏像素, 节点画布坐标未变: x.节点画布坐标未变, 平移没到位: x.平移没到位 || null,
    平移前节点顶: x.平移前节点顶, 点击前节点顶: x.点击前节点顶, 落定后节点顶: x.落定后节点顶,
    会话内: (x.会话内 || []).map((y) => (y.错 ? { 轮: y.轮, 错: y.错 } : { 轮: y.轮, 落点: y.落点, A: y.A, 落定: y.落定 })),
  })),
  失效臂: out.臂.filter((x) => x.错误).map((x) => ({ 键: x.键, 错: x.错误 })),
};
log('\n════ 判定 ════\n' + JSON.stringify({
  有效臂: out.判定.有效臂, P0: 判定P0, P2: 判定P2, P3: 判定P3, 组统计, 两两差,
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
