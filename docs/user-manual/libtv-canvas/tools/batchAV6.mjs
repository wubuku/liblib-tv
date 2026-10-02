// Batch AV6 —— 最后一张：把「图片节点 2」挪开，拍音频节点的「高级设置」展开画面。
//
// AV5 的 dump 一次性问穿了音频节点连续三轮点不中的原因（这正是 §「连续 N 次失败时先 dump 全部」的价值）：
//   音频节点 6 [599,308,148,148]  中心命中 → **图片节点 2**，自己命中不了
//   音频节点 1 [624,328,148,148]  中心命中 → **图片节点 2**，自己命中不了
//   图片节点 2 [604,339,263,148]  ← **它把两个音频节点整个压在下面**
//
// 算一下就知道为什么「怎么点都点不中」：
//   音频节点 1 的 x 范围 624..772 **完全落在**图片节点 2 的 604..867 之内 → 可见区 0 像素；
//   音频节点 6 的 x 范围 599..747，只有 599..604 这 **5 像素**露在外面。
//
// 于是本轮的顺序是：**先拖走图片节点 2 → 音频节点露出来 → 拖到上方 → 选中 → 点 ⚙ → 拍**。
//
// 视频那张已经拍到了（`M-142`，面板 `[391,307,658,411]` 整块在屏内），
// 并且画面上读出一条正文没记的细节：**「自动校验素材」和「智能引用 AutoLink」各带一个
// `?` 问号图标（带说明），而「联网搜索」没有**。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAV6';
const { browser, page } = await launch();

const allNodes = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
  const on = document.elementFromPoint(cx, cy);
  return { text: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20),
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    selfHit: !!(on && n.contains(on)) };
}));

const panelRect = () => page.evaluate(() => {
  const n = document.querySelector('.react-flow__node.selected');
  if (!n) return { err: '没有选中节点' };
  const c = [...n.querySelectorAll('div')].map((e) => ({ e, r: e.getBoundingClientRect() }))
    .filter((o) => o.r.width > 400 && o.r.height > 100)
    .filter((o) => (o.e.innerText || '').includes('参考'))
    .sort((a, b) => (a.r.width * a.r.height) - (b.r.width * b.r.height))[0];
  if (!c) return { err: '没找到面板' };
  return { rect: [Math.round(c.r.x), Math.round(c.r.y), Math.round(c.r.width), Math.round(c.r.height)],
    bottom: Math.round(c.r.bottom), fullyVisible: c.r.x >= 0 && c.r.y >= 0 && c.r.right <= 1440 && c.r.bottom <= 810 };
});

const gearRect = () => page.evaluate(() => {
  const n = document.querySelector('.react-flow__node.selected');
  if (!n) return null;
  const p = [...n.querySelectorAll('div')].map((e) => ({ e, r: e.getBoundingClientRect() }))
    .filter((o) => o.r.width > 400 && o.r.height > 100)
    .filter((o) => (o.e.innerText || '').includes('参考'))
    .sort((a, b) => (a.r.width * a.r.height) - (b.r.width * b.r.height))[0]?.e;
  if (!p) return null;
  const g = [...p.querySelectorAll('button')].find((e) => {
    const s = e.querySelector('svg'); if (!s) return false;
    return [...s.querySelectorAll('path')].map((x) => x.getAttribute('d') || '').some((d) => d.startsWith('M14 17H5')); });
  if (!g) return null;
  const q = g.getBoundingClientRect();
  return { rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
    inView: q.x >= 0 && q.y >= 0 && q.right <= 1440 && q.bottom <= 810 };
});

async function deselect() {
  await page.keyboard.press('Escape'); await page.waitForTimeout(900);
  await page.mouse.click(80, 120); await page.waitForTimeout(1600);
}

