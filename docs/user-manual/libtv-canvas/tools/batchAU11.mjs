// Batch AU11 —— **参数面板到底渲不渲染**？先关掉那个一直开着的 TV Director 抽屉。
//
// 事情起于 AU10 的截图：DOM 里参数面板的 rect 是 660×605（`fullyVisible: false` 只是因为下边超 78px），
// `innerText` 读得到全文，**但截图里一个面板都看不见** —— 最大的卡片就是视频节点本体 311×175。
//
// 于是有两种可能，两者的手册含义完全相反：
//   (a) 面板被某层浮层盖住 → 正文「参数面板是挂在节点下方的独立卡片」仍然成立
//   (b) 面板压根没渲染    → 手册整节「节点里的『高级设置』」的前提都要重写
//
// 头号嫌疑：**TV Director 抽屉**。AU10 截图右侧明明白白开着「新对话 / 让 TV Director 辅助你的无限创意」，
// 而 AU3/AU4 关过它两次都 `stillOpen: true`。这轮换三种关法，每关一次都**量容器坐标**确认，
// 关不掉就把它的 DOM 结构 dump 出来找真正的关闭入口。
//
// 附带解决一件小事：缩放菜单截图里能看清全貌了 ——
// `输入框 50 %` / `放大 ⌘+` / `缩小 ⌘-` / `适合屏幕 ⌘0` / `缩放至50%`（高亮）/ `缩放至100%` / `缩放至800%`，
// 底栏同时显示 `50%`。这张图有用，登记进 manifest。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAU11';
const { browser, page } = await launch();

/** 判据问「抽屉在不在」要问容器实时坐标，不是问有没有某段文字。 */
const drawerState = () => page.evaluate(() => {
  // 找那个带「新对话」和输入框的大浮层
  const cands = [...document.querySelectorAll('div,section,aside')]
    .filter((e) => {
      const r = e.getBoundingClientRect();
      if (r.width < 200 || r.height < 300) return false;
      if (r.x < 200) return false;                       // 靠右
      const t = (e.innerText || '');
      return t.includes('TV Director') || t.includes('新对话') || t.includes('全能创作');
    })
    .map((e) => { const r = e.getBoundingClientRect();
      return { cls: (e.className || '').toString().slice(0, 90),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        z: getComputedStyle(e).zIndex, pos: getComputedStyle(e).position,
        hitHead: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40) }; })
    .sort((a, b) => (a.rect[2] * a.rect[3]) - (b.rect[2] * b.rect[3]));
  return { count: cands.length, smallest: cands[0] || null, all: cands.slice(0, 3) };
});

/** 把抽屉里所有可点的关闭入口 dump 出来。 */
const drawerClosers = () => page.evaluate(() => {
  const big = [...document.querySelectorAll('div,section,aside')].filter((e) => {
    const r = e.getBoundingClientRect();
    return r.width >= 200 && r.height >= 300 && r.x >= 200;
  }).sort((a, b) => (a.getBoundingClientRect().width * a.getBoundingClientRect().height)
    - (b.getBoundingClientRect().width * b.getBoundingClientRect().height))[0];
  if (!big) return { err: '没找到抽屉容器' };
  return { container: (big.className || '').toString().slice(0, 90),
    buttons: [...big.querySelectorAll('button,[role="button"],[aria-label]')].map((e) => {
      const r = e.getBoundingClientRect();
      return { aria: e.getAttribute('aria-label'), title: e.getAttribute('title'),
        text: (e.innerText || '').trim().slice(0, 10),
        cls: (e.className || '').toString().slice(0, 60),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        onTop: !!(r.width > 0 && (() => { const o = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
          return o && (e === o || e.contains(o) || o.contains(e)); })()) };
    }) };
});

