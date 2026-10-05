// LibTV 画布手册取证 —— 共用无头浏览器 harness。
//
// 约定：
//   - 全部脚本通过本模块启动 **无头** Chromium + 已提取的 storageState，
//     绝不 attach、不复用、不干扰用户自己那个有头窗口（CDP 9222）。
//   - 每次启动都是全新的独立 user-data-dir，互不串味，也不需要再登录。
//   - viewport / locale / 时区 / reduced-motion 固定，保证截图可比。
//   - 站点有「单画布单编辑者保护」：同一 project 在第二处打开会给遮罩。
//     所以默认用 HANDOFF_PROJECT 之外的测试项目，见 PROGRESS.md 的项目台账。
import { chromium } from 'playwright';
import { existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { readFile } from 'node:fs/promises';

const HERE = dirname(fileURLToPath(import.meta.url));
export const AUTH = resolve(HERE, '.auth/libtv-storage-state.json');
export const ORIGIN = 'https://www.liblib.tv';
export const SHOTS = resolve(HERE, '../screenshots');

export const VIEWPORT = { width: 1440, height: 810 };

export async function launch(opts = {}) {
  if (!existsSync(AUTH)) {
    throw new Error(`缺少登录态 ${AUTH}；先运行 node tools/extract-auth.mjs`);
  }
  const storageState = JSON.parse(await readFile(AUTH, 'utf8'));
  const browser = await chromium.launch({
    headless: true,
    args: [
      '--disable-blink-features=AutomationControlled',
      '--disable-features=IsolateOrigins,site-per-process',
    ],
  });
  const ctx = await browser.newContext({
    storageState,
    viewport: opts.viewport ?? VIEWPORT,
    locale: 'zh-CN',
    timezoneId: 'Asia/Shanghai',
    deviceScaleFactor: 2,
    // 'reduce' 是为了让截图可比（动画停在中途不会每次都不一样）。
    // ⚠️ 但要**按需覆盖**：站点有些元素靠动画驱动 inline opacity，
    //    在 'reduce' 下过渡被跳过，它们可能停在 opacity 0 —— 也就是
    //    「DOM 里有、屏幕上没有」。要核实某个元素到底显不显示，
    //    用 launch({ reducedMotion: 'no-preference' }) 再量**整条祖先链的 opacity 连乘**
    //    （只看它自己那一层会读出假的稳定值，CI-2 就栽在这儿）。
    //
    // ⭐⭐ Batch DH 实测量化了这条的影响（别只当「可能有动画」）：
    //   无头 Chrome **默认报 `prefers-reduced-motion: reduce`**。
    //   站点大量使用 Tailwind 的 `motion-safe:` 前缀，它编译成
    //   `@media (prefers-reduced-motion: no-preference)` ⇒ 在此环境下**整条规则不匹配**。
    //   实测对照（`z-[180]` 那个全屏层）：
    //     无头默认          → transition-duration: 0s   transition-property: all
    //     覆盖 no-preference → transition-duration: 0.2s transition-property: opacity
    //   ⇒ **凡是要断言「某处有/没有动画 / 淡入淡出读不到」的结论，
    //     必须用 `reducedMotion: 'no-preference'` 重测**，否则量的是被关掉的规则。
    //   ⛔ 只量 **opacity 最终值** 的读数不受影响（opacity 不是被这条 media query 管的）。
    reducedMotion: opts.reducedMotion ?? 'reduce',
    colorScheme: 'light',
  });
  ctx.setDefaultTimeout(opts.timeout ?? 20000);
  const page = await ctx.newPage();
  return { browser, ctx, page };
}

/** 打开一个 URL 并等到画布 shell 稳定（字体就绪 + React Flow 挂载 + 网络静默）。 */
export async function open(page, url, { settle = 1200 } = {}) {
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => {});
  await page.evaluate(() => document.fonts?.ready).catch(() => {});
  await page.waitForTimeout(settle);
  return page;
}

/** 探测是否命中「单画布单编辑者保护」遮罩。返回 true 表示这个项目被别处占用。 */
export async function isEditorLocked(page) {
  return page.evaluate(() => {
    const t = document.body.innerText || '';
    return /会话已过期|请刷新页面以继续编辑/.test(t);
  });
}

