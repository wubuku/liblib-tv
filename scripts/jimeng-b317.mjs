/**
 * 批次 317 · 屏上有没有**屏固定**元素？—— 用坏区连测三遍的**落点互不相同**这件事去筛。
 *
 * 🔴 接批次 316（`5/5` 有效）：阈值处**没有任何元素被挂载或卸载** ——
 *    同一个 `音频 1`，`w=1210` 与 `w=1212` 的后代标识集合**逐字相同**（`20` vs `20`），
 *    文档级 `data-testid` 总数 `669` vs `669`，`position: fixed` 元素 **`0` 个**。
 *    🔴 **「多挂了一个装饰元素」被排除。**
 *    ⚠️ **但批次 316 答不了「同一元素变了尺寸」** —— 🔴 因为被解释的量本身就是全局缩放，
 *    落点一变所有元素一起缩放（节点屏盒 `560×560 → 348.5×348.5`，恰好 `320 × 落点`），
 *    📌 **对拍法对「整体缩放」天然不敏感**（立规 195 的由来）。
 *
 * 📌 **本批换个不需要换视口的筛法 —— 坏区连测本身就是天然的尺子**：
 *    🔴 批次 314/315 已证：**`w=1212` 同一个动作重复几遍，落点各不相同**（散布 `1%`–`4%`）。
 *    📌 **落点不同 ⇒ 同一个视口里，屏上同一批元素被画在了不同的大小上** ⇒
 *    📌 **这时去比元素的「屏像素尺寸」，就能把两类元素分开**：
 *      📌 **随画布缩放的元素** ⇒ 屏尺寸之比 `≈ 落点之比`（跟着缩）；
 *      📌 **屏固定元素** ⇒ 屏尺寸之比 `≈ 1`（**不跟着缩**，它在屏上一直是那么大）。
 *    ⇒ 📌 **屏固定元素的画布尺寸因此是 `K / 落点`** ⇒ 📌 那就是 `批次 306` 闭式里
 *    🔴 **少掉的那一项**：`分母本该是含屏固定装饰的 compound，而闭式用的是裸盒边长。**
 *
 * 📌 **三段设计**：
 *   **A 组（坏区三遍）**：`音频 1 @1212×720` × `3` ⇒ 📌 **落点彼此不同**才有判别力；
 *     🔴 **若三遍落点逐字相同 ⇒ 本批方法当场作废**（没有变化的尺子量不出差异），**这条判据先写死**。
 *   **B 组（好区两遍）**：`音频 1 @1210×720` × `2` ⇒ 📌 两遍落点都是 `1.75`、
 *     📌 **所有元素的屏盒也应逐字相同** ⇒ ✅ **这是采集本身可信的阳性对照**（不然后面全白测）。
 *   **C 组（阴性对照）**：`文本 1 @1212×720` ⇒ 📌 它的坏区落点是**稳定**的（批次 315），
 *     ⇒ ✅ **「屏固定元素存在」与「落点是否稳定」是两件事**，📌 这条用来防止把「稳定」误读成「没有屏固定元素」。
 *
 * 📌 **判据（测量前写死）**：
 *   **P0** B 组两遍落点都 `=== 1.75`，且两遍的**全部元素屏盒逐字相同** ⇒ 采集可信。
 *   **P1** A 组三遍落点的**自身极差 `> 1e-4`** ⇒ 否则本批方法作废（尺子没动）。
 *   **P2** A 组里存在某个 `data-testid`，其**屏宽之比 `≈ 1`** 而同时**节点屏宽之比 `≈ 落点之比`**
 *        ⇒ ✅ **找到了屏固定元素**，📌 它的名字与逐字尺寸就是本批的交付物。
 *   **P3** 阴性对照 `文本 1` 屏宽之比应**全部 `≈` 节点之比** ⇒ 🔴 若它也出现屏固定元素，
 *        📌 则「屏固定」**不是**音频/视频掉下去的原因（它与文本共有），🔴 **P2 的结论要收窄**。
 *
 * 前提检查：轴向自检 / 落定自检（三连读）/ 点击生效自检 /
 *   `aria` 精确匹配现找现量 / 参数写死 / 每臂独立浏览器 / 盒尺寸逐臂现量。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b317.json';
const 放大键 = 'Meta+Equal';
const 闭式 = (w, h, W, H, z0) => Math.min((w - 532) / W, (h - 160) / H, z0);

const 臂表 = [
  { 键: 'A坏区_1', 组: 'A', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 按: 13 },
  { 键: 'A坏区_2', 组: 'A', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 按: 13 },
  { 键: 'A坏区_3', 组: 'A', kind: '音频', 名: '音频 1', vw: 1212, vh: 720, 按: 13 },
  { 键: 'B好区_1', 组: 'B', kind: '音频', 名: '音频 1', vw: 1210, vh: 720, 按: 13, 期望: 1.75 },
  { 键: 'B好区_2', 组: 'B', kind: '音频', 名: '音频 1', vw: 1210, vh: 720, 按: 13, 期望: 1.75 },
  { 键: 'C文本_1212', 组: 'C', kind: '文本', 名: '文本 1', vw: 1212, vh: 720, 按: 13, 期望: 1.75 },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b317',
  问: '屏上有没有屏固定元素？它的画布尺寸是不是 K/落点，也就是闭式里少掉的那一项？',
  接批次316: {
    已排除: '阈值处没有任何元素被挂载或卸载（后代集合 20 vs 20、data-testid 总数 669 vs 669、position:fixed 0 个）',
    答不了的: '同一元素是否变了尺寸 —— 因为被解释的量就是全局缩放，对拍法对「整体缩放」天然不敏感',
    批次316的自身缺陷: '采集了全部 data-testid 的屏盒，却只落盘了「后代」与「fixed」两段 ⇒ 全域那段丢失，离线分析做不了',
  },
  判据: {
    P0: 'B 组两遍落点都 =1.75 且全部元素屏盒逐字相同 ⇒ 采集可信',
    P1: 'A 组三遍落点自身极差 > 1e-4 ⇒ 否则本批方法作废（尺子没动）',
    P2: '存在某 data-testid，其屏宽之比≈1 而节点屏宽之比≈落点之比 ⇒ 找到了屏固定元素',
    P3: '阴性对照 文本1 的屏宽之比应全部≈节点之比；若有屏固定元素 ⇒ P2 结论要收窄（它与文本共有）',
  },
  臂表, 臂: [], 判定: {},
};

/**
 * 📌 采集器：把**每一个** `[data-testid]` 的屏像素矩形原样带回来。
 * 🔴 批次 316 的教训：采了却不落盘 = 白采 ⇒ 📌 这一版把三段（后代 / 全域 / 盒）**全部**落盘。
 */
