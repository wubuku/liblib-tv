/* probe-panel-counts.js —— 数「某一个弹层里有几项、哪几项没勾」（M248 建立）
 *
 * 用法：
 *   CANVAS_URL=/canvas/<id> node scripts/probe-panel-counts.js
 *
 * ★ **为什么通用转储答不了这件事**（F57）：
 *   `probe-visible-strings.js` 只回答「这个字符串在不在屏幕上」，
 *   **而这里问的是「这个面板里有几项」「哪几项没勾」——那是容器内计数。**
 *   标题栏、工具条、Dock、弹窗的字符串在可见文字池里长得一模一样，
 *   **池子天然不区分容器**。
 *
 * ★★ **M248 当场踩的两个方向相反的错，都长得像真读数**：
 *   ① **去重按「元素」**——一个复选项在 DOM 里通常是
 *      `label > input.ant-checkbox-input + span.ant-checkbox-inner` **三个元素**，
 *      于是 **14 项被数成 43**。
 *      ★ 修法：**按最内层共同容器归并**（`input.closest('label')`，退回 `parentElement`），
 *      **按那个容器的身份去重**。修后 15（14 项快捷工具 + 1 个「显示按钮文字」独立开关）。
 *   ② **筛选按类名正则**——找画布右键菜单时用了 `/menu|dropdown|popover|context/i`，
 *      **而那个容器叫 `fixed z-[80] w-[212px]`，一个词都不含**，于是 **6 项菜单被判成 0 个容器**。
 *      ★ 修法：这一类「层」的判据是 **`position: fixed/absolute` + 非零几何**（外加 z-index 高的排前），
 *      **类名只是线索、不是判据**。
 *   ★ **两个数（43 和 0）都比「没有读数」更坏**——它们看起来是量出来的。
 *
 * ★ **纪律**：不点「保 存」（会把勾选写进本机设置）；不点任何删除类或计费类按钮。
 */

// M248 探针：只数「自定义工具栏」弹窗里那 14 项，以及哪几项没勾。
//
// 为什么要单独一支：通用转储（probe-visible-strings.js）只能回答
// 「这个字符串在不在屏幕上」——**而这里问的是「这个面板里有几项」「哪几项没勾」**，
// 那是**容器内计数**，两者不是一回事（F57）。
//
// 纪律：无头；真实鼠标点击；finally 关闭；只开面板、只读，**不点「保 存」**
// （保存会把勾选写进本机设置）；不点任何删除类或计费类按钮。
const { chromium } = require(process.env.PLAYWRIGHT_PATH ||
  '/Users/yangjiefeng/.nvm/versions/node/v24.6.0/lib/node_modules/@playwright/test/node_modules/playwright');
const APP = process.env.TD_APP || 'http://localhost:3000';
const PROFILE = process.env.TD_PROBE_PROFILE || '/tmp/m244-profile';
const CANVAS = process.env.CANVAS_URL || '/canvas/H4UgDBdT3NxvK_C5MLMq5';
const say = (...a) => console.log(...a);
const J = (o) => JSON.stringify(o, null, 2);

async function realClick(page, re) {
  const box = await page.evaluate((r) => {
    const rx = new RegExp(r);
    const hit = (s) => rx.test(s || '');
    const el = Array.from(document.querySelectorAll('button,[role="button"],[role="tab"],a,li'))
      .find((x) => hit(x.getAttribute('aria-label')) || hit(x.getAttribute('title')) ||
                    hit((x.innerText || '').replace(/\s+/g, ' ').trim()));
    if (!el) return null;
    const q = el.getBoundingClientRect();
    return { x: q.x + q.width / 2, y: q.y + q.height / 2, w: q.width, h: q.height };
  }, re);
  if (!box) return { ok: false, why: 'no match: ' + re };
  if (!box.w || !box.h) return { ok: false, why: 'zero-size' };
  await page.mouse.click(box.x, box.y);
  return { ok: true };
}

