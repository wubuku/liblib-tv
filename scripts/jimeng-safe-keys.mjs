// 即梦画布取证 —— 键盘安全守卫。
//
// 为什么需要它（2026-10-01 批次 39 / 批次 43 两次事故的共同根因）：
// 画布上有多个「会悄悄拿走焦点、把按键变成打字」的入口：
//   ① F 打开全屏文本编辑器（`contenteditable` 获焦点）
//   ② 单击选中「主体」节点 —— 标题 `input[aria-label="名称"]` **自动获焦点**
// 两者都会让「我以为在按快捷键」的字母键变成往别人的数据里打字。
//
// ⚠️ 早期版本的守卫只查 `[contenteditable]`，**漏掉了 ②**（它是 <input>）。
//    枚举元素类型永远补不全 —— **焦点是单一状态，直接问 activeElement**。
//
// 用法：
//   import { keyGuard, pressLetter } from './jimeng-safe-keys.mjs';
//   const g = await keyGuard(page);
//   if (!g.safe) throw new Error(`焦点在 ${g.where}，不许按字母键`);
//   await pressLetter(page, 'f');            // 内部自动断言
//
//   命令行自检：node scripts/jimeng-safe-keys.mjs
//     打印当前焦点状态与是否可以安全按字母键。
const PORT = 9444;   // 避开 9222（已被其他 Chrome 占用）

/**
 * 读取当前焦点，判断「现在按字母/数字键会不会变成打字」。
 * @returns {Promise<{safe:boolean, tag:string|null, testid:string|null,
 *   where:string, reason:string}>}
 */
export async function keyGuard(page) {
  const info = await page.evaluate(() => {
    const a = document.activeElement;
    if (!a) return { tag: null, testid: null, isCE: false, inCE: false, role: null, label: null };
    const tag = a.tagName;
    const inCE = !!a.closest('[contenteditable]') || a.isContentEditable === true;
    return {
      tag,
      testid: a.getAttribute('data-testid'),
      role: a.getAttribute('role'),
      label: a.getAttribute('aria-label'),
      isCE: tag === 'INPUT' || tag === 'TEXTAREA',
      inCE,
    };
  });

  const where = info.tag === null ? '(body)'
    : `${info.tag}${info.testid ? `[${info.testid}]` : ''}${info.label ? ` aria="${info.label}"` : ''}`;

  // 危险：焦点在输入面里 —— 字母键会变成打字
  if (info.isCE || info.inCE) {
    return { safe: false, tag: info.tag, testid: info.testid, where,
      reason: `焦点在输入面（${where}）——按字母键会变成打字，禁止` };
  }
  // 危险：焦点在浮层 / 侧栏 / 对话框里
  const RISKY_TAGS = ['ASIDE'];
  if (RISKY_TAGS.includes(info.tag) || (info.tag === 'DIV' && /dialog|drawer|sidecar|overlay|editor/i.test(info.testid || ''))) {
    return { safe: false, tag: info.tag, testid: info.testid, where,
      reason: `焦点在浮层容器（${where}）——按键可能被浮层吞掉，先 Esc 关闭` };
  }
  // 额外保险：页面上有可见的输入面时给出提醒（不阻断，但要看见）
  const openInputs = await page.evaluate(() => {
    const v = (s) => Array.from(document.querySelectorAll(s))
      .filter((e) => e.getBoundingClientRect().width > 1).length;
    return v('input') + v('textarea') + v('[contenteditable]');
  });

  return { safe: true, tag: info.tag, testid: info.testid, where,
    reason: `焦点在画布（${where}）——可以安全按字母键`,
    openInputs };
}

/** 断言后按键；不安全直接抛错，不执行。 */
export async function pressLetter(page, key, wait = 500) {
  const g = await keyGuard(page);
  if (!g.safe) {
    throw new Error(`[keyGuard 拒绝执行] ${g.reason}（准备按 "${key}"）`);
  }
  await page.keyboard.press(key);
  await page.waitForTimeout(wait);
  return g;
}

