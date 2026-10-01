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
        return {
          id: e.getAttribute('data-id'),
          box: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}x${Math.round(r.height)}`,
          text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24),
        };
      }),
    };
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
  await b.close();
  process.exit(g.safe ? 0 : 1);
}
