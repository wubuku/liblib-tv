// Batch AU3 —— AU2 的两处修正，把节点面板这一块做完。
//
// 修正一：**TV Director 抽屉挡住了节点**。
//   AU2 的 `elementFromPoint` 回读说得很清楚：节点 rect 是 `[721,409,622×350]`，
//   它的中心点 `(1032,469)` 落在 **`DIV.copilotKitMessagesContainer`**（抽屉的消息区）上。
//   于是 `hitsNode: false`，工具条一个都没读到。
//   修法：**先把抽屉关掉**（它头部有 `aria-label="关闭"` / `停靠到右侧`），
//   再点节点。点了之后还要回读确认。
//
// 修正二：**参数面板可能整个在视口外**。
//   音频节点 rect 是 `[565,301,350×350]`，参数面板挂在它**下方**，
//   起始 y 就到 651，视口只有 810 高 —— 面板大半截在外面。
//   `readFold()` 返回 `[]` 不是「没有折叠区」，是**折叠区压根没渲染出来**。
//   修法：**把缩放降到 50%**（菜单里的「缩放至50%」），面板跟着缩小就进来了；
//   读完再量一次高度。
//
// 关于「高级设置」：AU2 找到的 `aria-expanded="false"` 全是**顶栏**上的
// （`画布 2` / `发布与分享` / …），**跟音频节点无关** —— 说明
// 「高级设置」那个折叠开关**没有用 `aria-expanded`**。
// 这轮先确认它到底存不存在（把面板里所有可点的、带文字的元素都列出来），
// 找到了再点，找不到就如实记「没找到切换控件」。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAU3';
const { browser, page } = await launch();

