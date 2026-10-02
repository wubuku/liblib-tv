// Batch AU8 —— **先 dump，不动作**：把「高级设置到底默认展开还是折叠」这件事一次问穿。
//
// 为什么不能直接点：
//   正文 create-nodes.md:240 写「默认折叠」
//   AUDIT.md:60 / 137 / 158 写「折叠容器高度恒为 0」「点开没成功（四次尝试）」
//   AU5 却读到语速/声调/音量**一直可见**、值 1.00/0/1.0
//
// 三份记录互相矛盾。而 §「连续 N 次失败时先 dump 全部，别继续调条件」说得很清楚：
// 调条件是猜，dump 是看。所以这一轮**一个开关都不点**，
// 只把节点子树里所有可能相关的容器和「高级设置」这四个字的可点击祖先链**原样倒出来**。
//
// 要回答的四个问题：
//   Q1 节点子树里有哪些 `display:grid` 容器？各自的 `grid-template-rows` **计算值**是多少？
//      （`0fr` = 折叠，`1fr`/具体 px = 展开。写 `0px` 的话就是折叠态）
//   Q2 「高级设置」这四个字落在哪个元素上？它的**可点击祖先链**长什么样（tag/class/aria）？
//      —— 决定它到底是不是能点的（正文说是「折叠分区不是按钮」）
//   Q3 三个滑杆（语速/声调/音量）的**实测** rect + 那个点上现在是**谁**（elementFromPoint）
//   Q4 图片节点的参数面板长什么样（AU5 漏了它）
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView, listNodes } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAU8';
const { browser, page } = await launch();

/** 节点子树全景：所有 grid 容器 + 文字 + 滑杆 + 「高级设置」祖先链。**不做任何筛选。 */
const dumpNode = (t) => page.evaluate((title) => {
  const n = [...document.querySelectorAll('.react-flow__node.selected')][0]
    || [...document.querySelectorAll('.react-flow__node')].find((x) => (x.innerText || '').includes(title));
  if (!n) return { err: '没有选中节点，也找不到「' + title + '」' };
  const r = n.getBoundingClientRect();
  const vis = (e) => {
    const q = e.getBoundingClientRect();
    if (q.width < 1 || q.height < 1) return false;
    const cs = getComputedStyle(e);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return false;
    const cx = q.x + q.width / 2, cy = q.y + q.height / 2;
    if (cx < 0 || cy < 0 || cx > innerWidth || cy > innerHeight) return false;
    const on = document.elementFromPoint(cx, cy);
    return !!(on && (e === on || e.contains(on) || on.contains(e)));
  };
  const name = (e) => e.tagName.toLowerCase()
    + (e.getAttribute('class') || '').split(/\s+/).filter(Boolean).slice(0, 3).map((c) => '.' + c).join('')
    + (e.getAttribute('aria-label') ? `[aria=${e.getAttribute('aria-label')}]` : '')
    + (e.getAttribute('role') ? `[role=${e.getAttribute('role')}]` : '');

  // Q1 —— 全部 grid 容器，连计算值
  const grids = [...n.querySelectorAll('*')].filter((e) => {
    const cs = getComputedStyle(e);
    return cs.display === 'grid' || cs.display === 'inline-grid';
  }).map((e) => {
    const q = e.getBoundingClientRect();
    return { sel: name(e), rows: getComputedStyle(e).gridTemplateRows,
      h: Math.round(q.height), y: Math.round(q.y), w: Math.round(q.width),
      visible: vis(e), cls: (e.getAttribute('class') || '') };
  });

  // Q2 —— 含「高级设置」的元素 + 可点击祖先链
  let adv = null;
  for (const e of n.querySelectorAll('*')) {
    const t = (e.textContent || '').trim();
    if (t !== '高级设置') continue;
    const chain = [];
    for (let a = e; a && a !== n.parentElement; a = a.parentElement) chain.push(name(a));
    const q = e.getBoundingClientRect();
    adv = { self: name(e), tag: e.tagName, cls: (e.getAttribute('class') || ''),
      rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
      visible: vis(e), chain,
      // 链上第一个「看起来能点」的（button / role=button / [aria-label]）
      clickable: chain.find((c) => /^(button|summary)|\[role=(button|tab|switch|checkbox)\]|\[aria=/.test(c)) || null };
    break;
  }

  // Q3 —— 三个滑杆的实测状态
  const sliders = [...n.querySelectorAll('[role="slider"],input[type=range],.mantine-Slider-track,.mantine-Slider-root,[class*="Slider"]')]
    .map((e) => {
      const q = e.getBoundingClientRect();
      const cx = q.x + q.width / 2, cy = q.y + q.height / 2;
      const on = (cx >= 0 && cy >= 0 && cx < innerWidth && cy < innerHeight) ? document.elementFromPoint(cx, cy) : null;
      return { sel: name(e), rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
        visible: vis(e), value: e.getAttribute('aria-valuenow') || e.value || null,
        ariaMax: e.getAttribute('aria-valuemax') || e.max || null,
        onCenter: on ? on.tagName + '.' + (on.className || '').toString().slice(0, 50) : null };
    });

  // 标签 → 值的对应（把「语速/声调/音量」附近的数字抓出来）
  const labels = [...n.querySelectorAll('*')].filter((e) => {
    const t = (e.textContent || '').trim();
    return ['语速', '声调', '音量'].includes(t) && e.children.length === 0;
  }).map((e) => {
    const p = e.parentElement;
    return { text: (p ? p.textContent : e.textContent).replace(/\s+/g, ' ').trim().slice(0, 40) };
  });

  return {
    nodeRect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160),
    grids, adv, sliders, labels,
    inputNumbers: n.querySelectorAll('input[type=number]').length,
    totalEls: n.querySelectorAll('*').length,
  };
}, t);

