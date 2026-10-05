// ⭐⭐⭐⭐⭐ Batch FP-2：把 FP-1 那个「误点」变成正式读数，并找到**真正的 ⤢**
//
// FP-1 的教训（缺陷 461）：
//   我按「在节点右上角、尺寸 24~34」去找 ⤢，判定式写成 `(r0.y + r0.height - r.y) < 60`
//   —— 图片节点**折叠时只有 169 高**，而参数条在 y=657，远在节点框之下，
//   于是这个不等式**恒为真**，我点中的其实是**「预设」**按钮（落点自证读回「预设」才发现）。
//   ⭐ 但这个「误点」撞出了一个手册完全没写的东西：**预设面板（21 张卡、两栏三组）**。
//
// 本轮三件事：
//   ① 参数条逐枚读全（含四枚无名按钮：SVG 形状 + 悬停气泡）
//   ② 「预设」面板精确读数（分组 / 卡片框 / 副标题 / 灰态 / 蓝点标记）
//   ③ ⛔ 复核 FL 的十八枚编辑工具名在这两个面板里**到底出不出现**
//
// ⛔ 安全边界：⛔ 不点任何一张预设卡（= 提交生成）；⛔ 不点「生成」/「⚡」；
//   只开面板、悬停读气泡、开关面板。
import { launch, closePromos, ORIGIN, 全页文字, 归一, 断言器 } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFP2.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = 断言器(记);

const 浏览器 = await launch();
const page = 浏览器.page;

