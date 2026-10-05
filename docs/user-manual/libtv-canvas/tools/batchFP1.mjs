// ⭐⭐⭐⭐⭐ Batch FP-1：**图片编辑器**（`imgEditor*` 184 条文案）探路
//
// 缺口（20-reference.md 第 1601 行自己写着）：
//   「⭐ 图片编辑器（`imgEditor*`，**本手册一个字都没写**）」
// 已知零散线索：`画笔` `画笔大小` `关闭标注` `确认裁剪` `确认抠图` `多角度生成`
// `请先完成 AI 水印设置` `所有宫格图片均审核未通过`，
// 以及**协作锁的第三个入口** `等待编辑权限…` `取消等待编辑权限` `ESC 取消`。
// 另有 18 枚编辑工具名（`扩图` `擦除` `抠图` …）在 FL 里被判定为「被复用的命名空间」，
// ⛔ 但**它们在界面上到底出不出现，从来没验过**。
//
// 本轮目标：**找到入口**，把界面结构一次读全，再跟文案表对账。
// ⛔ 安全边界：只打开面板 / 展开工具条；⛔ **不点任何会消耗积分的工具**
//   （扩图/重绘/高清放大/生成…),⛔ 不提交任何生成。
import { launch, closePromos, ORIGIN, 全页文字, 归一, 断言器, 关面板 } from './lib.mjs';
import { writeFileSync, readFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFP1.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = 断言器(记);

const i18n = JSON.parse(readFileSync(EVID + 'i18n-canvas.json', 'utf8')).表;

const 浏览器 = await launch();
const page = 浏览器.page;

/** 把「所有能点的东西」连框带名字一次读全 —— 进任何新面板都先跑这个。 */
const 全量控件 = () => page.evaluate(() => {
  const 归 = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const 可见 = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const 出 = [];
  const 见 = new Set();
  for (const el of document.querySelectorAll('button,[role="button"],[role="tab"],[role="radio"],[role="menuitem"],input,select,a')) {
    if (!可见(el)) continue;
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    const 名字 = 归(el.innerText) || el.getAttribute('aria-label') || el.getAttribute('title') || el.getAttribute('placeholder') || el.value || '';
    if (!名字) continue;
    const k = 名字 + '@' + Math.round(r.x) + ',' + Math.round(r.y);
    if (见.has(k)) continue;
    见.add(k);
    出.push({
      名: 名字.slice(0, 40), 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      tag: el.tagName, role: el.getAttribute('role'), aria: el.getAttribute('aria-label'), title: el.getAttribute('title'),
      字色: cs.color, 底色: cs.backgroundColor, opacity: cs.opacity,
      class: String(el.className || '').slice(0, 60),
    });
  }
  return 出;
});

/** 找出所有非底栏、非画布节点的浮层容器（编辑器一般在这种壳里）。 */
const 浮层 = () => page.evaluate(() => {
  const 归 = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const 壳 = [];
  for (const el of document.querySelectorAll('div,section,dialog')) {
    const r = el.getBoundingClientRect();
    if (!(r.width > 400 && r.height > 300)) continue;
    const cs = getComputedStyle(el);
    if (cs.position !== 'fixed' && cs.position !== 'absolute') continue;
    if (Number(cs.zIndex) < 20) continue;
    // 排除 react-flow 的节点容器
    if (el.closest('.react-flow__node')) continue;
    壳.push({ 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], z: cs.zIndex, position: cs.position, class: String(el.className || '').slice(0, 110), 文字: 归(el.innerText).slice(0, 260) });
  }
  // 只留最外层（父级不在列表里）
  return 壳.filter((a) => !壳.some((b) => b !== a && b.框[0] <= a.框[0] && b.框[1] <= a.框[1] && b.框[0] + b.框[2] >= a.框[0] + a.框[2] && b.框[1] + b.框[3] >= a.框[1] + a.框[3] && (b.框[2] * b.框[3]) > (a.框[2] * a.框[3])));
});

