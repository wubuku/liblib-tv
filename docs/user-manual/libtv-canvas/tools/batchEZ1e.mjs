// Batch EZ-1e（EZ-1d 的修正版）：⭐⭐⭐ 挪开视频节点 → 选中 2 个纯图片节点 → 读 `合并分镜组` → 原样挪回去
//
// 前三轮把「阳性对照取不到」的原因查实了：
//   · EZ-1  三铁律之二当场抓到：图 A 的中心落在**视频节点**身上
//   · EZ-1b 6px 网格扫 1296 格：**1250 格归视频节点**，只剩 46 格（x∈[352,358] 一条缝），
//          而那条缝的质心自证回来的仍是视频节点的一个 `<circle>`
//   · EZ-1c `Tab` **走得到**图 A（Tab#13 焦点就是它），**但选中集全程为 `[]`**
//          —— 键盘导航只给焦点不给选区
//   ⇒ **图 A 既点不到、也框不到、也 Tab 不中**。手册当年写的
//      「框选会把它一起圈进来」不够狠，真正原因是**这个节点没法用鼠标选出来**。
//
// 剩下唯一一条路：**把视频节点挪开**。本轮严格执行画布坐标驱动的复原：
//   ① 从 DOM 的 `transform: translate()` 直接读画布坐标（不靠拖拽反推）
//   ② 拖 = 画布位移 × zoom（铁律一）
//   ③ 复原**循环到误差 < 0.5 画布单位**，不是「拖回去就行」
//   ④ 收尾静置 15s 后 `核对坐标` 必须 `[]`
//
// ⛔ 全程不点任何卡片本体、不触发生成。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEZ1e.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 图A = 'i-9nlG6HdjK2';
const 图B = 'i-sODTbgLUm1';
const 遮挡 = 'v-eMpqKtiLlx';

const 浏览器 = await launch();
const page = 浏览器.page;

/** 每个节点的画布坐标（来自 React Flow 写在 style 上的 translate）+ 屏上框 */
const 快照 = () => page.evaluate(() => {
  const 变换 = [...document.querySelectorAll('.react-flow__viewport')].map((v) => getComputedStyle(v).transform)[0];
  const 节 = (t) => {
    const m = /matrix\(([^)]+)\)/.exec(t || '');
    if (!m) return null;
    const p = m[1].split(',').map(Number);
    return { zoom: p[0], tx: p[4], ty: p[5] };
  };
  return {
    变换, 视口: 节(变换),
    节点: [...document.querySelectorAll('.react-flow__node')].map((n) => {
      const r = n.getBoundingClientRect();
      const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
      return {
        id: n.getAttribute('data-id'),
        画布: m ? [Number(m[1]), Number(m[2])] : null,
        屏: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)],
        选中: n.classList.contains('selected'),
      };
    }),
  };
});

const 落点 = (p) => page.evaluate(([x, y]) => {
  const e = document.elementFromPoint(x, y);
  if (!e) return { id: null, tag: null };
  const n = e.closest('.react-flow__node');
  return { id: n ? n.getAttribute('data-id') : null, tag: e.tagName };
}, p);

const 选中集 = async (标签) => {
  const s = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map((n) => n.getAttribute('data-id')));
  记(`  【${标签}】选中 ${s.length} 个：${JSON.stringify(s)}`);
  return s;
};

