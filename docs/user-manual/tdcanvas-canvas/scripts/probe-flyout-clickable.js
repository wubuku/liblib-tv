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
    // ── 落点行为相：那一带落着侧面板的节点标题，点下去到底发生了什么 ──────
    // F83：「没反应」至少对应三种事实（落在空白 / 落在别的控件 / 落在自己的内层），
    // **三种的正文写法不一样**。M259 只坐实了「落在节点标题上」，
    // ★ **本相回答剩下那一半：点下去有没有副作用。**
    // ★ **只点可逆的那一侧**：撤销会真改画布，**所以只点「落在节点标题上」的那一格，
    //   然后量选中态与视口变化**——两者都能用 Esc + 重置视图复位。
    OUT('\n################ 落点行为相：默认状态点「撤销」那一带 ################');
    try {
      const state = () => {
        // ★ 节点数读侧面板的「画布元素 N」，**不读 [data-node-id]**（F79）
        const side = document.querySelector('aside.td-canvas-side-panel');
        const cm = side && side.textContent.match(/画布元素\s*(\d+)/);
        const sel = Array.from(document.querySelectorAll('[data-node-id]'))
          .filter((n) => /z-50|selected/.test(n.className || ''))
          .map((n) => n.getAttribute('data-node-id').slice(0, 12));
        // ★ 「有选中」的可靠信号是产品自己给的：tool-delete 只在 selectedCount 时渲染（F80）
        const dock = document.querySelector('.td-canvas-dock');
        const hasDel = !!(dock && dock.querySelector('[data-canvas-tool="tool-delete"]'));
        const rowsHl = Array.from(document.querySelectorAll('aside.td-canvas-side-panel tr, aside.td-canvas-side-panel [class*="cursor-pointer"]'))
          .filter((e) => /bg-|active|selected/.test(e.className || ''))
          .map((e) => (e.textContent || '').trim().slice(0, 14));
        // ★ 视口那一项**删掉了**：第一版读的是一个「视口」开头的自定义属性，
        //   **而应用源码里根本没有那个属性**——于是它每次都返回空串，
        //   **是个不产出任何读数的死字段**。不往标记表里塞一个不存在的标记（F82 的反面）。
        //   ★ 顺带记一条同族的判据边界：**这段注释第一版直接写出了那个属性名**，
        //   而 `check-probe-contracts.py` 的标记扫描**连注释一起读**——
        //   于是「删了字段、注释里留个名字」照样报红。**同一个坑一天栽两次。**
        return { 画布元素: cm ? cm[1] : '(读不到)', 有选中: hasDel, 选中节点: sel, 面板高亮: rowsHl };
      };

      // ★ **面板必须保持「开」**——本相量的就是**被遮挡**那一档。
      // ★ 第一版这里写的是「先收面板」，量到的落点是飞层自己的「撤销」——
      //   **量错了对象（不是读数矛盾）**，而两个读数长得几乎一样。
      if (!(await page.evaluate(SIDE_OPEN))) await realClick(page, 'button[data-canvas-tool="tool-search"]');
      if (await page.evaluate(FLYOUT_OPEN)) await realClick(page, 'button[data-canvas-tool="tool-history"]');
      if (!(await realClick(page, 'button[data-canvas-tool="tool-history"]')) || !(await page.evaluate(FLYOUT_OPEN))) {
        OUT('  ⚠ 历史飞层没打开，跳过本相');
      } else {
        const undo = await page.evaluate(() => {
          const wrap = document.querySelector('.td-canvas-flyout');
          const el = Array.from(wrap.querySelectorAll('button')).find((b) => (b.textContent || '').trim() === '撤销');
          if (!el) return null;
          const r = el.getBoundingClientRect();
          return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
        });
        if (!undo) OUT('  ⚠ 飞层里没找到「撤销」按钮，跳过本相');
        else {
          const before = await page.evaluate(state);
          await page.mouse.click(undo.x, undo.y);          // ★ 真实坐标：让它打在节点标题上
          await page.waitForTimeout(1000);
          const after = await page.evaluate(state);
          const hit = await page.evaluate(([x, y]) => {
            const e = document.elementFromPoint(x, y);
            const row = e && e.closest('aside.td-canvas-side-panel');
            return { 落点: e ? e.tagName + '.' + String(e.className || '').split(' ').slice(0, 2).join('.') : 'null',
                     落点文字: e ? (e.textContent || '').trim().slice(0, 16) : '',
                     在面板节点行内: !!row };
          }, [undo.x, undo.y]);
          OUT('  落点 ' + hit.落点 + ' 文字 ' + JSON.stringify(hit.落点文字) + ' 面板行内=' + hit.在面板节点行内);
          OUT('  点之前 ' + JSON.stringify(before));
          OUT('  点之后 ' + JSON.stringify(after));
          OUT('  → 画布元素 ' + before.画布元素 + ' → ' + after.画布元素
              + '；有选中 ' + before.有选中 + ' → ' + after.有选中
              + '；选中节点 ' + (before.选中节点.join(',') || '无') + ' → ' + (after.选中节点.join(',') || '无')
              + '；面板高亮 ' + JSON.stringify(before.面板高亮) + ' → ' + JSON.stringify(after.面板高亮));
          const changed = before.画布元素 !== after.画布元素 || before.有选中 !== after.有选中
            || before.选中节点.join() !== after.选中节点.join() || JSON.stringify(before.面板高亮) !== JSON.stringify(after.面板高亮);
          OUT('  ★ 结论：这一下' + (changed ? '**有副作用**' : '**什么也没发生**（撤销没触发，也没有任何选中变化）'));

          // ── 探测器阳性对照：不改画布，只证明「这套读数看得见变化」 ──────
          // ★ **不做「收面板后真按一次撤销」**：那会真改画布，
          //   而**恢复要靠重做**——一旦重做失败，夹具就少一个节点。
          //   这里改用一个**零改动**的对照：直接点侧面板里的一个节点行。
          //   如果点它能选中节点，就证明 state() 看得见这类变化，
          //   **于是上面那个「什么也没发生」才是有意义的读数而不是探测器坏了。**
          const rowPt = await page.evaluate(() => {
            const side = document.querySelector('aside.td-canvas-side-panel');
            const rows = Array.from(side.querySelectorAll('*')).filter((e) => {
              const c = e.className || '';
              return typeof c === 'string' && /truncate/.test(c) && e.children.length === 0 && (e.textContent || '').trim();
            });
            if (!rows.length) return null;
            const r = rows[0].getBoundingClientRect();
            return { x: r.x + Math.min(r.width / 2, 40), y: r.y + r.height / 2, 文字: (rows[0].textContent || '').trim().slice(0, 14) };
          });
          if (!rowPt) OUT('  [阳性对照] ⚠ 侧面板里没找到可点的节点行，探测器有效性未验证，如实记下');
          else {
            await page.mouse.click(rowPt.x, rowPt.y);
            await page.waitForTimeout(900);
            const probe = await page.evaluate(state);
            OUT('  [阳性对照] 直接点侧面板节点行 ' + JSON.stringify(rowPt.文字)
                + ' → 有选中 ' + probe.有选中 + '、选中节点 ' + (probe.选中节点.join(',') || '无')
                + (probe.有选中 ? '  ✓ 探测器看得见这类变化，**上面的阴性读数因此有意义**'
                                 : '  ⚠ 探测器没反应，**上面的阴性读数不可信**'));
            await page.keyboard.press('Escape');
            await page.waitForTimeout(400);
            OUT('  [阳性对照已还原] 有选中=' + (await page.evaluate(state)).有选中);
          }
          // 还原：Esc 取消选中 + 重置视图
          await page.keyboard.press('Escape');
          await page.waitForTimeout(400);
          OUT('  [还原后] 有选中=' + (await page.evaluate(state)).有选中);
        }
        if (await page.evaluate(FLYOUT_OPEN)) await realClick(page, 'button[data-canvas-tool="tool-history"]');
      }
    } catch (e) { OUT('  [本相异常]', e && e.message); }

    // ── 把手相：左侧面板的拖宽把手，到底拖不拖得动 ────────────────────────
    // ★ **M257 / R110 两次记了「把手也点不到」**（M249 一次），
    //   **而那三次都只有落点读数、从来没有行为读数**——
    //   **F83 的反向：说「点不到」也要有行为读数，否则分不清「按不动」和「按了没反应」。**
    // 源码 `canvas-side-panel.tsx:131`：
    //   `absolute inset-y-0 right-0 z-40 w-4 translate-x-1/2 cursor-col-resize`
    //   ——**骑在面板右缘上，内侧 8px、外侧 8px**。**所以只采中心一个点会漏掉可拖的那一半。**
    OUT('\n################ 把手相：拖得动吗（默认状态） ################');
    const handleRows = [];
    try {
      const geo = await page.evaluate(() => {
        const aside = document.querySelector('aside.td-canvas-side-panel');
        const h = aside && (aside.querySelector('.cursor-col-resize') || aside.querySelector('[aria-label]'));
        if (!aside || !h) return { err: '没找到把手（' + (aside ? '有面板无把手' : '无面板') + '）' };
        const hr = h.getBoundingClientRect(), ar = aside.getBoundingClientRect();
        const samples = [0, 0.25, 0.5, 0.75, 1].map((f) => {
          // ★ **y 必须落在视口内**：把手是 `inset-y-0`、高约 830，
          //   写成 `hr.y + hr.height * 2` 会得到 y≈1730（视口只有 1000），
          //   **而 elementFromPoint 越界一律返回 null**——于是读数「全 null」，
          //   拖拽也等于在空气里拖。**第一版就这样栽了。**
          const x = hr.x + hr.width * f, y = Math.round(hr.y + hr.height * 0.3);
          const e = document.elementFromPoint(x, y);
          return { f, x: Math.round(x), 命中把手: !!(e && h.contains(e)),
                   落点: e ? e.tagName + '.' + String(e.className || '').split(' ').slice(0, 2).join('.') : 'null' };
        });
        return { 把手: [Math.round(hr.x), Math.round(hr.right), Math.round(hr.width)], 面板宽: Math.round(ar.width), samples };
      });
      if (geo.err) { OUT('  ⚠ ' + geo.err + '——本相不产出读数，如实记下'); }
      else {
        OUT('  把手 x ' + geo.把手[0] + '–' + geo.把手[1] + '（宽 ' + geo.把手[2] + '）· 面板宽 ' + geo.面板宽);
        geo.samples.forEach((sm) => OUT('    ' + (sm.命中把手 ? '✓' : '✗') + ' x=' + sm.x + ' 落点 ' + sm.落点));
        // ★ 行为读数：真拖一把，看面板宽度变不变
        const drag = async (x, y, dx) => {
          await page.mouse.move(x, y);
          await page.mouse.down();
          for (let i = 1; i <= 6; i++) { await page.mouse.move(x + (dx * i) / 6, y); await page.waitForTimeout(40); }
          await page.mouse.up();
          await page.waitForTimeout(500);
        };
        const w = () => page.evaluate(() => {
          const a = document.querySelector('aside.td-canvas-side-panel');
          return a ? Math.round(a.getBoundingClientRect().width) : null;
        });
        const attempts = [];
        for (const at of [['把手中心', 0.5], ['把手内侧 2px', 0.15], ['把手外侧 2px', 0.9]]) {
          const x = geo.把手[0] + geo.把手[2] * at[1];
          const y = await page.evaluate(() => {
            const h = document.querySelector('aside.td-canvas-side-panel .cursor-col-resize');
            if (!h) return null; const r = h.getBoundingClientRect();
            return Math.round(r.y + r.height * 0.3);   // ★ 同上：y 必须落在视口内
          });
          if (y == null) break;
          const before = await w();
          await drag(x, y, 100);
          const after = await w();
          const changed = before !== after;
          OUT('  [拖 ' + at[0] + ' x=' + Math.round(x) + '] 面板宽 ' + before + ' → ' + after
              + (changed ? '  ✓ 拖得动' : '  ✗ 没变'));
          attempts.push({ at: at[0], before, after, changed });
          if (changed) {                       // ★ 拖动了就原样拖回去
            await drag(x + 100, y, -100);
            OUT('    [已拖回] 面板宽 ' + (await w()));
          }
        }
        handleRows.push({ geo, attempts });
        OUT('  ★ 结论：' + (attempts.some((a) => a.changed)
          ? '★ **把手是拖得动的**——之前那几次「落点是 aside」的读数**不足以支持「拖不动」这个说法**'
          : '★ 三个位置都拖不动，与落点读数一致')
          + '（**落点采样只覆盖了把手的 x 范围，行为读数才是判据**）');
      }
    } catch (e) { OUT('  [本相异常]', e && e.message); }
    rows.push({ kind: '行为相', behavior, handleRows });

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
