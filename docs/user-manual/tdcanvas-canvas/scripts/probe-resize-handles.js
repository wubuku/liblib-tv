/**
 * probe-resize-handles.js —— 量「节点四角的缩放手柄，读者到底看不看得见」。
 *
 * 复现的断言（`10-tasks/edit-nodes.md`）：
 *   :311「选中节点，四角出现圆形缩放手柄。」
 *   :312「拖动任意一角向外/向内缩放。限制：最小 220×160，最大 1600×1200。」
 *   :326「缩放手柄会随画布缩放变小，在低缩放比例下只有十几像素。
 *         先用左下角缩放滑杆放大到 100% 以上，手柄会恢复到约 28px。」
 *   :263「图里两个节点都带蓝框（框边那圈圆点是选中态的缩放手柄）」
 *
 * 为什么要新写一支：`ResizeHandle` 在源码里是
 *   `absolute z-50 size-7 -left-[14px] -top-[14px] cursor-nwse-resize`
 * ——**没有任何背景、边框或阴影**，是个纯透明命中区。
 * 所以「DOM 里数得出 4 个」与「读者看得见 4 个圆点」是两件事，
 * 而手册 :311 与 :263 说的都是**看得见**。本探针量的是看得见的那件事：
 *   ① 4 个手柄元素的 DOM 事实（数量、盒模型、计算样式）
 *   ② 框边**端口圆点**的数量与盒模型（对照组：它们是真的有描边的可见圆点）
 *   ③ **截图像素读数**：手柄四角窗口 vs 边框中点对照窗口，谁亮
 *   ④ 三档缩放（50% / 100% / 150%）下 28px 命中区折算成屏幕像素是多少
 *
 * 用法：
 *   node scripts/probe-resize-handles.js [baseURL] [profile]
 *
 * ★ **用一次性 profile。** 本探针建自己的画布与节点，不碰共享 profile，
 *   也不删任何东西——它只建不删，所以不需要还原。
 *
 * ── 这支探针自己的纪律 ──
 * 1. **零结果先怀疑判据。** 手柄「数出来 0 个」和「截图像素读不出来」是两种
 *    完全不同的失败：前者是选择器没命中，后者才是「不可见」。两者分开报。
 * 2. **阳性对照必须先成立。** 端口圆点（`.size-3.rounded-full`，源码里带 `border-2`）
 *    是「可见圆点」的阳性对照——它读不出亮斑，整个像素判据就是坏的，不是产品的问题。
 * 3. **一条读数只证明一件事。** 「框上有 4 个 28px 命中区」只证明命中区存在；
 *    「框上没有亮斑」才是不可见的证据。两者都要报，缺一不可。
 * 4. **点节点一律用真实鼠标点击**（`page.mouse.click`），不用 `el.click()`——
 *    React 合成事件实测不触发选中。
 */
const { chromium } = require(process.env.PLAYWRIGHT_PATH ||
  '/Users/yangjiefeng/.nvm/versions/node/v24.6.0/lib/node_modules/@playwright/test/node_modules/playwright');

const BASE = (process.argv[2] || 'http://localhost:3000').replace(/\/$/, '');
const PROFILE = process.argv[3] || '/tmp/m228-handles-profile';
const say = (...a) => console.log(a.join(' '));
const round = (n) => Math.round(n * 10) / 10;

