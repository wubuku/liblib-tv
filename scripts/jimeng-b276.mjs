/**
 * 批次 276：去量立规 155 点名的**那半个盲点** —— 动作前 / 动作中 / 动作后三份快照。
 *
 * 📌 起意（批次 275 的结论 + 它自己写下的盲点）：
 *   273/274/275 三轮量纲换了三套，结论一路收紧到
 *   「`w = 373 → 374` 之间，**外框层、样式层都没有任何 `2px` 变化**」。
 *   🔴 但这三轮**全部只在「页面加载后、点任何东西之前」取样**，
 *   而那个 `2px` 台阶是**点完搜索结果行、相机取景之后**读 `.react-flow__viewport` 的 scale 测到的。
 *   ⇒ **动作本身可能改变被量的那个容器**（搜索面板打开会挤压画布容器），
 *     而那正是要找的东西 ⇒ 静止态的三份快照**结构上够不着**。
 *
 * 📌 **本批量什么**（每相位一份整棵 DOM 的逐元素快照）：
 *   `offsetWidth/clientWidth/offsetHeight/clientHeight/scrollWidth/scrollHeight/offsetLeft/offsetTop`
 *   ＋ `padding/margin/border/gap/left/right`（整数样式层，批次 275 的量纲）
 *   ⇒ **两种量纲在同一相位里一起量**，谁先出现 `2px` 就记谁。
 *
 * 📌 **四个相位**：
 *   A `动作前`　　—— 页面加载完、没点任何东西
 *   B `动作中`　　—— **搜索面板已开、结果行还没点**（立规 155 点名的那个瞬间）
 *   C `动作后`　　—— 已点结果行、相机取景完成
 *   D `动作后·面板已收` —— 按两次 Escape 之后（看容器会不会回来）
 *
 * 📌 **噪声底对照**（立规 153/154）：
 *   跨宽度比的是**同一相位内**的差：`374 − 373`（1px）与 `375 − 372`（3px）。
 *   若「动作前」的容器宽两档都 `+1`、而「动作中」变成 `+3` ⇒ **量纲换对了、有信号**；
 *   反之三相位都 `+1` ⇒ 面板打开**没有**引入台阶，`2px` 另有出处。
 *
 * 📌 **预测先写死**（立规 129/130，不允许看到实测再改）：
 *   H1 容器在面板打开时于 `w=374` 多跳 `2px`：动作中 pane 宽 `Δ(374−373)=+3`，动作前 `=+1`。
 *   H2 三相位都不跳：三个 `Δ` 全部 `=+1` ⇒ 台阶不来自容器宽度。
 *   H3 台阶在面板自己身上：面板宽 `Δ(374−373)=+3`（容器相应少 `3`）。
 *
 * 📌 **三条纪律**：只读（不新建/不删除/不上传/不分享/不进扣费页/绝不点生成）；
 *   每臂开新页；末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b276.mjs      （落盘 /tmp/b276.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B276_OUT || '/tmp/b276.json';
const 宽度组 = [[372, 244], [373, 244], [374, 244], [375, 244]];
const 帧数 = 3, 帧间隔 = 400;
const 节点id = 'node_tadm1nyykc';        // 音频 68（批次 272 在 w=360–380 用它测过异常分支）
const 节点名 = '音频 68';

const 整数量 = [
  'offsetWidth', 'clientWidth', 'offsetHeight', 'clientHeight',
  'scrollWidth', 'scrollHeight', 'offsetLeft', 'offsetTop',
];
/**
 * 🔴 v1 的教训（这一段是本文件修过的地方，别改回去）：
 *   v1 把 `offsetWidth` 之类当成 CSS 属性去 `getComputedStyle(el)[a]` 取，
 *   读回来全是 `undefined` → `parseFloat` → `NaN` → 落盘成空串
 *   ⇒ **整数量纲八个字段全部是空的**，而汇总里 `容器宽 = 0` 就是这么来的。
 *   ——**不是「容器宽为 0」，是「容器宽一次都没被量到」**。
 *   ⇒ `offsetWidth` / `clientWidth` / `scrollWidth` / `offsetLeft` 这些
 *   是 **DOM 属性**，只能直接读 `el.offsetWidth`；只有 CSS 属性才走 `getComputedStyle`。
 *   📕 一般形态：**量纲自己报错时，输出往往长得像「测到了 0」而不是「没测到」。**
 *   判据：报「零」之前，先确认这一列**不是恒定空串**。
 */