const 采集 = () => {
  const 号 = (e) => {
    const tid = e.getAttribute('data-testid');
    const cls = (e.getAttribute('class') || '').trim().split(/\s+/).slice(0, 2).join('.');
    return (tid ? tid : '') + '|' + (cls || e.tagName.toLowerCase());
  };
  const 矩形 = (e) => {
    const b = e.getBoundingClientRect();
    return [Math.round(b.x * 10) / 10, Math.round(b.y * 10) / 10, Math.round(b.width * 10) / 10, Math.round(b.height * 10) / 10];
  };
  const 节点 = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
    .find((x) => x.getAttribute('aria-label') === window.__找的aria);
  const 框 = (list, 标记) => list.map((e) => ({
    号: 号(e), rect: 矩形(e), pos: getComputedStyle(e).position,
    inNode: !!(节点 && 节点.contains(e)), 标: 标记 || null,
  }));
  const 全域 = 框(Array.from(document.querySelectorAll('[data-testid]')));
  const 后代 = 节点 ? 框(Array.from(节点.querySelectorAll('*')), '后代') : [];
  // 📌 节点的**直接同级**里、压在它上面的那些（compound 的真凶若在 DOM 上不是子元素，就在这里）
  const 同级 = 节点 && 节点.parentElement
    ? 框(Array.from(节点.parentElement.children).filter((x) => x !== 节点 && x.getBoundingClientRect().width > 0), '同级')
    : [];
  return {
    节点屏盒: 节点 ? 矩形(节点) : null,
    节点盒: 节点 ? { W: 节点.offsetWidth, H: 节点.offsetHeight } : null,
    选中: Array.from(document.querySelectorAll('.react-flow__node.selected')).map((x) => x.dataset.id),
    全域, 后代, 同级,
  };
};