const geom = () => page.evaluate(() => {
  const n = document.querySelector('.react-flow__node.selected');
  if (!n) return { err: '没有选中节点' };
  const nr = n.getBoundingClientRect();
  let x0 = nr.x, y0 = nr.y, x1 = nr.right, y1 = nr.bottom;
  for (const e of n.querySelectorAll('*')) {
    const q = e.getBoundingClientRect();
    if (q.width < 1 || q.height < 1) continue;
    x0 = Math.min(x0, q.x); y0 = Math.min(y0, q.y); x1 = Math.max(x1, q.right); y1 = Math.max(y1, q.bottom);
  }
  // 「渲染了吗」不看 rect，看**面板里有没有一块能真正被命中的内容**
  const adv = [...n.querySelectorAll('*')].find((e) => (e.textContent || '').trim() === '高级设置');
  let advHit = null;
  if (adv) {
    const r = adv.getBoundingClientRect();
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    const on = (cx >= 0 && cy >= 0 && cx < 1440 && cy < 810) ? document.elementFromPoint(cx, cy) : null;
    advHit = { cx: Math.round(cx), cy: Math.round(cy), inViewport: cx >= 0 && cy >= 0 && cx < 1440 && cy < 810,
      on: on ? on.tagName + '.' + (on.className || '').toString().slice(0, 40) : null,
      hits: !!(on && (on === adv || adv.contains(on))) };
  }
  return { nodeRect: [Math.round(nr.x), Math.round(nr.y), Math.round(nr.width), Math.round(nr.height)],
    panelUnion: [Math.round(x0), Math.round(y0), Math.round(x1 - x0), Math.round(y1 - y0)],
    fullyVisible: x0 >= 0 && y0 >= 0 && x1 <= 1440 && y1 <= 810, advHit,
    title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 100) };
});

async function selectByText(t) {
  const plan = await page.evaluate((t) => {
    for (const n of document.querySelectorAll('.react-flow__node')) {
      if (!(n.innerText || '').includes(t) || n.classList.contains('selected')) continue;
      const r = n.getBoundingClientRect();
      if (r.x < 5 || r.x + r.width > 1435 || r.y < 60 || r.y + r.height > 800) continue;
      for (const [fx, fy] of [[0.5, 0.4], [0.5, 0.5], [0.35, 0.5], [0.65, 0.5], [0.5, 0.3]]) {
        const cx = r.x + r.width * fx, cy = r.y + r.height * fy;
        const on = document.elementFromPoint(cx, cy);
        if (on && n.contains(on) && !on.closest('[class*="Popover"],[class*="Menu"],[class*="Dropdown"]')) {
          return { cx: Math.round(cx), cy: Math.round(cy),
            title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30) };
        }
      }
    }
    return { err: '找不到可点的「' + t + '」' };
  }, t);
  if (plan.err) return plan;
  await page.mouse.click(plan.cx, plan.cy);
  await page.waitForTimeout(3600);
  return plan;
}

