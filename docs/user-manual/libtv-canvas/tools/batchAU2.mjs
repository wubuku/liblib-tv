// Batch AU2 —— AU 的两处修正，外加把卡了五轮的「高级设置」做完。
//
// 修正一：**先把缩放归位**。
//   AU 跑的时候这张画布是 800%（上一批实测出来的持久化值），
//   于是节点的实际尺寸是 `4976×2800` —— 一个节点比整个视口还大。
//   我按 `rect.x + rect.width/2` 取点击点，落在 x=3217，**在视口外面**。
//   点了五下「选中」，`btns` 一直是空数组。
//   → 开头先 `⌘0` 适合屏幕（或点「缩放至100%」），让坐标回到正常量级。
//
// 修正二：**点击坐标 clamp 到视口内**。
//   即便归了位，节点也可能大到一半在视口外。取点时统一
//   `cx = min(max(命中点, 边距), 视口宽 - 边距)`，并用 `elementFromPoint` 回读确认。
//
// AU3「高级设置」换三路（§11 记着前五轮都失败）：
//   ① `aria-expanded="false"` 的元素 → Playwright locator 点（自带可见性与命中校验）
//   ② 找到「高度为 0 的折叠容器」→ 在它最近祖先里找可聚焦兄弟 → `.focus()` + `Enter`
//   ③ 同上 + `Space`
//   判据一律是**内容区实际高度从 0 变成 >40**，不看「点了没报错」。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAU2';
const { browser, page } = await launch();

