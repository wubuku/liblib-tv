// ⭐⭐⭐⭐⭐ Batch FD-2：关掉那个漏网浮层，然后验证「框选后拖动 = 整组移动」
//
// FD-1 的框选失败，根因在证据图里看得一清二楚（**两条都成立**）：
//   ① ⭐⭐⭐ 画布上盖着一个 **「Agent 已升级为 TV Director」**的浮层弹窗，
//      它的关闭按钮是 `知道了` [928,709,67,32]。
//      ⭐ **`lib.mjs` 的 `closePromos` 只认 `.mantine-Modal-overlay`（Mantine 模态框）**，
//      这个浮层**不是** Mantine 模态框 ⇒ 5 轮都关不掉它，一直留在画面上。
//      ⚠️ 这也解释了 PROGRESS 里 `z-[180]`/`z-[305]`「协作功能激活后实际观感」那个 📖 ——
//      现在第一次拿到它的真实读数与截图。
//   ② ⭐⭐ 框选起点 `(20,30)` **落在顶栏里**（`未命名工作区` / `画布 2` 都在 y 8~40），
//      不在 React Flow 的 pane 上 ⇒ `mouse.down` 根本没打在画布上 ⇒ 框选不启动。
//      EZ 当年用的 `(40,355)` 才是真正的 pane 空白区。
//
// 本轮：读浮层 DOM → 自证落点后点「下次再说」关掉它 → 用 pane 空白起点框选
//      → 拖一个已选节点 → 看**其余 10 个是否跟着动、位移是否完全相同**
//      → 搬一段后**原样拖回**（基线不变）。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFD2.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;
const 读 = (id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
  const r = n.getBoundingClientRect();
  return { 画布: t ? [Number(t[1]), Number(t[2])] : null, 框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 选中: n.classList.contains('selected') };
}, id);
const 选中数 = () => page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
/** 画面上除了 .react-flow__node 之外、还盖着哪些东西（找出所有大块浮层） */
const 找浮层 = () => page.evaluate(() => {
  const out = [];
  for (const el of document.body.querySelectorAll('div')) {
    const r = el.getBoundingClientRect();
    if (r.width < 200 || r.height < 150) continue;
    const t = (el.innerText || '').replace(/\s+/g, ' ').trim();
    if (!t || t.length > 160) continue;
    if (el.querySelector('.react-flow__node')) continue;
    const z = getComputedStyle(el).zIndex;
    out.push({ 框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], z, class: (el.getAttribute('class') || '').slice(0, 70), 文字: t.slice(0, 90) });
  }
  return out;
});

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(12000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(4000);

  // ① 找出漏网浮层
  记('—— ① 画面上盖着哪些非节点浮层 ——');
  const 浮 = await 找浮层();
  for (const f of 浮) 记(`   z=${f.z} 框${JSON.stringify(f.框)} class="${f.class}" 文字「${f.文字}」`);
  R.读数.浮层 = 浮;
  await page.screenshot({ path: EVID + 'fd2-01-浮层现场.png' });

  // ② 关掉它：找「下次再说」/「知道了」这类按钮
  记('—— ② 关掉漏网浮层 ——');
  const 关掉 = await page.evaluate(() => {
    const cands = [...document.querySelectorAll('button')].filter((b) => /下次再说|知道了|稍后|关闭|Close/.test((b.innerText || '').trim() + (b.getAttribute('aria-label') || '')));
    return cands.map((b) => {
      const r = b.getBoundingClientRect();
      return { 文字: (b.innerText || '').trim() || b.getAttribute('aria-label'), aria: b.getAttribute('aria-label'), 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)], 框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
    });
  });
  记('   候选关闭按钮：' + JSON.stringify(关掉));
  R.读数.关闭按钮 = 关掉;
  const 关 = 关掉.find((b) => /下次再说|知道了|稍后/.test(b.文字 || ''));
  if (关) {
    await page.mouse.move(关.中心[0], 关.中心[1]); await page.waitForTimeout(380);
    const v = await page.evaluate((p) => {
      const e = document.elementFromPoint(p[0], p[1]);
      return e ? (e.innerText || e.getAttribute('aria-label') || e.tagName).trim().slice(0, 20) : 'null';
    }, 关.中心);
    记('   ⭐ 自证落点 = ' + JSON.stringify(v));
    if (/下次再说|知道了|稍后/.test(v)) {
      await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(1200);
      await page.mouse.move(720, 300); await page.waitForTimeout(600);
      const after = await 找浮层();
      记(`   点完之后还在的浮层 ${after.length} 个` + (after.length ? '：' + JSON.stringify(after.map((f) => f.文字.slice(0, 20))) : '　✅ 关掉了'));
      R.读数.关后浮层 = after;
    } else 记('   ⛔ 落点不对，不点');
  } else 记('   ⛔ 没找到「下次再说」这类按钮');
  await page.screenshot({ path: EVID + 'fd2-02-关掉浮层后.png' });

  // ③ 框选：起点必须落在 pane 空白（y > 60，避开所有节点框）
  记('—— ③ 框选全部 11 个 ——');
  const 框集 = [];
  for (const id of Object.keys(坐标)) { const s = await 读(id); if (s) 框集.push([id, s.框]); }
  const pane空白 = (x, y) => {
    if (y < 60 || y > 735 || x < 8 || x > 1432) return false;
    for (const [, b] of 框集) if (x >= b[0] - 4 && x <= b[0] + b[2] + 4 && y >= b[1] - 4 && y <= b[1] + b[3] + 4) return false;
    return true;
  };
  const 顶 = { x: 0, y: 0 }; 顶.x = 12;
  for (let y = 64; y < 740; y += 4) if (pane空白(顶.x, y)) { 顶.y = y; break; }
  const 底 = { x: 0, y: 0 }; 底.x = 1430;
  for (let y = 735; y > 60; y -= 4) if (pane空白(底.x, y)) { 底.y = y; break; }
  记(`   ⭐ 起点 (${顶.x},${顶.y})｜终点 (${底.x},${底.y}) —— 两点都在 pane 空白且不在任何节点框里`);
  const 命中 = await page.evaluate(([a, b, c, d]) => {
    let n = 0;
    for (const x of document.querySelectorAll('.react-flow__node')) {
      const r = x.getBoundingClientRect();
      const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
      if (cx > a && cx < c && cy > b && cy < d) n++;
    }
    return n;
  }, [顶.x, 顶.y, 底.x, 底.y]);
  记(`   框内含 ${命中} 个节点中心`);
  await page.mouse.move(顶.x, 顶.y); await page.waitForTimeout(320);
  await page.mouse.down(); await page.waitForTimeout(140);
  for (let i = 1; i <= 10; i++) {
    await page.mouse.move(Math.round(顶.x + ((底.x - 顶.x) * i) / 10), Math.round(顶.y + ((底.y - 顶.y) * i) / 10));
    await page.waitForTimeout(130);
  }
  await page.mouse.up(); await page.waitForTimeout(900);
  const n1 = await 选中数();
  记(`   ⭐⭐ 框完后 .selected = ${n1} 个`);
  R.读数.选中数 = n1;
  const 各选 = [];
  for (const id of Object.keys(坐标)) { const s = await 读(id); if (s && s.选中) 各选.push(id); }
  记('   被选中的：' + JSON.stringify(各选));
  await page.screenshot({ path: EVID + 'fd2-03-框选后.png' });
  if (!n1) { R.收尾 = '框选仍未成功'; }
  else {
    // ④ 拖一个已选节点，看整组
    记('—— ④ 拖其中一个已选节点 ——');
    let 目标 = null;
    for (const id of 各选) {
      const s = await 读(id);
      const [L, T, W, H] = s.框;
      for (const [fc, fr] of [[0.5, 0.5], [0.2, 0.2], [0.5, 0.2], [0.2, 0.5], [0.8, 0.2], [0.8, 0.5], [0.5, 0.8], [0.2, 0.8], [0.8, 0.8]]) {
        const x = L + Math.round(W * fc), y = T + Math.round(H * fr);
        if (x < 4 || x > 1436 || y < 4 || y > 700) continue;
        const ok = await page.evaluate((p) => {
          const e = document.elementFromPoint(p[0], p[1]);
          const n = e ? e.closest('.react-flow__node') : null;
          return !!(n && !e.closest('.nodrag') && n.getAttribute('data-id') === p[2]);
        }, [x, y, id]);
        if (ok) { 目标 = [id, { x, y }]; break; }
      }
      if (目标) break;
    }
    if (!目标) 记('   ⛔ 已选节点里找不到可拖落点');
    else {
      记(`   拖 ${目标[0]}，落点 ${JSON.stringify(目标[1])}，位移 +1100 屏 px`);
      const 前 = await 读全部坐标(page);
      await page.mouse.move(目标[1].x, 目标[1].y); await page.waitForTimeout(320);
      await page.mouse.down(); await page.waitForTimeout(160);
      for (let i = 1; i <= 10; i++) { await page.mouse.move(Math.round(目标[1].x + (1100 * i) / 10), 目标[1].y); await page.waitForTimeout(150); }
      await page.mouse.up(); await page.waitForTimeout(800);
      await page.mouse.move(720, 300); await page.waitForTimeout(400);
      const 后 = await 读全部坐标(page);
      const 位移 = {};
      for (const id of Object.keys(坐标)) if (前[id] && 后[id]) 位移[id] = Number((后[id][0] - 前[id][0]).toFixed(3));
      const 动了 = Object.entries(位移).filter(([, d]) => Math.abs(d) > 0.5);
      const 没动 = Object.entries(位移).filter(([, d]) => Math.abs(d) <= 0.5);
      记(`   ⭐⭐⭐ 动了 ${动了.length} 个，没动 ${没动.length} 个`);
      记('      ' + JSON.stringify(位移));
      const xs = 动了.map(([, d]) => d);
      记(`   ⭐⭐⭐⭐ 所有动过的节点位移：min ${Math.min(...xs).toFixed(3)} max ${Math.max(...xs).toFixed(3)}｜**完全一致？ ${(Math.max(...xs) - Math.min(...xs)) < 0.5}**`);
      R.读数.整组位移 = 位移;
      await page.screenshot({ path: EVID + 'fd2-04-整组拖后.png' });
      R.搬移量 = 动了.length ? xs[0] : 0;
    }
  }
} catch (e) {
  R.错误 = String((e && e.stack) || e);
  记('❌ ' + e.message);
} finally {
  // ⭐ 把整组拖回去（方向相反、同样距离），基线不变
  if (R.搬移量) {
    记('—— finally：把整组原样拖回 ——');
    const 目标量 = -R.搬移量;
    for (let 轮 = 1; 轮 <= 6; 轮++) {
      const 前 = await 读全部坐标(page);
      const 基 = Object.entries(坐标).map(([id, xy]) => ({ id, d: 全差(前[id], xy[0]) })).filter((o) => Math.abs(o.d) > 0.5);
      if (!基.length) { 记(`   ✅ 复原到位（轮 ${轮}）`); break; }
      const 一致 = Math.max(...基.map((o) => o.d)) - Math.min(...基.map((o) => o.d));
      记(`   轮${轮}：偏离的节点 ${基.length} 个，位移区间宽度 ${一致.toFixed(3)}`);
      if (一致 >= 0.5) { 记('   ⛔ 各节点位移不一致，不再自动拖（避免加深错位）'); break; }
      const s = await 读(基[0].id);
      if (!s) break;
      const [L, T, W, H] = s.框;
      let p = null;
      for (const [fc, fr] of [[0.5, 0.5], [0.2, 0.2], [0.5, 0.2], [0.2, 0.5], [0.8, 0.2], [0.8, 0.5], [0.5, 0.8], [0.2, 0.8], [0.8, 0.8]]) {
        const x = L + Math.round(W * fc), y = T + Math.round(H * fr);
        if (x < 4 || x > 1436 || y < 4 || y > 700) continue;
        const ok = await page.evaluate((q) => {
          const e = document.elementFromPoint(q[0], q[1]);
          const n = e ? e.closest('.react-flow__node') : null;
          return !!(n && !e.closest('.nodrag') && n.getAttribute('data-id') === q[2]);
        }, [x, y, 基[0].id]);
        if (ok) { p = { x, y }; break; }
      }
      if (!p) { 记('   ⛔ 找不到落点'); break; }
      const z = await page.evaluate(() => {
        const v = document.querySelector('.react-flow__viewport');
        const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(v).transform || '');
        return m ? Number(m[1].split(',')[0]) : 1;
      });
      let px = Math.round(目标量 / z);
      if (Math.abs(px) < 4) px = 目标量 > 0 ? 5 : -5;
      await page.mouse.move(p.x, p.y); await page.waitForTimeout(300);
      await page.mouse.down(); await page.waitForTimeout(150);
      for (let i = 1; i <= 10; i++) { await page.mouse.move(Math.round(p.x + (px * i) / 10), p.y); await page.waitForTimeout(150); }
      await page.mouse.up(); await page.waitForTimeout(700);
      await page.mouse.move(720, 300); await page.waitForTimeout(300);
      记(`   拖 ${px}px → ${JSON.stringify((await 读全部坐标(page))[基[0].id])}`);
    }
  }
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 全 = await 读全部坐标(page);
  const 残 = Object.entries(坐标).filter(([id, xy]) => {
    const n = 全[id]; return !n || Math.hypot(n[0] - xy[0], n[1] - xy[1]) > 0.5;
  }).map(([id, xy]) => `${id} 基线${JSON.stringify(xy)} 现${JSON.stringify(全[id] || '未渲染')}`);
  记('⭐⭐ 静置 15s 后坐标复核：' + (残.length ? JSON.stringify(残) : '[]（全部一致）'));
  R.收尾 = 残;
  await 浏览器.browser.close();
  console.log('\n=== 已写 tools/batchFD2.json ===');

  function 全差(现, 标) { return 现 ? Number((现[0] - 标).toFixed(3)) : 99999; }
}
