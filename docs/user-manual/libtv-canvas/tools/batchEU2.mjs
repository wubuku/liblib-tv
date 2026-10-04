// Batch EU-2：给「开关型控件」攒够**成对**的开/关读数。
//
//   EU-1 的收获与教训：
//     收获：底栏两枚开关的**关态**指纹拿到了 ——
//       `隐藏节点连线` aria="隐藏节点连线"，svg 1 个 path `M9.28 0a2.28 2.28 0 1 1-2.22 2.8h-4.5a1.52 1.52`
//       `网格吸附`   aria="网格吸附"，  svg 1 个 path `M4.67 2.64a1 1 0 0 1 1.59-.8l7.3 5.36a1 1 0 0 `
//     教训：① 候选判据太宽（关键字正则把 89 个元素收进来，大部分不是开关）；
//           ② ⭐⭐ 又踩了 ET 的坑 —— **收起态读不到东西**（ET 已证 `grid-rows-[0fr]`）。
//              上一版要找的 `联网搜索/自动校验素材/智能引用 AutoLink` 三个开关
//              **在视频节点里**（不是音频节点），而且必须**先点 ⚙ 展开**才读得到。
//
//   本轮只做两件事，都安全：
//     ① 视频节点 ⚙ 里那三个开关（**只读形态，不点它们** —— 它们是节点的生成参数开关）
//        读法沿用 ET-6 的正路：点 ⚙ 后用 `grid-template-rows` 计算值确认真的展开了。
//        AUDIT 记它们「默认全开」，所以本轮只拿**开态**。
//     ② 底栏两枚（**纯视图开关，§289 有翻转先例**）做一次**同轮 A/B + 复原回归**：
//        关 → 开 → 关，并逐次读内部结构。
//        ⭐ 收尾必须复原，并用**第四种读数**确认复原（§289 的做法）。
//
// ⛔ 不点节点参数里的任何开关（联网搜索 / 自动校验素材 / 智能引用 AutoLink / 生成音频）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEU2.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 找起点 = (page, dx, dy) => page.evaluate((d) => {
  const 好 = [];
  for (let y = 130; y <= 690; y += 20) for (let x = 130; x <= 1310; x += 20) {
    const e = document.elementFromPoint(x, y);
    if (!e) continue;
    if (e.closest('.react-flow__node') || e.closest('button,[role="button"],a')) continue;
    const r = e.getBoundingClientRect();
    if (r.width < innerWidth && r.height < innerHeight) continue;
    if (!/react-flow/i.test(String(e.className)) && !/canvas/i.test(String(e.className))) continue;
    const 走X = d.dx < 0 ? x - 10 : (1310 - x), 走Y = d.dy < 0 ? y - 10 : (690 - y);
    好.push({ x, y, 走X, 走Y, 够: Math.min(走X / Math.max(1, Math.abs(d.dx)), 走Y / Math.max(1, Math.abs(d.dy))) });
  }
  if (!好.length) return null;
  好.sort((a, b) => b.够 - a.够);
  return 好[0];
}, { dx, dy });

const 平移到左上 = async (page, id) => {
  for (let 段 = 0; 段 < 7; 段++) {
    const 框 = await page.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null; const r = n.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; }, id);
    if (!框) { await page.keyboard.press('Meta+0'); await page.waitForTimeout(2200); continue; }
    const dx = 200 - 框[0], dy = 150 - 框[1];
    if (Math.abs(dx) < 12 && Math.abs(dy) < 12) return true;
    const 起 = await 找起点(page, dx, dy);
    if (!起) return false;
    const 本X = Math.round(Math.max(-起.走X, Math.min(起.走X, dx)));
    const 本Y = Math.round(Math.max(-起.走Y, Math.min(起.走Y, dy)));
    if (Math.abs(本X) < 10 && Math.abs(本Y) < 10) return false;
    await page.mouse.move(起.x, 起.y);
    await page.mouse.down({ button: 'middle' });
    for (let i = 1; i <= 12; i++) await page.mouse.move(起.x + 本X * i / 12, 起.y + 本Y * i / 12);
    await page.mouse.up({ button: 'middle' });
    await page.waitForTimeout(1600);
    const 现 = await 读全部坐标(page);
    if (Object.keys(坐标).some(k => 现[k] && (Math.abs(现[k][0] - 坐标[k][0]) > 1.5 || Math.abs(现[k][1] - 坐标[k][1]) > 1.5))) throw new Error('移动了节点');
  }
  return false;
};

const 安全点 = (page, id) => page.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  for (let a = 1; a < 10; a++) for (let b = 1; b < 10; b++) {
    const x = Math.round(r.left + r.width * a / 10), y = Math.round(r.top + r.height * b / 10);
    if (x < 5 || y < 5 || x > 1435 || y > 805) continue;
    const e = document.elementFromPoint(x, y);
    const g = e && e.closest('.react-flow__node');
    if (g && g.getAttribute('data-id') === i) return [x, y];
  }
  return null;
}, id);

