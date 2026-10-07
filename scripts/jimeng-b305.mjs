/**
 * 批次 305 · 反推缺的那 `39.6`（高）/ `116.7`（宽）画布单位外框，到底是谁？
 *
 * 🔴 起意：批次 304 留了一个**没闭合的账**——
 *    `文本 1` 在 `z0 = 1.93` 落到 `1.55727`，由终点反推：
 *      高度项 `compoundH = 560/1.55727 = 359.6` ⇒ 比盒高多 **`39.6`**
 *      宽度项 `compoundW = 680/1.55727 = 436.7` ⇒ 比盒宽多 **`116.7`**
 *    而实测到的 `selection-context-toolbar` 只有 `160×40` **屏幕**像素
 *    （换算画布 `102.8 × 25.7`）⇒ 🔴 **两个数都对不上，还缺一块。**
 *
 * 📌 本批换个问法：**不再猜「哪个 testid」，而是把整个包围盒里的几何全部列出来。**
 *    依据：批次 304 的教训（立规 182）—— 用 testid 找会取到折叠空壳，
 *    🔴 **几何不会骗人：谁占了那个位置、占了多大，按矩形列一遍就知道。**
 *
 * 📌 判据（**测量前写死**）：
 *   **P1** 若盒内有元素的**并集盒**满足
 *          `多出高 ≈ 39.6` 或 `多出宽 ≈ 116.7`（容差 ±6 画布单位）
 *          ⇒ ✅ 找到了，它就是那个外框的来源；
 *   **P2** 若盒内元素并集盒明显小于反推要求 ⇒ 🔴 **外框不来自盒内元素**，
 *          📌 缺口在**布局计算里**（inset 常量 / 预留位），不在 DOM 里 ⇒ 转去读 bundle；
 *   **P3** 必须先量到**没被本次实验改变过**的量作为对照
 *          —— `文本` 盒本身的画布宽（应恒 `320`）与 `z0 = 1.34` 档（终点 == z0，不跳）
 *          🔴 **若对照臂也算出「多出 0」，则说明反推式本身在该臂不适用，
 *          此时 P1 的「多出量」不能当作缺口，要重新审视。**
 *
 * 🔴 另设**阳性对照**：同一套几何列法也扫 `音频`（批次 304 已证明其 `compoundW`
 *    与实测 `634.69` 逐字一致）⇒ **尺子必须在已知为真的对象上也报出正确的「多出量」**，
 *    否则说明这套几何量法本身偏了。
 *
 * 前提检查：轴向自检 / 落定自检 / 点击生效自检 / `aria` 精确匹配现找现量 /
 *   参数写死 / 每臂独立浏览器。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b305.json';
const 放大键 = 'Meta+Equal';
const w = 1212;

/** 📌 缺口的两个候选量（来自批次 304 的反推，写死当判据基准） */
const 缺口高 = 39.6;
const 缺口宽 = 116.7;
const 容差 = 6;

const 臂表 = [
  { 键: '文本1/11', kind: '文本', 名: '文本 1', 按: 11, 角色: '主测' },
  { 键: '文本1/9', kind: '文本', 名: '文本 1', 按: 9, 角色: '对照(不跳)' },
  { 键: '音频1/11', kind: '音频', 名: '音频 1', 按: 11, 角色: '阳性对照' },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b305',
  问: '反推缺的那 39.6（高）/116.7（宽）画布单位外框，盒内几何能不能把它找出来？',
  判据: {
    P1: `盒内并集盒的多出高≈${缺口高} 或 多出宽≈${缺口宽}（±${容差}）⇒ 找到了`,
    P2: '并集盒明显小于反推要求 ⇒ 外框不在盒内 DOM，在布局计算里',
    P3: '对照臂(不跳)的多出量必须≈0，否则反推式在该臂不适用',
  },
  缺口高, 缺口宽, 容差, w, 臂表, 臂: [], 判定: {},
};

