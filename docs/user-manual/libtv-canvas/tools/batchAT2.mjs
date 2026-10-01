// Batch AT2 —— AT 的后两段，被**全屏遮罩挡住了**。
//
// AT 跑完角色造型室之后按了 `Esc`，但那个遮罩（`z-(--z-modal) fixed inset-0
// … bg-black/60`）**没关掉**（正文里其实已经记过这件事，我这次又踩了）。
// 于是后面找「风格库」「快捷键」全都报「找不到可见的」——
// 它们的触发点被遮罩盖住了，`getBoundingClientRect()` 还在但**点不到**。
//
// 修法：**关它自己的 `×`（`aria-label="关闭"`）**，不用 `Esc`。
// 而且每段做完都断言「遮罩确实没了」，不然又是静默连锁失败。
//
// 另外 AT 的角色造型室读数里，**角色列表其实不是空的**（截图里有两个真人形象），
// 但 `innerText` 只读到 84 个字 —— 角色卡上的性别/年龄/文化区域很可能是**图片而不是文字**。
// 这一段专门量一下卡片区到底有没有文本节点。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';

const SPACE = '10354929';
const B = 'batchAT2';
const { browser, page } = await launch();

const maskOpen = () => page.evaluate(() => !!document.querySelector('.z-\\(--z-modal\\)[class*="fixed"][class*="inset-0"]'));
const clickAria = async (aria, wait = 3000) => {
  const h = await page.evaluate((a) => {
    const e = [...document.querySelectorAll('button,[role="button"],[aria-label]')]
      .filter((x) => (x.getAttribute('aria-label') || '').trim() === a)
      .map((x) => { const r = x.getBoundingClientRect();
        // **关键**：还要问「那个点上是不是它」——被遮罩盖住时点不到（§20.3）
        const onTop = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
        return { area: Math.round(r.width * r.height), visible: r.width > 2 && r.height > 2,
          onTop: !!(onTop && (x.contains(onTop) || onTop.contains(x))),
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; })
      .filter((x) => x.visible && x.onTop)[0];
    return e || { err: '找不到**可点**的 aria-label="' + a + '"' };
  }, aria);
  if (h.err) return h;
  await page.mouse.click(h.cx, h.cy); await page.waitForTimeout(wait);
  return h;
};
const clickText = async (t, wait = 3200) => {
  const h = await page.evaluate((s) => {
    const el = [...document.querySelectorAll('div,li,button,span,a')]
      .filter((e) => (e.innerText || '').trim() === s)
      .map((e) => { const r = e.getBoundingClientRect();
        const onTop = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
        return { area: Math.round(r.width * r.height), visible: r.width > 2 && r.height > 2,
          onTop: !!(onTop && (e.contains(onTop) || onTop.contains(e))),
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; })
      .filter((x) => x.visible && x.onTop).sort((a, b) => a.area - b.area)[0];
    return el || { err: '找不到**可点**的「' + s + '」' };
  }, t);
  if (h.err) return h;
  await page.mouse.click(h.cx, h.cy); await page.waitForTimeout(wait);
  return h;
};
/** 展开新浮层的完整读数；**必须排除被遮罩那个全屏容器**（它什么都包含）。 */
const readNew = (hint) => page.evaluate((h) => {
  const cands = [...document.querySelectorAll('div,section,aside')].filter((e) => {
    const r = e.getBoundingClientRect();
    if (r.width < 240 || r.height < 120) return false;
    if (r.width >= 1400 && r.height >= 700) return false;        // 跳过全屏遮罩
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    return new RegExp(h).test(t) && t.length < 2500;
  });
  if (!cands.length) return { err: '没找到含「' + h + '」的容器（已排除全屏遮罩）' };
  let best = cands[0], bd = 1e9;
  for (const e of cands) { let d = 0, n = e; while ((n = n.parentElement)) d += 1; if (d < bd) { bd = d; best = e; } }
  const r = best.getBoundingClientRect();
  const inR = (el) => { const q = el.getBoundingClientRect();
    return q.width > 0 && q.height > 0 && q.x >= r.x - 2 && q.y >= r.y - 2
      && q.x + q.width <= r.x + r.width + 2 && q.y + q.height <= r.y + r.height + 2; };
  const rd = (el) => { const q = el.getBoundingClientRect();
    return [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)]; };
  return {
    rect: rd(best), cls: (best.className || '').toString().slice(0, 80),
    text: (best.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 1500),
    images: [...best.querySelectorAll('img')].filter(inR).map((i) => ({ alt: i.alt, src: (i.src || '').slice(-60), rect: rd(i) })).slice(0, 12),
    buttons: [...best.querySelectorAll('button,[role="button"],[role="tab"],[role="switch"]')]
      .filter(inR).map((b) => ({ t: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 50),
        aria: b.getAttribute('aria-label'), disabled: b.disabled === true, rect: rd(b) })),
    inputs: [...best.querySelectorAll('input:not([type=checkbox])')].filter(inR)
      .map((i) => ({ type: i.type, aria: i.getAttribute('aria-label'), ph: i.placeholder, v: i.value, rect: rd(i) })),
  };
}, hint);

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await beginBatch(B, { note: '关掉全屏遮罩再跑；每步断言遮罩状态' });

  const out = {};

  // ── AT2a 角色造型室：卡片区到底有没有文本 + 视图模式到底几个 ──
  await clickAria('角色造型室');
  out.maskOpen = await maskOpen();
  out.studio = await page.evaluate(() => {
    const viewBtns = [...document.querySelectorAll('button,[role="button"]')]
      .filter((b) => /模式$/.test(b.getAttribute('aria-label') || ''))
      .map((b) => { const r = b.getBoundingClientRect();
        return { aria: b.getAttribute('aria-label'), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          bg: getComputedStyle(b).backgroundColor, cls: (b.className || '').toString().slice(0, 60) }; });
    // 内容区：找有角色的那一块
    const imgs = [...document.querySelectorAll('img')].map((i) => { const r = i.getBoundingClientRect();
      return { alt: i.alt, area: Math.round(r.width * r.height),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; })
      .filter((i) => i.area > 20000).sort((a, b) => a.rect[0] - b.rect[0]);
    // 横向滚动条？
    const scrollers = [...document.querySelectorAll('div')].filter((e) => {
      const s = getComputedStyle(e);
      return (s.overflowX === 'auto' || s.overflowX === 'scroll')
        && e.getBoundingClientRect().width > 200 && e.scrollWidth > e.clientWidth + 10;
    }).map((e) => { const r = e.getBoundingClientRect();
      return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        scrollW: e.scrollWidth, clientW: e.clientWidth }; });
    return {
      viewModeButtons: viewBtns,
      viewModeCount: viewBtns.length,
      bigImages: imgs,
      bigImageCount: imgs.length,
      imageAlts: imgs.map((i) => i.alt),
      horizontalScrollers: scrollers,
      allAria: [...document.querySelectorAll('button,[role="button"],[aria-label]')]
        .map((b) => (b.getAttribute('aria-label') || b.innerText || '').trim()).filter(Boolean).slice(0, 40),
    };
  });
  console.log('AT2a 角色造型室:', JSON.stringify(out.studio).slice(0, 2400));
  await shot(page, 'M-133-角色造型室-完整.png');

  // ── 关键：**关它自己的 ×**，不用 Esc ──
  out.closeBtn = await clickAria('关闭', 2000);
  out.maskAfterClose = await maskOpen();
  console.log('AT2a 关闭后遮罩还在吗:', out.maskAfterClose, JSON.stringify(out.closeBtn));
  if (out.maskAfterClose) throw new Error('点了 × 遮罩还在 —— 后面几步都会被挡');

  // ── AT2b 风格库 / 特效库 ──────────────────────────────
  for (const [name, pat] of [['风格库', '风格|新增风格|预设'], ['特效库', '特效|新增特效|预设']]) {
    const lib = await clickAria('素材库', 2000);
    const hit = await clickText(name, 3000);
    out[name] = { lib, hit, ...(await readNew(pat)) };
    await shot(page, `M-13${name === '风格库' ? 4 : 5}-${name}.png`);
    console.log(`AT2b ${name}:`, JSON.stringify(out[name]).slice(0, 2000));
    // 退回画布
    const fpBefore = await fingerprint(page);
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(1400);
    if (await maskOpen()) { await clickAria('关闭', 1500); }
    out[name].closed = !(await maskOpen());
  }

  // ── AT2c 快捷键面板 ──────────────────────────────────
  const fp = await fingerprint(page);
  out.kbEntry = await clickAria('快捷键', 2600);
  out.kb = await readNew('成组|解组|连线|复制|删除|撤销|重做|移动画布|适应画布|整理画布|搜索|新建节点|创建副本|节点复制|缩放|放大|缩小');
  await shot(page, 'M-136-快捷键面板.png');
  console.log('AT2c 快捷键面板:', JSON.stringify(out.kb).slice(0, 3200));

  await logStep(B, {
    id: 'AT2-close-mask-then-read', title: '关掉全屏遮罩再读风格库 / 特效库 / 快捷键面板',
    target: '**关它自己的 `×`（aria="关闭"）而不是 `Esc`**，关完断言遮罩确实没了；点击前先 `elementFromPoint` 验「那个点是不是它」',
    evidence: out,
    visible_text: `角色造型室卡片区：${JSON.stringify(out.studio).slice(0, 1100)}。`
      + `\n\n遮罩关闭：${JSON.stringify({ closeBtn: out.closeBtn, maskAfterClose: out.maskAfterClose })}。`
      + `\n\n风格库：${JSON.stringify(out['风格库']).slice(0, 700)}。`
      + `\n\n特效库：${JSON.stringify(out['特效库']).slice(0, 700)}。`
      + `\n\n快捷键面板：${JSON.stringify(out.kb).slice(0, 1500)}`,
    shot: 'M-133-角色造型室-完整.png',
  });
  console.log('AT2 完成');
} finally {
  await browser.close();
}
