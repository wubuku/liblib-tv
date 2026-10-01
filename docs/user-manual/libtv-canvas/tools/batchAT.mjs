// Batch AT —— 三处「正文有描述、但没有逐控件读数」的面板：
//
//   AT1  **角色造型室** —— 正文 character-studio.md 写了「两个库标签、三个筛选下拉、
//        搜索、列表/卡片/网格三视图、空状态『创建新角色』」，但那是 Batch 时代的一张图。
//        这次逐控件读全。**「创建新角色」不点** —— 它会写账户数据。
//   AT2  **风格库 / 特效库** —— 素材库面板里那两项（都带 NEW 徽标）从没打开过。只读清单。
//   AT3  **快捷键面板** —— shortcuts.md 有一整张键位表，但没跟真实面板逐条对照过。
//        这次把面板里的每一行读出来，跟正文表格比。
//
// 沿用 AS 系列踩出来的三条规矩：
//   · **点之前先验 `rect` 面积**（§20.3）——空结果有两种读法，分不清就会把
//     「我没点到」写成「产品没反应」。
//   · **面板识别用 `fingerprint`/`diffPanels`，不用 class 白名单**（§20.2）。
//   · **筛选条件里不写 `!aria`**（§20.4）——这个产品几乎每枚按钮都有 aria。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';

const SPACE = '10354929';
const B = 'batchAT';
const { browser, page } = await launch();

