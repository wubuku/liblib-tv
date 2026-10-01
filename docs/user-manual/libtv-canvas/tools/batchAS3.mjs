// Batch AS3 —— AS2b/AS2c 两处的**判据失效**重做。
//
// 失效在哪：
//   AS2b `LibTV Plugin` 找到了这个元素，但 **`rect` 是 `[0,0,0,0]`** ——
//         抽屉没打开时它在 DOM 里但不可见（尺寸为 0）。我照着 `cx:0, cy:0` 点下去，
//         点的是屏幕左上角。于是 `diff: []` / `modals: []` 全是空的 ——
//         **这个空结果不能读成「点了没反应」，它只说明我没点到东西。**
//         修法：点之前先验 `rect` 面积，面积为 0 就报「不可见，没点」。
//
//   AS2c 找添加节点面板时用「页面上有没有『素材库』这几个字」来定位容器 ——
//         但**快捷键面板的内容是常驻在 DOM 里的**（实测整页文本里一直有
//         `成组 G / 解组 / 连线 L / 复制节点和连线 / 缩放 / 移动画布 / 整理画布 …`），
//         「最小匹配容器」一路爬到 `<body>`，读回来的是整张画布的文字。
//         修法：改用**浮层 class + 相对触发点的几何**，不用「文案包含」。
//         顺带记一条：**这个页面上「某段文案存在」不能用来定位面板** ——
//         常驻 DOM 太多，筛选条件必须加上「这是个浮层」。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAS3';
const { browser, page } = await launch();

/** 真正的浮层：有 Mantine 浮层 class + 有面积。**不含** `.react-flow__viewport`（§14 的坑）。 */
const floats = () => page.evaluate(() => [...document.querySelectorAll(
  '[class*="Menu-dropdown"],[class*="Popover-dropdown"],[class*="Dropdown-dropdown"],[class*="Modal-inner"],[role="dialog"]')]
  .map((e) => { const r = e.getBoundingClientRect();
    return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      cls: (e.className || '').toString().slice(0, 70),
      isModal: /Modal-inner|role="dialog"/.test((e.className || '').toString() + e.getAttribute('role')),
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400),
      items: [...e.querySelectorAll('button,[role="button"],[role="menuitem"],li')].map((b) => {
        const q = b.getBoundingClientRect();
        return { t: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 50),
          aria: b.getAttribute('aria-label'),
          area: Math.round(q.width * q.height),
          cx: Math.round(q.x + q.width / 2), cy: Math.round(q.y + q.height / 2) };
      }).filter((x) => x.area > 0 && (x.t || x.aria)) }; })
  .filter((m) => m.rect[2] > 60 && m.rect[3] > 20));

/** 按 aria 找可点元素，**并如实报告它可不可见**。 */
const byAria = (aria) => page.evaluate((a) => {
  const els = [...document.querySelectorAll('button,[role="button"],[aria-label]')]
    .filter((e) => (e.getAttribute('aria-label') || '').trim() === a);
  if (!els.length) return { err: 'DOM 里没有 aria-label="' + a + '"', count: 0 };
  return els.map((e) => { const r = e.getBoundingClientRect();
    return { area: Math.round(r.width * r.height),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
      visible: r.width > 2 && r.height > 2 && r.x >= 0 && r.y >= 0 && r.x < 1440 && r.y < 810,
      opacity: getComputedStyle(e).opacity }; });
}, aria);

