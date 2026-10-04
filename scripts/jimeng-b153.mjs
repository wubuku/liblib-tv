// 批次 153 —— 复测**全册最陈旧的任务页** `assets-and-upload.md`（元审计差距 109 批）。
//
// 🔑 靶子筛选（元审计，见 `jimeng-b153-meta-audit.mjs`）：
//    17 个任务页按「全册最大批次 − 该页最大批次」排序，本页**差距 109**，排第 1。
//    （批次 149 用同一套元审计换掉过 director-node.md；那页已刷新到 150。）
//
// 🎯 复测范围刻意收窄到**零风险**那一半：
//   ✅ 左栏「上传」按钮的 aria / 屏上盒
//   ✅ 左栏「上传」展开的**格式白名单**（111 条 / 48 扩展名 / 4 类）—— 只读菜单，不点文件
//   ✅ 左栏「资产库」模态的**九层结构全谱** + 两级页签 + 搜索框
//   ✅ 节点内「替换媒体」的**白名单**（23 条 / 10 扩展名 / 单选）
//   ⛔ **不点任何文件选择器**（会真上传 ⇒ 往共享资产库写不可逆数据）
//   ⛔ **不点「确认」**（会往画布插节点）
//
// 📌 一个已知的方法陷阱（页面第 390 行自己写着）：
//   `document.querySelector('input[type=file]')` 读到的是**某个图片节点内部**那个
//   「替换媒体」的输入框，**不是**左栏上传弹出来的那个。
//   ⇒ 本轮每个入口都**先记下触发前后 `input[type=file]` 的总数与归属**，
//   再断言读到的那个确实挂在触发元素下面。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf, canvasPos, 可点落点, 组数 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 153, 目的: '复测全册最陈旧的任务页 assets-and-upload.md（零风险那一半）' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b153.json', import.meta.url), JSON.stringify(rec, null, 1));

const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x * 10) / 10, Math.round(r.y * 10) / 10]; };
const cs = (e, k) => getComputedStyle(e)[k];

/** 画布上所有 `input[type=file]` 的归属清单 —— 用来证明「读到的是哪一个」。 */
const file输入清单 = () => p.evaluate(() => Array.from(document.querySelectorAll('input[type=file]')).map((e) => {
  const 宿主 = e.closest('[data-testid]');
  const 节点 = e.closest('.react-flow__node');
  const 菜单 = e.closest('[role=menu],[role=dialog],[data-state=open]');
  return {
    存在: true,
    accept: e.getAttribute('accept'), multiple: e.hasAttribute('multiple'),
    节点内: !!节点, 节点aria: 节点 && 节点.getAttribute('aria-label'),
    最近testid: 宿主 && 宿主.getAttribute('data-testid'),
    在菜单里: !!菜单, 菜单tag: 菜单 && 菜单.tagName,
  };
}));

