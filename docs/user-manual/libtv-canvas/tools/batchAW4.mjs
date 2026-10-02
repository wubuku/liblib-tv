// Batch AW4 —— 补最后两件事：**「运镜」点开是什么**，以及**「角色库」本体长什么样**。
//
// AW3 已经问出来四枚（详见 PROGRESS §24），剩两件没做完：
//   ① 「运镜」没点到 —— 点完「角色库」之后 Esc 收场，**节点选中态丢了**，
//      下一轮的 `panelState()` 直接返回「没有选中节点」。
//      修法：**每一枚都从同一套起点重来**（取消选中 → 拖到上部 → 用坐标点它），
//      而不是「点一枚、收场、再点下一枚」—— 收场本身会破坏起点。
//   ② 「角色库」弹出来的是**承诺书叠在角色库之上**（z=801 > 角色库本体），
//      所以上一轮只拍到了承诺书，没拍到角色库本身。
//      这一轮点开之后**先关掉承诺书**（点它自己的 `×`，不点「同意并使用」——
//      那是签署法律协议，不碰；复选框也不勾），再拍角色库本体。
//
// ⚠️ 两层都是 `mantine-Modal-inner`，靠**面积**区分：承诺书比角色库小一圈。
//    这个区分是必要的，否则差集里最大的那个到底是哪层会分不清。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAW4';
const { browser, page } = await launch();

const snap = () => page.evaluate(() => {
  const out = [];
  for (const e of document.querySelectorAll('body *')) {
    const cs = getComputedStyle(e);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) continue;
    if (cs.position !== 'fixed' && cs.position !== 'absolute' && cs.position !== 'sticky') continue;
    const r = e.getBoundingClientRect();
    if (r.width < 8 || r.height < 8) continue;
    if (r.bottom < 0 || r.right < 0 || r.y > 810 || r.x > 1440) continue;
    const txt = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (!txt) continue;
    out.push({ cls: (e.className || '').toString().slice(0, 55), z: cs.zIndex,
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], text: txt.slice(0, 500) });
  }
  const seen = new Set();
  return out.filter((o) => { const k = o.cls + '|' + o.rect.join(','); if (seen.has(k)) return false; seen.add(k); return true; });
});

const panelState = () => page.evaluate(() => {
  const n = document.querySelector('.react-flow__node.selected');
  if (!n) return { err: '没有选中节点' };
  const c = [...n.querySelectorAll('div')].map((e) => ({ e, r: e.getBoundingClientRect() }))
    .filter((o) => o.r.width > 400 && o.r.height > 100)
    .filter((o) => (o.e.innerText || '').includes('参考'))
    .sort((a, b) => (a.r.width * a.r.height) - (b.r.width * b.r.height))[0];
  if (!c) return { err: '没找到面板' };
  return { panelRect: [Math.round(c.r.x), Math.round(c.r.y), Math.round(c.r.width), Math.round(c.r.height)],
    btns: [...c.e.querySelectorAll('button,[role="button"]')].map((e) => {
      const q = e.getBoundingClientRect();
      return { text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 10), rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] };
    }).filter((b) => b.rect[2] > 0) };
});

