/**
 * probe-viewport-buttons.js —— 量「一条路由上有几个按钮真的落在视口里」。
 *
 * 复现的断言：
 *   `20-reference.md`「ComfyUI 本地页整页 17 个可见按钮，落在 `<main>` 内的为 0」
 *   —— M229 实测：这个 17 **只在右侧 Agent 面板「打开」时成立**，
 *   而面板**默认收起**，且**收起的面板仍按 440px 宽排在视口之外**。
 *
 * 用法：
 *   node scripts/probe-viewport-buttons.js [baseURL] [profile]
 *   node scripts/probe-viewport-buttons.js http://localhost:3000 /tmp/m229-fresh2
 *
 * ★ **只用一次性 profile。** 它只读 DOM 形状、只点「打开/收起 Agent 面板」这一个开关，
 *   不点任何删除类按钮、不改任何画布数据；但**面板开合状态会写进 localStorage**，
 *   所以必须用自己的 profile，且**收尾把面板收回初始态**。
 *
 * ══ 这支探针存在的理由：判「看得见」有**四种**不 ══
 *
 * 1. `0 × 0`（M127）
 * 2. `opacity: 0`（M117）
 * 3. `visibility: hidden`
 * 4. ★ **落在视口外**（M229 新增）——**前三种都会让 `getBoundingClientRect()` 或
 *    计算样式露馅，第四种不会**：收起的面板 `aside` 的 rect 是 `(1280, 0, 440, 900)`，
 *    宽高都是正的、`opacity: 1`、`visibility: visible`、祖先链也正常，
 *    **只有一条：`left` 恰好等于视口宽度**。
 *
 * ★ **所以 M57 那次「整页 17 个可见按钮」是判据的产物，不是产品的**：
 * 面板收起时那 11 个按钮确实还在 DOM 里、也确实「不隐藏」，**只是整个在屏幕外**。
 * **`scrollWidth == clientWidth`（没有横向滚动条）意味着它们够不着**——
 * 「存在」「不隐藏」「够得着」是三件事。
 *
 * ── 纪律 ──
 * 1. **两个读数必须一起报**：`predicate-visible`（老判据）与 `in-viewport`（新判据）
 *    的差值本身就是结论。**只报前者会得到一个看起来很正常的假数。**
 * 2. **收尾还原放 `finally`**（M224 F31 立的规矩）。
 * 3. **前置对照**：先确认这条路由确实渲染了应用壳（`aside` 在），否则「0 个按钮」
 *    可能是空 profile 伪造出来的（M199 的坑）。
 */
const { chromium } = require(process.env.PLAYWRIGHT_PATH ||
  '/Users/yangjiefeng/.nvm/versions/node/v24.6.0/lib/node_modules/@playwright/test/node_modules/playwright');

const BASE = (process.argv[2] || 'http://localhost:3000').replace(/\/$/, '');
const PROFILE = process.argv[3] || '/tmp/m229-viewport-profile';
const ROUTES = ['/comfyui-local', '/', '/config'];
const say = (...a) => console.log(a.join(' '));

