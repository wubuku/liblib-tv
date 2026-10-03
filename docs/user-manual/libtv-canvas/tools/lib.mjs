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
export async function closePromos(page) {
  const report = [];
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
