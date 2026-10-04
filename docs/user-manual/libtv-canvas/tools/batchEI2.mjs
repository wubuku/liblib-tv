// Batch EI-2：「转分镜组」在界面上找不到 —— 先确认**渲染它的那段代码有没有被加载**。
//
// EI-1 已建立多选（2 个 id 都在 selected 里），组操作条却整条没出现。
// 三种可能，逐个排：
//   ① 渲染代码没被加载（chunk 没进这个页面的依赖图）
//   ② 渲染了但被条件挡住（`!aF && !aG && !aN && targetNodeIds.length>=2` 之类）
//   ③ 渲染了但我找不到（它不是 button）
//
// 本步：查运行时已加载的 script 列表里有没有那段代码的证据（chunk id / 关键字符串）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchEI2.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {} };

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6500 });
  await closePromos(page);
  await page.waitForTimeout(1200);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1500);

  // ① 建立多选（2 个图片节点）
  const 点 = await page.evaluate(() => {
    const out = {};
    for (const id of ['i-9nlG6HdjK2', 'i-sODTbgLUm1']) {
      const el = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      const r = el.getBoundingClientRect();
      out[id] = [Math.round(r.left + r.width / 2), Math.round(r.top + 20)];
    }
    return out;
  });
  await page.mouse.click(点['i-9nlG6HdjK2'][0], 点['i-9nlG6HdjK2'][1]);
  await page.waitForTimeout(700);
  await page.keyboard.down('Shift');
  await page.mouse.click(点['i-sODTbgLUm1'][0], 点['i-sODTbgLUm1'][1]);
  await page.keyboard.up('Shift');
  await page.waitForTimeout(1500);

  const 选中 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
  结果.读数.选中 = 选中;
  console.log('选中:', JSON.stringify(选中));

  // ② ⭐ 全页搜「转分镜组」四个字
  const 找字 = await page.evaluate(() => {
    const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const 命中 = [];
    let n;
    while ((n = w.nextNode())) {
      const t = (n.nodeValue || '');
      if (/转分镜组|解组|整组执行|批量下载|添加到工具箱/.test(t)) {
        const p = n.parentElement;
        const r = p.getBoundingClientRect();
        命中.push({ 文本: t.trim().slice(0, 20), tag: p.tagName, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 可见: r.width > 0 && r.height > 0 });
      }
    }
    return 命中;
  });
  结果.读数.找字 = 找字;
  console.log('\n═══ 组操作条那几项文字的命中 ═══');
  for (const h of 找字) console.log(`  「${h.文本}」<${h.tag}> box=${JSON.stringify(h.box)} 可见=${h.可见}`);

  // ③ 查已加载的 script 里有没有 groupConvertToStoryboard
  const 加载 = await page.evaluate(async () => {
    const urls = [...document.querySelectorAll('script[src]')].map(s => s.src);
    const 命中url = [];
    for (const u of urls) {
      if (!/_next|\.js/.test(u)) continue;
      命中url.push(u.split('/').pop().slice(0, 40));
    }
    return { script数: urls.length, 名单: 命中url.slice(0, 12) };
  });
  结果.读数.已加载script = 加载;
  console.log(`\n已加载 script ${加载.script数} 个，抽样：${JSON.stringify(加载.名单)}`);

  // ④ ⭐ 直接在运行时全局找：Next 的 chunk 表里有没有这段代码
  const 运行时 = await page.evaluate(() => {
    // 找 React Flow 的多选工具条容器（它有 data- 属性或特定 class）
    const 候选 = [...document.querySelectorAll('div')].filter(e => {
      const r = e.getBoundingClientRect();
      if (r.width < 200 || r.height < 30 || r.height > 80) return false;
      const t = (e.innerText || '');
      return /整组执行|转分镜组|解组|排列/.test(t);
    }).map(e => {
      const r = e.getBoundingClientRect();
      return { cls: e.className.toString().slice(0, 90), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 文本: (e.innerText || '').replace(/\n/g, ' / ').slice(0, 100) };
    });
    return 候选;
  });
  结果.读数.工具条容器 = 运行时;
  console.log(`\n═══ 疑似工具条容器 ${运行时.length} 个 ═══`);
  for (const c of 运行时) console.log(`  box=${JSON.stringify(c.box)} 文本=${c.文本}\n    cls=${c.cls}`);

  await page.screenshot({ path: 'tools/.evidence/ei2-多选后的画面.png' });
  落盘(结果);
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEI2.json ===');
}