/** 只读两枚底栏开关的全部状态属性（§289 的正路：看内部结构，不只看外部属性） */
const 读底栏 = (page) => page.evaluate(() => {
  const 取 = (aria) => {
    const b = document.querySelector(`[aria-label="${aria}"], [title="${aria}"]`);
    if (!b) return null;
    const r = b.getBoundingClientRect();
    const cs = getComputedStyle(b);
    const svgs = [...b.querySelectorAll('svg')];
    return {
      找法: b.hasAttribute('aria-label') ? 'aria-label' : 'title',
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      文字: (b.innerText || '').replace(/\s+/g, ' ').trim(),
      aria: b.getAttribute('aria-label'), title: b.getAttribute('title'),
      子数: b.children.length,
      svg数: svgs.length,
      svg: svgs.map(s => { const p = s.querySelector('path'); const q = s.getBoundingClientRect(); return { 尺寸: [Math.round(q.width), Math.round(q.height)], pathd: p ? p.getAttribute('d').slice(0, 60) : null }; }),
      子cls: [...b.children].map(c => String(c.className).slice(0, 50)),
      背景: cs.backgroundColor, 边框: cs.borderColor, 边框宽: cs.borderTopWidth,
      cls: String(b.className).slice(0, 130),
      data: Object.fromEntries([...b.attributes].filter(a => a.name.startsWith('data-')).map(a => [a.name, a.value])),
    };
  };
  return { 网格吸附: 取('网格吸附'), 隐藏节点连线: 取('隐藏节点连线') };
});

/** 视频节点 ⚙ 展开后，读那三个开关（只读，不点） */
const 读三开关 = (page) => page.evaluate(() => {
  const 关键字 = ['联网搜索', '自动校验素材', '智能引用 AutoLink'];
  const 出 = {};
  for (const k of 关键字) {
    const 标签 = [...document.querySelectorAll('body *')].find(e => e.children.length === 0 && (e.innerText || '').trim() === k);
    if (!标签) { 出[k] = null; continue; }
    // 往上找到「既是标签的兄弟、又能点」的那一层：先看父，再看父的父
    let 命中 = null;
    let n = 标签.parentElement;
    for (let i = 0; i < 4 && n && !命中; i++) {
      const cs = getComputedStyle(n);
      if (cs.cursor === 'pointer' || n.tagName === 'BUTTON' || n.getAttribute('role') === 'switch' || n.getAttribute('role') === 'button') 命中 = n;
      n = n.parentElement;
    }
    const 目标 = 命中 || 标签.parentElement;
    const r = 目标.getBoundingClientRect();
    const cs = getComputedStyle(目标);
    const svgs = [...目标.querySelectorAll('svg')];
    出[k] = {
      标签box: (() => { const q = 标签.getBoundingClientRect(); return [Math.round(q.left), Math.round(q.top), Math.round(q.width), Math.round(q.height)]; })(),
      命中层: `${目标.tagName}.${String(目标.className).slice(0, 40)}`,
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      role: 目标.getAttribute('role'), ariaChecked: 目标.getAttribute('aria-checked'), ariaPressed: 目标.getAttribute('aria-pressed'),
      dataState: 目标.getAttribute('data-state'), dataChecked: 目标.getAttribute('data-checked'),
      子数: 目标.children.length, svg数: svgs.length,
      svg: svgs.map(s => { const p = s.querySelector('path'); const q = s.getBoundingClientRect(); return { 尺寸: [Math.round(q.width), Math.round(q.height)], pathd: p ? p.getAttribute('d').slice(0, 60) : null }; }),
      背景: cs.backgroundColor, 边框: cs.borderColor, 边框宽: cs.borderTopWidth, 不透明: cs.opacity, 光标: cs.cursor,
      cls: String(目标.className).slice(0, 140),
      整块文字: (目标.closest('div[class*="flex"],div') ? (目标.parentElement ? (目标.parentElement.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60) : null) : null),
    };
  }
  return 出;
});

