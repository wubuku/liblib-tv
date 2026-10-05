/* probe-flyout-clickable.js —— M259：Dock 三个飞层里的每一项，默认状态下点不点得到（并验行为）
 *
 * 用法：
 *   CANVAS_URL=/canvas/<id> node scripts/probe-flyout-clickable.js
 *
 * ── 这条要回答的问题，和 M255/M257 那两条是同一个形状 ──────────────────
 * M255 查了「Dock 的飞层被节点面板整块盖住」（R106），
 * M257 查了「左下缩放条 6 个控件只有 1 个点得到」（R110）。
 * ★ **但两者量的都是「按钮」**——**没人量过飞层打开之后，里面的东西点不点得到。**
 * 而手册 `organize-canvas.md` 教读者「在外观面板里点『深色』」，
 * **那正是飞层里的第二下点击**。
 *
 * ── 判据 ──────────────────────────────────────────────────────────
 * 逐个飞层内交互项问 `document.elementFromPoint(中心x, 中心y)`，
 * **要求返回的最上层元素落在该项自己的子树里**（F74：存在 ≠ 按得到）。
 * ★ **阳性对照**：节点面板收起时，**每一项**都必须命中自己；
 *   对照不成立的话，上面所有「落点不是它」都只能说明判据坏了。
 *
 * ── ★ 写这支探针时踩到的一个坑，留在代码里 ────────────────────────────
 * ⓪ **点开飞层不能用 `element.click()`**：那会绕过命中测试直接派发事件，
 *    于是**无论有没有被面板盖住都「点开了」**——量出来的「开得起来」是假的。
 *    ★ **必须用 `page.mouse.click(真实坐标)`**，让浏览器自己走命中测试。
 *    这正是 R106 那次的教训：Dock 按钮点得动，**不代表它开出来的面板点得动**。
 *
 * ① **不要按「有 data-* 属性」枚举**（F80）：飞层里的主题开关是
 *    `AnimatedThemeToggler`，只有 `aria-label` / `title`（`canvas-toolbar.tsx:482-499`），
 *    **一个 `data-` 开头的属性都没有**（`aria-label` / `title` 之外什么都没有）——按属性枚举会把它漏掉，
 *    **而它恰好是这一批里读者最常点的那一项**。
 *    正确写法：**飞层容器内 `button` 全量枚举**。
 * ② **飞层是 `z-30`、面板是 `z-[60]`**（`canvas-toolbar.tsx:299` vs `canvas-side-panel.tsx:96`），
 *    **而两者都挂在各自的定位层上**——所以**光看 class 里的 z 值会以为飞层赢**。
 *    ★ **层叠要看参与层叠的那一层**（F73），所以这里一律以 `elementFromPoint` 为准。
 * ③ **画布只渲染视口内的节点**（F79，`project.tsx:617`）：本探针不点节点，
 *    但**开局仍然打一次侧面板的「画布元素 N」**，用来确认画布是活的、
 *    且**页面确实处在默认状态**（面板开着）。
 */
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright');

const APP = process.env.APP_URL || 'http://localhost:3000';
const CANVAS = process.env.CANVAS_URL || '';
const PROFILE = process.env.PROFILE || '/tmp/m244-profile';
const OUT = (...a) => process.stdout.write(a.join(' ') + '\n');

/* ★ R106 说「三个飞层都被盖住」，但那是**几何推断**（区间相交）。
 *   这里把三个**逐一实测**——飞层能不能点开、里面的东西点不点得到，是两件事。 */
const FLYOUT_TOOLS = [
  { tool: 'tool-create', name: '添加节点' },
  { tool: 'tool-style', name: '画布外观' },
  { tool: 'tool-history', name: '历史' },
];

const SIDE_OPEN = () => !!document.querySelector('aside.td-canvas-side-panel');
const FLYOUT_OPEN = () => !!document.querySelector('.td-canvas-flyout');