const 下拉读数 = () => page.evaluate(() => {
  const 出 = [];
  for (const e of document.querySelectorAll('div,span,li,button')) {
    if (e.children.length) continue;
    const t = (e.innerText || '').trim();
    if (t !== '打组' && t !== '合并分镜组') continue;
    const r = e.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) continue;
    let 层 = e, op = getComputedStyle(e).opacity, cur = getComputedStyle(e).cursor;
    for (let i = 0; i < 2 && 层.parentElement; i++) {
      层 = 层.parentElement;
      const p = getComputedStyle(层);
      if (parseFloat(p.opacity) < 1) { op = p.opacity; cur = p.cursor; }
    }
    出.push({ 文字: t, 整行opacity: op, cursor: cur, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
  }
  return 出;
});

/**
 * ⭐ 手册 Batch EI 的实测读数：「打组」那枚按钮的 **`aria-label` 是 `打组菜单`**，
 *   而按钮的文字 `打组` 在 DOM 里**不一定落在叶子节点上**（可能被 `<span>`/`<p>` 包着，
 *   或带一个下拉箭头字符）。第一版按「叶子节点文字 == 打组」找，**报「找不到」**。
 *   ⇒ 定位改成 **aria 全等**，文字只用来交叉验。
 */
const 开下拉 = async () => {
  const b = await page.evaluate(() => {
    const c = [...document.querySelectorAll('[aria-label="打组菜单"]')];
    if (!c.length) return null;
    const r = c[0].getBoundingClientRect();
    return { pt: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)], box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 文字: (c[0].innerText || '').trim() };
  });
  if (!b) return null;
  记('  「打组菜单」按钮：' + JSON.stringify(b));
  await page.mouse.move(b.pt[0], b.pt[1]); await page.waitForTimeout(500);
  await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(1000);
  return b;
};

/** 选区包围盒上沿那一带的全部叶子文字元素 —— 用来看工具条到底在不在 */
const 选区上方 = async () => {
  const 选中框 = await page.evaluate(() => {
    const ns = [...document.querySelectorAll('.react-flow__node.selected')];
    if (!ns.length) return null;
    let l = Infinity, t = Infinity, r = -Infinity, b = -Infinity;
    for (const n of ns) { const q = n.getBoundingClientRect(); l = Math.min(l, q.left); t = Math.min(t, q.top); r = Math.max(r, q.right); b = Math.max(b, q.bottom); }
    return { l, t, r, b };
  });
  if (!选中框) return null;
  记('  选区包围盒：' + JSON.stringify(选中框.map(Math.round)));
  const 列 = await page.evaluate(([l, t, r, b]) => {
    const 出 = [];
    for (const e of document.querySelectorAll('div,span,button,p')) {
      const q = e.getBoundingClientRect();
      if (q.width < 6 || q.height < 6) continue;
      if (q.bottom < t - 220 || q.top > t + 10) continue;      // 只看选区上沿那一带
      if (q.left < l - 260 || q.left > r + 260) continue;
      const cs = getComputedStyle(e);
      if (cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) continue;
      const txt = (e.innerText || '').trim().replace(/\s+/g, ' ');
      if (!txt || txt.length > 18) continue;
      出.push({ t: txt, tag: e.tagName.toLowerCase(), aria: e.getAttribute('aria-label'), box: [Math.round(q.left), Math.round(q.top), Math.round(q.width), Math.round(q.height)], 子: e.children.length });
    }
    return 出;
  }, [选中框.l, 选中框.t, 选中框.r, 选中框.b]);
  记('  ⭐ 选区上沿那一带的文字元素 ' + 列.length + ' 个：');
  for (const c of 列.slice(0, 40)) 记(`     [${c.tag}${c.aria ? '/' + c.aria : ''}] "${c.t}" ${JSON.stringify(c.box)}`);
  await page.screenshot({ path: EVID + 'ez1e-选区上沿.png', clip: { x: Math.max(0, 选中框.l - 260), y: Math.max(0, 选中框.t - 220), width: Math.min(1400, 选中框.r - 选中框.l + 520), height: 260 } });
  记('  已拍 ez1e-选区上沿.png');
  return 列;
};

