// Batch AU5 —— 把「高级设置」这件事一次问清楚。
//
// AU4 暴露了三个真问题，这一轮逐个钉死：
//
// ① **我一直在找错的东西。** AU4 读到视频节点的 text 里**有**「高级设置」，
//    音频节点的 text 里**没有**（只有 `语速 声调 音量`）。
//    而 §11 记着「音频：高级设置是可折叠分区，内含语速/声调/音量三个滑杆」，
//    我照着这条去找了**六轮**。
//    → 这轮必须**把两个节点的完整面板逐字读完**（不是取一个切片），
//      才能判断「高级设置」到底属于谁。
//
// ② **AU3/AU4 的过滤条件把工具条滤掉了。** 参数面板**就是 `.react-flow__node`
//    元素的子树**（class 实测 `react-flow__node react-flow__node-video nopan
//    selected selectable draggable`），但它的布局**溢出**到节点的
//    `getBoundingClientRect()` 之外 —— 工具条 `relY ≈ 167`。
//    我过滤 `relY < 110`，**正好把工具条切掉了**。
//    → 这轮不加 relY 过滤，直接把节点元素里**所有**按钮按 y 排序列出来，
//      自己看哪一批是工具条。
//
// ③ **AU4 取的是「面积最小」的候选**，对音频节点取到了滑杆那一小块
//    （`658×116`），把面板其余部分漏掉了。
//    → 改成取**同一批候选里 y 最小（最高）且最宽**的那个 = 完整面板。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAU5';
const { browser, page } = await launch();

async function closeDrawer() {
  const hit = await page.evaluate(() => {
    const cands = [...document.querySelectorAll('button,[role="button"],[aria-label]')]
      .filter((x) => ['关闭', '停靠到右侧'].includes((x.getAttribute('aria-label') || '').trim()))
      .map((x) => { const r = x.getBoundingClientRect();
        const on = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
        return { aria: x.getAttribute('aria-label'), visible: r.width > 2 && r.height > 2,
          onTop: !!(on && (x.contains(on) || on.contains(x))),
          cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; })
      .filter((x) => x.visible && x.onTop);
    return cands.find((x) => x.aria === '关闭') || cands[0] || { err: '没找到关闭按钮' };
  });
  if (hit.err) return hit;
  await page.mouse.click(hit.cx, hit.cy); await page.waitForTimeout(2200);
  return { clicked: hit.aria };
}
async function selectNode(titlePart) {
  const plan = await page.evaluate((t) => {
    const n = [...document.querySelectorAll('.react-flow__node')]
      .find((x) => (x.innerText || '').includes(t) && !x.classList.contains('selected'));
    if (!n) return { err: '视口里没有未选中的「' + t + '」' };
    const r = n.getBoundingClientRect();
    const cx = Math.min(Math.max(r.x + r.width / 2, 40), 1400);
    const cy = Math.min(Math.max(r.y + Math.min(r.height * 0.4, 60), 100), 700);
    const on = document.elementFromPoint(cx, cy);
    return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      cx: Math.round(cx), cy: Math.round(cy), hitsNode: !!(on && n.contains(on)) };
  }, titlePart);
  if (plan.err) return plan;
  if (!plan.hitsNode) { plan.err = `点 (${plan.cx},${plan.cy}) 不在节点上`; return plan; }
  await page.mouse.click(plan.cx, plan.cy); await page.waitForTimeout(3200);
  return plan;
}
/**
 * 把「选中节点」那整块（含溢出的参数面板）读全。
 * 关键：**不加 relY 过滤**，按 y 排序，自己看哪一批是工具条。
 */