/** 侧面板的「画布元素 N」——★ 那是 store 的真值，`[data-node-id]` 不是（F79） */
const TRUTH = () => {
  const a = document.querySelector('aside.td-canvas-side-panel');
  const m = a && a.textContent.match(/画布元素\s*(\d+)/);
  return { 侧面板: m ? m[1] : '(关)', dom节点: document.querySelectorAll('[data-node-id]').length };
};

/** 主题真值：zustand persist 写在 localStorage 的 `tdcanvas:theme_store`（`stores/use-theme-store.ts:16`）。
 *  ★ **没写过时 store 的默认值是 `dark`**（同文件 `:12`），所以「未设置」要读成 dark，
 *   **不能原样报「未设置」**——那会让「点了没换」和「本来就没人设过」看起来像两件事。 */
const THEME = () => {
  try {
    const v = JSON.parse(localStorage.getItem('tdcanvas:theme_store') || '{}').state?.theme;
    return v || 'dark';
  } catch (e) { return '(读失败)'; }
};

/** 飞层里那两个主题开关是**一对常驻按钮**，标签是「切到哪个」而不是「现在是哪个」
 *  （`canvas-toolbar.tsx:487` 的 `targetTheme === "dark" ? darkTheme : lightTheme`）。
 *  ★ **所以按第一个找会点错**：当前已是浅色时，第一个仍写着「切换到浅色主题」，
 *  点它等于没点。**必须按「我要回到哪个主题」去点名。** */
const THEME_BTN = (want) => {
  const label = want === 'dark' ? '切换到深色主题' : '切换到浅色主题';
  const el = document.querySelector('.td-canvas-flyout [aria-label="' + label + '"]');
  if (!el) return null;
  const r = el.getBoundingClientRect();
  return { x: r.x + r.width / 2, y: r.y + r.height / 2, label };
};

/** ★ 飞层容器：必须限定在 `.td-canvas-flyout` 内（M168 的纪律）。
 *  只按 `button` 全局枚举会把整个 Dock 和侧面板的按钮一起捞进来。 */
const FLYOUT_ITEMS = () => {
  const wrap = document.querySelector('.td-canvas-flyout');
  if (!wrap) return null;
  const wr = wrap.getBoundingClientRect();
  const side = document.querySelector('aside.td-canvas-side-panel');
  const sr = side && side.getBoundingClientRect();
  const items = Array.from(wrap.querySelectorAll('button')).map((el) => {
    const r = el.getBoundingClientRect();
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    const top = document.elementFromPoint(cx, cy);
    const who = top ? top.tagName + '.' + String(top.className || '').split(' ').slice(0, 2).join('.') : 'null';
    return {
      id: (el.getAttribute('aria-label') || el.getAttribute('title') || el.textContent || el.tagName).trim().slice(0, 16),
      x: Math.round(cx), y: Math.round(cy),
      w: Math.round(r.width), h: Math.round(r.height),
      self: !!(top && el.contains(top)),
      inPanel: !!(top && top.closest('aside.td-canvas-side-panel')),
      who,
    };
  });
  return {
    飞层: [Math.round(wr.x), Math.round(wr.right)],
    面板: sr ? [Math.round(sr.x), Math.round(sr.right)] : null,
    重叠像素: sr ? Math.round(Math.min(wr.right, sr.right) - Math.max(wr.x, sr.x)) : null,
    items,
  };
};

/** ★ 用真实鼠标点击一个选择器的中心——让浏览器自己走命中测试（M259 的 ⓪ 号坑） */
async function realClick(page, selector) {
  const box = await page.evaluate((sel) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
  }, selector);
  if (!box) return false;
  await page.mouse.click(box.x, box.y);
  await page.waitForTimeout(900);
  return true;
}