const { b, p } = await openCanvas();
const R = readers(p);
let 基线canvas = null;
try {
  await keyGuard(p); await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(),
    积分: await R.credits(), 组数: await 组数(p), 选中: await selCount(p) };
  基线canvas = await canvasPos(p);
  rec.起点file输入数 = (await file输入清单()).length;

  // ===== 1. 左栏两个入口按钮 =====
  rec.入口 = await p.evaluate(() => {
    const 找 = (aria) => {
      const cands = Array.from(document.querySelectorAll('button,[role=button],[aria-label],a,div'))
        .filter((e) => (e.getAttribute('aria-label') || '').trim() === aria);
      return cands.map((e) => {
        const r = e.getBoundingClientRect();
        return { tag: e.tagName, testid: e.getAttribute('data-testid'), class: (e.className || '').slice(0, 60),
          aria: e.getAttribute('aria-label'), box: [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x * 10) / 10, Math.round(r.y * 10) / 10],
          display: getComputedStyle(e).display, visibility: getComputedStyle(e).visibility };
      });
    };
    return { 上传: 找('上传'), 资产库: 找('资产库') };
  });
  落盘();

  // ===== 2. 左栏「上传」→ 格式白名单（只读菜单，不点文件选择器）=====
  {
    const 入口盒 = (rec.入口.上传 || [])[0];
    rec.上传前 = { file输入: await file输入清单() };
    if (入口盒) {
      // 点开：悬停左栏 + 点上传按钮。**不点任何文件**。
      const pt = await 可点落点(p, '[aria-label="上传"]', 3, 3);
      if (!pt.__err) {
        await p.mouse.move(pt.x, pt.y); await p.waitForTimeout(900);
        await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1500);
        rec.上传后 = { file输入: await file输入清单() };
        rec.上传菜单 = await p.evaluate(() => {
          // 白名单从**可见的 file input** 上读，并记下它的 accept / multiple
          const vis = Array.from(document.querySelectorAll('input[type=file]')).map((e) => {
            const 节点 = e.closest('.react-flow__node');
            return { accept: e.getAttribute('accept'), multiple: e.hasAttribute('multiple'),
              visible: e.offsetParent !== null || getComputedStyle(e).visibility !== 'hidden',
              节点内: !!节点, 节点aria: 节点 && 节点.getAttribute('aria-label') };
          });
          const 菜单 = Array.from(document.querySelectorAll('[role=menu]')).map((m) => ({
            text: (m.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400),
            ariaExpanded: null, box: (() => { const r = m.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; })(),
            visibility: getComputedStyle(m).visibility,
          }));
          return { file输入: vis, 菜单 };
        });
        落盘();
        // 关掉：Esc（只关菜单，不触发上传）
        await p.keyboard.press('Escape'); await p.waitForTimeout(900);
        await p.keyboard.press('Escape'); await p.waitForTimeout(900);
        rec.上传关闭后浮层 = await R.overlays();
        落盘();
      } else rec.上传后 = { __err: '上传按钮找不到落点' };
    }
  }

  // ===== 3. 左栏「资产库」→ 模态九层全谱 =====
  {
    const 前 = await file输入清单();
    const pt = await 可点落点(p, '[aria-label="资产库"]', 3, 3);
    if (!pt.__err) {
      await p.mouse.move(pt.x, pt.y); await p.waitForTimeout(900);
      await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(2600); await settle(p, R);
      rec.资产库 = await p.evaluate(() => {
        const 层 = [
          'canvas-asset-library-dialog', 'canvas-asset-library-surface',
          'canvas-asset-library-operation-area', 'canvas-asset-library-navigation-controls',
          'canvas-asset-library-query-action-group', 'canvas-asset-library-viewport',
          'canvas-asset-library-footer', 'canvas-asset-library-import-status',
          'canvas-asset-library-box-selection',
        ];
        const 读 = (tid) => {
          const e = document.querySelector('[data-testid="' + tid + '"]');
          if (!e) return { testid: tid, 存在: false };
          const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
          return { testid: tid, 存在: true,
            box: [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x * 10) / 10, Math.round(r.y * 10) / 10],
            role: e.getAttribute('role'), tag: e.tagName, dataState: e.getAttribute('data-state'),
            visibility: s.visibility, display: s.display, text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160) };
        };
        const 页签 = Array.from(document.querySelectorAll('[role=tab],[data-testid*="navigation"] button,[data-testid*="tab"]'))
          .map((e) => ({ tag: e.tagName, role: e.getAttribute('role'), testid: e.getAttribute('data-testid'),
            aria: e.getAttribute('aria-label'), text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20),
            selected: e.getAttribute('aria-selected') }));
        const 搜索 = Array.from(document.querySelectorAll('input[type=search],input[placeholder]'))
          .filter((e) => e.offsetParent !== null)
          .map((e) => { const r = e.getBoundingClientRect(); return { aria: e.getAttribute('aria-label'), placeholder: e.getAttribute('placeholder'), type: e.getAttribute('type'), box: [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x * 10) / 10, Math.round(r.y * 10) / 10] }; });
        return { 层: 层.map(读), 页签, 搜索,
          关闭钮: Array.from(document.querySelectorAll('button')).filter((e) => (e.getAttribute('aria-label') || '').includes('Close')).map((e) => { const r = e.getBoundingClientRect(); return { aria: e.getAttribute('aria-label'), box: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; }),
          对话框数: document.querySelectorAll('[role=dialog]').length };
      });
      rec.资产库后file输入数 = (await file输入清单()).length;
      落盘();
      // Esc 关闭（页面第 120 行：Esc 关闭模态实测）
      await p.keyboard.press('Escape'); await p.waitForTimeout(1400);
      rec.资产库关闭后 = { 浮层: await R.overlays(), 对话框数: await p.evaluate(() => document.querySelectorAll('[role=dialog]').length) };
      void 前;
      落盘();
    } else rec.资产库 = { __err: '资产库按钮找不到落点' };
  }

  // ===== 4. 节点内「替换媒体」白名单（只读，不选文件）=====
  rec.替换媒体 = await p.evaluate(() => {
    const 全部 = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
      const e = n.querySelector('[aria-label*="替换"], [data-testid*="replace"]');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return { 节点aria: n.getAttribute('aria-label'), aria: e.getAttribute('aria-label'), testid: e.getAttribute('data-testid'),
        box: [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10] };
    }).filter(Boolean);
    const 输入 = Array.from(document.querySelectorAll('input[type=file]')).map((e) => {
      const 节点 = e.closest('.react-flow__node');
      return { accept: e.getAttribute('accept'), multiple: e.hasAttribute('multiple'), 节点内: !!节点,
        节点aria: 节点 && 节点.getAttribute('aria-label') };
    });
    return { 触发钮: 全部, file输入: 输入 };
  });
  落盘();

  const 末 = await idsOf(p); const 末c = await canvasPos(p);
  rec.收尾检查 = { 节点数: 末.length,
    位移节点: 基线canvas ? Object.keys(基线canvas).filter((k) => 末c[k] && (末c[k][0] !== 基线canvas[k][0] || 末c[k][1] !== 基线canvas[k][1])) : null };
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

