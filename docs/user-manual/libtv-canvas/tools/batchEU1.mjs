// Batch EU-1：画布上**所有开关型控件**的统一清点 —— 归纳「LibTV 怎么表达开/关」。
//
//   手法的来源：ET 跑通的「**不做预筛、全量倾倒、离线找判据**」。
//   §289 已立过一条规矩：**判「状态翻没翻」必须看内部结构**，
//   外部属性（aria-label / backgroundColor / 某个工具类）只能证伪、不能证成。
//   本批把这条规矩**用全站**：枚举全视口每一枚**可能是开关**的按钮，
//   把它内部装了什么（子元素数 / 每个 svg 的 path / class 组合 / aria-label）
//   全部倒出来，然后离线归纳有几种「开/关」表达方式。
//
//   ⭐⭐ 三枚**答案已知**的对照组（答案来自已验证的批次）：
//     ① 底栏 `网格吸附`   §289 验过：开=多叠一枚斜杠图标，关=单图标
//     ② 底栏 `隐藏节点连线` §289 验过：**靠 aria-label 改名**（关=隐藏节点连线 / 开=显示节点连线）
//     ③ 视频参数面板 `生成音频` EP 验过：两段选择器，当前项白描边
//   新读数若在这三者上复现不出已知答案，**整轮作废**。
//
//   ⭐ 本轮**只读**：不点任何开关、不改任何状态。
//   （要判「点一下会不会变」需要点开关，而开关会改画布状态，故本批只做「形态清点 + 归类」；
//     形态差异由 §289/EP 已有的开/关两态读数提供对照。）
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { BASE, 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEU1.json';
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

/**
 * ⭐⭐ 全视口枚举「可能是开关」的按钮，并把**内部装了什么**全量倾倒。
 *   判据（只用来**缩小候选**，不用来判状态）：
 *     · 它是可点元素（button / [role=button] / cursor:pointer 的 div）
 *     · 且满足下列任一「像开关」的特征：
 *       a) 有 aria-label 且文案里带 开/关/显示/隐藏/吸附/自动/智能/联网/校验/引用
 *       b) 自身文字里带 开/关/自动/智能/联网
 *       c) ⭐ 内部**叠了 2 个以上** svg 图标（§289 的「叠图标」式开关）
 *       d) class 里有 switch/toggle/chip/segment/active 之类
 *   倾倒字段：内部子元素逐个（tag/class/svg path d/尺寸）、
 *   全部 class 串、aria 全量、内部文本、box。
 */
const 扫开关 = (page, 场景) => page.evaluate((名) => {
  const 关键字 = /(开|关|显示|隐藏|吸附|自动|智能|联网|校验|引用|标注|特效|运镜|替换|网格)/;
  const 出 = [];
  const seen = new Set();
  for (const e of document.querySelectorAll('button,[role="button"],div,span')) {
    if (seen.has(e)) continue;
    const cs = getComputedStyle(e);
    if (cs.cursor !== 'pointer' && e.tagName !== 'BUTTON' && e.getAttribute('role') !== 'button') continue;
    const r = e.getBoundingClientRect();
    if (r.width < 12 || r.height < 12) continue;
    if (r.bottom < 0 || r.top > innerHeight || r.right < 0 || r.left > innerWidth) continue;
    if (e.querySelector('button,[role="button"]')) continue;                 // 只取最外层的可点元素
    const aria = e.getAttribute('aria-label') || e.getAttribute('title') || '';
    const 文字 = (e.innerText || '').replace(/\s+/g, ' ').trim();
    const cls = String(e.className || '');
    const svgs = [...e.querySelectorAll('svg')];
    const 像开关 = 关键字.test(aria) || 关键字.test(文字) || svgs.length >= 2
      || /switch|toggle|chip|segment|active|Slider/i.test(cls);
    if (!像开关) continue;
    seen.add(e);
    const 子 = [...e.children].map(c => {
      const q = c.getBoundingClientRect();
      const p = c.querySelector ? c.querySelector('path') : null;
      return {
        tag: c.tagName, cls: String(c.className).slice(0, 46),
        尺寸: [Math.round(q.width), Math.round(q.height)],
        pathd: p ? p.getAttribute('d').slice(0, 46) : null,
        文字: (c.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14),
      };
    });
    const paths = svgs.map(s => { const p = s.querySelector('path'); return { 尺寸: (() => { const q = s.getBoundingClientRect(); return [Math.round(q.width), Math.round(q.height)]; })(), pathd: p ? p.getAttribute('d').slice(0, 46) : null, 位置: (() => { const q = s.getBoundingClientRect(); return [Math.round(q.left - r.left), Math.round(q.top - r.top)]; })() }; });
    出.push({
      场景: 名, tag: e.tagName, 文字, aria, 光标: cs.cursor,
      禁用: { disabled: e.disabled === true, ariaDisabled: e.getAttribute('aria-disabled'), 不允许: cs.cursor === 'not-allowed' },
      不透明: cs.opacity, 背景: cs.backgroundColor,
      边框: cs.borderColor, 边框宽: cs.borderTopWidth,
      cls: cls.slice(0, 120),
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      子数: e.children.length, svg数: svgs.length, 子, paths,
      在节点内: !!e.closest('.react-flow__node'),
    });
  }
  出.sort((a, b) => (a.box[1] - b.box[1]) || (a.box[0] - b.box[0]));
  return 出;
}, 场景);

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

  const 全 = {};

  // ① 底栏（画布未选中任何东西时的状态）—— 网格吸附 / 隐藏节点连线两个对照在这
  记('\n════ ① 底栏与顶栏（未选中任何节点）════');
  const 基线 = await 扫开关(page, '底栏');
  记(`　候选 ${基线.length} 个`);
  for (const s of 基线) 记(`　　<${s.tag}> 文字「${s.文字}」aria=${JSON.stringify(s.aria)} box=${JSON.stringify(s.box)} 子数=${s.子数} svg数=${s.svg数} 光标=${s.光标} 禁用=${JSON.stringify(s.禁用)} 不透明=${s.不透明}`);
  for (const s of 基线) if (s.svg数 >= 1) 记(`　　　　└ svg 明细：${JSON.stringify(s.paths)}`);
  全.基线 = 基线;
  await page.screenshot({ path: EVID + 'eu1-底栏.png' });

  // ② 选中视频节点 → 参数面板里的「生成音频 ⓘ」两段选择器（第三个对照）
  记('\n════ ② 视频节点参数面板（生成音频两段选择器）════');
  if (!(await page.evaluate((id) => !!document.querySelector(`.react-flow__node[data-id="${id}"]`), 'v-v2hlWY4Br3'))) { await page.keyboard.press('Meta+0'); await page.waitForTimeout(2500); }
  记(`　平移视频节点：${await 平移到左上(page, 'v-v2hlWY4Br3')}`);
  const 落 = await 安全点(page, 'v-v2hlWY4Br3');
  if (落) {
    await page.mouse.click(落[0], 落[1]);
    await page.waitForTimeout(2500);
    const 选 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
    记(`　选中 ${JSON.stringify(选)}`);
    if (选.length === 1 && 选[0] === 'v-v2hlWY4Br3') {
      const 面板按钮 = await 扫开关(page, '视频节点参数面板');
      记(`　面板里候选 ${面板按钮.length} 个：`);
      for (const s of 面板按钮) {
        记(`　　<${s.tag}> 「${s.文字}」 box=${JSON.stringify(s.box)} 子数=${s.子数} svg数=${s.svg数} 边框=${s.边框} 边框宽=${s.边框宽} 背景=${s.背景}`);
        if (s.子.length) 记(`　　　└ 子元素：${JSON.stringify(s.子)}`);
      }
      全.面板 = 面板按钮;
      const 下拉 = await page.evaluate((i) => {
        const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
        for (const b of n.querySelectorAll('button')) { const x = (b.innerText || '').replace(/\s+/g, ' ').trim(); if (!x.includes('·')) continue; const r = b.getBoundingClientRect(); if (r.bottom < 0 || r.top > innerHeight) continue; return { 文字: x, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] }; }
        return null;
      }, 'v-v2hlWY4Br3');
      if (下拉) {
        await page.mouse.click(下拉.中心[0], 下拉.中心[1]);
        await page.waitForTimeout(2200);
        await page.screenshot({ path: EVID + 'eu1-视频面板.png' });
        const 面板开关 = await 扫开关(page, '视频参数面板已开');
        记(`　面板打开后候选 ${面板开关.length} 个：`);
        for (const s of 面板开关) 记(`　　<${s.tag}> 「${s.文字}」aria=${JSON.stringify(s.aria)} box=${JSON.stringify(s.box)} 子数=${s.子数} svg数=${s.svg数} 边框=${s.边框} 背景=${s.背景} cls=${s.cls.slice(0, 60)}`);
        全.面板开关 = 面板开关;
        await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
      }
    }
  }

  // ③ 音频节点大编辑器：联网搜索 / 自动校验素材 / 智能引用 AutoLink 三个开关（⚙ 里）
  记('\n════ ③ 音频大编辑器 ⚙ 里的开关 ════');
  await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
  await page.keyboard.press('Meta+0'); await page.waitForTimeout(2200);
  记(`　平移音频节点：${await 平移到左上(page, 'a-THmbuJXQj4')}`);
  const 落2 = await 安全点(page, 'a-THmbuJXQj4');
  if (落2) {
    await page.mouse.click(落2[0], 落2[1]);
    await page.waitForTimeout(2400);
    const 选 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
    记(`　选中 ${JSON.stringify(选)}`);
    if (选.length === 1 && 选[0] === 'a-THmbuJXQj4') {
      const 扫 = await 扫开关(page, '音频大编辑器');
      记(`　候选 ${扫.length} 个：`);
      for (const s of 扫) 记(`　　<${s.tag}> 「${s.文字}」aria=${JSON.stringify(s.aria)} box=${JSON.stringify(s.box)} 子数=${s.子数} svg数=${s.svg数} 边框=${s.边框} 背景=${s.背景} 光标=${s.光标} cls=${s.cls.slice(0, 70)}`);
      for (const s of 扫) if (s.svg数 >= 1) 记(`　　　└ svg：${JSON.stringify(s.paths)}`);
      全.音频 = 扫;
      await page.screenshot({ path: EVID + 'eu1-音频大编辑器.png' });
    }
  }

  结果.读数.全 = 全;
  记(`\n⭐ 三处合计候选 ${(全.基线 || []).length + (全.面板 || []).length + (全.面板开关 || []).length + (全.音频 || []).length} 个`);
  记('\n✅ 完成（未点任何开关）');
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
  console.log('\n=== 已写 tools/batchEU1.json ===');
}