(async () => {
  const ctx = await chromium.launchPersistentContext(PROFILE, {
    headless: true, viewport: { width: 1440, height: 900 },
  });
  const page = await ctx.newPage();
  const errs = [];
  page.on('pageerror', (e) => errs.push(String(e).slice(0, 140)));

  try {
    // ── 0. 前置对照：这是 TDCanvas，且 list 页打得开 ──
    await page.goto(BASE + '/', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);
    const h1 = await page.evaluate(() => document.querySelector('h1,h2')?.textContent?.trim() || '');
    const newBtn = page.getByRole('button', { name: /新建画布/ });
    const newBtnCount = await newBtn.count();
    say('[前置对照] 标题 =', JSON.stringify(h1), '「新建画布」按钮数 =', newBtnCount);
    if (newBtnCount !== 1) {
      say('[前置对照不成立] 不是可用的 TDCanvas 首页，中止（不报 0）。');
      await ctx.close();
      process.exit(3);
    }

    // ── 1. 建一张画布（真实点击） ──
    await newBtn.click();
    await page.waitForTimeout(2500);
    say('[1] 建画布后 URL =', page.url());
    const canvasUrl = page.url();
    const dockOk = await page.locator('.td-canvas-dock').count();
    say('[1] .td-canvas-dock 数 =', dockOk, dockOk > 0 ? '（画布壳在）' : '（不在 → 对照失败）');

    // ── 2. 建一个文本节点（点中央的「文字创作」芯片） ──
    const chip = page.getByText('文字创作', { exact: true }).first();
    const chipCount = await chip.count();
    say('[2] 「文字创作」芯片数 =', chipCount);
    if (chipCount === 0) {
      say('[2] 芯片没找到，中止。');
      await ctx.close();
      process.exit(3);
    }
    await chip.click();
    await page.waitForTimeout(2000);
    const nodeCount = await page.locator('[data-node-id]').count();
    say('[2] 建后 [data-node-id] 数 =', nodeCount);

    // ── 3. 真实鼠标点选节点 ──
    const nb = await page.evaluate(() => {
      const n = document.querySelector('[data-node-id]');
      if (!n) return null;
      const b = n.getBoundingClientRect();
      return { cx: b.left + b.width / 2, cy: b.top + b.height / 2 };
    });
    if (!nb) { say('[3] 找不到节点，中止。'); await ctx.close(); process.exit(3); }
    await page.mouse.click(nb.cx, nb.cy);
    await page.waitForTimeout(1200);
    const selCount = await page.evaluate(() =>
      document.querySelectorAll('[data-node-id].z-50, [data-node-id] [class*="ring"]').length);
    say('[3] 点选后带选中描边的节点数 =', selCount, '（z-50 / ring 是粗筛，只作记录）');

    // ── 4. ① 手柄 DOM 事实 ② 端口圆点（阳性对照） ──
    const domFacts = await page.evaluate(() => {
      // ★ round 必须在这里重定义一次：外层那个是 Node 侧的函数，
      //   page.evaluate 的代码跑在页面上下文里，拿不到模块作用域（M228 实测）。
      const round = (n) => Math.round(n * 10) / 10;
      const node = document.querySelector('[data-node-id]');
      if (!node) return { err: '没有节点' };
      const nb = node.getBoundingClientRect();
      // 手柄：源码是 `absolute z-50 size-7` + 负偏移
      const handles = Array.from(node.querySelectorAll('div.absolute.z-50.size-7')).map((el) => {
        const b = el.getBoundingClientRect();
        const cs = getComputedStyle(el);
        return {
          cls: el.className,
          w: round(b.width), h: round(b.height),
          cx: round(b.left + b.width / 2), cy: round(b.top + b.height / 2),
          bg: cs.backgroundColor, border: cs.borderTopWidth + ' ' + cs.borderTopColor,
          shadow: cs.boxShadow, opacity: cs.opacity, radius: cs.borderRadius,
        };
      });
      // 端口圆点：源码 ConnectionHandleDot 内层是 `size-3 rounded-full border-2`
      const dots = Array.from(node.querySelectorAll('div.size-3.rounded-full')).map((el) => {
        const b = el.getBoundingClientRect();
        const cs = getComputedStyle(el);
        return {
          w: round(b.width), h: round(b.height),
          cx: round(b.left + b.width / 2), cy: round(b.top + b.height / 2),
          bg: cs.backgroundColor, border: cs.borderTopWidth + ' ' + cs.borderTopColor,
          opacity: cs.opacity,
        };
      });
      return {
        nodeBox: { x: round(nb.left), y: round(nb.top), w: round(nb.width), h: round(nb.height) },
        handles, dots,
      };
    });
    say('--- ④ DOM 事实 ---');
    say('节点盒模型', JSON.stringify(domFacts.nodeBox || domFacts));
    say('手柄数 =', (domFacts.handles || []).length);
    for (const h of domFacts.handles || []) {
      say('   手柄', h.cls.replace(/\s+/g, ' ').slice(0, 60));
      say('      盒', h.w + 'x' + h.h, '@中心', h.cx + ',' + h.cy,
        '| background=', h.bg, '| border=', h.border, '| shadow=', h.shadow,
        '| opacity=', h.opacity, '| radius=', h.radius);
    }
    say('端口圆点数 =', (domFacts.dots || []).length, '（阳性对照：它们应当有描边且非透明）');
    for (const d of domFacts.dots || []) {
      say('   圆点', d.w + 'x' + d.h, '@', d.cx + ',' + d.cy,
        '| bg=', d.bg, '| border=', d.border, '| opacity=', d.opacity);
    }

    // ── 5. ③ 截图像素读数：手柄四角 vs 边框中点对照 ──
    const px = await page.evaluate(() => {
      const b = document.querySelector('[data-node-id]').getBoundingClientRect();
      return { x: b.left, y: b.top, w: b.width, h: b.height };
    });
    const clip = {
      x: Math.max(0, Math.floor(px.x - 30)), y: Math.max(0, Math.floor(px.y - 30)),
      width: Math.ceil(px.w + 60), height: Math.ceil(px.h + 60),
    };
    const shot = '/tmp/m228-handles-100.png';
    await page.screenshot({ path: shot, clip });
    say('--- ③ 截图像素读数（截图 =', shot, '，裁剪框 =', JSON.stringify(clip), '）---');

    // ── 6. ④ 缩放下命中区的屏幕像素尺寸：手册 :326 的可数断言 ──
    // ★ 用缩放滑杆（input[type=range]，5..500）逐档设值，不靠滚轮：
    //   第一版在画布上滚滚轮，5 次读数全是 100%——**这不是产品不能缩放**，
    //   是我把指针放在节点正中，滚轮被节点吃掉了。零结果先怀疑判据（M228）。
    const setZoom = (v) => page.evaluate((val) => {
      const el = document.querySelector('input[type=range]');
      if (!el) return null;
      // React 受控输入必须走原型上的原生 setter，直接赋值不会触发 onChange
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      setter.call(el, String(val));
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      return el.value;
    }, v);
    const readZoom = () => page.evaluate(() => {
      const cands = Array.from(document.querySelectorAll('button,span,div'))
        .filter((e) => e.children.length === 0 && /^\d{1,3}%$/.test((e.textContent || '').trim()));
      const e = cands.find((x) => {
        const b = x.getBoundingClientRect();
        return b.width > 0 && b.height > 0 && b.left < 700 && b.top > 700;
      });
      return e ? e.textContent.trim() : null;
    });
    const readHandle = () => page.evaluate(() => {
      const node = document.querySelector('[data-node-id]');
      const el = node && node.querySelector('div.absolute.z-50.size-7');
      if (!el) return null;
      const b = el.getBoundingClientRect();
      return { w: Math.round(b.width * 10) / 10, h: Math.round(b.height * 10) / 10 };
    });

    say('--- ④ 缩放 vs 手柄命中区屏幕尺寸（手册 :326 的可数断言）---');
    for (const z of [25, 50, 76, 100, 150, 200]) {
      const asked = await setZoom(z);
      await page.waitForTimeout(600);
      const readout = await readZoom();
      const h = await readHandle();
      say('  滑杆设为', String(z).padEnd(4), '→ 滑杆读数', String(asked).padEnd(4),
        '| 界面读数', String(readout).padEnd(6),
        '| 手柄命中区 =', h ? h.w + 'x' + h.h + ' px' : '(没找到)');
    }

    // ── 7. ⑤ 悬停读光标：手柄唯一的可发现性线索 ──
    // 源码：ResizeHandle 是 `cursor-nwse-resize`，ConnectionHandleDot 是 `cursor-crosshair`。
    // 所以「角上什么都没有、但光标会变」是可测的；而这正是读者唯一能认出缩放区的线索。
    say('--- ⑤ 悬停光标（手柄唯一的可发现性线索）---');
    const geo = await page.evaluate(() => {
      const node = document.querySelector('[data-node-id]');
      const h = node.querySelector('div.absolute.z-50.size-7');
      const hb = h.getBoundingClientRect();
      const dot = node.querySelector('div.size-3.rounded-full');
      const db = dot.getBoundingClientRect();
      const nb = node.getBoundingClientRect();
      return {
        tl: [hb.left + hb.width / 2, hb.top + hb.height / 2],
        br: [hb.right - hb.width / 2, hb.bottom - hb.height / 2],
        dot: [db.left + db.width / 2, db.top + db.height / 2],
        mid: [nb.left + nb.width / 2, nb.top + 12],
      };
    });
    for (const [name, pt] of [['左上角', geo.tl], ['右下角', geo.br],
      ['端口圆点', geo.dot], ['节点顶部中央', geo.mid]]) {
      await page.mouse.move(Math.round(pt[0]), Math.round(pt[1]));
      await page.waitForTimeout(350);
      const r = await page.evaluate(([x, y]) => {
        const el = document.elementFromPoint(x, y);
        return el ? { cls: (el.className || '').toString().slice(0, 46), cursor: getComputedStyle(el).cursor }
          : { cls: '(没有元素)', cursor: '(没有元素)' };
      }, [Math.round(pt[0]), Math.round(pt[1])]);
      say('  ', name.padEnd(7), '落点元素 =', r.cls, '| cursor =', r.cursor);
    }

    if (errs.length) say('页面报错：', errs.slice(0, 3).join(' | '));
    say('画布 URL =', canvasUrl);
    say('profile =', PROFILE, '（一次性，未删任何东西）');
  } finally {
    await ctx.close();
  }
})().catch((e) => { console.error('探针异常：', e); process.exit(1); });