for (const A of 臂表) {
  let br = null; let p = null; let nid = null;
  const 记 = { 键: A.键, w, 按: A.按, kind: A.kind, 名: A.名, 角色: A.角色 };
  try {
    br = await chromium.launch({ headless: true });
    const ctx = await br.newContext({ storageState: STATE, viewport: { width: w, height: 720 } });
    p = await ctx.newPage();
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 60000 });
    await p.waitForTimeout(6000);
    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== w || 实际.h !== 720) throw new Error(`轴向自检失败：实测 ${实际.w}×${实际.h}`);

    const ariaWant = `${A.kind} node: ${A.名}`;
    const 目标 = await p.evaluate((aria) => {
      const e = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
        .find((x) => x.getAttribute('aria-label') === aria);
      return e ? { id: e.dataset.id, W: e.offsetWidth, H: e.offsetHeight } : null;
    }, ariaWant);
    if (!目标) throw new Error(`找不到 aria 为「${ariaWant}」的节点`);
    nid = 目标.id;
    记.画布盒 = { W: 目标.W, H: 目标.H };

    for (let i = 0; i < A.按; i++) { await p.keyboard.press(放大键); await p.waitForTimeout(380); }
    await p.waitForTimeout(1400);
    const 读缩放 = () => p.evaluate(() => {
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      return m ? Number(m[1]) : null;
    });
    const z0 = await 读缩放();
    记.z0 = z0;
    if (z0 === null) throw new Error('读不到缩放');
    if (!(z0 > 0.5)) throw new Error(`z0(${z0}) 低于 .5，无法观察`);

    const 钮 = await p.evaluate(() => {
      const b = document.querySelector('button[aria-label="搜索"]');
      if (!b) return null;
      const r = b.getBoundingClientRect();
      return { 中心: [r.x + r.width / 2, r.y + r.height / 2], 可见: r.width > 0 && r.height > 0 && r.y >= 0 && r.bottom <= innerHeight };
    });
    if (!钮 || !钮.可见) throw new Error('找不到可见的搜索钮');
    await p.mouse.click(钮.中心[0],钮.中心[1]);
    await p.waitForTimeout(1600);

    let 行 = null; let 用名 = null;
    for (const 名 of [A.名, ariaWant, A.kind]) {
      await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-search-panel"] input'); if (i) { i.focus(); i.select(); } });
      await p.keyboard.type(名, { delay: 80 });
      await p.waitForTimeout(2000);
      const sel = `[data-testid="canvas-search-result-node_${nid.replace(/^node_/, '')}"]`;
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
      if (r && r.可见) { 行 = r; 用名 = 名; break; }
    }
    if (!行) throw new Error(`搜不到「${A.名}」的可见结果行`);
    记.用名 = 用名;
    await p.mouse.click(行.中心[0], 行.中心[1]);
    await p.waitForTimeout(3200);
    const a1 = await 读缩放();
    await p.waitForTimeout(2600);

    // 🔴 核心：按**几何**列盒内所有元素（不看 testid），并把盒自身也列进去当基准
    const 面 = await p.evaluate(({ nid }) => {
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      const z = m ? Number(m[1]) : null;
      const 选 = Array.from(document.querySelectorAll('.react-flow__node.selected')).map((x) => x.dataset.id);
      const 节点 = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      if (!节点) return { 错: '选中后节点不在 DOM 里' };
      const nb = 节点.getBoundingClientRect();
      // 📌 盒自身：以画布坐标量（除以 z），不受屏幕像素取整影响
      const 盒 = { W: 节点.offsetWidth, H: 节点.offsetHeight };
      // 📌 元素池：**只取带 testid 的元素**（手册要写可追溯的 UI 标识），
      //    并把节点自身与其内部后代排除掉 —— 它们是「盒的内容」不是「盒的外框」，
      //    📌 否则盒内会塞满几十个零件，并集盒必然等于盒本身，多出量恒为 0，量法就废了。
      const 池 = Array.from(document.querySelectorAll('[data-testid]'))
        .filter((e) => e !== 节点 && !节点.contains(e));
      const 候选 = [];
      for (const e of 池) {
        const r = e.getBoundingClientRect();
        if (r.width <= 0 || r.height <= 0) continue;
        // 📌 与节点盒**有交叠**才算「在盒子里/贴在盒上」
        const 交x = Math.max(0, Math.min(r.right, nb.right) - Math.max(r.left, nb.left));
        const 交y = Math.max(0, Math.min(r.bottom, nb.bottom) - Math.max(r.top, nb.top));
        if (交x <= 0 || 交y <= 0) continue;
        候选.push({
          testid: e.getAttribute('data-testid'),
          屏: { x: +r.x.toFixed(1), y: +r.y.toFixed(1), w: +r.width.toFixed(1), h: +r.height.toFixed(1) },
          画布: { w: +(r.width / z).toFixed(3), h: +(r.height / z).toFixed(3) },
          盒内: { x: +(r.x - nb.x).toFixed(1), y: +(r.y - nb.y).toFixed(1) },
          在盒内: r.x >= nb.x - 0.6 && r.y >= nb.y - 0.6 && r.right <= nb.right + 0.6 && r.bottom <= nb.bottom + 0.6,
          遮挡盒面积比: +((交x * 交y) / (nb.width * nb.height)).toFixed(3),
        });
      }
      return {
        终点: z, 选中: 选, 盒, 节点屏: { w: +nb.width.toFixed(1), h: +nb.height.toFixed(1), x: +nb.x.toFixed(1), y: +nb.y.toFixed(1) },
        候选: 候选.sort((a, b) => b.遮挡盒面积比 - a.遮挡盒面积比),
      };
    }, { nid });
    if (面.错) throw new Error(面.错);

    记.终点 = 面.终点;
    记.落定 = a1 === 面.终点;
    记.点击生效 = (面.选中 || []).includes(nid);
    if (!记.点击生效) throw new Error(`点击未生效（选中=${JSON.stringify(面.选中)}）`);
    记.盒 = 面.盒;
    记.节点屏 = 面.节点屏;
    记.候选 = 面.候选;

    // 📌 反推：由终点算宽度项/高度项要求的 compound
    // 📌 safeW / safeH 的来历（写死，勿临时改）：
    //    safeW = w - 532 = 1212 - 532 = 680  ← 批次 303/304 已用它反推并逐字对账成功
    //    safeH = h - 160 = 720 - 160 = 560   ← 批次 304 用的高度项分母就是 560
    const safeW = w - 532;
    const safeH = 720 - 160;
    记.safeW = safeW; 记.safeH = safeH;
    记.反推compoundW = +(safeW / 面.终点).toFixed(3);
    记.反推compoundH = +(safeH / 面.终点).toFixed(3);
    记.缺口宽实测 = +(记.反推compoundW - 面.盒.W).toFixed(3);
    记.缺口高实测 = +(记.反推compoundH - 面.盒.H).toFixed(3);
    记.与起点逐字相同 = 面.终点 === z0;

    // 📌 并集盒：把所有候选（屏坐标）合起来，比节点盒多多少（屏像素），再换算画布
    if (面.候选.length > 0) {
      let L = Infinity, T = Infinity, R = -Infinity, B = -Infinity;
      for (const c of 面.候选) { L = Math.min(L, c.屏.x); T = Math.min(T, c.屏.y); R = Math.max(R, c.屏.x + c.屏.w); B = Math.max(B, c.屏.y + c.屏.h); }
      记.并集屏 = { x: +L.toFixed(1), y: +T.toFixed(1), w: +(R - L).toFixed(1), h: +(B - T).toFixed(1) };
      记.并集画布 = { w: +((R - L) / 面.终点).toFixed(3), h: +((B - T) / 面.终点).toFixed(3) };
      记.并集多出宽 = +((R - L) / 面.终点 - 面.盒.W).toFixed(3);
      记.并集多出高 = +((B - T) / 面.终点 - 面.盒.H).toFixed(3);
    } else {
      记.并集屏 = null; 记.并集画布 = null; 记.并集多出宽 = null; 记.并集多出高 = null;
    }

    // 📌 只把「严格在盒内」的元素再算一遍并集（排除贴在下方的工具条等）
    const 内 = 面.候选.filter((c) => c.在盒内);
    记.盒内候选数 = 内.length;
    记.盒内testid = 内.map((c) => c.testid);
    if (内.length > 0) {
      let L = Infinity, T = Infinity, R = -Infinity, B = -Infinity;
      for (const c of 内) { L = Math.min(L, c.屏.x); T = Math.min(T, c.屏.y); R = Math.max(R, c.屏.x + c.屏.w); B = Math.max(B, c.屏.y + c.屏.h); }
      记.盒内并集画布 = { w: +((R - L) / 面.终点).toFixed(3), h: +((B - T) / 面.终点).toFixed(3) };
      记.盒内多出宽 = +((R - L) / 面.终点 - 面.盒.W).toFixed(3);
      记.盒内多出高 = +((B - T) / 面.终点 - 面.盒.H).toFixed(3);
    } else { 记.盒内并集画布 = null; 记.盒内多出宽 = null; 记.盒内多出高 = null; }

    const 宽命中 = Math.abs(记.缺口宽实测 - 缺口宽) <= 容差;
    const 高命中 = Math.abs(记.缺口高实测 - 缺口高) <= 容差;
    记.宽项命中 = 宽命中;
    记.高项命中 = 高命中;
    记.并集宽命中 = 记.并集多出宽 !== null && Math.abs(记.并集多出宽 - 缺口宽) <= 容差;
    记.并集高命中 = 记.并集多出高 !== null && Math.abs(记.并集多出高 - 缺口高) <= 容差;

    log(`${A.键.padEnd(10)}｜z0=${String(z0).padEnd(8)}｜终点=${String(面.终点).padEnd(10)}｜盒=${面.盒.W}×${面.盒.H}｜缺口宽=${记.缺口宽实测} 缺口高=${记.缺口高实测}｜并集多出 ${记.并集多出宽}×${记.并集多出高}｜盒内多出 ${记.盒内多出宽}×${记.盒内多出高}｜盒内testid=${JSON.stringify(记.盒内testid)}`);
  } catch (e) {
    记.错误 = e.message;
    log(`${A.键.padEnd(10)}🔴 ${e.message}`);
  } finally {
    try { if (p) await p.close(); } catch (e) { /* 忽略 */ }
    try { if (br) await br.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

const 好 = out.臂.filter((x) => !x.错误 && x.点击生效 && x.终点 !== undefined && x.落定);
const 主 = 好.find((x) => x.角色 === '主测');
const 阴 = 好.find((x) => x.角色 === '对照(不跳)');
const 阳 = 好.find((x) => x.角色 === '阳性对照');

log('\n════ 候选元素全表 ════');
for (const x of 好) {
  log(`\n── ${x.键}（${x.kind}，终点 ${x.终点}，盒 ${x.盒.W}×${x.盒.H}）`);
  for (const c of (x.候选 || []).slice(0, 14)) {
    log(`   ${String(c.遮挡盒面积比).padStart(6)}  ${c.testid.padEnd(44)} 屏 ${c.屏.w}×${c.屏.h}  画布 ${c.画布.w}×${c.画布.h}  ${c.在盒内 ? '盒内' : '盒外(交叠)'}`);
  }
}

let P1 = null; let P2 = null; let P3 = null; let 阳性 = null;
if (主) {
  if (主.并集宽命中) P1 = `✅ P1：并集盒多出宽 ${主.并集多出宽} ≈ ${缺口宽} ⇒ 找到了（占用者：${(主.候选 || []).filter((c) => c.遮挡盒面积比 > 0.02).map((c) => `${c.testid}(${c.画布.w}×${c.画布.h})`).slice(0, 6).join(' + ')}）`;
  else if (主.并集高命中) P1 = `✅ P1：并集盒多出高 ${主.并集多出高} ≈ ${缺口高} ⇒ 找到了`;
  else P1 = `🔴 P1 未命中：并集多出 ${主.并集多出宽}×${主.并集多出高}，盒内多出 ${主.盒内多出宽}×${主.盒内多出高}，与 ${缺口宽}/${缺口高} 都不吻合`;

  const 宽差 = 主.并集多出宽 === null ? 999 : Math.abs(主.并集多出宽 - 缺口宽);
  const 高差 = 主.并集多出高 === null ? 999 : Math.abs(主.并集多出高 - 缺口高);
  P2 = (宽差 > 容差 && 高差 > 容差)
    ? `✅ P2：并集多出 ${主.并集多出宽}×${主.并集多出高} 明显小于反推要求的 ${缺口宽}×${缺口高} ⇒ 🔴 外框不来自盒内带 testid 的元素，缺口在布局计算里（inset/预留位），不在 DOM 里`
    : '（P2 未触发：并集已命中）';
} else {
  P1 = '（主测臂无效）'; P2 = '（主测臂无效）';
}
if (阴) {
  const 阴差 = (阴.并集多出宽 === null) ? 999 : Math.abs(阴.并集多出宽 - 缺口宽);
  P3 = 阴.与起点逐字相同
    ? `✅ P3：对照臂(终点 ${阴.终点} 逐字等于 z0 ${阴.z0}，即不跳)并集多出 ${阴.并集多出宽}×${阴.并集多出高}，未命中 ${缺口宽} ⇒ 量法能区分「跳」与「不跳」，${阴差 <= 容差 ? '⚠️ 但它也命中了，反推式在该臂需重审' : '反推式在该臂未被触发，符合预期'}`
    : `⚠️ P3：对照臂终点 ${阴.终点} ≠ z0 ${阴.z0}，本该不跳却跳了 ⇒ 该臂无效，需复查`;
} else {
  P3 = '（对照臂无效）';
}
if (阳) {
  阳性 = `阳性对照(音频)：缺口宽 ${阳.缺口宽实测}、缺口高 ${阳.缺口高实测}；并集多出 ${阳.并集多出宽}×${阳.并集多出高}；盒内多出 ${阳.盒内多出宽}×${阳.盒内多出高}。${阳.盒内testid && 阳.盒内testid.length ? `盒内 testid=${JSON.stringify(阳.盒内testid)}` : '盒内无带 testid 元素'}`;
}

out.判定 = {
  有效臂: `${好.length}/${臂表.length}`,
  P1_主测: P1, P2_缺口不在盒内DOM: P2, P3_反推式适用边界: P3, 阳性对照: 阳性,
  主测缺口宽: 主 ? 主.缺口宽实测 : null,
  主测缺口高: 主 ? 主.缺口高实测 : null,
  主测并集多出: 主 ? `${主.并集多出宽}×${主.并集多出高}` : null,
  主测盒内多出: 主 ? `${主.盒内多出宽}×${主.盒内多出高}` : null,
  主测盒内testid: 主 ? 主.盒内testid : null,
  对照_不跳_并集多出: 阴 ? `${阴.并集多出宽}×${阴.并集多出高}（终点 ${阴.终点} vs z0 ${阴.z0}）` : null,
};
log('\n════ 判定 ════\n' + JSON.stringify(out.判定, null, 1));

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
  log('末态独立复查：', JSON.stringify(out.末态));
} finally { try { await pz.close(); await brz.close(); } catch (e) { /* 忽略 */ } }

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入', OUT);
process.exit(0);