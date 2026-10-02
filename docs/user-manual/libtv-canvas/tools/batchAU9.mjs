// Batch AU9 —— 定两件事：**`grid-rows-[0fr]` 能不能变成 `1fr`**，以及拍到完整面板。
//
// AU8 零点击 dump 出来的读数是决定性的：
//   视频/图片节点里唯一的折叠容器 class = `grid transition-[grid-template-rows] ease-in-out
//   grid-rows-[0fr] duration-200`，`grid-template-rows` **计算值 = 0px**，h=0，visible=false。
//   而 `联网搜索` / `自动校验素材` / `智能引用` 三个 Switch 在 y=699/739/779 ——
//   **在折叠容器（y=658, h=0）外面，一直 visible**。
//   「高级设置」标题的**可点击祖先链 = null**（一路到 .react-flow__node 没有 button/role/aria）。
//
// 但「祖先链里没有 button」**不能证明不能点** —— React 的 onClick 挂在普通 div 上完全合法。
// 所以这轮**实点**。点之前先验坐标确实落在那个 div 上（elementFromPoint），
// 免得又一次把「点偏了」记成「点不动」。
//
// 另有一件事决定截图怎么拍：
//   AU7 把视频节点拖到中心后，面板 [395,243,660,573] → 下边 243+573=816，**只超视口 6px**，
//   但网格吸附让「正好上移 6px」做不到（要 -6 实际只走 -63，且 x 被吃掉 5px）。
//   → 改用**缩放到 0.5**：面板变成 330×286，整块稳稳进屏。缩放 0.5 是 AP 批次实按验证过的档位。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAU9';
const { browser, page } = await launch();

/** 全页找 `grid-rows-[1fr]` —— 如果一个都没有，「展开态」在这个产品里可能根本不存在。 */
const anyExpanded = () => page.evaluate(() => {
  const all = [...document.querySelectorAll('*')].filter((e) => /grid-rows-\[1fr\]/.test(e.getAttribute('class') || ''));
  return { count: all.length,
    samples: all.slice(0, 5).map((e) => { const r = e.getBoundingClientRect();
      return { cls: (e.getAttribute('class') || '').slice(0, 80), h: Math.round(r.height) }; }) };
});

/** 选中节点里所有 grid 折叠容器的计算值 + 「高级设置」标题位置。 */
const readCollapsible = (label) => page.evaluate((t) => {
  const n = document.querySelector('.react-flow__node.selected');
  if (!n) return { err: '没有选中节点' };
  const rows = [...n.querySelectorAll('[class*="grid-rows-"]')].map((e) => {
    const r = e.getBoundingClientRect();
    return { cls: (e.getAttribute('class') || '').slice(0, 90),
      rowsComputed: getComputedStyle(e).gridTemplateRows, h: Math.round(r.height), w: Math.round(r.width),
      y: Math.round(r.y), innerH: e.firstElementChild ? e.firstElementChild.clientHeight : null };
  });
  let adv = null;
  for (const e of n.querySelectorAll('*')) {
    if ((e.textContent || '').trim() !== '高级设置') continue;
    const r = e.getBoundingClientRect();
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    const on = document.elementFromPoint(cx, cy);
    adv = { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      cx: Math.round(cx), cy: Math.round(cy),
      onTarget: !!(on && (e === on || e.contains(on) || on.contains(e))),
      on: on ? on.tagName + '.' + (on.className || '').toString().slice(0, 60) : null,
      cursor: getComputedStyle(e).cursor, pointerEvents: getComputedStyle(e).pointerEvents };
    break;
  }
  // 折叠容器外面、但紧邻着的开关们（证明它们常驻）
  const switches = [...n.querySelectorAll('.mantine-Switch-root,[class*="Switch-track"]')].map((e) => {
    const r = e.getBoundingClientRect();
    return { label: (e.closest('label') || e.parentElement)?.textContent?.trim().slice(0, 12) || '',
      y: Math.round(r.y), h: Math.round(r.height), visible: r.height > 2 && r.y > 0 && r.y < 810 };
  });
  return { nodeTitle: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40), label: t, rows, adv, switches };
}, label);