/** ⭐ 画布坐标驱动的拖拽：目标画布位移 → Δscreen = Δcanvas × zoom，**循环到误差 < 0.5** */
const 拖到 = async (id, 目标画布, 轮数上限 = 6) => {
  for (let 轮 = 1; 轮 <= 轮数上限; 轮++) {
    const 快照Now = await 快照();
    const n = 快照Now.节点.find((x) => x.id === id);
    if (!n || !n.画布) { 记(`  ⛔ ${id} 不在渲染里`); return false; }
    const dx = 目标画布[0] - n.画布[0];
    const dy = 目标画布[1] - n.画布[1];
    const 误 = Math.hypot(dx, dy);
    记(`  ${id} 第 ${轮} 轮：现画布 [${n.画布[0]}, ${n.画布[1]}] → 目标 [${目标画布[0]}, ${目标画布[1]}]，误差 ${误.toFixed(3)}`);
    if (误 < 0.5) { 记(`  ✅ ${id} 到位（误差 ${误.toFixed(3)} < 0.5）`); return true; }
    const z = 快照Now.视口 ? 快照Now.视口.zoom : 0.458621;
    const sx = n.中心[0] + dx * z;
    const sy = n.中心[1] + dy * z;
    if (sx < 0 || sy < 0 || sx > 1440 || sy > 810) { 记(`  ⛔ 目标落点 ${sx.toFixed(0)},${sy.toFixed(0)} 出视口，中止`); return false; }
    await page.mouse.move(n.中心[0], n.中心[1]); await page.waitForTimeout(380);
    const v = await 落点(n.中心);
    if (v.id !== id) { 记(`  ⛔ ${id} 落点被 ${v.id} 挡住，中止`); return false; }
    await page.mouse.down(); await page.waitForTimeout(120);
    const 步 = 12;
    for (let i = 1; i <= 步; i++) {
      await page.mouse.move(n.中心[0] + (sx - n.中心[0]) * i / 步, n.中心[1] + (sy - n.中心[1]) * i / 步);
      await page.waitForTimeout(35);
    }
    await page.mouse.up(); await page.waitForTimeout(700);
    await page.mouse.move(720, 780); await page.waitForTimeout(300);
  }
  return false;
};

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));

  const s0 = await 快照();
  记('视口：' + JSON.stringify(s0.视口));
  for (const n of s0.节点) 记(`  ${n.id} 画布 [${n.画布}] 屏 ${JSON.stringify(n.屏)}`);
  结果.读数.开局 = s0;
  const 遮挡起点 = (s0.节点.find((n) => n.id === 遮挡) || {}).画布;
  if (!遮挡起点) throw new Error('视频节点没渲染');
  记(`⭐ ${遮挡} 的画布坐标 = [${遮挡起点}]`);

  // ---- 阶段 1：把视频节点往下挪 420 个画布单位 ----
  const 挪后 = [遮挡起点[0], 遮挡起点[1] + 420];
  记('—— 阶段 1：把视频节点挪开 ——');
  const 挪成 = await 拖到(遮挡, 挪后);
  if (!挪成) throw new Error('挪开失败');
  await page.screenshot({ path: EVID + 'ez1e-1-视频节点挪开.png' });
  记('  已拍 ez1e-1-视频节点挪开.png');

  // ---- 阶段 2：扫一遍图 A 的框，确认它露出来了 ----
  const 扫 = await page.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!n) return null;
    const r = n.getBoundingClientRect();
    const S = 8;
    const 分布 = {};
    for (let x = Math.ceil(r.left); x < r.right; x += S)
      for (let y = Math.ceil(r.top); y < r.bottom; y += S) {
        const e = document.elementFromPoint(x, y);
        const nn = e ? e.closest('.react-flow__node') : null;
        const k = nn ? nn.getAttribute('data-id') : '(无)';
        分布[k] = (分布[k] || 0) + 1;
      }
    return { 框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 分布, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] };
  }, 图A);
  记('  挪开后图 A 的归属分布：' + JSON.stringify(扫.分布) + ' 框=' + JSON.stringify(扫.框));
  结果.读数.挪开后扫描 = 扫;

  // ---- 阶段 3：点图 A，再 Shift 加选图 B ----
  记('—— 阶段 2/3：选中两个纯图片节点 ——');
  const B屏 = (s0.节点.find((n) => n.id === 图B) || {}).中心;
  // 图 A 的中心可能仍被别的东西压着，先按分布挑一个「A 占比高」的位置
  const 点A = await page.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    const r = n.getBoundingClientRect();
    const S = 10;
    let 最佳 = null, 最好 = -1;
    for (let x = Math.ceil(r.left) + 20; x < r.right - 20; x += S)
      for (let y = Math.ceil(r.top) + 20; y < r.bottom - 20; y += S) {
        const e = document.elementFromPoint(x, y);
        const nn = e ? e.closest('.react-flow__node') : null;
        if (nn && nn.getAttribute('data-id') === id) { 最佳 = [x, y]; 最好 = 1; break; }
      }
    return 最佳;
  }, 图A);
  记('  图 A 的可用落点：' + JSON.stringify(点A));
  if (!点A) throw new Error('图 A 仍然点不到');
  await page.mouse.move(点A[0], 点A[1]); await page.waitForTimeout(450);
  const vA = await 落点(点A);
  记('  图 A 落点自证：' + JSON.stringify(vA));
  if (vA.id !== 图A) throw new Error('图 A 落点不对 ' + JSON.stringify(vA));
  await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(900);
  await page.mouse.move(720, 780); await page.waitForTimeout(500);
  const 选1 = await 选中集('图A');

  await page.keyboard.down('Shift');
  await page.mouse.move(B屏[0], B屏[1]); await page.waitForTimeout(450);
  const vB = await 落点(B屏);
  记('  图 B 落点自证：' + JSON.stringify(vB));
  if (vB.id === 图B) {
    await page.mouse.down(); await page.mouse.up();
    await page.keyboard.up('Shift');
    await page.waitForTimeout(1000);
    await page.mouse.move(720, 780); await page.waitForTimeout(500);
    const 选2 = await 选中集('图A + Shift图B');
    结果.读数.选中 = 选2;

    // ---- 阶段 3.5：工具条在不在？ ----
    await 选区上方();

    // ---- 阶段 4：读 `合并分镜组` ----
    const ok = await 开下拉();
    if (ok) {
      const d = await 下拉读数();
      记('  ⭐⭐⭐ 打组下拉：' + JSON.stringify(d));
      结果.读数.下拉_两个图片 = d;
      await page.screenshot({ path: EVID + 'ez1e-2-两个纯图片节点-合并分镜组.png' });
      记('  已拍 ez1e-2-两个纯图片节点-合并分镜组.png');
      const 合 = d.find((x) => x.文字 === '合并分镜组');
      const 组 = d.find((x) => x.文字 === '打组');
      if (合) 记(`  ⭐⭐⭐⭐ 结论：「合并分镜组」整行 opacity=${合.整行opacity} cursor=${合.cursor}；同屏「打组」opacity=${组 && 组.整行opacity} cursor=${组 && 组.cursor}`);
      await page.keyboard.press('Escape'); await page.waitForTimeout(700);
    } else {
      记('  ⛔ 找不到「打组」按钮');
    }
  } else {
    await page.keyboard.up('Shift');
    记('  ⛔ 图 B 落点不对：' + JSON.stringify(vB));
  }

  // ---- 阶段 5：原样挪回去 ----
  记('—— 阶段 3：把视频节点挪回原位 ——');
  const 复原成 = await 拖到(遮挡, 遮挡起点, 8);
  记('  复原结果：' + (复原成 ? '✅ 到位' : '⛔ 没到位'));
  await page.screenshot({ path: EVID + 'ez1e-3-复原之后.png' });
  记('  已拍 ez1e-3-复原之后.png');

  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 偏差 = await 核对坐标(page);
  记('⭐⭐ 静置 15s 后坐标复核：' + JSON.stringify(偏差));
  const 现 = await 读全部坐标(page);
  记('  视频节点画布坐标现值：' + JSON.stringify(现[遮挡]) + ' 基线：' + JSON.stringify(坐标[遮挡]));
  结果.收尾 = { 偏差, 已渲染: Object.keys(现).length, 遮挡现值: 现[遮挡], 遮挡基线: 坐标[遮挡] };
} catch (e) {
  记('❌ ' + e.message);
  结果.错误 = String((e && e.stack) || e);
} finally {
  落盘(结果);
  await 浏览器.browser.close();
  console.log('\n=== 已写 tools/batchEZ1e.json ===');
}