(async () => {
  const ctx = await chromium.launchPersistentContext(PROFILE, { headless: true, viewport: { width: 1600, height: 1000 } });
  const page = ctx.pages()[0] || await ctx.newPage();
  const rows = [];
  let panelAtEntry = null;
  let themeAtEntry = null;
  try {
    await page.goto(APP + CANVAS, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2500);
    panelAtEntry = await page.evaluate(SIDE_OPEN);
    themeAtEntry = await page.evaluate(THEME);
    OUT('[开局] 面板开=' + panelAtEntry + ' ' + JSON.stringify(await page.evaluate(TRUTH)));

    for (const want of [true, false]) {
      if (await page.evaluate(SIDE_OPEN) !== want) await realClick(page, 'button[data-canvas-tool="tool-search"]');
      const open = await page.evaluate(SIDE_OPEN);
      if (open !== want) { OUT('  ⚠ 想切到面板' + (want ? '开' : '关') + '，实测 ' + open + '——这一档不产出读数'); continue; }
      OUT('\n################ 面板' + (open ? '开（默认）' : '关') + ' ################');

      for (const T of FLYOUT_TOOLS) {
        // ★ 先确认 Dock 按钮本身点得动（R110：Dock 8/8 全通）——它点得动**不代表**它开出来的面板点得动
        if (await page.evaluate(FLYOUT_OPEN)) await realClick(page, 'button[data-canvas-tool="tool-style"]');
        const opened = await realClick(page, `button[data-canvas-tool="${T.tool}"]`);
        const flyoutOpen = await page.evaluate(FLYOUT_OPEN);
        OUT('\n[「' + T.name + '」' + T.tool + '] 派发=' + opened + ' 飞层真的出现=' + flyoutOpen);
        if (!flyoutOpen) { OUT('  ⚠ 飞层没打开（真实鼠标点击仍打不开）——这一档不产出读数'); continue; }

        const data = await page.evaluate(FLYOUT_ITEMS);
        if (!data) { OUT('  ⚠ 找不到 .td-canvas-flyout'); continue; }
        OUT('[几何] 飞层 x ' + data.飞层[0] + '–' + data.飞层[1]
            + ' | 面板 ' + (data.面板 ? data.面板[0] + '–' + data.面板[1] : '无')
            + ' | 重叠 ' + data.重叠像素 + 'px');
        OUT('  可点到 ' + data.items.filter((i) => i.self).length + ' / ' + data.items.length);
        data.items.forEach((i) => OUT('    ', i.self ? '✓' : '✗', JSON.stringify(i.id),
            '(' + i.x + ',' + i.y + ')', i.self ? '' : '落点 ' + i.who + (i.inPanel ? '〔在面板内〕' : '')));
        rows.push({ open, tool: T.name, items: data.items, geom: data });

        await realClick(page, `button[data-canvas-tool="${T.tool}"]`);  // 收起
      }
    }

    // ── 行为相：几何只说明「落点是谁」，不说明「点了有没有生效」 ──────────
    // `organize-canvas.md` 教读者「在外观面板里点『深色』」。
    // ★ **所以必须再问一次行为**：在默认状态（面板开着）点那个位置，主题到底换没换？
    //   若没换，手册那句「点完要关掉面板再打开才能看到新配色」就**不只是描述不准**，
    //   **而是把读者引向一条修不好的路**——他关掉再打开，看到的还是原配色。
    OUT('\n################ 行为相：点「切换到浅色主题」那个位置，主题换没换 ################');
    const behavior = [];
    for (const want of [true, false]) {
      if (await page.evaluate(SIDE_OPEN) !== want) await realClick(page, 'button[data-canvas-tool="tool-search"]');
      const open = await page.evaluate(SIDE_OPEN);
      if (await page.evaluate(FLYOUT_OPEN)) await realClick(page, 'button[data-canvas-tool="tool-style"]');
      if (!(await realClick(page, 'button[data-canvas-tool="tool-style"]')) || !(await page.evaluate(FLYOUT_OPEN))) {
        OUT('  面板' + (open ? '开' : '关') + '：飞层没打开——跳过'); continue;
      }
      const target = await page.evaluate(() => {
        const el = document.querySelector('.td-canvas-flyout [aria-label="切换到浅色主题"]');
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
      });
      if (!target) { OUT('  面板' + (open ? '开' : '关') + '：飞层里没有那个按钮——跳过'); continue; }
      const before = await page.evaluate(THEME);
      await page.mouse.click(target.x, target.y);          // ★ 真实鼠标：让浏览器走命中测试
      await page.waitForTimeout(1200);
      const after = await page.evaluate(THEME);
      OUT('  面板' + (open ? '开（默认）' : '关') + '：主题 ' + before + ' → ' + after
          + '  ' + (before === after ? '✗ 没换（点击被面板吃掉）' : '✓ 换了'));
      behavior.push({ open, before, after, changed: before !== after });
      if (await page.evaluate(FLYOUT_OPEN)) await realClick(page, 'button[data-canvas-tool="tool-style"]');
    }
    rows.push({ kind: '行为相', behavior });
    OUT('  结论：' + (behavior.every((b) => b.changed === !b.open)
      ? '★ 默认状态下点了不生效，收起面板后同一坐标才生效——与几何读数一致'
      : '⚠ 两相不一致，几何读数不能代替行为读数（如实记下）'));

    OUT('\n===== 汇总：飞层里存在但按不到的 =====');
    for (const r of rows.filter((x) => x.items)) {
      const bad = r.items.filter((i) => !i.self);
      OUT('  面板' + (r.open ? '开' : '关') + ' · ' + r.tool + '：' + bad.length + ' / ' + r.items.length
          + (bad.length ? '  → ' + bad.map((b) => JSON.stringify(b.id)).join(', ') : ''));
    }
  } catch (e) {
    OUT('[异常]', e && e.stack ? e.stack.split('\n').slice(0, 3).join(' | ') : e);
  } finally {
    // 还原：主题 → 收起飞层 → 面板恢复成开着的默认状态
    // ★ 行为相把主题切成了浅色，**必须还原**；走产品 UI（点开关）而不是直接改 localStorage。
    try {
      const now = await page.evaluate(THEME);
      if (themeAtEntry && now !== themeAtEntry) {
        // ★ 必须先收面板再【打开】飞层：主题开关在飞层里，而飞层默认被面板盖住（F61 本批的判据）
        if (await page.evaluate(SIDE_OPEN)) await realClick(page, 'button[data-canvas-tool="tool-search"]');
        if (!(await page.evaluate(FLYOUT_OPEN))) await realClick(page, 'button[data-canvas-tool="tool-style"]');
        if (!(await page.evaluate(FLYOUT_OPEN))) OUT('[还原] ⚠ 飞层没打开，主题没能还原，如实记下');
        const back = await page.evaluate(THEME_BTN, themeAtEntry);
        if (back) {
          await page.mouse.click(back.x, back.y);
          await page.waitForTimeout(1200);
          OUT('[还原] 点「' + back.label + '」→ 主题 ' + (await page.evaluate(THEME)));
        } else OUT('[还原] ⚠ 飞层里找不到主题开关，主题没能还原，如实记下');
        if (await page.evaluate(FLYOUT_OPEN)) await realClick(page, 'button[data-canvas-tool="tool-style"]');
      }
      if (await page.evaluate(FLYOUT_OPEN)) await realClick(page, 'button[data-canvas-tool="tool-style"]');
      if (panelAtEntry === true && !(await page.evaluate(SIDE_OPEN))) {
        await realClick(page, 'button[data-canvas-tool="tool-search"]');
      }
      OUT('\n[还原] 主题=' + (await page.evaluate(THEME)) + '（开局 ' + themeAtEntry + '）'
          + ' 飞层开=' + (await page.evaluate(FLYOUT_OPEN)) + ' 面板开=' + (await page.evaluate(SIDE_OPEN)));
    } catch (e) { OUT('[还原失败]', e && e.message); }
    await ctx.close();
  }
})();
