// Batch AU4 —— AU3 的关键修正：找错地方了。
//
// AU3 一直写的是 `n.querySelectorAll(...)`，`n` 是 `.react-flow__node` ——
// **节点卡片内部**。但 M-145 截图白纸黑字：视频节点选中后，
// `参考 / 标记 / 特效 / 角色库 / 运镜` 那一排出现在**参数面板的顶部**，
// 而参数面板是**挂在节点下方的独立容器**，不在节点卡片里面。
// 所以 `bar` 永远是 `[]` —— **不是按钮不存在，是我去错了房间。**
//
// 定位方式也一起换掉：不再靠「节点里面找」，
// 改用**内容锚点** —— 找同时含有 ≥2 个已知按钮文案的容器
// （视频：`参考`/`标记`/`特效`/`角色库`/`运镜`；音频：`语速`/`声调`/`音量`）。
// 这正是 §17.1 记的那条：「猜布局容器要么靠内容锚点，要么别猜」。
//
// 另外两处：
//   · 关抽屉要点**真正的「关闭」**，AU3 点的是「停靠到右侧」（`stillOpen: true`）。
//   · 定位节点用 **`⌘0` 适合屏幕**把全部节点框进视口，而不是「缩放至50%」
//     ——后者只改大小**不改位置**，AU3 的音频节点因此停在 `(-174,-25)`，视口外。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAU4';
const { browser, page } = await launch();

