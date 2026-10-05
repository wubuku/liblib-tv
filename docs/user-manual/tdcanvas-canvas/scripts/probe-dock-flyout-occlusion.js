/* probe-dock-flyout-occlusion.js —— 左侧 Dock 的三个飞层，在默认状态下点得到吗（M255）
 *
 * 用法：
 *   CANVAS_URL=/canvas/<id> node scripts/probe-dock-flyout-occlusion.js
 *
 * ── 为什么这个判据不能省 ──────────────────────────────────────────
 * 「元素存在」「能 量 到 rect」「getBoundingClientRect().width > 0」
 * ——**这三条全都会说它没问题**，因为被盖住的东西照样有尺寸有位置。
 * M132 就是这么把「添加节点面板 212×352」量进去的，量得完全正确，
 * **而那个面板在默认状态下根本点不到**。
 * ★ 唯一能回答「用户按不按得到」的判据是
 *   `document.elementFromPoint(中心x, 中心y)` —— 问布局引擎「这一格归谁」。
 *
 * ── 为什么三个飞层要一起测 ────────────────────────────────────────
 * 源码里三处 `td-canvas-flyout` 的定位分别是
 *   添加节点 left-[calc(100%+24px)]  画布外观 left-[calc(100%+10px)]  历史 同
 * Dock 自身在 left-4(16px)、宽 48，所以三者的左边界是 88 / 74 / 74。
 * 而节点面板是 `absolute left-14(56px) ... z-[60]`，默认宽 280 → 占 56..336。
 * **三者的横向区间全部落在 56..336 之内**，所以要么全被盖、要么全不被盖。
 * 但这是**源码推断**，必须三条各测一次才作数——**推断和实测要分账**。
 */
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright');
const APP = process.env.APP_URL || 'http://localhost:3000';
const CANVAS = process.env.CANVAS_URL || '';
const PROFILE = process.env.PROFILE || '/tmp/m244-profile';
const OUT = (...a) => process.stdout.write(a.join(' ') + '\n');

/** 飞层里挑一个「能代表它可用性」的点：菜单项的中点 */
const PROBE_FLYOUT = () => {
  const fly = document.querySelector('.td-canvas-flyout');
  if (!fly) return { flyout: false };
  const r = fly.getBoundingClientRect();
  // 菜单项 = 飞层里的 button
  const btns = Array.from(fly.querySelectorAll('button'));
  const target = btns[Math.floor(btns.length / 2)] || fly;
  const tr = target.getBoundingClientRect();
  const cx = tr.x + tr.width / 2, cy = tr.y + tr.height / 2;
  const top = document.elementFromPoint(cx, cy);
  const chain = [];
  let n = top;
  for (let i = 0; i < 5 && n; i++) { chain.push(n.tagName + '.' + String(n.className || '').split(' ').slice(0, 2).join('.')); n = n.parentElement; }
  return {
    flyout: true,
    flyRect: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
    btnCount: btns.length,
    sampleBtn: (target.textContent || '').trim().slice(0, 10),
    落点: chain,
    落点在飞层内: fly.contains(top),
  };
};

const SIDE_OPEN = () => !!document.querySelector('aside.td-canvas-side-panel');

/** 顺带量一下面板与飞层的横向区间是否真的重叠 */
const GEOM = () => {
  const fly = document.querySelector('.td-canvas-flyout');
  const side = document.querySelector('aside.td-canvas-side-panel');
  const f = fly && fly.getBoundingClientRect();
  const s = side && side.getBoundingClientRect();
  const z = (el) => el ? (getComputedStyle(el).zIndex || 'auto') : null;
  return {
    flyX: f ? [Math.round(f.x), Math.round(f.right)] : null,
    sideX: s ? [Math.round(s.x), Math.round(s.right)] : null,
    flyZ: z(fly), sideZ: z(side),
    // 飞层完全落在面板横向区间内？
    横向完全重叠: !!(f && s && f.x >= s.x && f.right <= s.right),
  };
};

const DOCK = [
  { tool: 'tool-create', name: '添加节点' },
  { tool: 'tool-style', name: '画布外观' },
  { tool: 'tool-history', name: '历史' },
];