const clickAria = async (aria) => {
  const h = await page.evaluate((a) => {
    const e = [...document.querySelectorAll('button,[role="button"],[aria-label]')]
      .filter((x) => (x.getAttribute('aria-label') || '').trim() === a)
      .map((x) => { const r = x.getBoundingClientRect();
        return { area: Math.round(r.width * r.height), visible: r.width > 2 && r.height > 2,
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; })
      .filter((x) => x.visible)[0];
    return e || { err: '找不到可见的 aria-label="' + a + '"' };
  }, aria);
  if (h.err) return h;
  await page.mouse.click(h.cx, h.cy); await page.waitForTimeout(3000);
  return h;
};
const clickText = async (t) => {
  const h = await page.evaluate((s) => {
    const el = [...document.querySelectorAll('div,li,button,span,a')]
      .filter((e) => (e.innerText || '').trim() === s)
      .map((e) => { const r = e.getBoundingClientRect();
        return { area: Math.round(r.width * r.height), visible: r.width > 2 && r.height > 2,
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; })
      .filter((x) => x.visible).sort((a, b) => a.area - b.area)[0];
    return el || { err: '找不到可见的「' + s + '」' };
  }, t);
  if (h.err) return h;
  await page.mouse.click(h.cx, h.cy); await page.waitForTimeout(3200);
  return h;
};
/** 展开新浮层的**完整读数**（不点里面任何东西）。 */
const readNew = (fpBefore, hint) => page.evaluate((h) => {
  // 用**文案特征**在页面里找容器（fingerprint 已经告诉我有没有，这里补细节）
  const cands = [...document.querySelectorAll('div,section,aside')].filter((e) => {
    const r = e.getBoundingClientRect();
    if (r.width < 260 || r.height < 140) return false;
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    return new RegExp(h).test(t) && t.length < 2000;
  });
  if (!cands.length) return { err: '没找到含「' + h + '」的容器' };
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
    text: (best.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 1200),
    buttons: [...best.querySelectorAll('button,[role="button"],[role="tab"],[role="switch"],[role="option"],[role="menuitem"]')]
      .filter(inR).map((b) => ({ t: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 50),
        aria: b.getAttribute('aria-label'), role: b.getAttribute('role'),
        selected: b.getAttribute('aria-selected'), checked: b.getAttribute('aria-checked'),
        disabled: b.disabled === true || b.getAttribute('aria-disabled') === 'true',
        opacity: getComputedStyle(b).opacity, rect: rd(b) })),
    inputs: [...best.querySelectorAll('input,textarea,select')].filter(inR)
      .map((i) => ({ tag: i.tagName, type: i.type, aria: i.getAttribute('aria-label'),
        ph: i.placeholder, v: i.value, rect: rd(i) })),
    roles: [...best.querySelectorAll('[role]')].filter(inR)
      .reduce((a, el) => { const k = el.getAttribute('role'); a[k] = (a[k] || 0) + 1; return a; }, {}),
  };
}, hint);

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await beginBatch(B, { note: '角色造型室 / 风格库 / 特效库 / 快捷键面板逐控件只读' });

  const out = {};

  // ── AT1 角色造型室 ────────────────────────────────────
  let fp = await fingerprint(page);
  out.charEntry = await clickAria('角色造型室');
  let fp2 = await fingerprint(page);
  out.charDiff = diffPanels(fp, fp2).length;
  out.char = await readNew(fp, '角色|我的角色|官方角色|创建新角色|性别|年龄段|文化区域');
  await shot(page, 'M-132-角色造型室.png');
  console.log('AT1 角色造型室:', JSON.stringify(out.char).slice(0, 2200));

  // 切一下两个库标签（**只读，不点创建**）
  for (const tab of ['官方角色库', '我的角色库']) {
    const hit = (out.char?.buttons || []).find((b) => b.t === tab);
    if (!hit) { out[`tab_${tab}`] = { err: '面板里没有这个标签' }; continue; }
    await page.mouse.click(hit.rect[0] + hit.rect[2] / 2, hit.rect[1] + hit.rect[3] / 2);
    await page.waitForTimeout(2600);
    out[`tab_${tab}`] = await page.evaluate((t) => {
      const on = [...document.querySelectorAll('button,[role="tab"]')]
        .filter((b) => (b.innerText || '').trim() === t)
        .map((b) => ({ ariaSelected: b.getAttribute('aria-selected'),
          dataActive: b.getAttribute('data-active'), cls: (b.className || '').toString().slice(0, 50),
          bg: getComputedStyle(b).backgroundColor }))
        .filter((x) => x.ariaSelected !== null || x.dataActive !== null || x.bg !== 'rgba(0, 0, 0, 0)')[0];
      return on || { err: '读不到该标签的状态标记' };
    }, tab);
    out[`tab_${tab}_text`] = await readNew(fp, tab);
    console.log(`AT1 切到「${tab}」:`, JSON.stringify(out[`tab_${tab}`]).slice(0, 400));
    await shot(page, `M-13${out[`tab_${tab}`]?.ariaSelected === 'true' ? 3 : 4}-角色造型室-${tab}.png`);
  }

  // ── AT2 风格库 / 特效库 ──────────────────────────────
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(1000);
  fp = await fingerprint(page);
  await clickAria('素材库');
  await page.waitForTimeout(1800);
  for (const [name, pat] of [['风格库', '风格|新增风格|预设|风格库'], ['特效库', '特效|新增特效|预设|特效库']]) {
    const hit = await clickText(name);
    fp2 = await fingerprint(page);
    out[name] = { hit, diff: diffPanels(fp, fp2).length, ...(await readNew(fp, pat)) };
    await shot(page, `M-13${name === '风格库' ? 5 : 6}-${name}.png`);
    console.log(`AT2 ${name}:`, JSON.stringify(out[name]).slice(0, 1600));
    // 退回去
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(1200);
    await clickAria('素材库');
    await page.waitForTimeout(1600);
  }

  // ── AT3 快捷键面板：逐条读 ──────────────────────────
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(1000);
  fp = await fingerprint(page);
  out.kbEntry = await clickAria('快捷键');
  await page.waitForTimeout(600);
  out.kb = await readNew(fp, '成组|解组|连线|复制|删除|撤销|重做|移动画布|适应画布|整理画布|搜索|新建节点|创建副本|节点复制');
  await shot(page, 'M-137-快捷键面板.png');
  console.log('AT3 快捷键面板:', JSON.stringify(out.kb).slice(0, 3000));

  await logStep(B, {
    id: 'AT-three-panels', title: '角色造型室 / 风格库 / 特效库 / 快捷键面板逐控件只读',
    target: '四处面板逐枚读按钮、输入框、role 分布；角色造型室**只切标签不点「创建新角色」**',
    evidence: out,
    visible_text: `角色造型室：${JSON.stringify(out.char).slice(0, 900)}。`
      + `\n\n风格库：${JSON.stringify(out['风格库']).slice(0, 600)}。`
      + `\n\n特效库：${JSON.stringify(out['特效库']).slice(0, 600)}。`
      + `\n\n快捷键面板：${JSON.stringify(out.kb).slice(0, 1400)}`,
    shot: 'M-132-角色造型室.png',
  });
  console.log('AT 完成');
} finally {
  await browser.close();
}