/** 关掉 TV Director 抽屉 —— 认 `aria-label="关闭"` 且**带个关闭图标**的那枚。 */
async function closeDrawer() {
  const hit = await page.evaluate(() => {
    const cands = [...document.querySelectorAll('button,[role="button"],[aria-label]')]
      .filter((x) => ['关闭', '停靠到右侧'].includes((x.getAttribute('aria-label') || '').trim()))
      .map((x) => { const r = x.getBoundingClientRect();
        const on = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
        return { aria: x.getAttribute('aria-label'), visible: r.width > 2 && r.height > 2,
          onTop: !!(on && (x.contains(on) || on.contains(x))), x: r.x,
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; })
      .filter((x) => x.visible && x.onTop)
      .sort((a, b) => (a.aria === '关闭' ? -1 : 1) - (b.aria === '关闭' ? -1 : 1));
    return cands[0] || { err: '没找到可点的抽屉关闭按钮' };
  });
  if (hit.err) return hit;
  await page.mouse.click(hit.cx, hit.cy); await page.waitForTimeout(2400);
  return { clicked: hit.aria,
    stillOpen: await page.evaluate(() => !!document.querySelector('.copilotKitMessagesContainer')) };
}
/** 点一个节点：取中心**偏上 1/3**，clamp 进视口，回读确认命中。 */
async function selectNode(titlePart) {
  const plan = await page.evaluate((t) => {
    const n = [...document.querySelectorAll('.react-flow__node')].find((x) => (x.innerText || '').includes(t));
    if (!n) return { err: '视口里没有「' + t + '」' };
    const r = n.getBoundingClientRect();
    const cx = Math.min(Math.max(r.x + r.width / 2, 40), 1400);
    const cy = Math.min(Math.max(r.y + Math.min(r.height * 0.35, 60), 100), 700);
    const on = document.elementFromPoint(cx, cy);
    return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      cx: Math.round(cx), cy: Math.round(cy), hitsNode: !!(on && n.contains(on)),
      onTop: on ? on.tagName + '.' + (on.className || '').toString().slice(0, 50) : null };
  }, titlePart);
  if (plan.err) return plan;
  if (!plan.hitsNode) { plan.err = `点 (${plan.cx},${plan.cy}) 落在 ${plan.onTop}`; return plan; }
  await page.mouse.click(plan.cx, plan.cy); await page.waitForTimeout(3200);
  return plan;
}
/** **用内容锚点**找参数面板：含有 ≥2 个指定文案的最小可见容器。 */
const panelByAnchors = (anchors) => page.evaluate((as) => {
  const cands = [...document.querySelectorAll('div,section')]
    .filter((e) => { const r = e.getBoundingClientRect();
      if (r.width < 220 || r.height < 60) return false;
      if (e.classList?.contains('react-flow__viewport')) return false;
      const t = (e.innerText || '').replace(/\s+/g, ' ');
      return as.filter((a) => t.includes(a)).length >= 2; });
  if (!cands.length) return { err: '没找到含 ≥2 个锚点文案的容器', anchors: as };
  // 取**面积最小**的那个 = 面板本身（不是包着它的更大容器）
  const sorted = cands.map((e) => { const r = e.getBoundingClientRect();
    return { e, area: r.width * r.height, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; })
    .sort((a, b) => a.area - b.area);
  const best = sorted[0].e;
  const r = best.getBoundingClientRect();
  const rd = (el) => { const q = el.getBoundingClientRect();
    return [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)]; };
  return {
    rect: sorted[0].rect, cls: (best.className || '').toString().slice(0, 80),
    text: (best.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 800),
    allLayers: sorted.slice(0, 4).map((s) => s.rect),
    toolbar: [...best.querySelectorAll('button,[role="button"],[aria-label]')].map((b) => {
      const q = b.getBoundingClientRect();
      return { t: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30),
        aria: b.getAttribute('aria-label'), title: b.getAttribute('title'),
        disabled: b.disabled === true, opacity: getComputedStyle(b).opacity,
        rect: rd(b), cy: Math.round(q.y + q.height / 2) }; })
      .filter((b) => b.rect[2] > 0)
      .sort((a, b) => a.rect[1] - b.rect[1]),
    inputs: [...best.querySelectorAll('input,textarea,select')].map((i) => ({
      tag: i.tagName, type: i.type, aria: i.getAttribute('aria-label'), ph: i.placeholder,
      v: i.value, rect: rd(i) })),
    sliders: best.querySelectorAll('[class*="Slider"]').length,
    switches: [...best.querySelectorAll('[role="switch"]')].map((s) => ({
      checked: s.getAttribute('aria-checked'), aria: s.getAttribute('aria-label'), rect: rd(s) })),
  };
}, anchors);

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await beginBatch(B, { note: '参数面板用内容锚点定位（不在节点卡片里）；⌘0 把节点框进视口；点真正的「关闭」' });

  const out = {};
  out.drawer = await closeDrawer();
  console.log('AU4 关抽屉:', JSON.stringify(out.drawer));
  await fitView(page, 1); await page.waitForTimeout(1600);      // ⌘0 适合屏幕
  out.afterFit = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')]
    .map((n) => { const r = n.getBoundingClientRect();
      return { title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 22),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        inView: r.x >= 0 && r.y >= 0 && r.x + r.width <= 1440 && r.y + r.height <= 810 }; }));
  console.log('AU4 ⌘0 后节点:', JSON.stringify(out.afterFit));
  await shot(page, 'M-138-适合屏幕-全部节点进视口.png');

  // ① 视频节点
  out.video = { sel: await selectNode('视频节点') };
  if (!out.video.sel.err) {
    out.video.panel = await panelByAnchors(['参考', '标记', '特效', '角色库', '运镜']);
    console.log('AU4 视频参数面板:', JSON.stringify(out.video.panel).slice(0, 2400));
    await shot(page, 'M-144-视频节点-参数面板.png');
    await page.mouse.click(120, 740); await page.waitForTimeout(1500);
  }

  // ② 图片节点
  out.image = { sel: await selectNode('图片节点') };
  if (!out.image.sel.err) {
    out.image.panel = await panelByAnchors(['参考', '标记', '风格']);
    console.log('AU4 图片参数面板:', JSON.stringify(out.image.panel).slice(0, 2000));
    await shot(page, 'M-145-图片节点-参数面板.png');
    await page.mouse.click(120, 740); await page.waitForTimeout(1500);
  }

  // ③ 音频节点 —— 「高级设置」
  out.audio = { count: await nodeCount(page) };
  let audioTitle = null;
  if (!out.audio.count) {
    await page.mouse.dblclick(460, 300); await page.waitForTimeout(1800);
    const it = await page.evaluate(() => {
      const el = [...document.querySelectorAll('div,button,li')].filter((e) => (e.innerText || '').trim() === '音频')
        .map((e) => { const r = e.getBoundingClientRect();
          return { area: Math.round(r.width * r.height), visible: r.width > 2 && r.height > 2 && r.y > 100 && r.y < 700,
            cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; })
        .filter((x) => x.visible).sort((a, b) => a.area - b.area)[0];
      return el || { err: '没有「音频」项' };
    });
    if (!it.err) { await page.mouse.click(it.cx, it.cy); await page.waitForTimeout(3000); }
    out.audio.created = await nodeCount(page);
    await fitView(page, 1); await page.waitForTimeout(1500);
  }
  out.audio.sel = await selectNode('音频节点');
  if (!out.audio.sel.err) {
    out.audio.panel = await panelByAnchors(['语速', '声调', '音量', '音频']);
    console.log('AU4 音频参数面板:', JSON.stringify(out.audio.panel).slice(0, 2600));
    await shot(page, 'M-146-音频节点-参数面板.png');

    // 找「高级设置」这一行：面板里所有文字 + 所有可点元素全列出来
    out.audio.survey = await page.evaluate(() => {
      const p = [...document.querySelectorAll('div,section')].filter((e) => {
        const r = e.getBoundingClientRect();
        return r.width > 220 && r.height > 60 && !e.classList?.contains('react-flow__viewport')
          && /语速|声调|音量|音频生成|高级设置/.test(e.innerText || '');
      }).map((e) => ({ r: e.getBoundingClientRect(), a: e.r || 0 })).sort((x, y) => x.r.width * x.r.height - y.r.width * y.r.height)[0];
      if (!p) return { err: '找不到音频参数面板' };
      const box = p.r;
      const inB = (el) => { const q = el.getBoundingClientRect();
        return q.x >= box.x - 4 && q.y >= box.y - 4 && q.x + q.width <= box.x + box.width + 4 && q.y + q.height <= box.y + box.height + 4; };
      const root = document.elementsFromPoint(box.x + box.width / 2, box.y + 20).pop();
      return {
        box: [Math.round(box.x), Math.round(box.y), Math.round(box.width), Math.round(box.height)],
        fullText: (p.r ? '' : '') || null,
        // 把面板附近（上下各扩 200px）所有可点元素与文本块列出来
        near: [...document.querySelectorAll('button,[role="button"],[tabindex="0"],[role="switch"],[class*="Slider"]')]
          .map((b) => { const q = b.getBoundingClientRect();
            return { t: (b.innerText || b.getAttribute('aria-label') || b.title || '').replace(/\s+/g, ' ').trim().slice(0, 26),
              tag: b.tagName, cls: (b.className || '').toString().slice(0, 46),
              rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
              inside: inB(b) }; })
          .filter((b) => b.rect[2] > 0 && b.rect[1] > box.y - 200 && b.rect[1] < box.y + box.height + 200),
      };
    });
    console.log('AU4 音频面板附近可点元素:', JSON.stringify(out.audio.survey).slice(0, 2600));
  }

  await logStep(B, {
    id: 'AU4-panel-by-anchors', title: '参数面板用内容锚点定位（工具条在面板里、不在节点卡片里）',
    target: '**不再从 `.react-flow__node` 内部找**（找错房间，恒为空数组）；改用「含 ≥2 个锚点文案的最小可见容器」；节点定位用 `⌘0` 适合屏幕而不是降缩放（后者只改大小不改位置）',
    evidence: out,
    visible_text: `关抽屉：${JSON.stringify(out.drawer)}；⌘0 后节点：${JSON.stringify(out.afterFit)}。`
      + `\n\n视频参数面板：${JSON.stringify(out.video).slice(0, 1600)}。`
      + `\n\n图片参数面板：${JSON.stringify(out.image).slice(0, 1400)}。`
      + `\n\n音频参数面板：${JSON.stringify(out.audio).slice(0, 1800)}`,
    shot: 'M-144-视频节点-参数面板.png',
  });
  console.log('AU4 完成');
} finally {
  await browser.close();
}