(async () => {
  const ctx = await chromium.launchPersistentContext(PROFILE, { headless: true, viewport: { width: 1600, height: 1000 } });
  const page = ctx.pages()[0] || await ctx.newPage();
  try {
    await page.goto(APP + CANVAS, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2200);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(400);

    // ★ 阳性对照：先确认「面板开关」这个按钮本身是点得到的，
    //   否则后面「面板关着就能点」可能被误读成运气好。
    const toggle = await page.$('button[data-canvas-tool="tool-search"]');
    OUT('面板开关按钮存在 =', !!toggle);
    if (toggle) {
      const b = await toggle.boundingBox();
      const hit = await page.evaluate(([x, y]) => {
        const e = document.elementFromPoint(x, y);
        return e ? (e.closest('button[data-canvas-tool]') ? e.closest('button[data-canvas-tool]').getAttribute('data-canvas-tool') : e.tagName) : null;
      }, [b.x + b.width / 2, b.y + b.height / 2]);
      OUT('[阳性对照] 该点命中 data-canvas-tool =', hit, '（=tool-search 才算按钮自己收到了指针）');
    }

    for (const state of ['面板开（默认）', '面板关']) {
      // 调到目标状态
      const wantOpen = state.startsWith('面板开');
      if (await page.evaluate(SIDE_OPEN) !== wantOpen) {
        const sb = await page.$('button[data-canvas-tool="tool-search"]');
        if (sb) { await sb.click({ force: true }); await page.waitForTimeout(800); }
      }
      OUT('\n########## ' + state + '（实测 ' + (await page.evaluate(SIDE_OPEN)) + '） ##########');
      for (const d of DOCK) {
        const btn = await page.$('button[data-canvas-tool="' + d.tool + '"]');
        if (!btn) { OUT('  [' + d.name + '] 按钮不存在（data-canvas-tool=' + d.tool + '）'); continue; }
        await btn.click({ force: true });
        await page.waitForTimeout(800);
        const p = await page.evaluate(PROBE_FLYOUT);
        if (!p.flyout) { OUT('  [' + d.name + '] 飞层没打开'); continue; }
        OUT('  [' + d.name + '] 飞层 ' + JSON.stringify(p.flyRect) + ' 按钮 ' + p.btnCount + ' 个');
        OUT('      落点是否在飞层内 = ' + p.落点在飞层内 + '  落点链 = ' + JSON.stringify(p.落点));
        OUT('      几何 = ' + JSON.stringify(await page.evaluate(GEOM)));
        await page.keyboard.press('Escape');
        await page.waitForTimeout(400);
        // 再点一次把它关掉（Escape 未必收）
        if (await page.$('.td-canvas-flyout')) { await btn.click({ force: true }); await page.waitForTimeout(500); }
      }
    }

    OUT('\n===== 对照：双击空白处的创建菜单是 fixed z-[120] =====');
    const c = await page.evaluate(() => {
      const s = document.createElement('style');
      return null;
    });
    await page.mouse.dblclick(900, 700);
    await page.waitForTimeout(800);
    const alt = await page.evaluate(() => {
      const el = document.querySelector('.td-canvas-flyout');
      if (!el) return { open: false };
      const r = el.getBoundingClientRect();
      return { open: true, pos: getComputedStyle(el).position, z: getComputedStyle(el).zIndex, rect: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) } };
    });
    OUT('  ', JSON.stringify(alt));
    await page.screenshot({ path: '/tmp/m255-dblclick-menu.png' });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(400);
  } catch (e) {
    OUT('[异常]', e && e.stack ? e.stack.split('\n').slice(0, 3).join(' | ') : e);
  } finally {
    // 还原：面板恢复成默认的「开」
    try {
      if (!(await page.evaluate(SIDE_OPEN))) {
        const sb = await page.$('button[data-canvas-tool="tool-search"]');
        if (sb) { await sb.click({ force: true }); await page.waitForTimeout(700); }
      }
      OUT('\n[还原] 面板开着吗 =', await page.evaluate(SIDE_OPEN));
    } catch (e) { OUT('[还原失败]', e); }
    await ctx.close();
  }
})();