const 样式量 = [
  'paddingLeft', 'paddingRight', 'paddingTop', 'paddingBottom',
  'marginLeft', 'marginRight', 'marginTop', 'marginBottom',
  'borderLeftWidth', 'borderRightWidth', 'borderTopWidth', 'borderBottomWidth',
  'gap', 'columnGap', 'rowGap', 'left', 'right',
];
const 属性 = [...整数量, ...样式量];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b276',
  问: '取景那一刻 react-flow 读到的容器尺寸，是否在 w=374 处差 2px？',
  预测: {
    H1: '动作中容器宽 Δ(374−373)=+3 而动作前 =+1',
    H2: '三个相位的 Δ 全部 =+1 ⇒ 台阶不来自容器宽度',
    H3: '面板自身宽 Δ(374−373)=+3',
  },
  宽度组, 节点id, 节点名, 整数量, 样式量, 臂: [], 收尾: {},
};

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

const 取一帧 = (p) => p.evaluate((attrs) => {
  // 🔴 `page.evaluate` 只能看见**传进去的**参数，看不见 Node 侧的模块变量。
  //    v2 死过一次（`样式量 is not defined`，四臂全废）。这里从入参切片推导，别改回引用外部变量。
  const 样式量 = attrs.slice(8);   // 整数量纲固定 8 个在前
  const 路径 = (el) => {
    const parts = [];
    let e = el;
    while (e && e.nodeType === 1) {
      const par = e.parentElement;
      let i2 = 1;
      if (par) i2 = Array.from(par.children).filter((c) => c.nodeType === 1 && c.tagName === e.tagName).indexOf(e) + 1;
      parts.unshift(`${e.tagName}:${i2}`);
      e = par;
    }
    return parts.join('>');
  };
  const o = { _路径: {}, _相机: null, _面板: null };
  document.querySelectorAll('*').forEach((el) => {
    const cs = getComputedStyle(el);
    const v = [
      el.offsetWidth, el.clientWidth, el.offsetHeight, el.clientHeight,
      el.scrollWidth, el.scrollHeight, el.offsetLeft, el.offsetTop,
    ];
    for (const a of 样式量) {
      const x = parseFloat(cs[a]);
      v.push(Number.isFinite(x) ? +x.toFixed(2) : '');
    }
    o[路径(el)] = v.join(',');
  });
  o._路径.reactFlow = 路径(document.querySelector('.react-flow'));
  o._路径.pane = 路径(document.querySelector('.react-flow__pane'));
  o._路径.renderer = 路径(document.querySelector('.react-flow__renderer'));
  o._路径.viewport = 路径(document.querySelector('.react-flow__viewport'));
  o._路径.section = 路径(document.querySelector('SECTION'));
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const t = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(vp.style.transform || '') : null;
  o._相机 = { scale: m ? Number(m[1]) : null, tx: t ? Number(t[1]) : null, ty: t ? Number(t[2]) : null };
  const pn = document.querySelector('[data-testid="canvas-search-panel"]');
  if (pn) { const r = pn.getBoundingClientRect(); o._面板 = { 路径: 路径(pn), offsetWidth: pn.offsetWidth, clientWidth: pn.clientWidth, 屏宽: +r.width.toFixed(2) }; }
  return o;
}, 属性);

const 融帧 = (帧) => {
  const 稳定 = {}, 标记 = {}, 相机 = [], 面板 = [];
  let 不稳定 = 0;
  const 键集 = Object.keys(帧[0]);
  for (const k of 键集) {
    if (k.startsWith('_')) continue;
    const v0 = 帧[0][k];
    if (帧.every((f) => f[k] === v0)) 稳定[k] = v0; else 不稳定++;
  }
  for (const f of 帧) { 相机.push(f._相机); 面板.push(f._面板); }
  标记.reactFlow = 帧[0]._路径.reactFlow;
  标记.pane = 帧[0]._路径.pane;
  标记.renderer = 帧[0]._路径.renderer;
  标记.viewport = 帧[0]._路径.viewport;
  标记.section = 帧[0]._路径.section;
  const 相机稳定 = 相机.every((x) => JSON.stringify(x) === JSON.stringify(相机[0])) ? 相机[0] : null;
  const 面板稳定 = 面板.every((x) => JSON.stringify(x) === JSON.stringify(面板[0])) ? 面板[0] : null;
  // 🔴 前提检查（v1 就是死在这里）：整数量纲八个字段**必须真的被量到**。
  //    恒为空串 ⇒ 不是「量到 0」，是「没量到」⇒ 整组读数作废。
  let 检查样本 = 0, 整数量非空 = 0;
  for (const k of Object.keys(稳定)) {
    if (检查样本++ >= 200) break;
    const a = 稳定[k].split(',');
    if (a.length !== 属性.length) continue;
    if (整数量.some((_, i) => a[i] !== '')) 整数量非空++;
  }
  const 整数量可用 = 检查样本 > 0 && 整数量非空 / 检查样本 > 0.9;
  return {
    稳定, 标记, 相机: 相机稳定, 相机逐帧: 相机, 面板: 面板稳定,
    元素总数: 键集.length, 稳定数: Object.keys(稳定).length, 不稳定元素数: 不稳定,
    前提检查: { 取样元素数: 检查样本, 整数量非空元素数: 整数量非空, 整数量可用 },
  };
};