(async () => {
  const ctx = await chromium.launchPersistentContext(PROFILE, {
    headless: true, viewport: { width: 1280, height: 900 },
  });
  const page = await ctx.newPage();
  let openedByProbe = false;

  // 页面里跑的函数：外层的 helper 拿不到（page.evaluate 跑在页面上下文，M228 F38）
  const snap = () => page.evaluate(() => {
    const W = window.innerWidth, H = window.innerHeight;
    const de = document.documentElement;
    const notHidden = (el) => {
      const b = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      return b.width > 0 && b.height > 0 &&
        cs.visibility !== 'hidden' && cs.display !== 'none' && cs.opacity !== '0';
    };
    const inViewport = (el) => {
      const b = el.getBoundingClientRect();
      return b.right > 0 && b.left < W && b.bottom > 0 && b.top < H;
    };
    const main = document.querySelector('main');
    // ★ 不能直接取第一个 aside：`/config` 页自己也有一个 <aside>（左栏 260px 宽），
    //   取错了会报出 [150,207,260,140] 这种**面板的坐标**——**报错的尺子会教错人**。
    //   按「里面有没有面板自己的开关」认，不按标签名认。
    const aside = Array.from(document.querySelectorAll('aside')).find((el) =>
      el.querySelector('button[aria-label="收起 Agent 面板"], button[aria-label="打开 Agent"]'))
      || null;
    const btns = Array.from(document.querySelectorAll('button')).filter(notHidden);
    const links = Array.from(document.querySelectorAll('a')).filter(notHidden);
    const ab = aside ? aside.getBoundingClientRect() : null;
    const label = (b) => (b.getAttribute('aria-label') || b.textContent || '').trim() || '(无文字)';
    return {
      innerW: W, innerH: H,
      scrollW: de.scrollWidth, clientW: de.clientWidth,
      // 老判据（M57 用的那个）
      predicateVisible: btns.length,
      // 新判据：真的落在视口内
      inViewport: btns.filter(inViewport).length,
      inMain: main ? btns.filter((b) => main.contains(b)).length : -1,
      visibleLinks: links.length,
      asideRect: ab ? [Math.round(ab.left), Math.round(ab.top), Math.round(ab.width), Math.round(ab.height)] : null,
      asideInViewport: ab ? inViewport(aside) : null,
      panelOpen: document.querySelectorAll('button[aria-label="收起 Agent 面板"]').length > 0,
      topBarButtons: btns.filter(inViewport)
        .map((b) => label(b)).slice(0, 8),
      outOfViewButtons: btns.filter((b) => !inViewport(b)).map(label).slice(0, 12),
    };
  });

  try {
    for (const route of ROUTES) {
      await page.goto(BASE + route, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(2200);

      // ★ 前置对照：应用壳在不在。空 profile 会伪造出「0 个按钮」（M199 的坑）。
      const shell = await page.evaluate(() => ({
        aside: Array.from(document.querySelectorAll('aside')).some((el) =>
          el.querySelector('button[aria-label="收起 Agent 面板"], button[aria-label="打开 Agent"]')),
        nav: !!document.querySelector('nav'),
        title: document.title,
      }));
      if (!shell.aside && !shell.nav) {
        say(`[前置对照不成立] ${route} 上没有应用壳，跳过（**不报 0**）。`);
        continue;
      }

      const a = await snap();
      say(`\n=== ${route} ===  视口 ${a.innerW}x${a.innerH}，scrollWidth ${a.scrollW}（clientWidth ${a.clientW}）`);
      say(`  收起态：predicate-visible ${a.predicateVisible} / 视口内 ${a.inViewport} / <main> 内 ${a.inMain} / 导航链接 ${a.visibleLinks}`);
      say(`    aside rect ${JSON.stringify(a.asideRect)} 在视口内=${a.asideInViewport} 面板开=${a.panelOpen}`);
      say(`    视口内按钮：${a.topBarButtons.join(' / ')}`);
      if (a.outOfViewButtons.length) {
        say(`    ★ 视口外却「不隐藏」的按钮 ${a.outOfViewButtons.length} 个：${a.outOfViewButtons.join(' / ')}`);
      }

      // 点开面板复测一次
      const openBtn = page.locator('button[aria-label="打开 Agent"]').first();
      if (await openBtn.count() === 1) {
        await openBtn.click();
        await page.waitForTimeout(900);
        openedByProbe = true;
        const b = await snap();
        say(`  展开态：predicate-visible ${b.predicateVisible} / 视口内 ${b.inViewport} / <main> 内 ${b.inMain}`);
        say(`    aside rect ${JSON.stringify(b.asideRect)} 在视口内=${b.asideInViewport} 面板开=${b.panelOpen}`);
        say(`  ★ 差值：predicate-visible ${a.predicateVisible} 与 视口内 ${a.inViewport} 相差 ${a.predicateVisible - a.inViewport} 个`
          + `——**那 ${a.predicateVisible - a.inViewport} 个不是「隐藏」，是「在视口外」**`);
      }
    }
    say('\n结论口径：「predicate-visible」只说明元素有几何且没被隐藏，**不说明读者够得着**；'
      + '要报数就得同时报「视口内」那个。');
  } finally {
    // ★ 还原必须放 finally（M224 F31）
    try {
      const collapse = page.locator('button[aria-label="收起 Agent 面板"]');
      if (openedByProbe && (await collapse.count()) === 1) {
        await collapse.first().click({ force: true });
        await page.waitForTimeout(600);
        const s = await snap();
        say(`[还原] 已收回 Agent 面板（视口内按钮回到 ${s.inViewport}）`);
      }
    } catch (e) {
      say('[还原失败]', String(e).slice(0, 120), '——**profile 是一次性的，不影响共享数据**');
    }
    await ctx.close();
  }
})().catch((e) => { console.error('探针异常：', e); process.exit(1); });
