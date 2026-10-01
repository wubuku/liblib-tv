// Batch AS —— 三处「正文标了 📖 没验证」的地方，加上 AR2 顺手撞见的一条线索：
//
//   AS1  缩放比例是不是按画布记的？
//        AR2 用「在新窗口打开」打开「画布 63」，新标签页里左下角还是 800%
//        ——而那张画布上一批刚被调成 800%。但我只读了一次，可能是加载瞬态。
//        判据设计成**两次独立重载**：改比例 → reload → 读；再切到另一张画布 → 读。
//        只有「同一张画布重载后还是自己那个值」+「另一张画布是它自己的值」
//        同时成立，才能说「按画布记」。**一张画布的一次读数证明不了持久化。**
//
//   AS2  `TV Director 全局设置` —— 正文 agent-director.md 标着「📖 没有验证」。
//   AS3  `LibTV Plugin` —— 同上。
//        这两个面板**只读**：读文案、读每个控件的 aria/坐标/disabled、读是否有输入框。
//        **不切换任何开关、不保存、不确认**——它们是账号级设置。
//
//   AS4  我的工具箱弹窗里每张卡片上的「使用」按钮 —— 只读它的文案与状态，不点
//        （点了会把工具箱套到当前画布上，属于写操作）。
//
// 判据：
//   · 抽屉/浮层是懒挂载的，**每次读之前重新定位**，坐标不复用（§环境坑）。
//   · 枚举面板内容时按 §14 的教训**取最外层匹配容器**，不取最小锚点。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchAS';
const { browser, page } = await launch();

const zoom = () => page.evaluate(() => {
  const v = document.querySelector('.react-flow__viewport');
  const m = v && /scale\(([\d.]+)\)/.exec(v.style.transform || '');
  const e = [...document.querySelectorAll('*')].find((x) => /^\d+%$/.test((x.innerText || '').trim())
    && x.getBoundingClientRect().width < 60 && x.getBoundingClientRect().y > 700);
  return { scale: m ? Number(m[1]) : null, label: e ? e.innerText.trim() : null };
});
const menuOpen = () => page.evaluate(() => [...document.querySelectorAll('[class*="Menu-dropdown"],[class*="Popover-dropdown"]')]
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 40 && r.height > 12; }).length > 0);
async function clickZoomPreset(label) {
  const trig = await page.evaluate(() => {
    const e = [...document.querySelectorAll('*')].find((x) => /^\d+%$/.test((x.innerText || '').trim())
      && x.getBoundingClientRect().width < 60 && x.getBoundingClientRect().y > 700);
    if (!e) return null;
    const b = (e.closest('button,[role="button"]') || e).getBoundingClientRect();
    return { cx: Math.round(b.x + b.width / 2), cy: Math.round(b.y + b.height / 2) };
  });
  if (!trig) return { err: '找不到百分比触发点' };
  if (await menuOpen()) { await page.mouse.click(trig.cx, trig.cy); await page.waitForTimeout(1100); }
  if (!(await menuOpen())) { await page.mouse.click(trig.cx, trig.cy); await page.waitForTimeout(1600); }
  const it = await page.evaluate((l) => {
    const m = [...document.querySelectorAll('[class*="Menu-dropdown"],[class*="Popover-dropdown"]')]
      .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 40 && r.height > 12; })[0];
    if (!m) return null;
    const el = [...m.querySelectorAll('button,div,li')].filter((e) => (e.innerText || '').trim() === l)
      .sort((a, b) => { const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
        return (ra.width * ra.height) - (rb.width * rb.height); })[0];
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
  }, label);
  if (!it) return { err: '菜单里没有「' + label + '」' };
  await page.mouse.click(it.cx, it.cy); await page.waitForTimeout(1900);
  return { ok: true, after: await zoom() };
}