const 取相位 = async (p, 名) => {
  const 帧 = [];
  for (let i = 0; i < 帧数; i++) { 帧.push(await 取一帧(p)); await p.waitForTimeout(帧间隔); }
  const 融 = 融帧(帧);
  融.相位 = 名;
  log(`    [${名}] 元素 ${融.元素总数}｜跨 ${帧数} 帧稳定 ${融.稳定数}｜不稳定 ${融.不稳定元素数}｜scale ${融.相机?.scale ?? '—'}｜面板 ${融.面板 ? 融.面板.offsetWidth + 'px' : '未开'}｜整数量可用 ${融.前提检查.整数量可用 ? '✅' : '🔴'}`);
  if (!融.前提检查.整数量可用) throw new Error(`前提检查失败：整数量纲可用率 ${融.前提检查.整数量非空元素数}/${融.前提检查.取样元素数} ⇒ 读数作废`);
  return 融;
};

for (const [宽, 高] of 宽度组) {
  const p = await ctx.newPage();
  const 键 = `${宽}x${高}`;
  const 记 = { 键, 宽, 高, 相位: {} };
  try {
    await p.setViewportSize({ width: 宽, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(6000);

    // 轴向自检（立规 153 的教训）：内宽/内高必须逐字等于我打算设的
    const 实际 = await p.evaluate(() => ({ w: window.innerWidth, h: window.innerHeight }));
    if (实际.w !== 宽 || 实际.h !== 高) throw new Error(`轴向自检失败：要 ${宽}×${高}，实测 ${实际.w}×${实际.h}`);
    记.实际视口 = 实际;

    // ── 相位 A：动作前（没点任何东西）──
    记.相位.A_动作前 = await 取相位(p, 'A_动作前');

    // ── 打开搜索面板（动作本身）──
    const 钮 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('button, [role="button"]')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return { 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 盒: [r.width, r.height], 在视口内: r.y >= 0 && r.bottom <= innerHeight };
    });
    记.搜索钮 = 钮;
    if (!钮 || !钮.盒 || !钮.盒[1]) { 记.结论 = '找不到搜索钮'; log(`${键} 🔴 ${记.结论}`); out.臂.push(记); await p.close(); continue; }
    await p.mouse.click(钮.中心[0], 钮.中心[1]);
    await p.waitForTimeout(1800);

    const 面板已开 = await p.evaluate(() => !!document.querySelector('[data-testid="canvas-search-panel"]'));
    记.面板已开 = 面板已开;
    if (!面板已开) { 记.结论 = '搜索面板没打开'; log(`${键} 🔴 ${记.结论}`); out.臂.push(记); await p.close(); continue; }

    // ── 相位 B：动作中（面板已开、结果行还没点）—— 立规 155 点名的那个瞬间 ──
    记.相位.B_动作中 = await 取相位(p, 'B_动作中');

    // ── 输入并定位结果行（仍然不点）──
    const 短名 = 节点id.replace(/^node_/, '');
    await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-search-panel"] input'); if (i) { i.focus(); i.select(); } });
    await p.keyboard.type(节点名, { delay: 85 });
    await p.waitForTimeout(2200);
    const 行 = await p.evaluate((nid) => {
      const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
      if (!e) return { 有行: false };
      const r = e.getBoundingClientRect();
      return { 有行: true, 盒: [Math.round(r.width), Math.round(r.height)], 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 在视口内: r.y >= 0 && r.bottom <= innerHeight && r.x >= 0 && r.right <= innerWidth, 可见: r.width > 0 && r.height > 0 };
    }, 短名);
    记.结果行 = 行;
    if (!行.有行 || !行.可见 || !行.在视口内) {
      记.结论 = !行.有行 ? '搜不到那一行' : !行.可见 ? '结果行零尺寸' : '结果行在视口外';
      log(`${键} ⚠️ ${记.结论}`);
      out.臂.push(记); await p.close(); continue;
    }

    // ── 点结果行 → 相机取景 ──
    await p.mouse.click(行.中心[0], 行.中心[1]);
    await p.waitForTimeout(5000);

    // ── 相位 C：动作后（已取景）──
    记.相位.C_动作后 = await 取相位(p, 'C_动作后');
    记.落点 = 记.相位.C_动作后.相机?.scale ?? null;

    // ── 相位 D：按两次 Escape 收掉面板 ──
    await p.keyboard.press('Escape'); await p.waitForTimeout(700);
    await p.keyboard.press('Escape'); await p.waitForTimeout(1200);
    记.相位.D_面板已收 = await 取相位(p, 'D_面板已收');

    // 从稳定快照里取出各关键容器的整数外框
    const 取 = (融, 名) => {
      const r = {};
      for (const [k, v] of Object.entries(融.标记)) if (k !== 'viewport' && 融.稳定[v]) {
        const a = 融.稳定[v].split(',');
        r[k] = { offsetWidth: +a[0], clientWidth: +a[1], offsetHeight: +a[2], clientHeight: +a[3] };
      }
      r.相机 = 融.相机;
      r.面板 = 融.面板;
      return r;
    };
    for (const 相 of ['A_动作前', 'B_动作中', 'C_动作后', 'D_面板已收']) 记.容器 = { ...(记.容器 || {}), [相]: 取(记.相位[相], 相) };

    记.结论 = '✅ 四相位齐';
    log(`${键} 落点 ${记.落点}｜pane 宽 A=${记.容器.A_动作前?.pane?.offsetWidth} B=${记.容器.B_动作中?.pane?.offsetWidth} C=${记.容器.C_动作后?.pane?.offsetWidth} D=${记.容器.D_面板已收?.pane?.offsetWidth}`);
  } catch (e) {
    记.结论 = e.message;
    log(`${键} 🔴 ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

// ═══ 汇总：同相位内跨宽度比 ═══
const 相位表 = ['A_动作前', 'B_动作中', 'C_动作后', 'D_面板已收'];
const by键 = Object.fromEntries(out.臂.map((a) => [a.键, a]));
out.汇总 = { 各臂结论: out.臂.map((a) => ({ 键: a.键, 结论: a.结论, 落点: a.落点 ?? null })), 相位: {} };

for (const 相 of 相位表) {
  const 行 = out.汇总.相位[相] = {};
  for (const [名, 量] of [['reactFlow', 'reactFlow'], ['pane', 'pane'], ['renderer', 'renderer'], ['section', 'section']]) {
    const 宽表 = {};
    for (const a of out.臂) 宽表[a.键] = a.容器?.[相]?.[量]?.offsetWidth ?? null;
    行[名] = {
      逐宽: 宽表,
      Δ_374减373: 宽表['374x244'] != null && 宽表['373x244'] != null ? 宽表['374x244'] - 宽表['373x244'] : null,
      Δ_375减372_对照: 宽表['375x244'] != null && 宽表['372x244'] != null ? 宽表['375x244'] - 宽表['372x244'] : null,
      面板宽: Object.fromEntries(out.臂.map((a) => [a.键, a.容器?.[相]?.面板?.offsetWidth ?? null])),
      相机: Object.fromEntries(out.臂.map((a) => [a.键, a.容器?.[相]?.相机?.scale ?? null])),
    };
  }
}

log('\n════ 同相位内跨宽度：容器宽 Δ（1px 档 vs 3px 档对照）════');
for (const 相 of 相位表) {
  log(`\n--- ${相} ---`);
  for (const 名 of ['reactFlow', 'pane', 'renderer', 'section']) {
    const r = out.汇总.相位[相][名];
    log(`  ${名.padEnd(10)} 逐宽 ${JSON.stringify(r.逐宽)}｜Δ(374−373)=${r.Δ_374减373}｜Δ(375−372)=${r.Δ_375减372_对照}`);
  }
  log(`  面板宽     ${JSON.stringify(out.汇总.相位[相].pane.面板宽)}`);
  log(`  相机 scale ${JSON.stringify(out.汇总.相位[相].pane.相机)}`);
}

// ═══ 逐元素跨宽度 diff（分相位、分量纲）═══
// 找的还是同一个东西：w=373 → 374 之间，**变化量恰为 2** 的元素有几个。
// 现在按量纲分开报：整数量纲（外框）vs 样式量纲（padding/margin/border/gap/left/right）。
const 元素diff = (相, a键, b键) => {
  const A = by键[a键]?.相位[相]?.稳定, B = by键[b键]?.相位[相]?.稳定;
  if (!A || !B) return { 错误: `缺快照 ${a键}/${b键}` };
  const 整数恰2 = [], 样式恰2 = [], 整数变 = [], 样式变 = [];
  for (const k of new Set([...Object.keys(A), ...Object.keys(B)])) {
    const a = (A[k] || '').split(','), b = (B[k] || '').split(',');
    if (a.length !== 属性.length || b.length !== 属性.length) continue;
    for (let i = 0; i < 属性.length; i++) {
      if (a[i] === b[i] || a[i] === '' || b[i] === '') continue;
      const d = +(b[i] - a[i]);
      const 名 = 属性[i], 是整数 = i < 整数量.length;
      (是整数 ? 整数变 : 样式变).push({ 路径: k, 量: 名, 从: a[i], 到: b[i], 差: d });
      if (Math.abs(d) === 2) (是整数 ? 整数恰2 : 样式恰2).push({ 路径: k, 量: 名, 从: a[i], 到: b[i] });
    }
  }
  const 直方 = (arr) => {
    const h = {};
    for (const e of arr) h[e.差] = (h[e.差] || 0) + 1;
    return Object.fromEntries(Object.entries(h).sort((x, y) => Math.abs(+x[0]) - Math.abs(+y[0])).slice(0, 12));
  };
  return {
    整数维度变化数: 整数变.length, 整数维度恰为2: 整数恰2.length,
    样式维度变化数: 样式变.length, 样式维度恰为2: 样式恰2.length,
    整数差直方图: 直方(整数变), 样式差直方图: 直方(样式变),
    整数恰2明细: 整数恰2.slice(0, 20), 样式恰2明细: 样式恰2.slice(0, 20),
    整数变明细: 整数变.slice(0, 25),
  };
};

out.元素diff = {};
for (const 相 of 相位表) {
  out.元素diff[相] = {
    '1px_373对374': 元素diff(相, '373x244', '374x244'),
    '3px_372对375_对照': 元素diff(相, '372x244', '375x244'),
  };
  const d1 = out.元素diff[相]['1px_373对374'], d3 = out.元素diff[相]['3px_372对375_对照'];
  log(`\n--- 逐元素 diff @${相} ---`);
  log(`  1px(373→374)：整数维度变化 ${d1.整数维度变化数}（恰2 = ${d1.整数维度恰为2}）｜样式维度变化 ${d1.样式维度变化数}（恰2 = ${d1.样式维度恰为2}）｜整数差直方 ${JSON.stringify(d1.整数差直方图)}`);
  log(`  3px(372→375) 对照：整数维度变化 ${d3.整数维度变化数}（恰2 = ${d3.整数维度恰为2}）｜样式维度变化 ${d3.样式维度变化数}（恰2 = ${d3.样式维度恰为2}）｜整数差直方 ${JSON.stringify(d3.整数差直方图)}`);
  for (const m of (d1.整数恰2明细 || []).slice(0, 10)) log(`    ★恰2 ${m.路径.slice(-60)}｜${m.量} ${m.从}→${m.到}`);
}

// 判定
const A = out.汇总.相位['A_动作前']?.pane, B = out.汇总.相位['B_动作中']?.pane;
const 面板列 = B?.面板宽 ?? {};
const 面板值 = Object.entries(面板列).filter(([, v]) => v != null).map(([, v]) => v);
out.判定 = {
  H1_动作中比动作前多跳2: B && A ? B.Δ_374减373 === A.Δ_374减373 + 2 : null,
  H2_三相位Δ全等: [A, B].every((x) => x && x.Δ_374减373 === x.Δ_375减372_对照) ? true : null,
  H3_面板宽有2px台阶: B ? (Object.values(B.面板宽).some((v) => v != null)) : null,
  面板宽逐档: B?.面板宽 ?? null,
};
log('\n════ 判定 ════');
log(JSON.stringify(out.判定, null, 1));

// 末态独立复查（立规 140）
{
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: 1280, height: 720 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(6000);
    out.收尾.节点数 = await p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
    out.收尾.状态行 = await p.evaluate(() => (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null);
    out.收尾.通过 = out.收尾.节点数 === 76 && /0 selected/.test(out.收尾.状态行 || '');
    log(`\n末态独立复查：节点 ${out.收尾.节点数}｜${out.收尾.状态行} ⇒ ${out.收尾.通过 ? '✅' : '🔴'}`);
  } catch (e) { out.收尾.错误 = e.message; } finally { try { await p.close(); } catch (e) { /* 忽略 */ } }
}

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log(`\n写入 ${OUT}`);
process.exit(0);