async function selectNode(titlePart) {
  const plan = await page.evaluate((t) => {
    const n = [...document.querySelectorAll('.react-flow__node')]
      .find((x) => (x.innerText || '').includes(t) && !x.classList.contains('selected'));
    if (!n) return { err: '视口里没有未选中的「' + t + '」' };
    const r = n.getBoundingClientRect();
    for (const [fx, fy] of [[0.5, 0.4], [0.5, 0.5], [0.35, 0.5], [0.65, 0.5], [0.5, 0.25], [0.5, 0.7]]) {
      const cx = r.x + r.width * fx, cy = r.y + r.height * fy;
      if (cx < 5 || cx > 1435 || cy < 60 || cy > 780) continue;
      const on = document.elementFromPoint(cx, cy);
      if (on && n.contains(on) && !on.closest('[class*="Popover"],[class*="Menu"],[class*="Dropdown"]')) {
        return { cx: Math.round(cx), cy: Math.round(cy), fx, fy,
          on: on.tagName + '.' + (on.className || '').toString().slice(0, 50) };
      }
    }
    return { err: '节点内部没有可点的点（都被挡住了）', rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  }, titlePart);
  if (plan.err) return plan;
  await page.mouse.click(plan.cx, plan.cy);
  await page.waitForTimeout(3600);
  return plan;
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page);
  await beginBatch(B, { note: '零点击 dump：把「高级设置」的折叠状态一次问穿，同时补上图片节点' });

  const out = {};
  out.overview = await listNodes(page);
  console.log('AU8 视口节点:', JSON.stringify(out.overview, null, 1).slice(0, 1400));

  for (const [key, title] of [['audio', '音频节点'], ['video', '视频节点'], ['image', '图片节点']]) {
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(900);
    out[key] = { sel: await selectNode(title) };
    if (out[key].sel.err) { console.log(`AU8 ${title}:`, out[key].sel.err); continue; }
    out[key].dump = await dumpNode(title);
    const d = out[key].dump;
    console.log(`\n===== AU8 ${title} =====`);
    console.log('节点 rect:', JSON.stringify(d.nodeRect), '| 子元素总数:', d.totalEls, '| input[type=number]:', d.inputNumbers);
    console.log('grid 容器:', JSON.stringify(d.grids, null, 1));
    console.log('「高级设置」:', JSON.stringify(d.adv, null, 1));
    console.log('滑杆:', JSON.stringify(d.sliders, null, 1));
    console.log('标签值:', JSON.stringify(d.labels));
    await shot(page, `M-15${['audio', 'video', 'image'].indexOf(key)}-${title}-dump.png`);
  }

  await logStep(B, {
    id: 'AU8-dump-advanced-state', title: '零点击 dump：高级设置的折叠状态、图片节点面板',
    target: '**一个开关都不点**，把节点子树里所有 grid 容器的 `grid-template-rows` 计算值、'
      + '「高级设置」四字的可点击祖先链、三个滑杆的实测 rect 全倒出来；图片节点本轮补上',
    evidence: out,
    visible_text: JSON.stringify(out).slice(0, 3000),
    shot: 'M-150-音频节点-dump.png',
  });
  console.log('\nAU8 完成');
} finally {
  await browser.close();
}