const menuOpen = () => page.evaluate(() => [...document.querySelectorAll('[class*="Menu-dropdown"],[class*="Popover-dropdown"]')]
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 40 && r.height > 12; }).length > 0);
async function setZoom(label) {
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
  await page.mouse.click(it.cx, it.cy); await page.waitForTimeout(2200);
  return { ok: true, scale: await page.evaluate(() => {
    const v = document.querySelector('.react-flow__viewport');
    const m = v && /scale\(([\d.]+)\)/.exec(v.style.transform || '');
    return m ? Number(m[1]) : null; }) };
}
/** 关掉 TV Director 抽屉（如果开着）。 */
async function closeDrawer() {
  const has = await page.evaluate(() => !!document.querySelector('.copilotKitMessagesContainer,[class*="chat-welcome"]'));
  if (!has) return { wasOpen: false };
  const hit = await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,[role="button"],[aria-label]')]
      .filter((x) => ['关闭', '停靠到右侧'].includes((x.getAttribute('aria-label') || '').trim()))
      .map((x) => { const r = x.getBoundingClientRect();
        const on = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
        return { aria: x.getAttribute('aria-label'), visible: r.width > 2 && r.height > 2,
          onTop: !!(on && (x.contains(on) || on.contains(x))),
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; })
      .filter((x) => x.visible && x.onTop)[0];
    return e || { err: '抽屉开着但找不到它的关闭按钮' };
  });
  if (hit.err) return { wasOpen: true, err: hit.err };
  await page.mouse.click(hit.cx, hit.cy); await page.waitForTimeout(2200);
  return { wasOpen: true, clicked: hit.aria,
    stillOpen: await page.evaluate(() => !!document.querySelector('.copilotKitMessagesContainer')) };
}
/** 点一个节点：取**左上角内侧**而不是中心，并回读确认命中。 */
async function selectNode(titlePart) {
  const plan = await page.evaluate((t) => {
    const n = [...document.querySelectorAll('.react-flow__node')].find((x) => (x.innerText || '').includes(t));
    if (!n) return { err: '视口里没有「' + t + '」' };
    const r = n.getBoundingClientRect();
    // 取**左上角内侧 30% 处**：避开中心（可能压在别的浮层上）
    const cx = Math.min(Math.max(r.x + r.width * 0.3, 30), 1410);
    const cy = Math.min(Math.max(r.y + r.height * 0.3, 90), 700);
    const on = document.elementFromPoint(cx, cy);
    return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      cx: Math.round(cx), cy: Math.round(cy), hitsNode: !!(on && n.contains(on)),
      onTop: on ? on.tagName + '.' + (on.className || '').toString().slice(0, 50) : null };
  }, titlePart);
  if (plan.err) return plan;
  if (!plan.hitsNode) { plan.err = `点 (${plan.cx},${plan.cy}) 落在 ${plan.onTop}，不在节点上`; return plan; }
  await page.mouse.click(plan.cx, plan.cy); await page.waitForTimeout(3000);
  return plan;
}
/** 参数面板：找到挂在节点下方/侧边的那块，读里面每一个可点元素。 */
const paramPanel = (titlePart) => page.evaluate((t) => {
  const n = [...document.querySelectorAll('.react-flow__node')].find((x) => (x.innerText || '').includes(t));
  if (!n) return { err: '节点不见了' };
  const nr = n.getBoundingClientRect();
  const cands = [...document.querySelectorAll('div,section')]
    .filter((e) => { const r = e.getBoundingClientRect();
      // 排除画布本身、排除节点自身
      if (e.classList?.contains('react-flow__viewport')) return false;
      if (r.width < 150 || r.height < 60) return false;
      const txt = (e.innerText || '').replace(/\s+/g, ' ').trim();
      return /高级设置|语速|声调|音量|智能引用|AutoLink|联网搜索|自动校验素材|参数/.test(txt); })
    .map((e) => { const r = e.getBoundingClientRect();
      return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        nearNode: r.x >= nr.x - 700 && r.x < nr.x + nr.width + 700 && r.y > nr.y - 100 && r.y < nr.y + nr.height + 500,
        cls: (e.className || '').toString().slice(0, 70),
        text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300),
        clickable: [...e.querySelectorAll('button,[role="button"],[tabindex="0"]')].map((b) => {
          const q = b.getBoundingClientRect();
          return { t: (b.innerText || b.getAttribute('aria-label') || b.title || '').replace(/\s+/g, ' ').trim().slice(0, 30),
            area: Math.round(q.width * q.height), visible: q.width > 2 && q.height > 2,
            cx: Math.round(q.x + q.width / 2), cy: Math.round(q.y + q.height / 2) };
        }).filter((b) => b.visible && b.area > 60).slice(0, 20),
        sliders: e.querySelectorAll('[class*="Slider"]').length,
        switches: e.querySelectorAll('[role="switch"]').length,
      }; });
  return { nodeRect: [Math.round(nr.x), Math.round(nr.y), Math.round(nr.width), Math.round(nr.height)], cands };
}, titlePart);

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await beginBatch(B, { note: '先关抽屉再点节点（避开遮挡）+ 降到 50% 让参数面板进视口' });

  const out = {};
  out.drawer = await closeDrawer();
  out.zoom = await setZoom('缩放至50%');
  console.log('AU3 关抽屉:', JSON.stringify(out.drawer), '| 缩放:', JSON.stringify(out.zoom));
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(1000);

  // 音频节点
  out.audio = { count: await nodeCount(page) };
  if (!out.audio.count) {
    await page.mouse.dblclick(500, 320); await page.waitForTimeout(1600);
    const it = await page.evaluate(() => {
      const el = [...document.querySelectorAll('div,button,li')].filter((e) => (e.innerText || '').trim() === '音频')
        .map((e) => { const r = e.getBoundingClientRect();
          return { area: Math.round(r.width * r.height), visible: r.width > 2 && r.height > 2 && r.y > 100 && r.y < 700,
            cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; })
        .filter((x) => x.visible).sort((a, b) => a.area - b.area)[0];
      return el || { err: '没有「音频」项' };
    });
    if (!it.err) { await page.mouse.click(it.cx, it.cy); await page.waitForTimeout(2800); }
    out.audio.created = await nodeCount(page);
  }

  out.selAudio = await selectNode('音频节点');
  console.log('AU3 选中音频节点:', JSON.stringify(out.selAudio));
  out.panelAudio = await paramPanel('音频节点');
  console.log('AU3 音频参数面板:', JSON.stringify(out.panelAudio).slice(0, 2200));
  await shot(page, 'M-142-音频节点-参数面板.png');

  // 图片 / 视频节点的顶部工具条
  out.bars = {};
  for (const t of ['图片节点', '视频节点']) {
    const sel = await selectNode(t);
    if (sel.err) { out.bars[t] = { sel }; continue; }
    out.bars[t] = { sel, bar: await page.evaluate((tt) => {
      const n = [...document.querySelectorAll('.react-flow__node')].find((x) => (x.innerText || '').includes(tt));
      const r = n.getBoundingClientRect();
      return [...n.querySelectorAll('button,[role="button"],[aria-label]')].map((b) => {
        const q = b.getBoundingClientRect();
        return { t: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24),
          aria: b.getAttribute('aria-label'), title: b.getAttribute('title'),
          disabled: b.disabled === true, opacity: getComputedStyle(b).opacity,
          relY: Math.round(q.y - r.y), rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] };
      }).filter((b) => b.rect[2] > 0 && b.relY >= 0 && b.relY < 110);
    }, t) };
    console.log(`AU3 ${t} 顶部工具条:`, JSON.stringify(out.bars[t].bar).slice(0, 800));
    await shot(page, `M-14${t === '图片节点' ? 4 : 5}-${t}-顶部工具条.png`);
    await page.mouse.click(100, 700); await page.waitForTimeout(1400);
  }

  await logStep(B, {
    id: 'AU3-close-drawer-then-read', title: '关掉 TV Director 抽屉 + 降到 50% 后读节点顶部工具条与参数面板',
    target: '抽屉开着时节点中心点落在 `.copilotKitMessagesContainer` 上 —— 改点节点左上角内侧 30% 处并回读；参数面板多半在视口外，降到 50% 让它进来',
    evidence: out,
    visible_text: `关抽屉：${JSON.stringify(out.drawer)}；缩放：${JSON.stringify(out.zoom)}。`
      + `\n\n音频节点选中：${JSON.stringify(out.selAudio)}。`
      + `\n\n音频参数面板：${JSON.stringify(out.panelAudio).slice(0, 1500)}。`
      + `\n\n顶部工具条：${JSON.stringify(out.bars).slice(0, 1500)}`,
    shot: 'M-142-音频节点-参数面板.png',
  });
  console.log('AU3 完成');
} finally {
  await browser.close();
}