const menuOpen = () => page.evaluate(() => [...document.querySelectorAll('[class*="Menu-dropdown"],[class*="Popover-dropdown"]')]
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 40 && r.height > 12; }).length > 0);
/** 缩放归位：走菜单「缩放至100%」（toggle 安全版） */
async function resetZoom() {
  const trig = await page.evaluate(() => {
    const e = [...document.querySelectorAll('*')].find((x) => /^\d+%$/.test((x.innerText || '').trim())
      && x.getBoundingClientRect().width < 60 && x.getBoundingClientRect().y > 700);
    if (!e) return null;
    const b = (e.closest('button,[role="button"]') || e).getBoundingClientRect();
    return { cx: Math.round(b.x + b.width / 2), cy: Math.round(b.y + b.height / 2) };
  });
  if (!trig) return { err: '找不到缩放触发点' };
  if (await menuOpen()) { await page.mouse.click(trig.cx, trig.cy); await page.waitForTimeout(1100); }
  if (!(await menuOpen())) { await page.mouse.click(trig.cx, trig.cy); await page.waitForTimeout(1600); }
  const it = await page.evaluate(() => {
    const m = [...document.querySelectorAll('[class*="Menu-dropdown"],[class*="Popover-dropdown"]')]
      .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 40 && r.height > 12; })[0];
    if (!m) return null;
    const el = [...m.querySelectorAll('button,div,li')].filter((e) => (e.innerText || '').trim() === '缩放至100%')
      .sort((a, b) => { const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
        return (ra.width * ra.height) - (rb.width * rb.height); })[0];
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
  });
  if (!it) return { err: '菜单里没有「缩放至100%」' };
  await page.mouse.click(it.cx, it.cy); await page.waitForTimeout(2000);
  return { ok: true, scale: await page.evaluate(() => {
    const v = document.querySelector('.react-flow__viewport');
    const m = v && /scale\(([\d.]+)\)/.exec(v.style.transform || '');
    return m ? Number(m[1]) : null; }) };
}
/** 点一个节点，**坐标 clamp 进视口并回读确认**。 */
async function selectNode(titlePart) {
  const plan = await page.evaluate((t) => {
    const n = [...document.querySelectorAll('.react-flow__node')]
      .find((x) => (x.innerText || '').includes(t));
    if (!n) return { err: '视口里没有「' + t + '」' };
    const r = n.getBoundingClientRect();
    const cx = Math.min(Math.max(r.x + r.width / 2, 30), 1410);
    const cy = Math.min(Math.max(r.y + 60, 90), 720);
    const on = document.elementFromPoint(cx, cy);
    return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      cx, cy, hitsNode: !!(on && n.contains(on)),
      onTop: on ? on.tagName + '.' + (on.className || '').toString().slice(0, 40) : null };
  }, titlePart);
  if (plan.err) return plan;
  if (!plan.hitsNode) { plan.err = `按下的点 (${plan.cx},${plan.cy}) 不在节点上，落在 ${plan.onTop}`; return plan; }
  await page.mouse.click(plan.cx, plan.cy); await page.waitForTimeout(2800);
  return plan;
}
/** 节点顶部一排按钮（只读）。 */
const toolbars = (titlePart) => page.evaluate((t) => {
  const n = [...document.querySelectorAll('.react-flow__node')].find((x) => (x.innerText || '').includes(t));
  if (!n) return { err: '节点不见了' };
  const r = n.getBoundingClientRect();
  const all = [...n.querySelectorAll('button,[role="button"],[aria-label]')].map((b) => {
    const q = b.getBoundingClientRect();
    return { t: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24),
      aria: b.getAttribute('aria-label'), title: b.getAttribute('title'),
      disabled: b.disabled === true, opacity: getComputedStyle(b).opacity,
      relY: Math.round(q.y - r.y), relX: Math.round(q.x - r.x),
      rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] };
  }).filter((b) => b.rect[2] > 0);
  return { nodeRect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    total: all.length,
    topBand: all.filter((b) => b.relY >= 0 && b.relY < 90),
    rest: all.filter((b) => b.relY >= 90).map((b) => b.t || b.aria || b.title).slice(0, 20) };
}, titlePart);
const clickAria = async (aria, wait = 2600) => {
  const h = await page.evaluate((a) => {
    const e = [...document.querySelectorAll('button,[role="button"],[aria-label]')]
      .filter((x) => (x.getAttribute('aria-label') || '').trim() === a)
      .map((x) => { const r = x.getBoundingClientRect();
        const on = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
        return { visible: r.width > 2 && r.height > 2, onTop: !!(on && (x.contains(on) || on.contains(x))),
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; })
      .filter((x) => x.visible && x.onTop)[0];
    return e || { err: '找不到**可点**的 aria-label="' + a + '"' };
  }, aria);
  if (h.err) return h;
  await page.mouse.click(h.cx, h.cy); await page.waitForTimeout(wait);
  return h;
};
const readFold = () => page.evaluate(() => [...document.querySelectorAll('div')]
  .filter((e) => { const s = getComputedStyle(e);
    return (/grid-template-rows/.test(s.transitionProperty) || s.display === 'grid') && /overflow-hidden/.test(s.overflowY + s.overflow) && e.children.length > 0; })
  .map((e) => { const r = e.getBoundingClientRect();
    return { h: Math.round(r.height), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      cls: (e.className || '').toString().slice(0, 70),
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200),
      sliders: e.querySelectorAll('[class*="Slider"]').length }; })
  .filter((x) => x.text.length > 0 || x.h > 0).slice(0, 10));

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await beginBatch(B, { note: '缩放先归位 + 坐标 clamp + 高级设置三路激活' });

  const out = {};

  // ① 缩放归位
  out.zoom = await resetZoom();
  console.log('AU2 缩放归位:', JSON.stringify(out.zoom));
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(900);

  // ② 节点顶部工具条
  out.nodes = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')]
    .map((n) => { const r = n.getBoundingClientRect();
      return { title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }));
  console.log('AU2 视口节点:', JSON.stringify(out.nodes));

  out.bars = {};
  for (const title of ['图片节点', '视频节点', '文本节点']) {
    const sel = await selectNode(title);
    if (sel.err) { out.bars[title] = { sel }; continue; }
    out.bars[title] = { sel, bar: await toolbars(title) };
    console.log(`AU2 ${title} 顶部:`, JSON.stringify(out.bars[title].bar?.topBand).slice(0, 700));
    await shot(page, `M-13${title === '图片节点' ? 8 : title === '视频节点' ? 9 : 9}-${title}-顶部工具条.png`);
    await page.mouse.click(1300, 130); await page.waitForTimeout(1400);
  }

  // ③ 高级设置：先建一个音频节点（视口里没有）
  out.audioCreate = { before: await nodeCount(page) };
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(800);
  await page.mouse.dblclick(560, 300); await page.waitForTimeout(1600);
  const audioItem = await page.evaluate(() => {
    const el = [...document.querySelectorAll('[data-guide-lockable-portal="true"] *,div,button,li')]
      .filter((e) => (e.innerText || '').trim() === '音频')
      .map((e) => { const r = e.getBoundingClientRect();
        return { area: Math.round(r.width * r.height), visible: r.width > 2 && r.height > 2,
          cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; })
      .filter((x) => x.visible && x.cy > 100 && x.cy < 700).sort((a, b) => a.area - b.area)[0];
    return el || { err: '添加节点面板里没有「音频」' };
  });
  out.audioCreate.item = audioItem;
  if (!audioItem.err) {
    await page.mouse.click(audioItem.cx, audioItem.cy); await page.waitForTimeout(2800);
    out.audioCreate.after = await nodeCount(page);
    console.log('AU2 建音频节点:', JSON.stringify(out.audioCreate));
  }
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(1200);

  // ④ 三路激活
  out.au3 = {};
  const selA = await selectNode('音频节点');
  out.au3.select = selA;
  if (!selA.err) {
    out.au3.before = await readFold();
    console.log('AU2 展开前:', JSON.stringify(out.au3.before).slice(0, 700));
    await shot(page, 'M-142-音频-高级设置-展开前.png');

    // 路径①：aria-expanded
    const a1 = await page.evaluate(() => [...document.querySelectorAll('[aria-expanded]')].map((x) => {
      const r = x.getBoundingClientRect();
      return { tag: x.tagName, expanded: x.getAttribute('aria-expanded'),
        label: (x.innerText || x.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim().slice(0, 24),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        visible: r.width > 2 && r.height > 2 }; }));
    out.au3.ariaExpandedCandidates = a1;
    const target = a1.find((x) => x.visible && x.expanded === 'false');
    if (target) {
      await page.locator(`[aria-expanded="false"]`).first().click({ timeout: 5000 }).catch((e) => { out.au3.clickErr = String(e).slice(0, 150); });
      await page.waitForTimeout(2000);
      out.au3.afterPath1 = await readFold();
      out.au3.grew = (out.au3.afterPath1 || []).some((x) => x.h > 40 && x.text.length > 0);
      console.log('AU2 路径① aria-expanded:', JSON.stringify(target), '| 长大了?', out.au3.grew);
    } else {
      out.au3.noAriaExpanded = true;
      console.log('AU2 没有 aria-expanded=false 的元素；候选 =', JSON.stringify(a1).slice(0, 500));
    }

    // 路径②③：找到高度 0 的折叠容器，在它最近祖先里找可聚焦兄弟
    if (!out.au3.grew) {
      const foldInfo = await page.evaluate(() => {
        const fold = [...document.querySelectorAll('div')].find((e) => {
          const r = e.getBoundingClientRect();
          return r.height < 3 && e.children.length > 0 && /overflow-hidden/.test(getComputedStyle(e).overflowY);
        });
        if (!fold) return { err: '找不到高度为 0 的折叠容器' };
        let scope = fold.parentElement;
        for (let i = 0; i < 3 && scope; i += 1) {
          const c = [...scope.querySelectorAll('button,[role="button"],[tabindex="0"]')].map((b) => {
            const r = b.getBoundingClientRect();
            return { t: (b.innerText || b.getAttribute('aria-label') || b.title || '').replace(/\s+/g, ' ').trim().slice(0, 30),
              tag: b.tagName, visible: r.width > 2 && r.height > 2,
              rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
          }).filter((b) => b.visible);
          if (c.length) return { scopeDepth: i, cands: c.slice(0, 12),
            foldRect: (({ x, y, width, height }) => [Math.round(x), Math.round(y), Math.round(width), Math.round(height)])(fold.getBoundingClientRect()) };
          scope = scope.parentElement;
        }
        return { err: '折叠区最近三层祖先里没有可点元素' };
      });
      out.au3.foldInfo = foldInfo;
      console.log('AU2 折叠区候选:', JSON.stringify(foldInfo).slice(0, 900));
      for (const key of ['Enter', ' ']) {
        const cand = foldInfo.cands?.find((c) => /高级设置|设置|展开|更多/.test(c.t)) || foldInfo.cands?.[0];
        if (!cand) break;
        const loc = page.locator('button, [role="button"]').filter({ hasText: cand.t || /^$/ }).first();
        await loc.focus({ timeout: 4000 }).catch((e) => { out.au3['focusErr' + key] = String(e).slice(0, 100); });
        await page.keyboard.press(key === ' ' ? 'Space' : 'Enter');
        await page.waitForTimeout(1800);
        out.au3['after' + key] = await readFold();
        const grew = (out.au3['after' + key] || []).some((x) => x.h > 40 && x.text.length > 0);
        console.log(`AU2 路径 focus+${key}:`, JSON.stringify(cand.t), '| 长大了?', grew);
        if (grew) { out.au3.hit = 'focus+' + key; break; }
      }
    }
    out.au3.verdict = out.au3.hit
      ? `成功：「${out.au3.hit}」让折叠内容区从 0 长起来`
      : '三路都没让内容区从 0 长起来（aria-expanded / focus+Enter / focus+Space 全部试过）';
    await shot(page, 'M-143-音频-高级设置-尝试之后.png');
    console.log('AU2 高级设置结论:', out.au3.verdict);
  }

  await logStep(B, {
    id: 'AU2-zoom-reset-and-accordion', title: '缩放归位后重读节点顶部工具条 + 高级设置三路激活',
    target: '开头先把缩放归到 100%（800% 时节点 4976×2800，AU 的点击点全落在视口外）；节点点击坐标 clamp 并用 elementFromPoint 回读；高级设置 aria-expanded → focus+Enter → focus+Space，判据是内容区高度 0→>40',
    evidence: out,
    visible_text: `缩放归位：${JSON.stringify(out.zoom)}。视口节点：${JSON.stringify(out.nodes)}。`
      + `\n\n各类型顶部工具条：${JSON.stringify(out.bars).slice(0, 1800)}。`
      + `\n\n高级设置：${JSON.stringify(out.au3).slice(0, 1400)}`,
    shot: 'M-142-音频-高级设置-展开前.png',
  });
  console.log('AU2 完成');
} finally {
  await browser.close();
}