async function freshSelectVideo() {
  await page.keyboard.press('Escape'); await page.waitForTimeout(800);
  await page.mouse.click(80, 120); await page.waitForTimeout(1400);
  const g = await page.evaluate(() => {
    for (const n of document.querySelectorAll('.react-flow__node')) {
      if (!(n.innerText || '').includes('视频节点')) continue;
      const r = n.getBoundingClientRect();
      if (r.x < 5 || r.x + r.width > 1435 || r.y < 60 || r.y + r.height > 800) continue;
      for (const [fx, fy] of [[0.5, 0.5], [0.35, 0.5], [0.65, 0.5], [0.5, 0.3], [0.5, 0.7]]) {
        const cx = r.x + r.width * fx, cy = r.y + r.height * fy;
        const on = document.elementFromPoint(cx, cy);
        if (on && n.contains(on) && !on.closest('[class*="Popover"],[class*="Menu"],[class*="Dropdown"]')) {
          return { cx: Math.round(cx), cy: Math.round(cy), y: Math.round(r.y) };
        }
      }
    }
    return { err: '找不到可拖的视频节点' };
  });
  if (g.err) return g;
  // 拖到 y=150
  const dy = Math.round(150 - g.y);
  if (Math.abs(dy) > 4) {
    await page.mouse.move(g.cx, g.cy); await page.mouse.down();
    for (let i = 1; i <= 12; i += 1) { await page.mouse.move(g.cx, g.cy + (dy * i) / 12); await page.waitForTimeout(70); }
    await page.mouse.up(); await page.waitForTimeout(2000);
  }
  const g2 = await page.evaluate(() => {
    for (const n of document.querySelectorAll('.react-flow__node')) {
      if (!(n.innerText || '').includes('视频节点')) continue;
      const r = n.getBoundingClientRect();
      if (r.x < 5 || r.x + r.width > 1435 || r.y < 60 || r.y + r.height > 800) continue;
      return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
    }
    return null;
  });
  if (!g2) return { err: '拖完找不到了' };
  await page.mouse.click(g2.cx, g2.cy);
  await page.waitForTimeout(4200);
  return { ...g2, selected: await page.evaluate(() => !!document.querySelector('.react-flow__node.selected')) };
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(2200);
  await beginBatch(B, { note: '补「运镜」+ 关掉承诺书后拍角色库本体（不点同意并使用）' });

  const out = {};

  // ── ① 运镜
  console.log('--- AW4 运镜 ---');
  out.yunjing = { start: await freshSelectVideo() };
  const st = await panelState();
  out.yunjing.panel = st.panelRect || st.err;
  const yb = st.btns && st.btns.find((b) => b.text === '运镜');
  out.yunjing.target = yb || null;
  if (yb) {
    const before = await snap();
    const cx = yb.rect[0] + yb.rect[2] / 2, cy = yb.rect[1] + yb.rect[3] / 2;
    await page.mouse.click(cx, cy);
    await page.waitForTimeout(3200);
    await clearToasts(page);
    const after = await snap();
    const bs = new Set(before.map((o) => o.cls + '|' + o.rect.join(',')));
    out.yunjing.added = after.filter((o) => !bs.has(o.cls + '|' + o.rect.join(',')))
      .sort((a, b) => (b.rect[2] * b.rect[3]) - (a.rect[2] * a.rect[3]));
    out.yunjing.nAdded = out.yunjing.added.length;
    console.log('运镜 新增', out.yunjing.nAdded, '个:');
    for (const a of out.yunjing.added.slice(0, 6)) {
      console.log(`  + [${String(a.rect).padEnd(22)}] z=${a.z} ${a.cls}`);
      console.log('     ', a.text.slice(0, 240));
    }
    if (out.yunjing.nAdded) { await shot(page, 'M-156-工具条-运镜.png'); out.yunjing.shot = 'M-156-工具条-运镜.png'; }
    await page.keyboard.press('Escape'); await page.waitForTimeout(1600);
  } else {
    out.yunjing.err = '面板里没有「运镜」';
  }

  // ── ② 角色库本体：点开 → 关掉承诺书 → 拍
  console.log('\n--- AW4 角色库本体 ---');
  out.roles = { start: await freshSelectVideo() };
  const st2 = await panelState();
  const rb = st2.btns && st2.btns.find((b) => b.text === '角色库');
  if (rb) {
    await page.mouse.click(rb.rect[0] + rb.rect[2] / 2, rb.rect[1] + rb.rect[3] / 2);
    await page.waitForTimeout(3400);
    await clearToasts(page);
    // 两层都是 mantine-Modal-inner，按面积分：小的 = 承诺书
    const layers = await page.evaluate(() => [...document.querySelectorAll('.mantine-Modal-inner')].map((e) => {
      const r = e.getBoundingClientRect();
      return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        z: getComputedStyle(e).zIndex, area: Math.round(r.width * r.height),
        text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300),
        head: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24) };
    }).filter((x) => x.area > 1000).sort((a, b) => b.area - a.area));
    out.roles.layers = layers;
    console.log('角色库 弹出的层（按面积大→小）:');
    for (const l of layers) console.log(`  [${String(l.rect).padEnd(22)}] z=${l.z} area=${l.area} 「${l.head}」`);
    // 找到承诺书（正文含「承诺书」），点它自己的 × 关掉
    const pledge = layers.find((l) => l.text.includes('承诺书'));
    if (pledge) {
      out.roles.pledge = pledge;
      const closed = await page.evaluate(() => {
        const m = [...document.querySelectorAll('.mantine-Modal-inner')].find((e) => (e.innerText || '').includes('承诺书'));
        if (!m) return { err: '没找到承诺书那层' };
        const xs = [...m.querySelectorAll('button,[aria-label],[role="button"]')].filter((b) => {
          const r = b.getBoundingClientRect();
          if (r.width < 10 || r.height < 10) return false;
          const t = (b.getAttribute('aria-label') || b.innerText || '').trim();
          return /^[×✕xX]$/.test(t) || /关闭|close/i.test(b.getAttribute('aria-label') || '');
        });
        if (!xs.length) return { err: '承诺书里没找到 ×', all: [...m.querySelectorAll('button')].map((b) => (b.getAttribute('aria-label') || b.innerText || '').trim().slice(0, 8)) };
        const r = xs[0].getBoundingClientRect();
        return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
      });
      out.roles.closePledge = closed;
      if (!closed.err) {
        await page.mouse.click(closed.cx, closed.cy);
        await page.waitForTimeout(2400);
        await clearToasts(page);
        out.roles.afterClose = await page.evaluate(() => [...document.querySelectorAll('.mantine-Modal-inner')].map((e) => {
          const r = e.getBoundingClientRect();
          return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
            z: getComputedStyle(e).zIndex,
            text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400) };
        }).filter((x) => x.rect[2] > 200));
        console.log('关掉承诺书之后剩下的层:', JSON.stringify(out.roles.afterClose).slice(0, 600));
        await shot(page, 'M-157-角色库-本体.png');
        out.roles.shot = 'M-157-角色库-本体.png';
      }
    }
  } else {
    out.roles.err = '面板里没有「角色库」';
  }

  await logStep(B, {
    id: 'AW4-yunjing-and-role-library', title: '补「运镜」+ 角色库本体（关掉合规承诺书之后那层）',
    target: '**每一枚都从同一起点重来**（取消选中 → 拖到上部 → 坐标点它）——'
      + 'AW3 那种「点一枚、Esc 收场、再点下一枚」的写法，收场本身会弄丢选中态；'
      + '承诺书按**面积**和角色库本体区分（都是 mantine-Modal-inner），**不点「同意并使用」**',
    evidence: out,
    visible_text: JSON.stringify(out).slice(0, 3000),
    shot: out.roles.shot || out.yunjing.shot || 'M-139-视频节点-参数面板.png',
  });
  console.log('\nAW4 完成');
} finally {
  await browser.close();
}