/** 只读地枚举一个浮层：取最外层匹配容器（§14），列出里面每一个控件。 */
const dumpPanel = (probe) => page.evaluate((p) => {
  const cands = [...document.querySelectorAll('div,section,aside')].filter((e) => {
    const r = e.getBoundingClientRect();
    if (r.width < 200 || r.height < 100) return false;
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    return new RegExp(p).test(t) && t.length < 1400;
  });
  if (!cands.length) return { err: '没有匹配的浮层' };
  let best = cands[0], bd = 1e9;
  for (const e of cands) { let d = 0, n = e; while ((n = n.parentElement)) d += 1; if (d < bd) { bd = d; best = e; } }
  const r = best.getBoundingClientRect();
  const inR = (el) => { const q = el.getBoundingClientRect();
    return q.width > 0 && q.height > 0 && q.x >= r.x - 2 && q.y >= r.y - 2
      && q.x + q.width <= r.x + r.width + 2 && q.y + q.height <= r.y + r.height + 2; };
  return {
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    cls: (best.className || '').toString().slice(0, 90),
    text: (best.innerText || '').replace(/\s+/g, ' ').trim(),
    buttons: [...best.querySelectorAll('button,[role="button"],[role="tab"],[role="switch"],[role="menuitem"]')]
      .filter(inR).map((b) => { const q = b.getBoundingClientRect();
        return { t: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60),
          aria: b.getAttribute('aria-label'), title: b.getAttribute('title'), role: b.getAttribute('role'),
          checked: b.getAttribute('aria-checked'), disabled: b.getAttribute('aria-disabled') === 'true' || b.disabled === true,
          opacity: getComputedStyle(b).opacity,
          rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] }; }),
    inputs: [...best.querySelectorAll('input,textarea,select')].filter(inR).map((i) => {
      const q = i.getBoundingClientRect();
      return { tag: i.tagName, type: i.type, aria: i.getAttribute('aria-label'), ph: i.placeholder,
        v: i.value, checked: i.checked, rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] }; }),
    links: [...best.querySelectorAll('a')].filter(inR).map((a) => ({ t: (a.innerText || '').trim(), href: a.getAttribute('href') })),
  };
}, probe);

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '缩放持久化两次独立重载 + TV Director 两个未进过的面板只读 + 工具箱卡片「使用」只读' });

  // ── AS1 缩放是不是按画布记的 ──────────────────────────
  const url = page.url();
  const as1 = { url, z0: await zoom() };
  as1.setTo50 = await clickZoomPreset('缩放至50%');
  as1.afterSet = await zoom();
  await shot(page, 'M-123-缩放-设为50.png');
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => {});
  await page.waitForTimeout(5000);
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  as1.afterReload1 = await zoom();
  // 第二次独立重载：排除「第一次重载只是把内存里那份写回去」
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => {});
  await page.waitForTimeout(5000);
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  as1.afterReload2 = await zoom();
  as1.persisted = as1.afterReload1.label === as1.afterSet.label
    && as1.afterReload2.label === as1.afterSet.label;
  console.log('AS1:', JSON.stringify(as1));

  // ── AS2/AS3 TV Director 抽屉 + 那两个面板 ─────────────
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(800);
  // 头图右下角那枚蓝色球
  const tvBtn = await page.evaluate(() => {
    const c = [...document.querySelectorAll('button,[role="button"]')];
    const withAria = c.filter((b) => /TV\s*Director/i.test(b.getAttribute('aria-label') || ''));
    if (withAria.length) { const r = withAria[0].getBoundingClientRect();
      return { via: 'aria', aria: withAria[0].getAttribute('aria-label'),
        cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }
    // 没有 aria 就找右下角那枚圆形按钮
    const cand = c.filter((b) => { const r = b.getBoundingClientRect();
      return r.width > 24 && r.width < 60 && r.x > 1200 && r.y > 600 && !b.innerText.trim(); })
      .map((b) => { const r = b.getBoundingClientRect();
        return { via: 'geom', cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], cls: (b.className || '').toString().slice(0, 60) }; });
    return cand[0] || null;
  });
  console.log('AS2 TV Director 入口:', JSON.stringify(tvBtn));

  const as23 = { entry: tvBtn, global: {}, plugin: {} };
  if (tvBtn) {
    await page.mouse.click(tvBtn.cx, tvBtn.cy); await page.waitForTimeout(2600);
    as23.drawerText = await page.evaluate(() => {
      const d = [...document.querySelectorAll('div,aside,section')].filter((e) => {
        const r = e.getBoundingClientRect();
        return r.width > 300 && r.width < 520 && r.height > 400 && r.x > 900 && /TV Director|新对话|让 TV/.test(e.innerText || '');
      }).sort((a, b) => a.getBoundingClientRect().width - b.getBoundingClientRect().width)[0];
      return d ? { rect: (({ x, y, width, height }) => [Math.round(x), Math.round(y), Math.round(width), Math.round(height)])(d.getBoundingClientRect()),
        head: (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200) } : null;
    });
    await shot(page, 'M-124-TV-Director-抽屉.png');

    for (const [key, aria] of [['global', 'TV Director 全局设置'], ['plugin', 'LibTV Plugin']]) {
      const hit = await page.evaluate((a) => {
        const el = [...document.querySelectorAll('button,[role="button"],[aria-label]')]
          .find((e) => (e.getAttribute('aria-label') || '').trim() === a
                 || (e.innerText || '').trim() === a);
        if (!el) return { err: '抽屉头部没有「' + a + '」', heads: [...document.querySelectorAll('button,[role="button"]')]
          .map((b) => (b.getAttribute('aria-label') || b.innerText || '').trim()).filter(Boolean).slice(0, 40) };
        const r = el.getBoundingClientRect();
        return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          opacity: getComputedStyle(el).opacity };
      }, aria);
      if (hit.err) { as23[key] = { err: hit.err, heads: hit.heads }; console.log(`AS ${key}:`, JSON.stringify(hit).slice(0, 600)); continue; }
      await page.mouse.click(hit.cx, hit.cy); await page.waitForTimeout(2600);
      as23[key] = { clicked: hit, ...(await dumpPanel(key === 'global' ? '全局设置|模型|语言|记忆|Temperature' : 'Plugin|插件|安装|市场')) };
      await shot(page, `M-12${key === 'global' ? 5 : 6}-${key === 'global' ? 'TV-Director-全局设置' : 'LibTV-Plugin'}.png`);
      console.log(`AS ${key}:`, JSON.stringify(as23[key]).slice(0, 1200));
      // **不点关闭**（怕它有"保存"），改用点原处再点一次把面板 toggle 掉；读完之后就刷新页面
      await page.reload({ waitUntil: 'domcontentloaded' });
      await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => {});
      await page.waitForTimeout(4500);
      await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
      const t2 = await page.evaluate((a) => {
        const el = [...document.querySelectorAll('button,[role="button"],[aria-label]')]
          .find((e) => (e.getAttribute('aria-label') || '').trim() === a);
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
      }, aria);
      if (t2) { await page.mouse.click(t2.cx, t2.cy); await page.waitForTimeout(2200); }   // 重开抽屉
    }
  }

  // ── AS4 工具箱弹窗卡片「使用」只读 ────────────────────
  let toolbox = { err: '没找到打开工具箱的入口' };
  const tb = await page.evaluate(() => {
    const hits = [...document.querySelectorAll('button,[role="button"]')]
      .filter((b) => /工具箱/.test((b.innerText || '') + (b.getAttribute('aria-label') || '')));
    if (!hits.length) return null;
    const b = hits[0]; const r = b.getBoundingClientRect();
    return { t: (b.innerText || b.getAttribute('aria-label')).trim(),
      cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  });
  console.log('AS4 工具箱入口:', JSON.stringify(tb));
  if (tb) {
    await page.mouse.click(tb.cx, tb.cy); await page.waitForTimeout(2600);
    await shot(page, 'M-127-工具箱弹窗.png');
    toolbox = await dumpPanel('工具箱|新建工具箱|使用');
    toolbox.entry = tb;
    console.log('AS4 工具箱:', JSON.stringify(toolbox).slice(0, 1500));
  }

  await logStep(B, {
    id: 'AS-zoom-persist-and-panels', title: '缩放持久化（两次独立重载）+ TV Director 两个未进过的面板只读 + 工具箱卡片「使用」只读',
    target: '改缩放 → **重载两次**再读（一次重载排除不了内存写回）；两个设置面板与工具箱**只枚举不操作**',
    evidence: { as1, as23, toolbox },
    visible_text: `缩放持久化：${JSON.stringify(as1)}。`
      + `\n\nTV Director：${JSON.stringify(as23).slice(0, 1200)}。`
      + `\n\n工具箱：${JSON.stringify(toolbox).slice(0, 800)}`,
    shot: 'M-124-TV-Director-抽屉.png',
  });
  console.log('AS 完成');
} finally {
  await browser.close();
}
