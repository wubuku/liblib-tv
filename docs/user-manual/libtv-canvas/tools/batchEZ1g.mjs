// Batch EZ-1g：⭐⭐⭐ 改用**框选**——点选/Shift 加选**根本不弹多选工具条**
//
// EZ-1f 的读数：选中 2 个纯图片节点（`.selected` 实打实有两个），
//   选区包围盒 `[76,319,1093,480]`，**上沿 220px 带里一个工具条文字元素都没有**，
//   `aria-label="打组菜单"` 全页 0 命中，截图里那一带也是空的。
//   ⇒ ⭐⭐ **多选工具条是「框选」才有的**，点选 + Shift 加选走的是另一条路，没有它。
//
// 本轮把选法换成**框选**：视频节点挪开之后，两个图片节点之间没有障碍，
//   框选矩形只要避开 `音频节点`（屏 `[263,182,161,161]`，下缘 y=343）就能只圈中两张图片卡。
//
// ⭐⭐⭐ 复原归 `finally`（EZ-1e 丢过一个节点的教训）。⭐⭐⭐ 挪开视频节点 → 选中 2 个纯图片节点 → 读 `合并分镜组` → 原样挪回去
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
const OUT = HERE + 'batchEZ1g.json';
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
  记('  选区包围盒：' + JSON.stringify([选中框.l, 选中框.t, 选中框.r, 选中框.b].map(Math.round)));
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
  await page.screenshot({ path: EVID + 'ez1f-选区上沿.png', clip: { x: Math.max(0, 选中框.l - 260), y: Math.max(0, 选中框.t - 220), width: Math.min(1400, 选中框.r - 选中框.l + 520), height: 260 } });
  记('  已拍 ez1f-选区上沿.png');
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

// ⭐⭐⭐ **复原放在主流程里就等于「前面任何一步抛错 = 画布留伤」。**
//    EZ-1e 正是这么丢了一个节点：`选中框.map is not a function` 抛在复原之前，
//    异常直接跳过复原，`v-eMpqKtiLlx` 留在 [-1787,1320]（差 420 画布单位，已另行复原）。
//    ⇒ 凡是会改画布的实验，复原归 `finally`，且 `finally` 里先复原再关浏览器。
let 挪前 = null;
let 已挪开 = false;

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
  挪前 = 遮挡起点;
  记(`⭐ ${遮挡} 的画布坐标 = [${遮挡起点}]`);

  // ---- 阶段 1：挪开视频节点 ----
  记('—— 阶段 1：把视频节点挪开 ——');
  const 挪成 = await 拖到(遮挡, [遮挡起点[0], 遮挡起点[1] + 420]);
  已挪开 = true;
  if (!挪成) throw new Error('挪开失败');
  await page.screenshot({ path: EVID + 'ez1g-1-视频节点挪开.png' });
  记('  已拍 ez1g-1-视频节点挪开.png');

  // ---- 阶段 2：框选两个图片节点 ----
  // ⭐ 框选矩形要**避开** `a-GgqvrVz0pw`（屏 `[263,182,161,161]`，下缘 y=343），
  //    否则它会被一起圈进来 —— 而「2 图片 + 1 音频」正是**阴性**那一档。
  //    所以起点 y 取 355（在 343 之下），终点 y 取 495（在图片节点下缘 480 之上）。
  const 起 = [40, 355];
  const 止 = [1110, 495];
  记('—— 阶段 2：框选 ——');
  const 起落 = await 落点(起);
  记('  框选起点落点=' + JSON.stringify(起落) + '（必须是 null，才说明点在空白上）');
  if (起落.id !== null) throw new Error('框选起点落在 ' + 起落.id + ' 上，改用点选');
  await page.mouse.move(起[0], 起[1]); await page.waitForTimeout(420);
  await page.mouse.down(); await page.waitForTimeout(140);
  for (let i = 1; i <= 16; i++) {
    await page.mouse.move(起[0] + (止[0] - 起[0]) * i / 16, 起[1] + (止[1] - 起[1]) * i / 16);
    await page.waitForTimeout(38);
  }
  await page.mouse.up(); await page.waitForTimeout(1000);
  await page.mouse.move(720, 780); await page.waitForTimeout(600);
  const 选 = await 选中集('框选');
  结果.读数.框选选中 = 选;

  if (选.length !== 2 || 选[0] !== 图A || 选[1] !== 图B) {
    记('  ⛔ 选区不是「恰好 2 个纯图片节点」，本轮到此为止');
  } else {
    // ---- 阶段 3：工具条 + 打组下拉 ----
    const ok = await 开下拉();
    if (!ok) {
      记('  ⛔ 仍然找不到「打组菜单」——记一次「框选 2 个节点时工具条没有出现」');
      await 选区上方();
    } else {
      const d = await 下拉读数();
      记('  ⭐⭐⭐ 打组下拉：' + JSON.stringify(d));
      结果.读数.下拉 = d;
      await page.screenshot({ path: EVID + 'ez1g-2-两个纯图片节点-打组下拉.png' });
      记('  已拍 ez1g-2-两个纯图片节点-打组下拉.png');
      const 合 = d.find((x) => x.文字 === '合并分镜组');
      const 组 = d.find((x) => x.文字 === '打组');
      if (合) {
        记(`  ⭐⭐⭐⭐ 阳性对照：「合并分镜组」整行 opacity=${合.整行opacity} cursor=${合.cursor}`);
        记(`  同屏「打组」opacity=${组 && 组.整行opacity} cursor=${组 && 组.cursor}`);
        记(`  判「变亮」：${parseFloat(合.整行opacity) > 0.9 && 合.cursor === 'pointer' ? '✅ 是' : '⛔ 否'}`);
      }
      await page.keyboard.press('Escape'); await page.waitForTimeout(700);
    }
  }

  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 偏差 = await 核对坐标(page);
  记('⭐⭐ 静置 15s 后坐标复核：' + JSON.stringify(偏差));
  const 现 = await 读全部坐标(page);
  记('  视频节点画布坐标现值：' + JSON.stringify(现[遮挡]) + ' 基线：' + JSON.stringify(坐标[遮挡]));
  结果.收尾 = Object.assign(结果.收尾 || {}, { 偏差, 已渲染: Object.keys(现).length, 遮挡现值: 现[遮挡], 遮挡基线: 坐标[遮挡] });
} catch (e) {
  记('❌ ' + e.message);
  结果.错误 = String((e && e.stack) || e);
} finally {
  // ⭐⭐⭐ 复原先于关浏览器，且**无条件执行**
  if (已挪开 && 挪前) {
    记('—— finally：把 ' + 遮挡 + ' 挪回原位（无条件）——');
    try {
      const 成 = await 拖到(遮挡, 挪前, 8);
      记('  复原结果：' + (成 ? '✅ 到位' : '⛔ 没到位'));
      结果.收尾.复原 = 成 ? '到位' : '没到位';
    } catch (e2) {
      记('  ⛔ 复原抛错：' + e2.message);
      结果.收尾.复原 = '抛错：' + e2.message;
    }
  }
  落盘(结果);
  await 浏览器.browser.close();
  console.log('\n=== 已写 tools/batchEZ1g.json ===');
}