for (let k = 0; k < 3 && (await R.overlays()) > 0; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
const 小地图前 = await R.minimap();
if (!小地图前 || 小地图前.ariaPressed !== 'true') {
  const t = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3);
  if (!t.__err) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(1400); }
}
rec.小地图后 = await R.minimap();
await settle(p, R);
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p),
  浮层: await R.overlays(), zoom: await R.zoom(), 积分: await R.credits(), 组数: await 组数(p),
  边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length),
  file输入数: (await file输入清单()).length };

console.log('入口 上传:', JSON.stringify((rec.入口 || {}).上传));
console.log('入口 资产库:', JSON.stringify((rec.入口 || {}).资产库));
console.log('\n上传前 file 输入:', JSON.stringify((rec.上传前 || {}).file输入));
console.log('上传后 file 输入:', JSON.stringify((rec.上传后 || {}).file输入));
console.log('上传菜单 file 输入:', JSON.stringify(((rec.上传菜单 || {}).file输入 || [])));
console.log('上传菜单 菜单:', JSON.stringify(((rec.上传菜单 || {}).菜单 || [])));
console.log('上传关闭后浮层:', rec.上传关闭后浮层);
console.log('\n资产库九层:');
for (const l of ((rec.资产库 || {}).层 || [])) console.log('  ' + (l.存在 ? '✔' : '✘') + ' ' + l.testid + ' ' + JSON.stringify(l.box || null) + ' ' + (l.role || '') + ' ' + (l.dataState || '') + ' | ' + (l.text || '').slice(0, 60));
console.log('页签:', JSON.stringify(((rec.资产库 || {}).页签 || [])));
console.log('搜索:', JSON.stringify(((rec.资产库 || {}).搜索 || [])));
console.log('关闭钮:', JSON.stringify(((rec.资产库 || {}).关闭钮 || [])));
console.log('对话框数:', (rec.资产库 || {}).对话框数, '| 关闭后浮层', (rec.资产库关闭后 || {}).浮层, '| 关闭后对话框数', (rec.资产库关闭后 || {}).对话框数);
console.log('\n替换媒体 触发钮:', JSON.stringify(((rec.替换媒体 || {}).触发钮 || [])));
console.log('替换媒体 file 输入:', JSON.stringify(((rec.替换媒体 || {}).file输入 || [])));
console.log('\n收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');

断言('① 起点无异常、两个入口都读到', rec.入口 && (rec.入口.上传 || []).length >= 1 && (rec.入口.资产库 || []).length >= 1 && !rec.异常, { 上传: ((rec.入口 || {}).上传 || []).length, 资产库: ((rec.入口 || {}).资产库 || []).length, 异常: rec.异常 });
断言('② 资产库模态九层**逐层存在且非零面积**', ((rec.资产库 || {}).层 || []).every((l) => l.存在 && l.box && l.box[0] > 0) === true && ((rec.资产库 || {}).层 || []).length === 9, ((rec.资产库 || {}).层 || []).map((l) => [l.testid, l.存在, l.box && l.box[0]]));
断言('③ Esc 关闭资产库后浮层与对话框都归零', (rec.资产库关闭后 || {}).浮层 === 0 && (rec.资产库关闭后 || {}).对话框数 === 0, rec.资产库关闭后);
断言('④ 🔑 复现页面第 390 行的陷阱：读到的 file input **挂在节点里**（不是左栏那个）', (((rec.替换媒体 || {}).file输入 || []).length > 0 && (rec.替换媒体 || {}).file输入.every((f) => f.节点内)), (rec.替换媒体 || {}).file输入);
断言('⑤ 全程 `input[type=file]` 数量回到起点（没触发真上传）', (rec.收尾 || {}).file输入数 === (rec.起点file输入数 || 0), { 起: rec.起点file输入数, 收: (rec.收尾 || {}).file输入数 });
if (rec.收尾检查 && rec.收尾检查.位移节点) 断言('⑥ 其余节点零位移', rec.收尾检查.位移节点.length === 0, rec.收尾检查);

rec.断言全过 = 断言过; 落盘();
await b.close();