const 悬停气泡 = async (x, y) => {
  await page.mouse.move(x - 60, y);
  await page.waitForTimeout(250);
  await page.mouse.move(x, y);
  await page.waitForTimeout(1600);
  return page.evaluate(() => [...document.querySelectorAll('[role="tooltip"],.mantine-Tooltip-tooltip,[class*="Tooltip"]')].filter((e) => {
    const r = e.getBoundingClientRect();
    return r.width > 30 && r.height > 10 && e.innerText && e.innerText.trim();
  }).map((e) => { const r = e.getBoundingClientRect(); return { 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 文字: e.innerText.replace(/\s+/g, ' ').trim().slice(0, 90) }; }));
};

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(13000);
  记('closePromos：' + JSON.stringify(await closePromos(page)).slice(0, 80));
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);

  // ── ① 选图片节点，把参数条逐枚读全 ──
  记('—— ① 图片节点的参数条 ——');
  const 节点 = await page.evaluate(() => {
    for (const n of document.querySelectorAll('.react-flow__node')) {
      const r = n.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) continue;
      if ((n.getAttribute('data-id') || '').startsWith('i-')) return { id: n.getAttribute('data-id'), 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
    }
    return null;
  });
  await page.mouse.click(节点.点[0], 节点.点[1]);
  await page.waitForTimeout(2000);
  断言(await page.evaluate((id) => document.querySelector('.react-flow__node[data-id="' + id + '"]')?.className.includes('selected'), 节点.id), '图片节点选上了');

  const 条 = await page.evaluate(() => {
    const 归 = (s) => (s || '').replace(/\s+/g, ' ').trim();
    const 可见 = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    // 参数条 = 视口下半部分、与选中节点同列的一排按钮
    const 出 = [];
    for (const el of document.querySelectorAll('button,[role="button"]')) {
      if (!可见(el)) continue;
      const r = el.getBoundingClientRect();
      if (r.y < 600 || r.y > 800) continue;
      const svg = el.querySelector('svg');
      const p = svg ? [...svg.querySelectorAll('path')].map((x) => (x.getAttribute('d') || '').slice(0, 28)).join('|').slice(0, 90) : null;
      出.push({
        名: (归(el.innerText) || el.getAttribute('aria-label') || el.getAttribute('title') || '').slice(0, 30),
        框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        aria: el.getAttribute('aria-label'), title: el.getAttribute('title'),
        灰: getComputedStyle(el).opacity, 字色: getComputedStyle(el).color,
        svg数: el.querySelectorAll('svg').length, path指纹: p,
        子: [...el.children].map((c) => c.tagName + '.' + String(c.className || '').slice(0, 26)).slice(0, 4),
      });
    }
    return 出;
  });
  R.读数.参数条 = 条;
  记(`   参数条可见控件 ${条.length} 枚`);
  for (const c of 条) 记('   · ' + JSON.stringify(c));

  // 逐枚悬停，给四枚无名按钮起名字
  const 无名 = 条.filter((c) => !c.名 && c.框[2] >= 24);
  for (const c of 无名.slice(0, 6)) {
    const 泡 = await 悬停气泡(c.框[0] + c.框[2] / 2, c.框[1] + c.框[3] / 2);
    记(`   ⭐ 悬停 [${c.框}] → ${JSON.stringify(泡.map((b) => b.文字))}`);
    R.读数.悬停 = R.读数.悬停 || {};
    R.读数.悬停[c.框.join(',')] = 泡.map((b) => b.文字);
  }
  await page.screenshot({ path: EVID + 'fp2-01-参数条全貌.png' });

  // ── ② 「预设」面板：精确读数 ──
  记('—— ② 预设面板 ——');
  const 预设 = 条.find((c) => c.aria === '预设' || c.名 === '预设');
  断言(!!预设, '参数条上找得到「预设」按钮', 条.map((c) => c.名 || '(无名)'));
  await page.mouse.click(预设.框[0] + 预设.框[2] / 2, 预设.框[1] + 预设.框[3] / 2);
  await page.waitForTimeout(2500);

  const 面板 = await page.evaluate(() => {
    const 归 = (s) => (s || '').replace(/\s+/g, ' ').trim();
    const 可见 = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    // 分组标题：短、没有卡片底色、字号较大的文字节点
    const 标题 = [];
    for (const el of document.querySelectorAll('div,span,h3,p')) {
      if (!可见(el)) continue;
      const t = 归(el.innerText);
      if (!t || t.length > 8 || /生成|调节|分镜|视图|校|设定|推演/.test(t) === false) continue;
      const r = el.getBoundingClientRect();
      if (r.x < 200 || r.x > 900 || r.y < 100 || r.y > 700) continue;
      标题.push({ 字: t, 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 字号: getComputedStyle(el).fontSize, 字重: getComputedStyle(el).fontWeight });
    }
    // 卡片：h-[52px] 那一排
    const 卡片 = [];
    for (const el of document.querySelectorAll('button,[role="button"]')) {
      if (!可见(el)) continue;
      const r = el.getBoundingClientRect();
      if (Math.round(r.height) !== 52 || r.width < 150) continue;
      const cs = getComputedStyle(el);
      const 小圆 = el.querySelector('span.rounded-full,span[class*="rounded-full"]');
      卡片.push({
        名: 归(el.innerText).slice(0, 60),
        框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        opacity: cs.opacity, cursor: cs.cursor,
        蓝点: 小圆 ? { 文字: 归(小圆.innerText), 底色: getComputedStyle(小圆).backgroundColor, 框: [Math.round(小圆.getBoundingClientRect().x), Math.round(小圆.getBoundingClientRect().y), Math.round(小圆.getBoundingClientRect().width), Math.round(小圆.getBoundingClientRect().height)] } : null,
      });
    }
    return { 标题, 卡片 };
  });
  R.读数.预设面板 = 面板;
  记(`   分组标题 ${面板.标题.length} 个：${面板.标题.map((t) => t.字).join(' / ')}`);
  记(`   卡片 ${面板.卡片.length} 张`);
  for (const c of 面板.卡片) 记('   · ' + JSON.stringify(c));
  断言(面板.卡片.length >= 15, '⭐ 预设面板是一张「卡片墙」，卡片 ≥15 张', 面板.卡片.length);
  const 灰 = 面板.卡片.filter((c) => Number(c.opacity) < 0.6);
  R.读数.灰态 = { 灰数: 灰.length, 总数: 面板.卡片.length };
  断言(灰.length === 面板.卡片.length, '⭐⭐ 全部卡片都是灰态（opacity 0.45）—— 因为节点里没有图', { 灰: 灰.length, 总: 面板.卡片.length });
  await page.screenshot({ path: EVID + 'fp2-02-预设面板.png' });

  // 面板外壳
  const 壳 = await page.evaluate(() => {
    const 归 = (s) => (s || '').replace(/\s+/g, ' ');
    for (const el of document.querySelectorAll('div')) {
      const t = 归(el.innerText);
      if (!t.includes('分镜叙事') || !t.includes('质感调节') || !t.includes('空间与机位')) continue;
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      return { 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], z: cs.zIndex, position: cs.position, class: String(el.className || '').slice(0, 110) };
    }
    return null;
  });
  R.读数.预设外壳 = 壳;
  记('   外壳 ' + JSON.stringify(壳));
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);

  // ── ③ ⛔ 复核十八枚编辑工具名 ──
  记('—— ③ 十八枚工具名复核 ——');
  const 十八 = ['扩图', '擦除', '抠图', '旋转', '旋转镜像', '裁剪', '补光', '打光', '重绘', '增强', '高清放大', '多角度', '标注',
    '文本生成器', '图片生成器', '视频生成器', '音频生成器', '角色生成器', '脚本生成器', '图片增强', '视频增强'];
  const 文字 = await 全页文字(page, { 含透明: true });
  const 集 = new Set(文字.map(归一));
  const 命中 = 十八.filter((w) => 集.has(归一(w)));
  R.读数.十八工具 = { 命中, 总: 十八.length, 可见文字数: 文字.length };
  记(`   ⭐⭐ 十八枚命中 ${命中.length}/${十八.length}：${命中.join(' ') || '(一条都没有)'}`);
  断言(命中.length === 0, '⭐⭐⭐ 「扩图/擦除/抠图…」这 18 枚在界面上**一条都不出现** —— FL 的更正得到运行时确认', 命中);

  记(`—— 共跑了 ${断言.统计.次数} 条断言，失败 ${断言.统计.失败} 条 ——`);
} catch (e) {
  记('❌ ' + (e && e.message ? e.message : String(e)));
} finally {
  try { await 浏览器.browser.close(); } catch (e) { /* 关 */ }
  记('done');
}