async function selectNode(idx) {
  const plan = await page.evaluate((i) => {
    const ns = [...document.querySelectorAll('.react-flow__node')].filter((x) => !x.classList.contains('selected'));
    const n = ns[i];
    if (!n) return { err: '视口里没有第 ' + i + ' 个未选中节点' };
    const r = n.getBoundingClientRect();
    for (const [fx, fy] of [[0.5, 0.4], [0.5, 0.5], [0.35, 0.5], [0.65, 0.5], [0.5, 0.25]]) {
      const cx = r.x + r.width * fx, cy = r.y + r.height * fy;
      if (cx < 5 || cx > 1435 || cy < 60 || cy > 780) continue;
      const on = document.elementFromPoint(cx, cy);
      if (on && n.contains(on) && !on.closest('[class*="Popover"],[class*="Menu"],[class*="Dropdown"]')) {
        return { cx: Math.round(cx), cy: Math.round(cy),
          title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30) };
      }
    }
    return { err: '节点内部没有可点的点', title: (n.innerText || '').slice(0, 30) };
  }, idx);
  if (plan.err) return plan;
  await page.mouse.click(plan.cx, plan.cy);
  await page.waitForTimeout(3600);
  return plan;
}

/** 底栏缩放选项 → 0.5 档（AP 批次实按验证过）。 */
async function zoomHalf() {
  const before = await page.evaluate(() => {
    const m = document.querySelector('.react-flow__viewport');
    return m ? getComputedStyle(m).transform : null;
  });
  const btn = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button,[role="button"]')].find((x) =>
      /缩放/.test(x.getAttribute('aria-label') || x.getAttribute('title') || ''));
    if (!b) return { err: '没找到缩放按钮' };
    const r = b.getBoundingClientRect();
    return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
  });
  if (btn.err) return btn;
  await page.mouse.click(btn.cx, btn.cy);
  await page.waitForTimeout(700);
  const preset = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button,[role="menuitem"],[role="button"]')]
      .find((x) => (x.innerText || '').trim() === '50%');
    if (!b) {
      const cands = [...document.querySelectorAll('button,[role="menuitem"],[role="button"]')]
        .map((x) => (x.innerText || '').trim()).filter(Boolean);
      return { err: '菜单里没有 50%', cands: cands.slice(0, 20) };
    }
    const r = b.getBoundingClientRect();
    return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
  });
  if (preset.err) return preset;
  await page.mouse.click(preset.cx, preset.cy);
  await page.waitForTimeout(2600);
  const after = await page.evaluate(() => {
    const m = document.querySelector('.react-flow__viewport');
    return m ? getComputedStyle(m).transform : null;
  });
  return { before, after, changed: before !== after };
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(800);
  await beginBatch(B, { note: '实点「高级设置」看 0fr 变不变 + 缩放 0.5 拍完整面板' });

  const out = {};

  // ── Q1：全页有没有 grid-rows-[1fr]（= 展开态在这个产品里存不存在）
  out.anyExpanded_atStart = await anyExpanded();
  console.log('AU9 全页 grid-rows-[1fr] 数量:', out.anyExpanded_atStart.count,
    JSON.stringify(out.anyExpanded_atStart.samples));

  // ── Q2：选视频节点，实点「高级设置」三下，看 0fr 变不变
  out.video = { sel: await selectNode(4) };
  console.log('AU9 选中:', JSON.stringify(out.video.sel));
  if (!out.video.sel.err) {
    out.video.base = await readCollapsible('视频');
    console.log('AU9 视频 基线 rows:', JSON.stringify(out.video.base.rows.map((r) => [r.rowsComputed, r.h])));
    console.log('AU9 视频 高级设置:', JSON.stringify(out.video.base.adv));
    console.log('AU9 视频 常驻开关:', JSON.stringify(out.video.base.switches));

    const a = out.video.base.adv;
    if (a && a.onTarget) {
      out.video.click1 = { at: [a.cx, a.cy] };
      await page.mouse.click(a.cx, a.cy);
      await page.waitForTimeout(900);
      out.video.afterClick1 = await readCollapsible('视频');
      console.log('AU9 点第1下 rows:', JSON.stringify(out.video.afterClick1.rows.map((r) => [r.rowsComputed, r.h])));

      const a1 = out.video.afterClick1.adv;
      if (a1) {
        await page.mouse.click(a1.cx, a1.cy);
        await page.waitForTimeout(900);
        out.video.afterClick2 = await readCollapsible('视频');
        console.log('AU9 点第2下 rows:', JSON.stringify(out.video.afterClick2.rows.map((r) => [r.rowsComputed, r.h])));
      }
      // 面板还在不在？点了会不会把它关掉？
      out.video.stillSelected = await page.evaluate(() =>
        !!document.querySelector('.react-flow__node.selected'));
    } else {
      out.video.click1 = { skipped: '点上不是目标元素', got: a && a.on };
    }
  }

  // ── Q3：换音频节点（先关掉视频面板）
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1000);
  out.audio = { sel: await selectNode(0) };
  console.log('AU9 音频 选中:', JSON.stringify(out.audio.sel));
  if (!out.audio.sel.err) {
    out.audio.base = await readCollapsible('音频');
    console.log('AU9 音频 基线 rows:', JSON.stringify(out.audio.base.rows.map((r) => [r.rowsComputed, r.h])));
    console.log('AU9 音频 高级设置:', JSON.stringify(out.audio.base.adv));
    console.log('AU9 音频 开关:', JSON.stringify(out.audio.base.switches));
    const a2 = out.audio.base.adv;
    if (a2 && a2.onTarget) {
      await page.mouse.click(a2.cx, a2.cy);
      await page.waitForTimeout(900);
      out.audio.afterClick1 = await readCollapsible('音频');
      console.log('AU9 音频 点第1下 rows:', JSON.stringify(out.audio.afterClick1.rows.map((r) => [r.rowsComputed, r.h])));
    }
  }

  out.anyExpanded_afterAllClicks = await anyExpanded();
  console.log('AU9 点完之后全页 grid-rows-[1fr] 数量:', out.anyExpanded_afterAllClicks.count);

  // ── Q4：缩放到 0.5，拍完整面板（这时节点小，面板也小，整块进屏）
  out.zoom = await zoomHalf();
  console.log('AU9 缩放 0.5:', JSON.stringify(out.zoom));
  await page.waitForTimeout(1200);
  out.collapsed = await page.evaluate(() => {
    const n = [...document.querySelectorAll('.react-flow__node')].map((x) => {
      const r = x.getBoundingClientRect();
      return { t: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 18),
        r: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
    });
    return n;
  });
  await shot(page, 'M-160-缩放50-全画布.png');

  // 50% 下重新选视频节点 → 面板整块应在屏内
  out.videoAtHalf = { sel: await selectNode(0) };
  console.log('AU9 50% 选中:', JSON.stringify(out.videoAtHalf.sel));
  if (!out.videoAtHalf.sel.err) {
    out.videoAtHalf.geom = await page.evaluate(() => {
      const n = document.querySelector('.react-flow__node.selected');
      if (!n) return { err: '没选中' };
      const nr = n.getBoundingClientRect();
      let x0 = nr.x, y0 = nr.y, x1 = nr.right, y1 = nr.bottom;
      for (const e of n.querySelectorAll('*')) {
        const q = e.getBoundingClientRect();
        if (q.width < 1 || q.height < 1) continue;
        x0 = Math.min(x0, q.x); y0 = Math.min(y0, q.y);
        x1 = Math.max(x1, q.right); y1 = Math.max(y1, q.bottom);
      }
      return { nodeRect: [Math.round(nr.x), Math.round(nr.y), Math.round(nr.width), Math.round(nr.height)],
        panelUnion: [Math.round(x0), Math.round(y0), Math.round(x1 - x0), Math.round(y1 - y0)],
        fullyVisible: x0 >= 0 && y0 >= 0 && x1 <= 1440 && y1 <= 810 };
    });
    console.log('AU9 50% 视频几何:', JSON.stringify(out.videoAtHalf.geom));
    if (out.videoAtHalf.geom.fullyVisible) {
      await shot(page, 'M-161-视频节点-面板完整.png');
      out.videoAtHalf.shot = 'M-161-视频节点-面板完整.png';
    }
  }

  await logStep(B, {
    id: 'AU9-click-advanced-zoom-half', title: '实点「高级设置」验证 0fr 能否变 1fr + 缩放 50% 拍完整面板',
    target: '**「祖先链里没有 button」不能证明不能点**（React onClick 可以挂在普通 div 上）—— 所以实点，'
      + '点之前先验 elementFromPoint 落在目标上；同时用缩放 50% 绕开网格吸附拍到整块面板',
    evidence: out,
    visible_text: JSON.stringify(out).slice(0, 3000),
    shot: 'M-161-视频节点-面板完整.png',
  });
  console.log('\nAU9 完成');
} finally {
  await browser.close();
}