const readSelected = (titlePart) => page.evaluate((t) => {
  const n = [...document.querySelectorAll('.react-flow__node.selected')][0]
    || [...document.querySelectorAll('.react-flow__node')].find((x) => (x.className || '').includes('selected'));
  if (!n) return { err: '没有选中的节点' };
  const r = n.getBoundingClientRect();
  const all = [...n.querySelectorAll('button,[role="button"],[aria-label],input')].map((b) => {
    const q = b.getBoundingClientRect();
    return { t: (b.innerText || b.value || '').replace(/\s+/g, ' ').trim().slice(0, 30),
      aria: b.getAttribute('aria-label'), tag: b.tagName, type: b.type,
      disabled: b.disabled === true, opacity: getComputedStyle(b).opacity,
      rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
      relY: Math.round(q.y - r.y) }; })
    .filter((b) => b.rect[2] > 0)
    .sort((a, b) => a.rect[1] - b.rect[1] || a.rect[0] - b.rect[0]);
  return {
    nodeCls: (n.className || '').toString().slice(0, 90),
    nodeRect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    fullText: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 900),
    allControls: all,
    /** 同一水平带上的按钮 = 工具条（y 差 < 12 且都在节点 rect 之下） */
    bands: (() => {
      const out = [];
      for (const b of all) {
        const hit = out.find((g) => Math.abs(g.cy - b.rect[1]) < 12);
        if (hit) { hit.items.push(b.t || b.aria || `${b.tag}[${b.type}]`); hit.y = Math.min(hit.y, b.rect[1]); }
        else out.push({ y: b.rect[1], cy: Math.round(b.rect[1] + b.rect[3] / 2), items: [b.t || b.aria || `${b.tag}[${b.type}]`] });
      }
      return out.map((g) => ({ y: g.y, cy: g.cy, n: g.items.length, items: g.items })).sort((a, b) => a.y - b.y);
    })(),
    hasAdvancedText: /高级设置/.test(n.innerText || ''),
    checkboxLike: all.filter((b) => b.tag === 'INPUT' && b.type === 'checkbox')
      .map((b) => ({ t: b.aria || b.t, rect: b.rect, relY: b.relY })),
    sliders: [...n.querySelectorAll('[class*="Slider-root"]')].map((s) => {
      const q = s.getBoundingClientRect();
      return { rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
        value: (s.parentElement?.parentElement?.querySelector('input[type=text]')?.value) || null }; }),
  };
}, titlePart);

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await beginBatch(B, { note: '读全「选中节点」整块（不加 relY 过滤），逐字比对音频/视频有没有「高级设置」' });

  const out = {};
  out.drawer = await closeDrawer();
  await fitView(page, 1); await page.waitForTimeout(1800);

  for (const [key, title, anchors] of [
    ['video', '视频节点', ['参考', '标记', '特效', '角色库', '运镜']],
    ['audio', '音频节点', ['语速', '声调', '音量']],
    ['image', '图片节点', ['参考', '标记', '风格']],
  ]) {
    await page.mouse.click(120, 760).catch(() => {}); await page.waitForTimeout(1000);   // 点空白取消选中
    const sel = await selectNode(title);
    out[key] = { sel };
    if (sel.err) { console.log(`AU5 ${title}:`, sel.err); continue; }
    out[key].read = await readSelected(title);
    const rd = out[key].read;
    console.log(`AU5 ${title} 完整文字:`, rd?.fullText);
    console.log(`AU5 ${title} 有「高级设置」?`, rd?.hasAdvancedText, '| nodeCls:', rd?.nodeCls);
    console.log(`AU5 ${title} 水平带:`, JSON.stringify(rd?.bands).slice(0, 1400));
    console.log(`AU5 ${title} checkbox:`, JSON.stringify(rd?.checkboxLike).slice(0, 500));
    await shot(page, `M-14${key === 'video' ? 4 : key === 'audio' ? 6 : 5}-${title}-面板全读.png`);
  }

  out.verdict = {
    videoHasAdvanced: out.video?.read?.hasAdvancedText,
    audioHasAdvanced: out.audio?.read?.hasAdvancedText,
    imageHasAdvanced: out.image?.read?.hasAdvancedText,
    audioText: out.audio?.read?.fullText,
    videoAdvancedContext: (out.video?.read?.fullText || '').match(/.{0,40}高级设置.{0,60}/)?.[0] || null,
  };
  console.log('AU5 判定:', JSON.stringify(out.verdict, null, 1));

  await logStep(B, {
    id: 'AU5-who-has-advanced', title: '「高级设置」到底属于哪个节点（音频还是视频）',
    target: '**不加 relY 过滤**读全选中节点元素（工具条 relY≈167，被我之前的 `<110` 切掉了）；逐字比对三种节点的面板全文',
    evidence: out,
    visible_text: `视频节点：${JSON.stringify(out.video).slice(0, 1200)}。`
      + `\n\n音频节点：${JSON.stringify(out.audio).slice(0, 1200)}。`
      + `\n\n图片节点：${JSON.stringify(out.image).slice(0, 1000)}。`
      + `\n\n判定：${JSON.stringify(out.verdict)}`,
    shot: 'M-144-视频节点-面板全读.png',
  });
  console.log('AU5 完成');
} finally {
  await browser.close();
}