const 找 = (词, { 前缀 = false, 限 = null } = {}) => page.evaluate(([w, p, 限位]) => {
  for (const el of document.querySelectorAll('button,[role="button"],[role="tab"],[role="menuitem"],a')) {
    const t = (el.innerText || '').replace(/\s+/g, ' ').trim();
    if (p ? !t.startsWith(w) : t !== w) continue;
    const r = el.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) continue;
    if (限位 && (r.y < 限位[0] || r.y > 限位[1])) continue;
    const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2);
    const hb = document.elementFromPoint(x, y)?.closest('button,[role="button"],[role="tab"],[role="menuitem"],a');
    return { 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 点: [x, y], 命中: hb ? (hb.innerText || hb.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim().slice(0, 20) : null };
  }
  return null;
}, [词, 前缀, 限]);

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(13000);
  记('closePromos：' + JSON.stringify(await closePromos(page)).slice(0, 80));
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);

  // ── ① 先看图片节点被选中时，顶部工具条上有什么 ──
  记('—— ① 选中一个图片节点 ——');
  const 节点 = await page.evaluate(() => {
    for (const n of document.querySelectorAll('.react-flow__node')) {
      const r = n.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) continue;
      if ((n.getAttribute('data-id') || '').startsWith('i-')) return { id: n.getAttribute('data-id'), 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
    }
    return null;
  });
  记('   节点 ' + JSON.stringify(节点));
  if (节点) {
    await page.mouse.click(节点.框[0] + 节点.框[2] / 2, 节点.框[1] + 节点.框[3] / 2);
    await page.waitForTimeout(2000);
    const 选中 = await page.evaluate((id) => document.querySelector('.react-flow__node[data-id="' + id + '"]')?.className.includes('selected'), 节点.id);
    断言(选中, '图片节点选上了', { id: 节点.id, 选中 });
    await page.screenshot({ path: EVID + 'fp1-01-图片节点选中.png' });

    // 节点内部 / 参数条上的全部控件
    const 条 = await page.evaluate((id) => {
      const 归 = (s) => (s || '').replace(/\s+/g, ' ').trim();
      const n = document.querySelector('.react-flow__node[data-id="' + id + '"]');
      if (!n) return null;
      const r0 = n.getBoundingClientRect();
      const 出 = [];
      for (const el of n.querySelectorAll('button,[role="button"],input,a')) {
        const r = el.getBoundingClientRect();
        if (!(r.width > 0 && r.height > 0)) continue;
        出.push({ 名: (归(el.innerText) || el.getAttribute('aria-label') || el.getAttribute('title') || '').slice(0, 30), 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], aria: el.getAttribute('aria-label'), title: el.getAttribute('title') });
      }
      return { 节点框: [Math.round(r0.x), Math.round(r0.y), Math.round(r0.width), Math.round(r0.height)], 控件: 出 };
    }, 节点.id);
    R.读数.节点控件 = 条;
    记('   节点框 ' + JSON.stringify(条?.节点框));
    for (const c of 条?.控件 || []) 记('   · ' + JSON.stringify(c));
  }

  // ── ② ⤢：手册说它会弹出「居中的大编辑器」 ──
  记('—— ② 点 ⤢ ——');
  const 箭头 = await page.evaluate((id) => {
    const n = document.querySelector('.react-flow__node[data-id="' + id + '"]');
    if (!n) return null;
    const r0 = n.getBoundingClientRect();
    for (const el of n.querySelectorAll('button,[role="button"]')) {
      const r = el.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) continue;
      // ⤢ 通常在节点右上角，28×28 或 32×32
      if (r.width <= 34 && r.width >= 24 && (r0.y + r0.height - r.y) < 60 && r.x > r0.x + r0.width * 0.55) {
        const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2);
        const hb = document.elementFromPoint(x, y)?.closest('button,[role="button"]');
        return { 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 点: [x, y], 命中: hb ? (hb.getAttribute('aria-label') || hb.innerText || '').trim().slice(0, 20) : null };
      }
    }
    return null;
  }, 节点.id);
  记('   ⤢ 候选 ' + JSON.stringify(箭头));
  if (箭头) {
    const 前层 = (await 浮层()).length;
    await page.mouse.click(箭头.点[0], 箭头.点[1]);
    await page.waitForTimeout(3500);
    const 层 = await 浮层();
    R.读数.大编辑器浮层 = 层;
    记(`   浮层 ${前层} → ${层.length} 个`);
    for (const l of 层) 记('   # ' + JSON.stringify(l).slice(0, 700));
    断言(层.length > 前层, '⭐ 点 ⤢ 之后确实多出一个浮层', { 前层, 后: 层.length });
    await page.screenshot({ path: EVID + 'fp1-02-大编辑器.png' });
    const 控件 = await 全量控件();
    R.读数.大编辑器控件 = 控件;
    记(`   大编辑器里可见控件 ${控件.length} 枚`);
    for (const c of 控件) 记('   · ' + JSON.stringify(c));
  }

  // ── ③ 与文案表对账 ──
  记('—— ③ 与文案表对账 ——');
  const 文字 = await 全页文字(page, { 含透明: true });
  const 集 = new Set(文字.map(归一));
  const 组 = ['imgEditor', 'img', 'imageEditor', 'editor'];
  const 命中 = [];
  for (const [k, v] of Object.entries(i18n)) {
    if (!组.some((g) => k.toLowerCase().includes(g.toLowerCase()))) continue;
    if (集.has(归一(v))) 命中.push([k, v]);
  }
  R.读数.对账 = { 可见文字数: 文字.length, 命中数: 命中.length, 命中: 命中.slice(0, 60) };
  记(`   ⭐ img* 组命中 ${命中.length} 条（可见文字共 ${文字.length} 条）`);
  for (const [k, v] of 命中.slice(0, 60)) 记('   ✅ ' + k + ' = ' + v);

  const 十八 = ['扩图', '擦除', '抠图', '旋转', '旋转镜像', '裁剪', '补光', '打光', '重绘', '增强', '高清放大', '多角度', '标注',
    '文本生成器', '图片生成器', '视频生成器', '音频生成器', '角色生成器', '脚本生成器', '图片增强', '视频增强'];
  const 十八命中 = 十八.filter((w) => 集.has(归一(w)));
  R.读数.十八工具 = { 命中: 十八命中 };
  记('   ⭐⭐ 十八枚编辑工具命中 ' + 十八命中.length + '/' + 十八.length + '：' + 十八命中.join(' '));
  记(`—— 共跑了 ${断言.统计.次数} 条断言，失败 ${断言.统计.失败} 条 ——`);
} catch (e) {
  记('❌ ' + (e && e.message ? e.message : String(e)));
} finally {
  try { await 浏览器.browser.close(); } catch (e) { /* 关 */ }
  记('done');
}