for (const 臂 of 臂表) {
  let br = null; let p = null; let nid = null;
  const 记 = { 键: 臂.键, 组: 臂.组, kind: 臂.kind, 名: 臂.名, vw: 臂.vw, vh: 臂.vh };
  try {
    br = await chromium.launch({ headless: true });
    const ctx = await br.newContext({ storageState: STATE, viewport: { width: 臂.vw, height: 臂.vh } });
    p = await ctx.newPage();
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 60000 });
    await p.waitForTimeout(6000);

    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== 臂.vw || 实际.h !== 臂.vh) throw new Error('轴向自检失败：' + 实际.w + 'x' + 实际.h);
    if (实际.h < 249) throw new Error('视口高不足 249');

    const ariaWant = 臂.kind + ' node: ' + 臂.名;
    const 目标 = await p.evaluate((aria) => {
      const e = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
        .find((x) => x.getAttribute('aria-label') === aria);
      return e ? { id: e.dataset.id, W: e.offsetWidth, H: e.offsetHeight } : null;
    }, ariaWant);
    if (!目标) throw new Error('找不到 aria 为「' + ariaWant + '」的节点');
    nid = 目标.id;
    记.画布盒 = { W: 目标.W, H: 目标.H };

    for (let i = 0; i < 臂.按; i++) { await p.keyboard.press(放大键); await p.waitForTimeout(380); }
    await p.waitForTimeout(1600);
    const 读缩放 = () => p.evaluate(() => {
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      return m ? Number(m[1]) : null;
    });
    记.点之前 = await 读缩放();
    if (记.点之前 === null) throw new Error('点之前读不到 scale');

    const 钮 = await p.evaluate(() => {
      const b = document.querySelector('button[aria-label="搜索"]');
      if (!b) return null;
      const r = b.getBoundingClientRect();
      return { 中心: [r.x + r.width / 2, r.y + r.height / 2], 可见: r.width > 0 && r.height > 0 && r.y >= 0 && r.bottom <= innerHeight };
    });
    if (!钮 || !钮.可见) throw new Error('找不到可见的搜索钮');
    await p.mouse.click(钮.中心[0], 钮.中心[1]);
    await p.waitForTimeout(1600);

    let 行 = null;
    for (const 词 of [臂.名, ariaWant, 臂.kind]) {
      await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-search-panel"] input'); if (i) { i.focus(); i.select(); } });
      await p.keyboard.type(词, { delay: 80 });
      await p.waitForTimeout(2000);
      const sel = '[data-testid="canvas-search-result-node_' + nid.replace(/^node_/, '') + '"]';
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
      if (r && r.可见) { 行 = r; break; }
    }
    if (!行) throw new Error('搜不到「' + 臂.名 + '」的可见结果行');
    await p.mouse.click(行.中心[0], 行.中心[1]);
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

    记.闭式预测 = +闭式(臂.vw, 臂.vh, 目标.W, 目标.H, 记.点之前).toFixed(6);
    记.命中闭式 = Math.abs(记.终点 - 记.闭式预测) < 5e-5;
    if (臂.期望 !== undefined) 记.命中期望 = Math.abs(记.终点 - 臂.期望) < 5e-6;

    await p.evaluate((aria) => { window.__找的aria = aria; }, ariaWant);
    记.清单 = await p.evaluate(采集);
    记.清单.选中与目标一致 = 记.清单.选中.join(',') === nid;

    log(臂.键.padEnd(10) + '｜落点=' + String(记.终点).padEnd(10)
      + '｜闭式=' + String(记.闭式预测).padEnd(10)
      + (记.命中闭式 ? '｜✅命中' : '｜🔴不中')
      + '｜节点屏盒=' + JSON.stringify(记.清单.节点屏盒)
      + '｜全域=' + 记.清单.全域.length + '｜后代=' + 记.清单.后代.length + '｜同级=' + 记.清单.同级.length);
  } catch (e) {
    记.错误 = e.message;
    log(臂.键.padEnd(10) + '🔴 ' + e.message);
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
const A = 好.filter((x) => x.组 === 'A').sort((x, y) => x.键);
const B = 好.filter((x) => x.组 === 'B').sort((x, y) => x.键);
const C = 取('C文本_1212');

/** 📌 两臂之间：把屏宽之比分成「跟着缩」与「不跟着缩」两类 */
function 分类(甲, 乙, 字段) {
  const a = 甲.清单[字段]; const b = 乙.清单[字段];
  if (!a || !b || a.length < 2 || b.length < 2) return null;
  const mb = new Map(b.map((x) => [x.号, x]));
  const 缩放比 = 乙.终点 / 甲.终点;
  const 跟 = []; const 不跟 = [];
  for (const x of a) {
    const y = mb.get(x.号);
    if (!y) continue;
    if (x.rect[2] <= 0.5 || y.rect[2] <= 0.5) continue;
    const r = y.rect[2] / x.rect[2];
    const 偏 = r / 缩放比 - 1;
    (Math.abs(偏) < 0.02 ? 跟 : 不跟).push({ 号: x.号, 比: +r.toFixed(5), 偏: +(偏 * 100).toFixed(2), 甲: x.rect, 乙: y.rect, pos: y.pos, inNode: y.inNode, 标: y.标 });
  }
  不跟.sort((x, y) => Math.abs(y.偏) - Math.abs(x.偏));
  跟.sort((x, y) => Math.abs(y.偏) - Math.abs(x.偏));
  return { 甲: 甲.键, 乙: 乙.键, 字段, 缩放比: +缩放比.toFixed(5), 跟: 跟.length, 不跟: 不跟.length, 跟的: 跟.slice(0, 6), 不跟的: 不跟.slice(0, 14) };
}

// P0 采集可信性：B 组两遍落点都 1.75，且全部元素屏盒逐字相同
const 屏盒一致 = (() => {
  if (B.length !== 2) return null;
  const [x, y] = B;
  const f = (z) => JSON.stringify(z.清单.全域.map((e) => [e.号, e.rect]).sort());
  return f(x) === f(y);
})();
const 判定P0 = (B.length === 2 && B.every((x) => x.命中期望) && 屏盒一致)
  ? '✅ P0：B 组两遍落点都 `1.75`，且**全部元素的屏盒逐字相同** ⇒ 采集可信'
  : '🔴 P0：B 组落点=' + B.map((x) => x.终点).join('/') + '、屏盒逐字相同=' + 屏盒一致 + ' ⇒ 本批作废';

// P1 尺子有没有动
const A落 = A.map((x) => x.终点);
const A极差 = A落.length >= 2 ? +(Math.max.apply(null, A落) - Math.min.apply(null, A落)).toFixed(6) : null;
const 判定P1 = A极差 === null ? '（A 组臂不全）'
  : (A极差 > 1e-4
    ? '✅ P1：A 组三遍落点 ' + A落.join(' / ') + '，**自身极差 ' + A极差 + '** ⇒ ✅ 尺子动了，本批方法成立'
    : '🔴 P1：A 组三遍落点逐字相同（极差 ' + A极差 + '）⇒ 🔴 **尺子没动 ⇒ 本批方法当场作废**，没有变化就量不出差异');

// P2/P3 分类
const 分1 = A.length >= 2 ? 分类(A[0], A[1], '全域') : null;
const 分2 = A.length >= 2 ? 分类(A[0], A[1], '同级') : null;
const 分文 = C ? 分类(B[0], C, '全域') : null;

const 判定P2 = !分1 ? '（A 组臂不全）'
  : (分1.不跟.length
    ? '✅ P2：`音频 1` 坏区两遍之间，落点比 ' + 分1.缩放比 + '，而**有 ' + 分1.不跟.length + ' 个 `data-testid` 的屏宽之比明显偏离它** ⇒ ✅ **屏固定元素存在**；📌 前几个：'
      + JSON.stringify(分1.不跟的.slice(0, 6).map((x) => ({ 号: x.号, 比: x.比, 偏离: x.偏 + '%', inNode: x.inNode, pos: x.pos })))
    : '🔴 P2：坏区两遍之间**所有元素都跟着缩放**（' + 分1.跟 + '/' + (分1.跟 + 分1.不跟) + '）⇒ 🔴 **屏上没有屏固定元素** ⇒ 那份额另有来源');

const 判定P3 = !分文 ? '（C 组臂无效）'
  : (分文.不跟.length === 0
    ? '✅ P3：阴性对照 `文本 1` 的屏宽之比**全部跟着落点比**（' + 分文.跟 + '/' + (分文.跟 + 分文.不跟) + '）⇒ ✅ **屏固定元素是 `音频`/`视频` 独有的** ⇒ P2 的结论成立'
    : '⚠️ P3：阴性对照 `文本 1` 也有 ' + 分文.不跟.length + ' 个元素屏宽不跟缩放 ⇒ 🔴 **「屏固定」是文本共有的，不是落点掉下去的原因** ⇒ P2 结论要收窄');

out.判定 = {
  有效臂: 好.length + '/' + 臂表.length,
  判定P0_采集可信: 判定P0,
  判定P1_尺子动了: 判定P1,
  判定P2_屏固定元素: 判定P2,
  判定P3_阴性对照: 判定P3,
  分类_A组全局域: 分1,
  分类_A组同级: 分2,
  分类_文本对照: 分文,
  逐臂: 好.map((x) => ({ 键: x.键, 名: x.名, 视口: x.vw + 'x' + x.vh, z0: x.点之前, 落点: x.终点, 闭式预测: x.闭式预测, 命中闭式: x.命中闭式, 节点屏盒: x.清单.节点屏盒 })),
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
  log('末态独立复查：' + JSON.stringify(out.末态));
} finally { try { await pz.close(); await brz.close(); } catch (e) { /* 忽略 */ } }

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
process.exit(0);