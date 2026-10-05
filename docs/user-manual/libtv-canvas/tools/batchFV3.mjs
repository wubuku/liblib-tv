// ⭐⭐⭐⭐⭐ Batch FV-3：上界面实拍主画布所有节点的标题，坐实 `{index}` 到底是什么
//
// FQ-2 当时的读数是「两个音频节点都写着 1、两个图片节点都写着 2」，
// 由此排除了「同名实例序号」，剩下两种可能都判了 📖 未验：
//   A. 同一个 index 被多个节点复用
//   B. index 是**建节点时的画布全局计数**，之后不再自增
//
// ⭐ 但 FV-2 在文案表里挖出了另一半证据：手册自己别的批次里记过
// `音频节点 6` / `音频节点 7` / `视频节点 18` / `导演台 1` / `导演台 3`。
// ⇒ **同一张画布上 1~18 各种数字都出现过** ⇒ 强烈指向 B（全局递增）。
//
// 本轮直接读当前主画布：把 12 个节点的标题逐个读出来，看数字怎么分布。
// ⛔ 只读 DOM，不点任何按钮，不新建节点。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFV3.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(14000);
  await closePromos(page);

  const 读 = await page.evaluate(() => {
    const out = [];
    for (const el of document.querySelectorAll('.react-flow__node')) {
      const cls = [...el.classList].find((c) => c.startsWith('react-flow__node-')) || '';
      const id = (el.getAttribute('data-id') || '').trim();
      const b = el.getBoundingClientRect();
      // 标题取最靠上的那行非空文本节点
      let 标题 = '';
      for (const t of el.querySelectorAll('*')) {
        if (t.children.length) continue;
        const s = (t.textContent || '').trim();
        if (!s || s.length > 24) continue;
        const r = t.getBoundingClientRect();
        if (r.top < b.top + 44 && (!标题 || r.top < 标题.top)) 标题 = { 文: s, top: r.top };
      }
      out.push({
        id, 类型: cls.replace('react-flow__node-', ''),
        标题: 标题 ? 标题.文 : '', 数字: 标题 ? (标题.文.match(/(\d+)\s*$/) || [])[1] || '' : '',
        位置: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
      });
    }
    return out;
  });

  R.读数.节点 = 读;
  记(`主画布读到 ${读.length} 个节点\n`);
  记('| 类型 | 标题逐字 | 数字 | 位置 |');
  记('|---|---|---|---|');
  const 按数字 = [];
  for (const n of 读.sort((a, b) => (+a.数字 || 0) - (+b.数字 || 0))) {
    记(`| ${n.类型} | \`${n.标题}\` | ${n.数字 || '—'} | ${n.位置.join(',')} |`);
    if (n.数字) 按数字.push(+n.数字);
  }
  记('');
  记(`有数字的节点 ${按数字.length} 个，数字分别是：${按数字.join(' / ')}`);
  const 重复 = 按数字.filter((v, i) => 按数字.indexOf(v) !== i);
  记(重复.length
    ? `⚠️ 有重复数字：${[...new Set(重复)].join(' / ')} ⇒ 不是全局唯一序号`
    : `✅ **数字无重复** ⇒ 与「建节点时的画布全局计数」一致`);
  记(`极差：${Math.min(...按数字)} ~ ${Math.max(...按数字)}`);
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFV3.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