const 展开态 = (page) => page.evaluate(() => [...document.querySelectorAll('div')]
  .filter(e => /grid-rows-\[0fr\]|grid-rows-\[1fr\]/.test(String(e.className)))
  .map(e => { const cs = getComputedStyle(e); const r = e.getBoundingClientRect(); return { 行高: cs.gridTemplateRows, 高: Math.round(r.height), 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60) }; }));

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 7000 });
  await closePromos(page);
  await page.waitForTimeout(1500);
  await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim() === '知道了'); if (b) b.click(); });
  await page.waitForTimeout(800);
  await page.evaluate(() => {
    const 条 = [...document.querySelectorAll('div')].filter(d => /开启浏览器通知/.test(d.innerText || ''));
    if (条.length) { 条.sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width); const btn = [...条[条.length - 1].querySelectorAll('button')].find(b => (b.innerText || '').trim() === ''); if (btn) btn.click(); }
  });
  await page.waitForTimeout(700);
  await page.evaluate(() => { for (const b of document.querySelectorAll('button')) if (b.getAttribute('aria-label') === '关闭' && b.getBoundingClientRect().width < 40) { b.click(); return; } });
  await page.waitForTimeout(1000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3200);
  记(`开局坐标偏差：${JSON.stringify(await 核对坐标(page))}`);

  const 全 = { 底栏: [], 三开关: null };

  // ① 视频节点 ⚙ 里的三个开关（只读）
  记('\n════ ① 视频节点 ⚙ 里的三个开关（只读形态）════');
  if (!(await page.evaluate((id) => !!document.querySelector(`.react-flow__node[data-id="${id}"]`), 'v-v2hlWY4Br3'))) { await page.keyboard.press('Meta+0'); await page.waitForTimeout(2500); }
  记(`　平移视频节点：${await 平移到左上(page, 'v-v2hlWY4Br3')}`);
  const 落 = await 安全点(page, 'v-v2hlWY4Br3');
  if (落) {
    await page.mouse.click(落[0], 落[1]);
    await page.waitForTimeout(2500);
    const 选 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
    记(`　选中 ${JSON.stringify(选)}`);
    if (选.length === 1 && 选[0] === 'v-v2hlWY4Br3') {
      const 齿轮 = await page.evaluate((id) => {
        const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
        for (const b of n.querySelectorAll('button')) {
          if (!/text-canvas-controls-text/.test(String(b.className))) continue;
          const r = b.getBoundingClientRect();
          if (r.bottom < 0 || r.top > innerHeight) continue;
          return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
        }
        return null;
      }, 'v-v2hlWY4Br3');
      记(`　⚙ 中心 ${JSON.stringify(齿轮)}`);
      if (齿轮) {
        记(`　点之前：${JSON.stringify(await 展开态(page))}`);
        await page.mouse.click(齿轮[0], 齿轮[1]);
        await page.waitForTimeout(2000);
        const 态 = await 展开态(page);
        记(`　点之后：${JSON.stringify(态)}`);
        const 展开了 = 态.some(x => x.行高 && x.行高 !== '0px');
        记(`　⭐ 展开判定（grid-template-rows ≠ 0px）= ${展开了 ? '✅ 已展开' : '⛔ 仍收起'}`);
        if (展开了) {
          const 三 = await 读三开关(page);
          全.三开关 = 三;
          for (const k of Object.keys(三)) {
            const s = 三[k];
            if (!s) { 记(`　　${k}：⛔ 没找到标签`); continue; }
            记(`　　${k}：${s.命中层} box=${JSON.stringify(s.box)} role=${s.role} aria-checked=${s.ariaChecked} aria-pressed=${s.ariaPressed} data-state=${s.dataState}`);
            记(`　　　子数=${s.子数} svg数=${s.边框 ? s.svg数 : 0} 背景=${s.背景} 边框=${s.边框}/${s.边框宽} 不透明=${s.不透明} 光标=${s.光标}`);
            记(`　　　svg：${JSON.stringify(s.svg)}`);
            记(`　　　cls：${s.cls}`);
          }
          await page.mouse.move(1400, 60); await page.waitForTimeout(900);
          await page.screenshot({ path: EVID + 'eu2-视频-三个开关.png' });
        }
      }
      await page.keyboard.press('Escape'); await page.waitForTimeout(1300);
    }
  }

  // ② 底栏两枚：关 → 开 → 关 → 复原验证
  记('\n════ ② 底栏两枚开关 A/B（纯视图开关，收尾必须复原）════');
  await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
  await page.keyboard.press('Meta+0'); await page.waitForTimeout(2200);
  const 态0 = await 读底栏(page);
  记(`　【起始】网格吸附 aria=${JSON.stringify(态0.网格吸附 && 态0.网格吸附.aria)} svg数=${态0.网格吸附 && 态0.网格吸附.svg数} 背景=${态0.网格吸附 && 态0.网格吸附.背景} 子数=${态0.网格吸附 && 态0.网格吸附.子数} cls含active=${态0.网格吸附 ? /active/.test(态0.网格吸附.cls) : null}`);
  记(`　　　　　隐藏节点连线 aria=${JSON.stringify(态0.隐藏节点连线 && 态0.隐藏节点连线.aria)} svg数=${态0.隐藏节点连线 && 态0.隐藏节点连线.svg数} 背景=${态0.隐藏节点连线 && 态0.隐藏节点连线.背景} 子数=${态0.隐藏节点连线 && 态0.隐藏节点连线.子数}`);
  全.底栏.push({ 状态: '起始', ...态0 });

  const 点底栏 = async (aria) => {
    const b = await page.evaluate((a) => { const e = document.querySelector(`[aria-label="${a}"]`); if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)]; }, aria);
    if (!b) { 记(`　⛔ 找不到 ${aria}`); return false; }
    const 验 = await page.evaluate((c) => { const e = document.elementFromPoint(c[0], c[1]); const g = e && e.closest('[aria-label]'); return g ? g.getAttribute('aria-label') : null; }, b);
    记(`　　点 ${aria} 中心 ${JSON.stringify(b)}｜elementFromPoint 自证落在 ${JSON.stringify(验)}`);
    if (验 !== aria) { 记(`　　　⛔ 落点不符，不点`); return false; }
    await page.mouse.click(b[0], b[1]);
    await page.waitForTimeout(1600);
    return true;
  };

  if (await 点底栏('隐藏节点连线')) {
    const s = await 读底栏(page);
    全.底栏.push({ 状态: '点了隐藏节点连线', ...s });
    记(`　【之后】隐藏节点连线 aria=${JSON.stringify(s.隐藏节点连线 && s.隐藏节点连线.aria)} svg数=${s.隐藏节点连线 && s.隐藏节点连线.svg数} 背景=${s.隐藏节点连线 && s.隐藏节点连线.背景} 子数=${s.隐藏节点连线 && s.隐藏节点连线.子数}`);
    记(`　　　　　svg：${JSON.stringify(s.隐藏节点连线 && s.隐藏节点连线.svg)}`);
    await page.screenshot({ path: EVID + 'eu2-底栏-连线已隐藏.png' });
    if (await 点底栏('隐藏节点连线')) {
      const s2 = await 读底栏(page);
      全.底栏.push({ 状态: '复原隐藏节点连线', ...s2 });
      记(`　【复原】隐藏节点连线 aria=${JSON.stringify(s2.隐藏节点连线 && s2.隐藏节点连线.aria)} svg数=${s2.隐藏节点连线 && s2.隐藏节点连线.svg数} 子数=${s2.隐藏节点连线 && s2.隐藏节点连线.子数}`);
    }
  }
  if (await 点底栏('网格吸附')) {
    const s = await 读底栏(page);
    全.底栏.push({ 状态: '点了网格吸附', ...s });
    记(`　【开】网格吸附 aria=${JSON.stringify(s.网格吸附 && s.网格吸附.aria)} svg数=${s.网格吸附 && s.网格吸附.svg数} 背景=${s.网格吸附 && s.网格吸附.背景} 子数=${s.网格吸附 && s.网格吸附.子数} cls含active=${s.网格吸附 ? /active/.test(s.网格吸附.cls) : null}`);
    记(`　　　svg：${JSON.stringify(s.网格吸附 && s.网格吸附.svg)}`);
    记(`　　　子cls：${JSON.stringify(s.网格吸附 && s.网格吸附.子cls)}`);
    await page.screenshot({ path: EVID + 'eu2-底栏-网格吸附已开.png' });
    if (await 点底栏('网格吸附')) {
      const s2 = await 读底栏(page);
      全.底栏.push({ 状态: '复原网格吸附', ...s2 });
      记(`　【复原】网格吸附 aria=${JSON.stringify(s2.网格吸附 && s2.网格吸附.aria)} svg数=${s2.网格吸附 && s2.网格吸附.svg数} 子数=${s2.网格吸附 && s2.网格吸附.子数} cls含active=${s2.网格吸附 ? /active/.test(s2.网格吸附.cls) : null}`);
    }
  }

  // 收尾：第四种读数确认复原
  const 末 = await 读底栏(page);
  记(`\n⭐⭐ 收尾复核：隐藏节点连线 aria=${JSON.stringify(末.隐藏节点连线 && 末.隐藏节点连线.aria)}（应为 隐藏节点连线）｜网格吸附 aria=${JSON.stringify(末.网格吸附 && 末.网格吸附.aria)} 子数=${末.网格吸附 && 末.网格吸附.子数}（起始应为 1）`);
  全.收尾 = 末;
  记('\n✅ 完成（只点了底栏两枚纯视图开关，已复原）');
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  try {
    记('⏳ ⌘0 复位 + 静置 15s…');
    await page.keyboard.press('Meta+0');
    await page.waitForTimeout(15000);
    const 现 = await 读全部坐标(page);
    const 真动 = Object.keys(坐标).filter(id => 现[id] && (Math.abs(现[id][0] - 坐标[id][0]) > 1.5 || Math.abs(现[id][1] - 坐标[id][1]) > 1.5));
    记(`⭐ 真的被移动：${真动.length} 个 ${JSON.stringify(真动)}`);
  } catch (e) { console.error(e); }
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEU2.json ===');
}
