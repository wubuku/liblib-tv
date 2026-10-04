// Batch EL-1：验一个**已经写进手册的阴性结论**——
//   20-reference.md §「无文字按钮的识别办法」断言：
//   「高级设置滑块」[437,640,32,32] 和「展开/收起箭头」[521,498,28,28]
//   「都没有 aria、没有 [title]、没有悬停气泡，也没有任何 data-*」。
//
// ⭐⭐ 那个结论当初很可能也是用**叶子文本节点**判据得出的——
//   EK 批刚证明 Mantine 气泡容器带子元素、会被叶子过滤器整枚滤掉
//   （「画布小地图」「缩放选项」就是这么被读成「没有气泡」的）。
// ⇒ 本轮：(1) 用**修正后的判据**（class 含 Tooltip，或任意短文本 + 合理尺寸）重验；
//        (2) **先跑一枚阳性对照**，证明本轮判据在本页确实能读出气泡；
//        (3) **每枚无条件截图**（阴性结果也必须留证据）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEL1.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

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
  await page.waitForTimeout(3000);
  记(`开局坐标偏差：${JSON.stringify(await 核对坐标(page))}`);

  // ---- 选中图片节点 i-9nlG6HdjK2，让内联卡片展开
  const 图片 = await page.evaluate(() => {
    const el = document.querySelector('.react-flow__node[data-id="i-9nlG6HdjK2"]');
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
  });
  if (!图片) throw new Error('图片节点不在视口内');
  await page.mouse.click(图片[0], 图片[1]);
  await page.waitForTimeout(2500);
  const 选中了 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
  记(`点击图片节点后选中：${JSON.stringify(选中了)}`);

  // ---- 普查：把节点内所有「小尺寸可点容器」连同**全部属性**导出
  //      （不靠选择器猜，靠「尺寸像按钮」这条更弱的判据，漏网之鱼更少）
  const 普查 = await page.evaluate(() => {
    const 节点 = document.querySelector('.react-flow__node[data-id="i-9nlG6HdjK2"]');
    if (!节点) return [];
    const 出 = [];
    const 集 = new Set();
    for (const e of 节点.querySelectorAll('*')) {
      const r = e.getBoundingClientRect();
      if (r.width < 14 || r.width > 90 || r.height < 14 || r.height > 90) continue;
      // 圆角小方块或圆形才可能是按钮
      const cs = getComputedStyle(e);
      if (cs.borderRadius === '0px' && !/button/.test(e.tagName.toLowerCase())) continue;
      if (集.has(e)) continue; 集.add(e);
      const attrs = {};
      for (const a of e.attributes) attrs[a.name] = a.value;
      出.push({
        tag: e.tagName,
        cls: (e.className || '').toString().slice(0, 130),
        attrs,
        文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30),
        有效文字: (() => { // ⭐ 叶子文本 = 自己没有子元素但有文本节点的元素
          const has = [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
          const kid = [...e.children].some(c => (c.innerText || '').trim());
          return has && !kid ? e.innerText.trim().slice(0, 30) : '';
        })(),
        cursor: cs.cursor,
        opacity: cs.opacity,
        box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)],
        svg: [...e.querySelectorAll('path')].map(p => (p.getAttribute('d') || '').slice(0, 30))[0] || '',
      });
    }
    return 出;
  });
  记(`\n⭐ 节点内小尺寸可点容器 ${普查.length} 个（全属性已落盘）`);
  结果.读数.普查 = 普查;
  await page.screenshot({ path: EVID + 'el1-卡片展开.png' });

  // ---- 正向定位手册点名的两枚
  const 滑块 = 普查.find(x => x.svg.includes('M14 17H5M19 7h-9'));
  const 箭头 = 普查.find(x => /bg-panel-background/.test(x.cls) && /absolute right-2 top-2/.test(x.cls));
  记(`\n　手册点名的 高级设置滑块：${滑块 ? JSON.stringify({ tag: 滑块.tag, box: 滑块.box, svg: 滑块.svg, cursor: 滑块.cursor, opacity: 滑块.opacity }) : '❌ 没在本轮找到'}`);
  记(`　手册点名的 展开/收起箭头：${箭头 ? JSON.stringify({ tag: 箭头.tag, box: 箭头.box, cls: 箭头.cls, cursor: 箭头.cursor, opacity: 箭头.opacity }) : '❌ 没在本轮找到'}`);
  结果.读数.滑块 = 滑块 || null;
  结果.读数.箭头 = 箭头 || null;

  // ---- 修正后的气泡判据（**不要求叶子节点**）
  const 气泡 = () => page.evaluate(() => {
    const 出 = [];
    const 已 = new Set();
    for (const e of document.querySelectorAll('body *')) {
      const cls = (e.className || '').toString();
      const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
      const r = e.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) continue;
      if (/Tooltip|tooltip/.test(cls)) {
        const k = 'T|' + t + '|' + Math.round(r.left);
        if (已.has(k)) continue; 已.add(k);
        出.push({ 文本: t.slice(0, 60), cls: cls.slice(0, 46), Tip: true, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
        continue;
      }
      if (t && t.length <= 16 && r.height < 60 && r.width < 300) {
        const k = 'N|' + t + '|' + Math.round(r.left);
        if (已.has(k)) continue; 已.add(k);
        出.push({ 文本: t, cls: cls.slice(0, 46), Tip: false, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
      }
    }
    return 出;
  });

  const 避开 = [图片[0], 图片[1] - 240];
  const 试悬停 = async (目标, 标签) => {
    if (!目标) return { 标签, 缺失: true, 新: [] };
    await page.mouse.move(避开[0], 避开[1]);
    await page.waitForTimeout(1200);
    const 前 = await 气泡();
    await page.mouse.move(目标.中心[0] - 3, 目标.中心[1] - 3);
    await page.waitForTimeout(260);
    await page.mouse.move(目标.中心[0], 目标.中心[1]);
    await page.waitForTimeout(2800);
    const 后 = await 气泡();
    const 新 = 后.filter(y => !前.some(x => x.文本 === y.文本 && Math.abs(x.box[0] - y.box[0]) < 4));
    记(`\n　[${标签}] 悬停 box=${JSON.stringify(目标.box)} → 新出现 ${新.length} 个：${JSON.stringify(新.map(n => [n.文本, n.box, n.Tip ? 'Tip' : '普通']))}`);
    const bx = 目标.中心[0], by = 目标.中心[1];
    await page.screenshot({ path: EVID + `el1-悬停-${标签}.png` }); // ⭐ 无条件全视口截图
    await page.screenshot({ path: EVID + `el1-悬停-${标签}-近景.png`, clip: { x: Math.max(0, Math.min(1440 - 700, bx - 350)), y: Math.max(0, Math.min(810 - 420, by - 300)), width: 700, height: 420 } });
    return { 标签, box: 目标.box, 新: 新.map(n => n.文本), 新全: 新 };
  };

  // ---- ⭐ 阳性对照：手册明写「视频节点上的 提示词优化」等有气泡。
  //      先在**图片节点**上找一枚手册记过有气泡的（`翻译提示词` / `预设`），
  //      证明本轮判据在这页确实读得出东西 —— 否则「读不出」无法区分
  //      「真没有」和「判据又坏了」。
  const 阳性目标 = 普查.find(x => /翻译提示词|预设/.test(x.文字)) || 普查.find(x => x.文字 && x.文字.length <= 8);
  记(`\n⭐ 阳性对照目标：${阳性目标 ? JSON.stringify({ 文字: 阳性目标.文字, box: 阳性目标.box }) : '没找到带文字的小控件'}`);
  结果.读数.阳性对照 = await 试悬停(阳性目标, '阳性对照');

  结果.读数.滑块悬停 = await 试悬停(滑块, '高级设置滑块');
  结果.读数.箭头悬停 = await 试悬停(箭头, '展开收起箭头');

  记('\n✅ 三轮悬停都已留下全视口截图 + 近景截图（含阴性）');
  落盘(结果);
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  try { 记(`⭐ 收尾坐标偏差：${JSON.stringify(await 核对坐标(page))}`); } catch {}
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEL1.json ===');
}