async function dragToCenter() {
  const g = await page.evaluate(() => {
    const n = document.querySelector('.react-flow__node.selected');
    if (!n) return { err: '没有选中节点' };
    const r = n.getBoundingClientRect();
    for (const [fx, fy] of [[0.5, 0.5], [0.35, 0.5], [0.65, 0.5], [0.5, 0.3], [0.5, 0.7]]) {
      const cx = r.x + r.width * fx, cy = r.y + r.height * fy;
      if (cx < 5 || cx > 1435 || cy < 60 || cy > 780) continue;
      const on = document.elementFromPoint(cx, cy);
      if (on && n.contains(on) && !on.closest('[class*="Popover"],[class*="Menu"],[class*="Dropdown"]')) {
        return { cx: Math.round(cx), cy: Math.round(cy) };
      }
    }
    return { err: '节点内部没有可按下的点' };
  });
  if (g.err) return g;
  const t = await page.evaluate(() => {
    const n = document.querySelector('.react-flow__node.selected');
    const r = n.getBoundingClientRect();
    return { dx: Math.round(720 - (r.x + r.width / 2)), dy: Math.round(400 - (r.y + r.height / 2)) };
  });
  await page.mouse.move(g.cx, g.cy); await page.mouse.down();
  for (let i = 1; i <= 12; i += 1) { await page.mouse.move(g.cx + (t.dx * i) / 12, g.cy + (t.dy * i) / 12); await page.waitForTimeout(70); }
  await page.mouse.up(); await page.waitForTimeout(1900);
  return { grabbed: g, ...t };
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1000);
  await beginBatch(B, { note: '关掉一直开着的 TV Director 抽屉，验参数面板到底渲不渲染' });

  const out = {};
  out.before = await drawerState();
  console.log('AU11 抽屉(前):', JSON.stringify(out.before.all, null, 1).slice(0, 700));
  await shot(page, 'M-165-抽屉开着.png');

  // ── 关抽屉：三种办法，每种都回量坐标
  out.closeAttempts = [];
  // 法 1：找容器里最像「关闭」的按钮
  const cl = await drawerClosers();
  console.log('AU11 抽屉按钮:', JSON.stringify(cl).slice(0, 1200));
  out.closeAttempts.push({ method: 'dump', closers: cl });
  const likeClose = (cl.buttons || []).filter((b) =>
    /关闭|收起|折叠|close|收起|最小/i.test((b.aria || '') + (b.title || '') + (b.text || '')) && b.onTop);
  if (likeClose.length) {
    const b = likeClose[0];
    await page.mouse.click(b.rect[0] + b.rect[2] / 2, b.rect[1] + b.rect[3] / 2);
    await page.waitForTimeout(2200);
    out.closeAttempts.push({ method: '点关闭按钮', target: b, after: await drawerState() });
    console.log('AU11 点关闭后:', JSON.stringify((await drawerState()).all?.[0] || 'GONE'));
  }
  // 法 2：Esc
  if ((await drawerState()).count > 0) {
    await page.keyboard.press('Escape'); await page.waitForTimeout(2000);
    out.closeAttempts.push({ method: 'Esc', after: await drawerState() });
    console.log('AU11 Esc 后:', JSON.stringify((await drawerState()).all?.[0] || 'GONE'));
  }
  // 法 3：点画布空白
  if ((await drawerState()).count > 0) {
    await page.mouse.click(120, 120); await page.waitForTimeout(2200);
    out.closeAttempts.push({ method: '点空白', after: await drawerState() });
    console.log('AU11 点空白后:', JSON.stringify((await drawerState()).all?.[0] || 'GONE'));
  }
  out.drawerAfter = await drawerState();
  console.log('AU11 抽屉最终 count:', out.drawerAfter.count);
  await shot(page, 'M-166-关抽屉之后.png');

  // ── 现在才问参数面板渲不渲染
  out.video = { sel: await selectByText('视频节点') };
  console.log('AU11 选中视频:', JSON.stringify(out.video.sel).slice(0, 300));
  if (!out.video.sel.err) {
    out.video.geom = await geom();
    console.log('AU11 视频几何:', JSON.stringify(out.video.geom));
    await shot(page, 'M-167-视频节点-面板渲染测试.png');
    if (!out.video.geom.fullyVisible) {
      out.video.drag = await dragToCenter();
      out.video.geom2 = await geom();
      console.log('AU11 视频拖后:', JSON.stringify(out.video.geom2));
      await shot(page, 'M-167-视频节点-面板渲染测试.png');
    }
  }

  await logStep(B, {
    id: 'AU11-drawer-blocks-panel', title: '关掉常开的 TV Director 抽屉，验参数面板到底渲不渲染',
    target: 'DOM 里有面板 ≠ 屏幕上有面板。**截图是最后的裁判** —— AU10 里 rect 是 660×605、'
      + '`innerText` 读得到全文，但画面上一个面板都看不见，而右侧 TV Director 抽屉一直开着',
    evidence: out,
    visible_text: JSON.stringify(out).slice(0, 3000),
    shot: 'M-167-视频节点-面板渲染测试.png',
  });
  console.log('\nAU11 完成');
} finally {
  await browser.close();
}