const drawerOpen = () => page.evaluate(() => {
  const d = [...document.querySelectorAll('div,aside,section')].filter((e) => {
    const r = e.getBoundingClientRect();
    return r.width > 300 && r.width < 560 && r.height > 380 && r.x > 880
      && /让 TV Director|开始你的创作|新对话/.test(e.innerText || '');
  }).sort((a, b) => a.getBoundingClientRect().width - b.getBoundingClientRect().width)[0];
  if (!d) return { open: false };
  const r = d.getBoundingClientRect();
  return { open: true, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
});

const openDrawer = async () => {
  if ((await drawerOpen()).open) return { already: true };
  const tv = (await byAria('TV Director'))[0];
  if (!tv || !tv.visible) return { err: '找不到可点的 TV Director 入口', tv };
  await page.mouse.click(tv.cx, tv.cy); await page.waitForTimeout(2600);
  return { clicked: true, ...(await drawerOpen()) };
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '点之前先验可见性 + 浮层改用 class/几何定位，不用文案包含' });

  // ── AS3a LibTV Plugin ─────────────────────────────────
  const as3a = { drawer: await openDrawer() };
  console.log('AS3a 抽屉:', JSON.stringify(as3a.drawer));
  const plugin = await byAria('LibTV Plugin');
  as3a.found = plugin;
  if (!plugin.err && plugin.length) {
    const vis = plugin.filter((p) => p.visible);
    as3a.visibleCount = vis.length;
    if (!vis.length) {
      as3a.verdict = `DOM 里有 ${plugin.length} 个「LibTV Plugin」，但**全部 rect 面积为 ${plugin.map((p) => p.area).join('/')}（不可见）** —— `
        + '所以本轮**没有点到它**。空结果不能读成「点了没反应」。';
      console.log('AS3a:', JSON.stringify(as3a));
    } else {
      const urlBefore = page.url(); const nodesBefore = await nodeCount(page);
      const f0 = await floats();
      await page.mouse.click(vis[0].cx, vis[0].cy);
      await page.waitForTimeout(3400);
      const f1 = await floats();
      as3a.floatsBefore = f0.length; as3a.floatsAfter = f1.length;
      as3a.newFloats = f1.filter((n) => !f0.some((o) => o.rect.join() === n.rect.join() && o.text === n.text));
      as3a.urlChanged = page.url() !== urlBefore;
      as3a.nodesChanged = (await nodeCount(page)) !== nodesBefore;
      as3a.drawerStillOpen = (await drawerOpen()).open;
      await shot(page, 'M-126-LibTV-Plugin-点开之后.png');
      as3a.verdict = as3a.newFloats.length
        ? `点开之后新出现 ${as3a.newFloats.length} 个浮层，内容见 newFloats`
        : '点开之后**没有新浮层**（差集为空），也没有弹窗/提示 —— 点了等于没反应';
      console.log('AS3a:', JSON.stringify(as3a).slice(0, 2000));
    }
  } else {
    as3a.verdict = '抽屉里找不到 aria-label="LibTV Plugin"';
    console.log('AS3a:', JSON.stringify(as3a));
  }

  // ── AS3b 「+」→「素材库」→ 工具箱 ────────────────────
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(900);
  const as3b = {};
  const f0 = await floats();
  const addBtn = await page.evaluate(() => {
    // 底栏那枚「+」：在快捷键面板那一排里，取**最靠中间**的
    const bar = [...document.querySelectorAll('div')].filter((e) => {
      const r = e.getBoundingClientRect();
      return r.width > 300 && r.height > 30 && r.height < 60 && r.y > 720;
    }).sort((a, b) => a.getBoundingClientRect().width - b.getBoundingClientRect().width)[0];
    if (!bar) return null;
    const btns = [...bar.querySelectorAll('button,[role="button"]')].map((b) => {
      const r = b.getBoundingClientRect();
      return { t: (b.innerText || '').trim(), aria: b.getAttribute('aria-label'),
        area: Math.round(r.width * r.height),
        cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
    }).filter((b) => b.area > 0);
    // 「+」是底栏里唯一没有文字也没有 aria 的那个
    return btns.find((b) => !b.t && !b.aria) || null;
  });
  as3b.addBtn = addBtn;
  if (addBtn) {
    await page.mouse.click(addBtn.cx, addBtn.cy);
    await page.waitForTimeout(2400);
    const f1 = await floats();
    as3b.newFloats = f1.filter((n) => !f0.some((o) => o.rect.join() === n.rect.join() && o.text === n.text));
    as3b.panel = as3b.newFloats.find((n) => !n.isModal) || as3b.newFloats[0] || null;
    await shot(page, 'M-127-添加节点面板.png');
    console.log('AS3b 面板:', JSON.stringify(as3b.panel).slice(0, 900));

    const lib = (as3b.panel?.items || []).find((i) => i.t === '素材库');
    as3b.libItem = lib || null;
    if (lib) {
      // 悬停出子菜单（§16：素材库是 hover 出子菜单的）
      const f2 = await floats();
      await page.mouse.move(lib.cx, lib.cy); await page.waitForTimeout(1500);
      await page.mouse.move(lib.cx, lib.cy + 1); await page.waitForTimeout(1800);
      await page.mouse.move(lib.cx + 2, lib.cy); await page.waitForTimeout(1800);
      const f3 = await floats();
      as3b.submenu = f3.filter((n) => !f2.some((o) => o.rect.join() === n.rect.join() && o.text === n.text))
        .find((n) => !n.isModal) || null;
      await shot(page, 'M-128-素材库子菜单.png');
      console.log('AS3b 子菜单:', JSON.stringify(as3b.submenu).slice(0, 900));

      const tb = (as3b.submenu?.items || []).find((i) => /打开工具箱/.test(i.t) || /工具箱/.test(i.aria || ''));
      as3b.toolboxBtn = tb || null;
      if (tb) {
        await page.mouse.click(tb.cx, tb.cy);
        await page.waitForTimeout(3000);
        await shot(page, 'M-129-工具箱弹窗.png');
        const f4 = await floats();
        as3b.dialog = f4.find((n) => n.isModal) || null;
        console.log('AS3b 工具箱弹窗:', JSON.stringify(as3b.dialog).slice(0, 1500));
      } else {
        as3b.toolboxErr = '子菜单里没有「打开工具箱」；子菜单 items = '
          + JSON.stringify((as3b.submenu?.items || []).map((i) => i.t || i.aria));
      }
    } else {
      as3b.libErr = '面板 items 里没有「素材库」；items = '
        + JSON.stringify((as3b.panel?.items || []).map((i) => i.t || i.aria));
    }
  }
  console.log('AS3b:', JSON.stringify(as3b).slice(0, 2500));

  await logStep(B, {
    id: 'AS3-visible-check', title: 'Plugin 点之前先验可见性 + 浮层改用 class/几何定位',
    target: '每个目标点之前先读 `rect` 面积；浮层一律用 Mantine 浮层 class + 面积筛，不用「页面上有这段文案」',
    evidence: { as3a, as3b },
    visible_text: `LibTV Plugin：${JSON.stringify(as3a).slice(0, 900)}。`
      + `\n\n添加节点面板 → 素材库 → 工具箱：${JSON.stringify(as3b).slice(0, 1100)}`,
    shot: 'M-127-添加节点面板.png',
  });
  console.log('AS3 完成');
} finally {
  await browser.close();
}
