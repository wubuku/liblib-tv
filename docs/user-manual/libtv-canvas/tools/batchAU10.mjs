// Batch AU10 —— 收口：把两张完整面板拍下来，并把「高级设置」这四个字钉死。
//
// AU9 的三条硬读数（互相独立，全部指向同一个结论）：
//   ① 全页 `grid-rows-[1fr]` 数量 = **0**，点击前后都是 0
//      → 这个折叠区在产品里**从来没有展开态**
//   ② 折叠容器 `grid-template-rows` 计算值 = **0px**，`innerH` = **0**，`h` = **0**
//      → 不是「内容被裁掉」，是**内容根本不在**
//   ③ 「高级设置」标题是 `div.pt-3.text-xs.font-bold`，祖先链上**没有 button/role/aria**，
//      链底是 `.react-flow__node`；而且它那个点上 `elementFromPoint` 命中的是
//      `DIV.flex h-full items-center justify-center`（`cursor: grab`）——
//      **参数面板顶部被节点卡片本体压住了**（面板宽 642 居中在 263 宽的节点上，必然重叠）
//   ④ 三个开关 `联网搜索/自动校验素材/智能引用` 在 y=489，**在折叠容器（y=448,h=0）外面、visible: true**
//
// ①②③④ 合起来 = 「高级设置」是**一个点不动的静态标签**，三个开关是**它下面独立的一行、常驻可见**。
// 正文写「点它展开/收起」「默认折叠」是错的。
//
// 这轮只做三件实事：
//   A. 缩放到 50% → 选视频节点 → 拍到**整块**参数面板（AU9 菜单没开是触发点找错了：
//      不是底栏的 aria 按钮，而是**左下角那串百分比文本**）
//   B. 拖到视口中心 → 拍到**整块**音频参数面板（AU7 已证明这条路走得通）
//   C. 把「参数面板顶部被节点本体压住」这件事也量出来（z 序 + 重叠面积），
//      因为这是「为什么点不到高级设置」的解释，不解释清楚读者会以为自己手残
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAU10';
const { browser, page } = await launch();

const menuOpen = () => page.evaluate(() =>
  [...document.querySelectorAll('[class*="Menu-dropdown"],[class*="Popover-dropdown"]')]
    .some((e) => { const r = e.getBoundingClientRect(); return r.width > 40 && r.height > 12; }));

/** 抄 AU3 的做法：触发点是**左下角那串百分比文本**，不是底栏那枚 aria 按钮。 */
async function setZoom(label) {
  const trig = await page.evaluate(() => {
    const e = [...document.querySelectorAll('*')].find((x) => /^\d+%$/.test((x.innerText || '').trim())
      && x.getBoundingClientRect().width < 60 && x.getBoundingClientRect().y > 700);
    if (!e) return null;
    const b = (e.closest('button,[role="button"]') || e).getBoundingClientRect();
    return { cx: Math.round(b.x + b.width / 2), cy: Math.round(b.y + b.height / 2),
      text: (e.innerText || '').trim() };
  });
  if (!trig) return { err: '找不到缩放触发点' };
  for (let i = 0; i < 2 && !(await menuOpen()); i += 1) {
    await page.mouse.click(trig.cx, trig.cy); await page.waitForTimeout(1500);
  }
  if (!(await menuOpen())) return { err: '点了触发点菜单还是没开', trig };
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
  await page.mouse.click(it.cx, it.cy); await page.waitForTimeout(2400);
  return { ok: true, trig, scale: await page.evaluate(() => {
    const v = document.querySelector('.react-flow__viewport');
    const m = v && /scale\(([\d.]+)\)/.exec(v.style.transform || '');
    return m ? Number(m[1]) : null; }) };
}

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
  return { nodeRect: [Math.round(nr.x), Math.round(nr.y), Math.round(nr.width), Math.round(nr.height)],
    panelUnion: [Math.round(x0), Math.round(y0), Math.round(x1 - x0), Math.round(y1 - y0)],
    fullyVisible: x0 >= 0 && y0 >= 0 && x1 <= 1440 && y1 <= 810,
    title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 130) };
});