/** 拖一个「中心点能命中自己」的节点到 (toX, toY)。 */
async function dragNode(textExact, toX, toY) {
  const g = await page.evaluate((t) => {
    for (const n of document.querySelectorAll('.react-flow__node')) {
      if (!(n.innerText || '').includes(t)) continue;
      const r = n.getBoundingClientRect();
      for (const [fx, fy] of [[0.5, 0.5], [0.35, 0.5], [0.65, 0.5], [0.5, 0.3], [0.5, 0.7]]) {
        const cx = r.x + r.width * fx, cy = r.y + r.height * fy;
        const on = document.elementFromPoint(cx, cy);
        if (on && n.contains(on) && !on.closest('[class*="Popover"],[class*="Menu"],[class*="Dropdown"]')) {
          return { cx: Math.round(cx), cy: Math.round(cy), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
        }
      }
      return { err: '「' + t + '」中心点被挡', rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
    }
    return { err: '找不到「' + t + '」' };
  }, textExact);
  if (g.err) return g;
  const dx = Math.round(toX - (g.rect[0] + g.rect[2] / 2));
  const dy = Math.round(toY - (g.rect[1] + g.rect[3] / 2));
  await page.mouse.move(g.cx, g.cy); await page.mouse.down();
  for (let i = 1; i <= 12; i += 1) { await page.mouse.move(g.cx + (dx * i) / 12, g.cy + (dy * i) / 12); await page.waitForTimeout(70); }
  await page.mouse.up(); await page.waitForTimeout(2000);
  return { grabbed: g, dx, dy };
}

/** 点「离目标最近的同类节点」—— 不按 innerText 取第一个（视口里有两个同类节点）。 */
async function selectNearest(textPart, wantY) {
  const p = await page.evaluate(([t, wy]) => {
    const c = [...document.querySelectorAll('.react-flow__node')]
      .filter((n) => (n.innerText || '').includes(t) && !n.classList.contains('selected'))
      .map((n) => { const r = n.getBoundingClientRect();
        const ccx = r.x + r.width / 2, ccy = r.y + r.height / 2;
        const o = (ccx >= 0 && ccy >= 0 && ccx < innerWidth && ccy < innerHeight)
          ? document.elementFromPoint(ccx, ccy) : null;
        return { n, r, d: Math.abs(r.y - wy), selfHit: !!(o && n.contains(o)) }; })
      // **先按 selfHit 排，再按 y 接近度排** —— AV6 选了个离目标近但被别的节点压住的
      .sort((a, b) => (b.selfHit - a.selfHit) || (a.d - b.d));
    if (!c.length) return { err: '没有未选中的「' + t + '」' };
    const { n, r } = c[0];
    for (const [fx, fy] of [[0.5, 0.5], [0.5, 0.4], [0.35, 0.5], [0.65, 0.5], [0.5, 0.3], [0.5, 0.7]]) {
      const cx = r.x + r.width * fx, cy = r.y + r.height * fy;
      const on = document.elementFromPoint(cx, cy);
      if (on && n.contains(on) && !on.closest('[class*="Popover"],[class*="Menu"],[class*="Dropdown"]')) {
        return { cx: Math.round(cx), cy: Math.round(cy),
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          text: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24) };
      }
    }
    return { err: '「' + t + '」可点区全被挡住', rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  }, [textPart, wantY]);
  if (p.err) return p;
  await page.mouse.click(p.cx, p.cy);
  await page.waitForTimeout(4200);
  return p;
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(2200);
  await beginBatch(B, { note: '先拖走压在音频节点上的图片节点 2，再拍音频的「高级设置」展开画面' });

  const out = {};
  await deselect();
  out.before = await allNodes();
  console.log('AV6 拖之前:', JSON.stringify(out.before.filter((n) => /图片节点 2|音频节点/.test(n.text))));

  // ① 把图片节点 2 拖到左下角空位
  out.moveImage = await dragNode('图片节点 2', 200, 700);
  console.log('AV6 挪图片节点 2:', JSON.stringify(out.moveImage).slice(0, 260));
  await deselect();
  out.afterMove = await allNodes();
  console.log('AV6 挪之后:');
  for (const n of out.afterMove.filter((x) => /图片节点 2|音频节点/.test(x.text))) {
    console.log(`  ${String(n.rect).padEnd(22)} selfHit=${n.selfHit ? 'Y' : 'N'} ${n.text}`);
  }

  // ② 音频节点拖到上方
  out.moveAudio = await dragNode('音频节点 1', 500, 170);
  if (out.moveAudio.err) out.moveAudio2 = await dragNode('音频节点 6', 500, 170);
  console.log('AV6 挪音频:', JSON.stringify(out.moveAudio).slice(0, 200), JSON.stringify(out.moveAudio2 || '').slice(0, 200));
  await deselect();

  // ③ 选中最近的音频节点 → 点 ⚙ → 拍
  out.sel = await selectNearest('音频节点', 170);
  console.log('AV6 选中音频:', JSON.stringify(out.sel).slice(0, 260));
  if (!out.sel.err) {
    out.panelCollapsed = await panelRect();
    out.gear = await gearRect();
    console.log('AV6 折叠面板:', JSON.stringify(out.panelCollapsed.rect), 'gear:', JSON.stringify(out.gear));
    if (out.gear && out.gear.inView) {
      const g = out.gear.rect;
      await page.mouse.click(g[0] + g[2] / 2, g[1] + g[3] / 2);
      await page.waitForTimeout(3000);
      out.panelExpanded = await panelRect();
      console.log('AV6 展开面板:', JSON.stringify(out.panelExpanded.rect), '完整?', out.panelExpanded.fullyVisible);
      out.sliders = await page.evaluate(() => {
        const n = document.querySelector('.react-flow__node.selected');
        if (!n) return { err: '没选中' };
        return [...n.querySelectorAll('.mantine-Slider-root')].map((e) => {
          const q = e.getBoundingClientRect();
          return { rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
            now: e.querySelector('[aria-valuenow]')?.getAttribute('aria-valuenow') || null,
            max: e.querySelector('[aria-valuemax]')?.getAttribute('aria-valuemax') || null };
        });
      });
      console.log('AV6 三个滑杆:', JSON.stringify(out.sliders));
      if (out.panelExpanded.fullyVisible) {
        await shot(page, 'M-143-音频节点-高级设置展开.png');
        out.shot = 'M-143-音频节点-高级设置展开.png';
      }
    }
  }

  await logStep(B, {
    id: 'AV6-audio-advanced-shot', title: '挪开图片节点 2，拍到音频节点「高级设置」展开后的三个滑杆',
    target: '音频节点连三轮点不中，dump 出来的原因是**图片节点 2 [604,339,263×148] 把两个音频节点'
      + '整个压在下面**（音频节点 1 的可见区 0 像素、音频节点 6 只有 5 像素）。先挪走它才拍得到',
    evidence: out,
    visible_text: JSON.stringify({ move: out.moveImage, sel: out.sel, panel: out.panelExpanded, sliders: out.sliders }).slice(0, 2500),
    shot: 'M-143-音频节点-高级设置展开.png',
  });
  console.log('\nAV6 完成');
} finally {
  await browser.close();
}