(async () => {
  const ctx = await chromium.launchPersistentContext(PROFILE, {
    headless: true, viewport: { width: 1600, height: 1000 },
  });
  const page = ctx.pages()[0] || await ctx.newPage();
  try {
    await page.goto(APP + CANVAS, { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);
    say('[选中图片节点]', J(await realClick(page, '^55dd39e3')));
    await page.waitForTimeout(1200);
    say('[点更多]', J(await realClick(page, '^更多$')));
    await page.waitForTimeout(1500);

    // ★ 阳性对照：面板没开的话，后面全是空数组——所以先证明它开着
    const open = await page.evaluate(() => {
      const d = Array.from(document.querySelectorAll('[role="dialog"]'))
        .find((x) => { const r = x.getBoundingClientRect(); return r.width > 0; });
      return d ? { found: true, text: (d.innerText || '').replace(/\s+/g, ' ').slice(0, 200) } : { found: false };
    });
    say('[阳性对照] 面板开着吗 =', open.found, open.found ? '｜' + open.text : '');

    const r = await page.evaluate(() => {
      const dlg = Array.from(document.querySelectorAll('[role="dialog"]'))
        .find((x) => { const r = x.getBoundingClientRect(); return r.width > 0; });
      if (!dlg) return { error: 'no dialog' };
      const txt = (e) => (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim();
      // 候选「一项」：复选框本身、带 role=checkbox 的、以及每个可点的方块
      // ★★ **去重必须按「项」，不能按「元素」**（M248 自己踩的）：
      //    一个复选项在 DOM 里通常是 `label > input.ant-checkbox-input + span.ant-checkbox-inner`
      //    **三个元素**；只按元素身份去重会把 14 项数成 **43**（实测）。
      //    而 43 是个看着像读数的假数——**判据坏掉的读数比没有读数更坏**。
      //    → 按**最内层共同容器**归并：取 `input.closest('label')`，没有就退回
      //      `input.parentElement`，再按这个容器的身份去重。
      const raw = Array.from(dlg.querySelectorAll(
        'input[type="checkbox"],[role="checkbox"],[role="switch"],.ant-checkbox'));
      const items = [];
      const seen = new Set();
      for (const b of raw) {
        const input = b.tagName === 'INPUT' ? b : (b.querySelector('input') || b);
        const owner = b.closest('label') || b.parentElement || b;
        if (seen.has(owner)) continue;
        seen.add(owner);
        const checked = input.tagName === 'INPUT'
          ? (input.checked === true || input.getAttribute('aria-checked') === 'true')
          : (b.getAttribute('aria-checked') === 'true' ||
             /ant-checkbox-checked|checked\b/.test(b.getAttribute('class') || ''));
        items.push({
          checked,
          label: txt(owner).slice(0, 40),
          aria: owner.getAttribute('aria-label') || input.getAttribute('aria-label') || '',
        });
      }
      // 面板自己写的计数（右上角那个 x/y）
      const counter = txt(dlg).match(/(\d+)\s*\/\s*(\d+)/);
      return {
        counterText: counter ? counter[0] : null,
        counterNums: counter ? [Number(counter[1]), Number(counter[2])] : null,
        boxCount: items.length,
        checkedCount: items.filter((x) => x.checked).length,
        unchecked: items.filter((x) => !x.checked).map((x) => x.label || x.aria),
        checked: items.filter((x) => x.checked).map((x) => x.label || x.aria),
        all: items,
      };
    });
    say('[面板内计数]', J(r));

    // 顺带：画布空白处右键的菜单（手册对它也有断言）
    await page.keyboard.press('Escape');
    await page.waitForTimeout(600);
    const pt = { x: 1150, y: 700 };
    await page.mouse.click(pt.x, pt.y, { button: 'right' });
    await page.waitForTimeout(1200);
    const menu = await page.evaluate(() => {
      const cands = Array.from(document.querySelectorAll('body *'))
        .filter((e) => {
          const s = getComputedStyle(e);
          const r = e.getBoundingClientRect();
          // ★ 判据是「浮层」的几何特征，**不是类名**（M248 踩过：那个容器叫
          //   `fixed z-[80] w-[212px]`，类名正则一个词都不匹配，6 项菜单被判成 0 个容器）
          const z = Number(s.zIndex) || 0;
          return r.width > 0 && r.height > 0 && z >= 40 &&
                 (s.position === 'fixed' || s.position === 'absolute');
        });
      return cands.map((e) => ({
        cls: (e.getAttribute('class') || '').slice(0, 50),
        text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200),
        items: e.querySelectorAll('li,[role="menuitem"],[role="option"]').length,
      })).slice(0, 5);
    });
    say('[画布右键菜单候选]', J(menu));
  } catch (e) {
    say('[出错]', e && e.message);
    process.exitCode = 1;
  } finally {
    await ctx.close();
  }
})();