async function selectByText(t) {
  const plan = await page.evaluate((t) => {
    const ns = [...document.querySelectorAll('.react-flow__node')];
    // 优先挑**没被选中、且中心点没被别的浮层盖住**的那个
    for (const n of ns) {
      if ((n.innerText || '').includes(t) && !n.classList.contains('selected')) {
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
    }
    return { err: '找不到可点的「' + t + '」', all: ns.map((n) => {
      const r = n.getBoundingClientRect();
      return { t: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 22), sel: n.classList.contains('selected'),
        r: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }) };
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
        return { cx: Math.round(cx), cy: Math.round(cy),
          on: on.tagName + '.' + (on.className || '').toString().slice(0, 45) };
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
  await beginBatch(B, { note: '50% 拍视频面板 + 拖拽拍音频面板 + 量「节点本体压住面板顶部」' });

  const out = {};

  // ── A. 缩放到 50% 拍视频面板
  out.zoom = await setZoom('缩放至50%');
  console.log('AU10 缩放:', JSON.stringify(out.zoom));
  await page.waitForTimeout(1200);
  await shot(page, 'M-162-缩放50-全画布.png');

  out.video = { sel: await selectByText('视频节点') };
  console.log('AU10 选中视频:', JSON.stringify(out.video.sel).slice(0, 400));
  if (!out.video.sel.err) {
    out.video.geom = await geom();
    console.log('AU10 视频几何:', JSON.stringify(out.video.geom));
    if (out.video.geom.fullyVisible) {
      await shot(page, 'M-163-视频节点-面板完整.png');
      out.video.shot = 'M-163-视频节点-面板完整.png';
    } else {
      // 50% 还不够就把节点拖到中心
      out.video.drag = await dragToCenter();
      out.video.geom2 = await geom();
      console.log('AU10 视频拖后几何:', JSON.stringify(out.video.geom2));
      if (out.video.geom2.fullyVisible) {
        await shot(page, 'M-163-视频节点-面板完整.png');
        out.video.shot = 'M-163-视频节点-面板完整.png';
      }
    }
    // C. 量「节点本体压住面板顶部」：z 序 + 重叠
    out.video.overlap = await page.evaluate(() => {
      const n = document.querySelector('.react-flow__node.selected');
      if (!n) return { err: '没选中' };
      let adv = null;
      for (const e of n.querySelectorAll('*')) {
        if ((e.textContent || '').trim() !== '高级设置') continue;
        adv = e; break;
      }
      if (!adv) return { err: '没有「高级设置」' };
      const r = adv.getBoundingClientRect();
      const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
      const on = document.elementFromPoint(cx, cy);
      // 重叠面积：标题 rect ∩ 节点本体 rect
      const nr = n.getBoundingClientRect();
      const ow = Math.max(0, Math.min(r.right, nr.right) - Math.max(r.x, nr.x));
      const oh = Math.max(0, Math.min(r.bottom, nr.bottom) - Math.max(r.y, nr.y));
      return {
        advRect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        nodeRect: [Math.round(nr.x), Math.round(nr.y), Math.round(nr.width), Math.round(nr.height)],
        overlapPx: [Math.round(ow), Math.round(oh)],
        overlapRatio: +(ow * oh / (r.width * r.height)).toFixed(2),
        hitAtCenter: on ? on.tagName + '.' + (on.className || '').toString().slice(0, 50) : null,
        hitIsInsideNodeBody: !!(on && n.contains(on) && !adv.contains(on) && on !== adv),
        hitCursor: on ? getComputedStyle(on).cursor : null,
        advZ: getComputedStyle(adv).zIndex, nodeZ: getComputedStyle(n).zIndex,
      };
    });
    console.log('AU10 重叠:', JSON.stringify(out.video.overlap));
  }

  // ── B. 拖到中心拍音频面板
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1000);
  out.audio = { sel: await selectByText('音频节点') };
  console.log('AU10 选中音频:', JSON.stringify(out.audio.sel).slice(0, 400));
  if (!out.audio.sel.err) {
    out.audio.geom = await geom();
    console.log('AU10 音频几何:', JSON.stringify(out.audio.geom));
    if (!out.audio.geom.fullyVisible) {
      out.audio.drag = await dragToCenter();
      out.audio.geom2 = await geom();
      console.log('AU10 音频拖后几何:', JSON.stringify(out.audio.geom2));
    }
    const fin = out.audio.geom2 || out.audio.geom;
    if (fin.fullyVisible) {
      await shot(page, 'M-164-音频节点-面板完整.png');
      out.audio.shot = 'M-164-音频节点-面板完整.png';
    }
    // 音频的折叠区 + 滑杆，一起读
    out.audio.advanced = await page.evaluate(() => {
      const n = document.querySelector('.react-flow__node.selected');
      if (!n) return { err: '没选中' };
      const rows = [...n.querySelectorAll('[class*="grid-rows-"]')].map((e) => ({
        cls: (e.getAttribute('class') || '').slice(0, 80),
        rows: getComputedStyle(e).gridTemplateRows, h: Math.round(e.getBoundingClientRect().height) }));
      const sliders = [...n.querySelectorAll('.mantine-Slider-root,[class*="Slider"]')].map((e) => {
        const r = e.getBoundingClientRect();
        return { cls: (e.getAttribute('class') || '').slice(0, 50),
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          hiddenByClip: r.height < 1 || r.width < 1 };
      });
      const any1fr = document.querySelectorAll('[class*="grid-rows-\\[1fr\\]"]').length;
      return { rows, sliders, anyExpanded1fr: any1fr,
        fullText: (n.innerText || '').replace(/\s+/g, ' ').trim() };
    });
    console.log('AU10 音频高级:', JSON.stringify(out.audio.advanced).slice(0, 900));
  }

  await logStep(B, {
    id: 'AU10-full-panels-and-advanced', title: '50% 拍整块视频面板 + 拖拽拍整块音频面板 + 量节点本体压住面板顶部',
    target: '**「祖先链没有 button」不能证明不能点**——但「全页 `grid-rows-[1fr]` = 0」+'
      + '「折叠容器 innerH = 0」+「三个开关在容器外且 visible」+「标题那个点命中节点本体（cursor:grab）」'
      + '四条独立证据合起来说明：高级设置是点不动的静态标签，开关本来就常驻',
    evidence: out,
    visible_text: JSON.stringify(out).slice(0, 3000),
    shot: out.video.shot || 'M-162-缩放50-全画布.png',
  });
  console.log('\nAU10 完成');
} finally {
  await browser.close();
}
