/**
 * 批次 324b · 找「那一拖」的门槛 —— 🔴 **批次 323c 的 `A ≡ 200.000` 至今没被复现**。
 *
 * 🔴 **接批次 323c / 324 的实测，两边对不上**：
 *    `b323c`：`dx = ±120`（`steps = 60`）**六臂全部 `A = 200.000`**，📌 实测画布位移只有 `4.3`–`4.9` 屏像素。
 *    `b324`：`拖 4.6` → `203.341` / `216.282`；`拖 5` → `202.870` / `202.477`；`拖 40`（实测位移 `6.2`）→ `210.499` / `209.907`；
 *          `空白单击` → `201.315` / `212.227`；`缩放往返` → `203.760` / `214.781`；`无干预` → `201.757` / `204.419` / `211.923`
 *    ⇒ 🔴 **没有一个手势锁住 `200.000`** ⇒ 📌 **b323c 那六臂的锁是另一个原因，不是「拖」本身。**
 *    📌 **b324 的臂表里恰好没有 `|dx| = 120` 这一档** ⇒ 📌 **变量没被覆盖，不是被否**（立规 204 的同款：**没测 ≠ 被否**）。
 *
 * 📌 **本批只做一件事：把拖动距离扫成 `0 / 60 / 120 / 240`，每档 `2` 臂，并把拖动量改成读 `.react-flow__viewport` 的 translate。**
 *    📌 **为什么换读法**：`b323`/`b324` 量的是「节点屏顶变了多少」，📌 那只是**结果**；
 *    📌 **画布 transform 的 translate 才是「画布有没有被平移」的地真** ⇒ 📌 顺带解释「命令拖 120 像素、实测只动 4.6 像素」。
 *
 * 📌 **判据（测量前写死）**：
 *   **P0** 阳性对照 `文本 @1212×720` 必须逐字落 `1.75`；🔴 不中 ⇒ 本批作废。
 *   **P1** 某一档 `2` 臂的 `A` 逐字相同 ⇒ ✅ **那一档就是门槛**（并报出该档的实测 translate）；
 *        📌 **全档都在散布里 ⇒ 🔴 `b323c` 的锁不是拖动造成的**，📌 而要找「除拖动外还差了什么」。
 *   **P2** 「命令位移 vs 实测 translate」逐档对照 ⇒ 🔴 **实测远小于命令 ⇒ 画布把平移吃掉了**（📌 这一条独立于 `A`，先把它记清楚）。
 *
 * ⛔ 本批不做：不平移任何节点（📌 逐臂核对节点画布 `transform` 未变）、不删除、不新建、不触发生成。
 *
 * 前提检查：轴向自检 / 落定自检（三连读，📌 **点完先等 `3200ms`**）/ 点击生效自检 /
 *   `aria` 精确匹配现找现量 / 参数写死 / 每臂独立浏览器 / 盒尺寸逐臂现量 / 平移量逐臂现量。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b324b.json';
const 放大键 = 'Meta+Equal';
const 闭式 = (w, h, W, H, z0) => Math.min((w - 532) / W, (h - 160) / H, z0);
const VW = 1212;
const VH = 720;
const SAFE_H = VH - 160;
const H0 = 320;
const 距离档 = [0, 60, 120, 240];
const 每档臂数 = 2;

const 臂表 = [];
let 序号 = 0;
for (const dx of 距离档) {
  for (let k = 0; k < 每档臂数; k++) {
    序号 += 1;
    臂表.push({ 键: 'D' + 序号, 组: '距离' + dx, kind: '音频', 名: '音频 1', dx });
  }
}
臂表.push({ 键: 'W_1', 组: '对照', kind: '文本', 名: '文本 1', dx: 0, 期望: 1.75 });

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b324b',
  问: '「那一拖」的门槛在哪？b323c 的 A≡200.000 到底是不是拖出来的？',
  两边对不上: {
    b323c: 'dx = ±120（steps=60）六臂全部 A = 200.000，实测画布位移只有 4.3–4.9 屏像素',
    b324: '拖4.6 → 203.341/216.282；拖5 → 202.870/202.477；拖40（实测位移 6.2）→ 210.499/209.907；空白单击 → 201.315/212.227；缩放往返 → 203.760/214.781；无干预 → 201.757/204.419/211.923',
    结论: '🔴 没有一个手势锁住 200.000；而 b324 的臂表里恰好没有 |dx|=120 这一档 ⇒ 📌 变量没被覆盖，不是被否',
  },
  本批改的读法: '平移量改读 .react-flow__viewport 的 translate（画布有没有被平移的地真），不再只读节点屏顶（那只是结果）',
  判据: {
    P0: '阳性对照 文本 @1212×720 必须逐字落 1.75，不中即本批作废',
    P1: '某一档 2 臂的 A 逐字相同 ⇒ 那一档就是门槛；全档都在散布里 ⇒ b323c 的锁不是拖动造成的',
    P2: '命令位移 vs 实测 translate 逐档对照；实测远小于命令 ⇒ 画布把平移吃掉了',
  },
  距离档, 每档臂数, 臂表, 臂: [], 判定: {},
};

const 读画布 = () => {
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(document.querySelector('.react-flow__viewport').style.transform || '');
  return { x: m ? Number(m[1]) : null, y: m ? Number(m[2]) : null, 整串: (document.querySelector('.react-flow__viewport').style.transform || '') };
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
    记.拖前节点顶 = (await 读节点()).top;

    if (臂.dx) {
      const 起点 = await p.evaluate(() => {
        for (let y = 60; y < innerHeight - 60; y += 40) {
          for (let x = 40; x < innerWidth - 40; x += 40) {
            const e = document.elementFromPoint(x, y);
            if (e && !e.closest('.react-flow__node') && !e.closest('[data-testid="canvas-search-panel"]')) return { x, y };
          }
        }
        return null;
      });
      记.起点 = 起点;
      if (!起点) throw new Error('找不到空白起点');
      记.终点x = Math.min(起点.x + 臂.dx, VW - 2);
      await p.mouse.move(起点.x, 起点.y);
      await p.mouse.down();
      await p.mouse.move(记.终点x, 起点.y, { steps: Math.max(2, Math.round(臂.dx / 2)) });
      await p.mouse.up();
      await p.waitForTimeout(1400);
    }
    记.拖后画布 = await p.evaluate(读画布);
    记.拖后节点顶 = (await 读节点()).top;
    记.节点画布坐标未变 = 记.拖后节点顶 !== null ? ((await 读节点()).tf === 找.tf) : null;
    记.实测平移x = (记.拖前画布.x !== null && 记.拖后画布.x !== null) ? +(记.拖后画布.x - 记.拖前画布.x).toFixed(1) : null;
    记.实测平移y = (记.拖前画布.y !== null && 记.拖后画布.y !== null) ? +(记.拖后画布.y - 记.拖前画布.y).toFixed(1) : null;
    记.节点屏顶变化 = (记.拖前节点顶 !== null && 记.拖后节点顶 !== null) ? +(记.拖后节点顶 - 记.拖前节点顶).toFixed(1) : null;

    const ariaWant = 臂.kind + ' node: ' + 臂.名;
    const 行 = await 备好结果行(p, [臂.名, ariaWant, 臂.kind], nid);
    if (行.错) throw new Error(行.错);
    记.点击前节点顶 = (await 读节点()).top;
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

    记.闭式预测 = +闭式(VW, VH, 找.W, 找.H, 记.点之前).toFixed(6);
    记.命中闭式 = Math.abs(记.终点 - 记.闭式预测) < 5e-5;
    if (臂.期望 !== undefined) 记.命中期望 = Math.abs(记.终点 - 臂.期望) < 5e-6;
    记.A = 臂.kind === '音频' ? +(SAFE_H - H0 * 记.终点).toFixed(3) : 0;

    log(臂.键.padEnd(4) + '｜命令dx=' + String(臂.dx).padEnd(5)
      + '｜实测translate x=' + String(记.实测平移x).padEnd(8) + 'y=' + String(记.实测平移y).padEnd(7)
      + '｜节点屏顶变化=' + String(记.节点屏顶变化).padEnd(8)
      + '｜落点=' + String(记.终点).padEnd(10) + '｜A=' + String(记.A).padEnd(9)
      + (臂.kind === '音频' ? '' : '｜对照'));
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
const 对照 = 取('W_1');
const 判定P0 = 对照 && 对照.命中期望
  ? '✅ P0：阳性对照 `文本 @1212×720` 落 `' + 对照.终点 + '` 逐字等于闭式 `1.75` ⇒ 尺子没漂'
  : '🔴 P0：阳性对照=' + (对照 ? 对照.终点 : '—') + '（期望 1.75）⇒ 本批作废';

const 档汇总 = 距离档.map((dx) => {
  const g = 好.filter((x) => x.组 === '距离' + dx && x.kind === '音频');
  return {
    dx, n: g.length, A: g.map((x) => x.A),
    实测平移x: g.map((x) => x.实测平移x),
    节点画布坐标未变: g.every((x) => x.节点画布坐标未变 === true),
    逐字相同: g.length > 1 && new Set(g.map((x) => x.A)).size === 1,
  };
});
const 锁定档 = 档汇总.filter((x) => x.逐字相同);
const 判定P1 = '📌 P1：拖动距离 `0 / 60 / 120 / 240`，每档 `n = ' + 每档臂数 + '` ⇒ `A` 逐档 = '
  + 档汇总.map((x) => '`' + x.dx + '`→[' + x.A.join(', ') + ']').join('、')
  + '｜**逐字相同的档** = ' + (锁定档.length ? 锁定档.map((x) => '`' + x.dx + '`（值 `' + x.A[0] + '`，实测平移 `' + x.实测平移x.join('/') + '`）').join('、') : '无')
  + ' ⇒ ' + (锁定档.length
    ? '✅ **门槛就在这些档里**'
    : '🔴 **全档都在散布里** ⇒ 📌 **`b323c` 的 `A ≡ 200.000` 不是拖出来的** ⇒ 📌 那一跑里除拖动外还差着别的东西（🔴 变量仍未被识别）');

const 被吃掉 = 距离档.some((dx) => {
  const 档 = 档汇总.find((x) => x.dx === dx);
  return 档.实测平移x.some((v) => v !== null && Math.abs(v) < Math.abs(dx) * 0.5);
});
const 判定P2 = '📌 P2：命令位移 vs 实测 `.react-flow__viewport` translate 的 `x` 分量逐档 = '
  + 档汇总.map((x) => '`' + x.dx + '`→[' + x.实测平移x.join(', ') + ']').join('、')
  + ' ⇒ ' + (被吃掉
    ? '🔴 **实测平移远小于命令位移** ⇒ 📌 **画布把平移吃掉了大部分**（📌 这解释了「命令拖 `120` 像素、节点屏顶只动 `4.6` 像素」）'
    : '📌 实测平移与命令位移同量级');

out.判定 = {
  有效臂: 好.length + '/' + 臂表.length,
  判定P0_尺子: 判定P0,
  判定P1_门槛: 判定P1,
  判定P2_平移地真: 判定P2,
  档汇总,
  逐臂: 好.map((x) => ({
    键: x.键, 组: x.组, dx: x.dx, z0: x.点之前, 起点: x.起点, 终点x: x.终点x,
    拖前画布: x.拖前画布, 拖后画布: x.拖后画布, 实测平移x: x.实测平移x, 实测平移y: x.实测平移y,
    节点屏顶变化: x.节点屏顶变化, 节点画布坐标未变: x.节点画布坐标未变,
    点后首读: x.点后首读, 读1: x.读1, 读2: x.读2, 读3: x.读3, 落点: x.终点,
    闭式预测: x.闭式预测, 命中闭式: x.命中闭式, A: x.A,
  })),
  失效臂: out.臂.filter((x) => x.错误).map((x) => ({ 键: x.键, 错: x.错误 })),
};
log('\n════ 判定 ════\n' + JSON.stringify({
  有效臂: out.判定.有效臂, P0: 判定P0, P1: 判定P1, P2: 判定P2, 档汇总,
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