/** 读画布基线（节点/边/选中数/缩放/积分），用于每批收尾核对。 */
export async function canvasBaseline(page) {
  return page.evaluate(() => {
    const t = document.body.innerText;
    return {
      status: (t.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0] || null,
      credit: (t.match(/(\d[\d,]*)\s*基础会员/) || [])[1] || null,
      zoom: (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label') || null,
      transform: (() => { const e = document.querySelector('.react-flow__viewport'); return e ? e.style.transform : null; })(),
      groups: document.querySelectorAll('.react-flow__node-group').length,
      dialogs: Array.from(document.querySelectorAll('[role="dialog"]'))
        .filter((e) => e.getBoundingClientRect().width > 1)
        .map((e) => e.getAttribute('data-testid') || e.getAttribute('aria-label')),
      nodes: Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
        const r = e.getBoundingClientRect();
        // ⚠️ 屏幕坐标随视口平移变化，**不能用来判断节点有没有被移动**。
        // canvas 是节点自身 inline transform 里的画布坐标，与平移无关 —— 位置核对必须用它。
        const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || '');
        return {
          id: e.getAttribute('data-id'),
          box: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}x${Math.round(r.height)}`,
          canvas: m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null,
          title: (e.querySelector('[data-testid="flow-node-title"]') || {}).innerText || null,
          text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24),
        };
      }),
    };
  });
}

/**
 * 与给定基线比对节点 canvas 坐标；返回偏离的 id 列表。
 *
 * ⚠️ 2026-10-01 批次 57 修一个**恒真**的缺陷：
 *   原实现写 `const e = baseCanvasById[id]; Math.abs(c[0] - e[0]) > tol`。
 *   而 `jimeng-baseline-nodes.json` 里每个节点是 `{ canvas:[x,y], title }` ——
 *   传进来的形状对不上，`e[0]` 是 `undefined`，
 *   `Math.abs(x - undefined)` = `NaN`，而 **`NaN > tol` 恒为 false**。
 *   ⇒ 第 8 道门的「节点位置偏离」无论节点实际偏了多少，都报「0 个」。
 *   实测证据：故意把基线写偏 100 canvas px（容差 1.5），
 *   旧形状返回 `[]`，正确形状返回 `["node_236ctpehgg"]`。
 *
 *   现在两种形状都接受，并且**形状不认识时直接抛错** ——
 *   宁可报错，也不要静悄悄地把检查变成恒真。
 *   🔑 一道质量门「从不失败」和「没有这道门」是同一件事。
 */
export async function diffNodePositions(page, baseCanvasById, tol = 1.5) {
  const cur = await canvasBaseline(page);
  const now = Object.fromEntries(cur.nodes.map((n) => [n.id, n.canvas]));
  const pick = (v) => {
    if (Array.isArray(v)) return v;                                  // { id: [x, y] }
    if (v && Array.isArray(v.canvas)) return v.canvas;                // { id: { canvas:[x,y], … } }
    throw new Error(
      `[diffNodePositions] 基线条目形状不认识：${JSON.stringify(v)}。`
      + ' 应为 [x, y] 或 { canvas: [x, y] } —— 传错形状会让本检查恒真（批次 57 事故）。');
  };
  return Object.keys(baseCanvasById).filter((id) => {
    const c = now[id], e = pick(baseCanvasById[id]);
    if (!c || !e) return true;
    return Math.abs(c[0] - e[0]) > tol || Math.abs(c[1] - e[1]) > tol;
  });
}

/** 视口钉死 1280×720 @dpr2；不匹配直接抛错。 */
export async function pinViewport(page) {
  await page.context().newCDPSession(page).then(async (s) => {
    await s.send('Emulation.setDeviceMetricsOverride',
      { width: 1280, height: 720, deviceScaleFactor: 2, mobile: false });
  });
  await page.waitForTimeout(400);
  const vp = await page.evaluate(() => ({ w: innerWidth, h: innerHeight }));
  if (vp.w !== 1280 || vp.h !== 720) {
    throw new Error(`视口被污染：${JSON.stringify(vp)}，应为 1280×720`);
  }
  return vp;
}

// ---- 命令行自检 ----
if (import.meta.url === `file://${process.argv[1]}`) {
  const { chromium } = await import('playwright');
  const b = await chromium.connectOverCDP(`http://127.0.0.1:${PORT}`);
  const page = b.contexts()[0].pages().find((p) => p.url().includes('ai-canvas'));
  if (!page) { console.error('ABORT: 找不到画布页面'); await b.close(); process.exit(2); }
  await pinViewport(page);
  const g = await keyGuard(page);
  const base = await canvasBaseline(page);
  console.log('焦点守卫:', g.safe ? '✅ 可按字母键' : '⛔ 不可按字母键');
  console.log('  where  :', g.where);
  console.log('  reason :', g.reason);
  if (g.openInputs !== undefined) console.log('  页面上可见的输入面数量:', g.openInputs, '（不阻断，但要看见）');
  console.log('画布基线:', JSON.stringify({
    status: base.status, credit: base.credit, zoom: base.zoom,
    transform: base.transform, groups: base.groups, dialogs: base.dialogs,
    nodeCount: base.nodes.length,
  }, null, 1));
  console.log('\n节点（canvas 坐标与平移无关，位置核对必须用它）:');
  for (const n of base.nodes) {
    console.log(`  ${n.id}  canvas=[${n.canvas ? n.canvas.join(', ') : '?'}]  title=${JSON.stringify(n.title)}`);
  }

  // ---- 位置检查的**阳性对照**（批次 57 新增）----
  // 🔑 一道「从不失败」的检查等于没有这道门。所以这里不测「有没有漂移」，
  //    而是**故意**把基线写偏 100 canvas px（容差 1.5），断言它**必须被报出来**。
  //    旧实现在这个用例上返回 []（恒真），正是它被漏掉那么多批次的原因。
  if (base.nodes.length) {
    const mk = (shape) => Object.fromEntries(base.nodes.map((n, i) => {
      const c = i === 0 && n.canvas ? [n.canvas[0] + 100, n.canvas[1]] : n.canvas;
      return [n.id, shape === 'flat' ? c : { canvas: c, title: n.title }];
    }));
    const victim = base.nodes[0].id;
    const hitFlat = await diffNodePositions(page, mk('flat'), 1.5);
    const hitWrapped = await diffNodePositions(page, mk('wrapped'), 1.5);
    const okFlat = hitFlat.includes(victim);
    const okWrapped = hitWrapped.includes(victim);
    let threw = null;
    try { await diffNodePositions(page, { [victim]: { nope: 1 } }, 1.5); }
    catch (e) { threw = e.message; }
    const okThrow = !!threw;
    console.log('\n位置检查阳性对照（故意把第一个节点的基线写偏 +100 canvas px，容差 1.5）:');
    console.log(`  {id:[x,y]} 形状        → ${JSON.stringify(hitFlat)}  ${okFlat ? '✅ 报出来了' : '❌ 漏报 —— 这门恒真了'}`);
    console.log(`  {id:{canvas}} 形状      → ${JSON.stringify(hitWrapped)}  ${okWrapped ? '✅ 报出来了' : '❌ 漏报 —— 这门恒真了'}`);
    console.log(`  形状不认识时是否抛错     → ${okThrow ? '✅ ' + String(threw).slice(0, 60) + '…' : '❌ 静悄悄通过'}`);
    if (!okFlat || !okWrapped || !okThrow) {
      console.log('  ⛔ 位置检查自测未通过 —— 第 8 道门不可信。');
      await b.close();
      process.exit(3);
    }
    console.log('  ✅ 位置检查自测通过：这门会失败，因此它有意义。');
  }

  await b.close();
  process.exit(g.safe ? 0 : 1);
}