/** Skill 自带的目标高亮脚本绝对路径（tools → libtv-canvas → user-manual → docs → 仓库根）。 */
export const HIGHLIGHT_JS = resolve(HERE, '../../../../.agents/skills/web-studio-user-manual/scripts/highlight-target.js');

/** 注入目标高亮脚本（幂等）。 */
export async function injectHighlight(page) {
  await page.addScriptTag({ path: HIGHLIGHT_JS });
}

/**
 * 拍一张带目标高亮的截图。
 * @param {import('playwright').Locator} locator 目标元素
 * @param {string} file 相对 screenshots/ 的文件名
 * @param {{step?:number, note?:string, clip?:{x,y,width,height}}} opts
 */
export async function shotHighlighted(page, locator, file, opts = {}) {
  await injectHighlight(page);
  await locator.scrollIntoViewIfNeeded();
  if (opts.step != null) {
    await locator.evaluate((el, step) => window.canvasUserManualHighlight.show(el, { step }), opts.step);
  }
  await page.waitForTimeout(220);
  await page.screenshot({ path: resolve(SHOTS, file), ...(opts.clip ? { clip: opts.clip } : {}) });
  if (opts.step != null) await page.evaluate(() => window.canvasUserManualHighlight.clear());
  return file;
}

/** 不带高亮拍一张（概览图 / 结果图）。 */
export async function shot(page, file, opts = {}) {
  await page.screenshot({ path: resolve(SHOTS, file), ...(opts.clip ? { clip: opts.clip } : {}) });
  return file;
}

/**
 * 关掉所有「不该出现在取证画面里」的浮层：促销弹窗、引导蒙层、下载提示等。
 * 站点用 Mantine Modal。实测 `.mantine-Modal-root` 可能是空的壳节点，真正的
 * 遮罩是 `.mantine-Modal-overlay`，且促销弹窗的关闭按钮不在 `.mantine-Modal-content`
 * 里（aria-label=关闭 那个属于顶部横幅）。所以这里按可靠性排序：Escape → 点遮罩 → 找关闭钮。
 * 站点有单画布单编辑者锁，那个遮罩**不能**关（它是被测行为本身），因此先识别再关。
 */
/**
 * ⭐⭐⭐⭐ 关掉**非 Mantine 模态**的固定定位推广浮层。
 *
 * 起因（Batch FD-3 实测）：「Agent 已升级为 TV Director」是
 *   `<div class="fixed w-[280px] max-w-[calc(100vw-24px)]">`，**z-index 101**，
 *   ⛔ 不是 `.mantine-Modal-overlay` ⇒ 老版 closePromos 连关 5 轮都关不掉，
 *   它会一直挡着画面、把 innerText 读数搅浑。
 *
 * ⛔ 安全边界（必须保留）：只点**纯 dismiss 文案**的白名单按钮。
 *   ⛔ **绝不点 `去体验` / `开始体验`** —— 那会真的进入体验流程。
 *   白名单里的每一个字都是「知道了 / 我知道了 / 关闭 / 不再提示」，
 *   点下去的唯一后果是这个浮层消失。
 * 判据要窄：position:fixed + 尺寸 200~600 + 自身文案命中推广词 + 按钮文案在白名单里。
 */
const 关浮层白名单 = ['知道了', '我知道了', '知道了！', '关闭', '不再提示', '以后再说', '稍后再说'];

async function closeFixedPromos(page, max = 4) {
  const 关掉的 = [];
  for (let i = 0; i < max; i += 1) {
    const 目标 = await page.evaluate((白名单) => {
      const 推广词 = /已升级|新功能|来试|体验一下|限时|推荐|抢先|内测/i;
      const 可见 = (el) => {
        const r = el.getBoundingClientRect();
        return r.width > 0 && r.height > 0;
      };
      const 浮层 = [...document.querySelectorAll('div.fixed, section.fixed, aside.fixed')]
        .filter((el) => {
          if (!可见(el)) return false;
          const cs = getComputedStyle(el);
          if (cs.position !== 'fixed') return false;
          const r = el.getBoundingClientRect();
          if (r.width < 180 || r.width > 640 || r.height < 120 || r.height > 720) return false;
          return 推广词.test((el.innerText || '').slice(0, 300));
        });
      for (const f of 浮层) {
        const btn = [...f.querySelectorAll('button,[role="button"]')]
          .find((b) => 可见(b) && 白名单.includes((b.innerText || b.getAttribute('aria-label') || '').trim()));
        if (!btn) continue;
        const r = f.getBoundingClientRect();
        const br = btn.getBoundingClientRect();
        return {
          文字: (f.innerText || '').replace(/\s+/g, ' ').slice(0, 80),
          按钮: (btn.innerText || btn.getAttribute('aria-label') || '').trim(),
          框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          点击点: [Math.round(br.x + br.width / 2), Math.round(br.y + br.height / 2)],
        };
      }
      return null;
    }, 关浮层白名单);
    if (!目标) break;
    await page.mouse.click(目标.点击点[0], 目标.点击点[1]);
    await page.waitForTimeout(400);
    关掉的.push(目标);
  }
  return 关掉的;
}

