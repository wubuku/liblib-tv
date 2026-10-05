/* probe-a16-a27.js —— M256：核 §14 的 A27（弹窗打开时那 12 个点全落在遮罩上）
 *
 * ★ **本文件只做 A27，A16 那半边已经拆走了**：A16 要沿一条连线逐点问「这一格归谁」，
 *   而本机一条连线都建不出来（四次尝试的记录见 `probe-a16.js` 的头注），
 *   **合成一支探针会让 A27 这条已经跑通的读数跟着一个跑不通的分支一起被怀疑**。
 *
 * A27 的限定词 = 「12 个点无一命中按钮本身，全部落在遮罩上」。
 * ★ 判据用 `elementFromPoint` 而不是「按钮还在不在 DOM 里」——
 *   被遮罩盖住的按钮照样在 DOM 里、照样有 rect（M255 的 F74，本批第二次应用同一个 API）。
 * ★ 阳性对照是**同一组点在弹窗开之前先读一遍**：
 *   12/12 命中自己 → 之后变成 0/12 才说明是弹窗造成的，不是判据本来就坏。
 */
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright');
const OUT = (...a) => process.stdout.write(a.join(' ') + '\n');

/** A16：连线层与节点层的真实层叠关系 */
const LAYER = () => {
  const node = document.querySelector('[data-node-id]');
  const conn = document.querySelector('[data-connection-id]');
  if (!node || !conn) return { err: 'node=' + !!node + ' conn=' + !!conn };
  const path = conn.closest('svg') || conn.ownerSVGElement;
  const z = (el) => el ? getComputedStyle(el).zIndex : null;
  // DOM 顺序：谁在文档流里更靠后
  const pos = (el) => {
    const all = Array.from(document.querySelectorAll('body *'));
    return all.indexOf(el);
  };
  // 阳性对照：连线上没有被节点盖住的那一段，落点归谁
  const cr = conn.getBoundingClientRect();
  let exposed = null;
  for (let t = 0.05; t <= 0.95; t += 0.05) {
    const x = cr.left + cr.width * t, y = cr.top + cr.height * t;
    const e = document.elementFromPoint(x, y);
    if (e && e.closest('[data-connection-id]')) { exposed = { t: +t.toFixed(2), x: Math.round(x), y: Math.round(y) }; break; }
  }
  return {
    连接层_svg: path ? path.tagName + '.' + String(path.className.baseVal || path.getAttribute('class') || '').slice(0, 40) : null,
    连接层_z: z(path),
    节点_z: z(node),
    节点类: String(node.className).match(/z-\S+/)?.[0] || null,
    文档序_节点在前: pos(node) < pos(path),
    阳性对照_线上未遮挡处的落点: exposed,
  };
};

/** A27：弹窗打开时，逐个按钮中心「这一格归谁」 */
const POINTS = () => Array.from(document.querySelectorAll('.td-canvas-dock button, [data-canvas-view-control]'))
  .map((b) => {
    const r = b.getBoundingClientRect();
    const x = r.x + r.width / 2, y = r.y + r.height / 2;
    const top = document.elementFromPoint(x, y);
    const inBtn = !!(top && b.contains(top));
    const inMask = !!(top && top.closest('.ant-modal-root, .ant-modal-wrap, [role="dialog"]'));
    return {
      label: (b.getAttribute('aria-label') || '').slice(0, 10),
      x: Math.round(x), y: Math.round(y),
      命中自己: inBtn, 命中遮罩: inMask,
      落点: top ? top.tagName + '.' + String(top.className || '').split(' ').slice(0, 2).join('.') : 'null',
    };
  });

(async () => {
  const ctx = await chromium.launchPersistentContext(process.env.PROFILE || '/tmp/m244-profile', { headless: true, viewport: { width: 1600, height: 1000 } });
  const page = ctx.pages()[0] || await ctx.newPage();
  try {
    await page.goto((process.env.APP_URL || 'http://localhost:3000') + (process.env.CANVAS_URL || '/canvas/H4UgDBdT3NxvK_C5MLMq5'), { waitUntil: 'networkidle' });
    await page.waitForTimeout(2200);

    OUT('===== A16：节点与连线的层叠 =====');
    OUT(JSON.stringify(await page.evaluate(LAYER), null, 1));

    OUT('\n===== A27-① 弹窗未开 =====');
    const before = await page.evaluate(POINTS);
    OUT('点数 =', before.length);
    OUT('命中自己的 =', before.filter((p) => p.命中自己).length, ' 命中遮罩的 =', before.filter((p) => p.命中遮罩).length);
    before.forEach((p) => OUT('  ', p.label, '→', p.落点, p.命中自己 ? '✓自己' : ''));

    // 开一个弹窗：左下角「快捷键」那个问号按钮
    await page.click('button[aria-label*="快捷键"], button[aria-label*="Shortcut"], button[aria-label*="shortcut"]');
    await page.waitForTimeout(900);
    const dlg = await page.evaluate(() => {
      const d = document.querySelector('[role="dialog"]');
      if (!d) return null;
      const r = d.getBoundingClientRect();
      return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
    });
    OUT('\n===== A27-② 弹窗已开 =====');
    OUT('dialog =', JSON.stringify(dlg));
    const after = await page.evaluate(POINTS);
    OUT('点数 =', after.length);
    OUT('命中自己的 =', after.filter((p) => p.命中自己).length, ' 命中遮罩的 =', after.filter((p) => p.命中遮罩).length);
    after.forEach((p) => OUT('  ', p.label, '→', p.落点, p.命中遮罩 ? '〔遮罩〕' : (p.命中自己 ? '✓自己' : '〔别的〕')));
    await page.screenshot({ path: '/tmp/m256-a27-modal.png' });
  } catch (e) { OUT('[异常]', e && e.stack ? e.stack.split('\n').slice(0, 3).join(' | ') : e); }
  finally { await ctx.close(); }
})();