export async function closePromos(page) {
  const report = [];
  // ⭐ 先收非模态的 fixed 推广浮层（老版漏了这一类，见上方注释）
  const fixed = await closeFixedPromos(page);
  for (const f of fixed) report.push({ 模态: false, 文字: f.文字, 按钮: f.按钮, 框: f.框, 怎么关的: 'fixed-按钮', gone: true });
  for (let i = 0; i < 5; i += 1) {
    const info = await page.evaluate(() => {
      const ov = [...document.querySelectorAll('.mantine-Modal-overlay')].filter((m) => {
        const r = m.getBoundingClientRect();
        return r.width > 0 && r.height > 0;
      });
      if (!ov.length) return null;
      const host = ov[ov.length - 1].parentElement || ov[ov.length - 1];
      const label = (host.innerText || '').replace(/\s+/g, ' ').slice(0, 100);
      const btns = [...host.querySelectorAll('button,[role="button"]')].map((b) => b.getAttribute('aria-label') || (b.innerText || '').trim().slice(0, 12));
      return { label, btns, hostSel: host.className?.toString?.().slice(0, 50) };
    });
    if (!info) break;

    let how = null;
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(350);
    let gone = await page.evaluate(() => ![...document.querySelectorAll('.mantine-Modal-overlay')].some((m) => m.getBoundingClientRect().width > 0));
    if (gone) how = 'Escape';

    if (!gone) {
      const closeBtn = page.locator('.mantine-Modal-overlay').last().locator('xpath=..').locator('button[aria-label="关闭"], button[aria-label="Close"]');
      await closeBtn.first().click({ timeout: 3000 }).then(() => { how = 'close-btn'; }).catch(() => {});
      await page.waitForTimeout(350);
      gone = await page.evaluate(() => ![...document.querySelectorAll('.mantine-Modal-overlay')].some((m) => m.getBoundingClientRect().width > 0));
    }
    if (!gone) {
      await page.locator('.mantine-Modal-overlay').last().click({ position: { x: 5, y: 5 }, timeout: 3000 }).then(() => { how = 'overlay-click'; }).catch(() => {});
      await page.waitForTimeout(350);
      gone = await page.evaluate(() => ![...document.querySelectorAll('.mantine-Modal-overlay')].some((m) => m.getBoundingClientRect().width > 0));
    }
    report.push({ modal: info.label, btns: info.btns.slice(0, 6), how, gone });
    if (!gone) break;
  }
  return report;
}

/** 打印页面壳信息 + 一级可交互表面，用于快速建立候选任务清单。 */
export async function shell(page) {
  return page.evaluate(() => {
    const vis = (el) => {
      const r = el.getBoundingClientRect();
      return r.width > 0 && r.height > 0;
    };
    const btns = [...document.querySelectorAll('button,[role="button"],[role="menuitem"],[role="tab"]')]
      .filter(vis)
      .map((b) => ({
        text: (b.innerText || b.getAttribute('aria-label') || '').trim().slice(0, 24),
        aria: b.getAttribute('aria-label') || null,
        role: b.getAttribute('role'),
        testid: b.getAttribute('data-testid'),
        x: Math.round(b.getBoundingClientRect().x),
        y: Math.round(b.getBoundingClientRect().y),
      }))
      .filter((b) => b.text);
    return {
      url: location.href,
      title: document.title,
      buttons: btns,
      dialogs: [...document.querySelectorAll('[role="dialog"]')].filter(vis).map((d) => (d.innerText || '').slice(0, 200)),
      text: (document.body.innerText || '').slice(0, 1500),
    };
  });
}
