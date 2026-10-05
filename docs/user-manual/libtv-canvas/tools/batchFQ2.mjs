// ⭐⭐⭐⭐⭐ Batch FQ-2：FQ-1 撞出三块新大陆，逐个量
//
// FQ-1 的读数（本轮全部要在这一批坐实）：
//   ① 「脚本 NEW」**真的能建**，class = `react-flow__node-script-v2`
//      ⇒ 前缀 `scriptV2*` 就是这个节点，93 条文案第一次有了归属对象
//      ⇒ 建完页面上出现「脚本生成器」「尝试：」「剧本生成分镜脚本」
//         （= `scriptV2NodeScriptStoryboardGenerate`），危险按钮 0 枚，没自动开跑
//   ② ⭐⭐⭐ **class 名就是节点类型** —— 测试画布上量到主画布**根本没有**的三种：
//        `react-flow__node-video-clip`     × 3   ←「智能剪辑」
//        `react-flow__node-shot-breakdown`× 3   ←「分镜拆解 / 逐帧拉片」
//        `react-flow__node-script-v2`     × 1   ← FQ-1 建的
//      ⇒ `clip*` 348 条（文案表最大的一块之一）第一次有了落点
//   ③ 主画布全页（含透明）**一条「续写」都没有** ⇒ 智能续写不在默认状态里
//
// ⛔ 安全边界（同 FQ-1，且更严）：
//   ⛔ 不点「批量生成分镜」/「批量生视频」/「一键合成全部提示词」/「重新生成脚本」
//      /「批量生成资产图」/「确认续写」/「下载」/「同意并使用」—— 每一个都消耗积分或要签协议
//   ⛔ 不点任何会**提交生成**的按钮；只读、只量、只点页签切换
//   ⛔ 页签切换（脚本生成器 / 自己编写分镜脚本 这类）**不算提交**，可以点，但点完先量再决定
import { launch, closePromos, ORIGIN, 全页文字, 归一, 断言器, 量浮层 } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const 测试画布 = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=a4ef3de0cdca4977ba45b373eb5165b5`;
const HERE = new URL('.', import.meta.url).pathname;
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFQ2.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = 断言器(记);

const 浏览器 = await launch();
const page = 浏览器.page;

/** ⛔ 每一步之后都扫一遍危险按钮，只看不做。 */
const 危险 = ['批量生成分镜', '批量生视频', '一键合成全部提示词', '重新生成脚本', '批量生成资产图', '生成资产图', '确认续写', '下载', '同意并使用', '开始生成', '立即生成'];
async function 扫危险(标签) {
  const 命中 = await page.evaluate((黑) => {
    const 归 = (s) => (s || '').replace(/\s+/g, '');
    return [...document.querySelectorAll('button,[role="button"]')].map((b) => {
      const r = b.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) return null;
      const t = 归(b.innerText) || 归(b.getAttribute('aria-label')) || 归(b.title);
      if (!t || !黑.some((k) => t.includes(归(k)))) return null;
      const cs = getComputedStyle(b);
      return { 文字: t.slice(0, 24), 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 禁用: b.disabled === true, opacity: Number(cs.opacity).toFixed(2), cursor: cs.cursor };
    }).filter(Boolean);
  }, 危险);
  记(`   ⛔ ${标签}：危险按钮 ${命中.length} 枚 ${JSON.stringify(命中)}`);
  return 命中;
}

/** 量一个节点：class / 框 / 里面所有可点元素 + 全文。 */
async function 量节点(前缀) {
  return page.evaluate((pfx) => {
    const 归 = (s) => (s || '').replace(/\s+/g, ' ');
    const n = [...document.querySelectorAll('.react-flow__node')].find((e) => String(e.className).includes(pfx));
    if (!n) return null;
    const r = n.getBoundingClientRect();
    const 点 = [...n.querySelectorAll('button,[role="button"],[role="tab"],input,textarea,select')].map((b) => {
      const br = b.getBoundingClientRect();
      if (!(br.width > 0 && br.height > 0)) return null;
      const cs = getComputedStyle(b);
      return {
        文字: 归(b.innerText) || 归(b.getAttribute('aria-label')) || 归(b.title) || 归(b.placeholder) || '',
        框: [Math.round(br.x), Math.round(br.y), Math.round(br.width), Math.round(br.height)],
        点: [Math.round(br.x + br.width / 2), Math.round(br.y + br.height / 2)],
        禁用: b.disabled === true, opacity: Number(cs.opacity).toFixed(2), cursor: cs.cursor,
        tag: b.tagName.toLowerCase(), role: b.getAttribute('role') || '',
      };
    }).filter(Boolean);
    return {
      id: n.getAttribute('data-id'), class: String(n.className).slice(0, 90),
      框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      全文: 归(n.innerText).slice(0, 900), 可点: 点,
    };
  }, 前缀);
}

try {
  await page.goto(测试画布, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(14000);
  记('closePromos：' + JSON.stringify(await closePromos(page)).slice(0, 80));
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);

  R.读数.zoom = await page.evaluate(() => {
    const v = document.querySelector('.react-flow__viewport');
    return v ? v.style.transform : null;
  });
  记('   ⌘0 后 viewport transform = ' + JSON.stringify(R.读数.zoom));

  R.读数.全部节点 = await page.evaluate(() => {
    const 集 = {};
    for (const n of document.querySelectorAll('.react-flow__node')) {
      const r = n.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) continue;
      const m = String(n.className).match(/react-flow__node-([a-z0-9-]+)/);
      const 型 = m ? m[1] : '(无)';
      集[型] = 集[型] || { 个数: 0, 例: [] };
      集[型].个数 += 1;
      if (集[型].例.length < 3) 集[型].例.push({ id: n.getAttribute('data-id'), 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
    }
    return 集;
  });
  记('   ⭐ 测试画布上的节点类型分布 ' + JSON.stringify(R.读数.全部节点, null, 1));
  断言(Object.keys(R.读数.全部节点).includes('script-v2'), '测试画布上有 script-v2 节点（FQ-1 建的那个还在）', Object.keys(R.读数.全部节点));
  断言(Object.keys(R.读数.全部节点).includes('video-clip'), '测试画布上有 video-clip 节点（主画布没有）', Object.keys(R.读数.全部节点));
  断言(Object.keys(R.读数.全部节点).includes('shot-breakdown'), '测试画布上有 shot-breakdown 节点（主画布没有）', Object.keys(R.读数.全部节点));

  // ── ① 脚本 V2 节点
  记('=== ① 脚本 V2 节点 ===');
  R.读数.脚本节点 = await 量节点('node-script-v2');
  记('   ' + JSON.stringify({ 框: R.读数.脚本节点?.框, 全文: R.读数.脚本节点?.全文 }).slice(0, 700));
  记('   可点元素 ' + JSON.stringify(R.读数.脚本节点?.可点));
  await 扫危险('脚本节点量完');

  // ── ② video-clip 节点（智能剪辑）
  记('=== ② video-clip 节点 ===');
  R.读数.clip节点 = await 量节点('node-video-clip');
  记('   ' + JSON.stringify({ 框: R.读数.clip节点?.框, 全文: R.读数.clip节点?.全文 }).slice(0, 700));
  记('   可点元素 ' + JSON.stringify(R.读数.clip节点?.可点));
  await 扫危险('clip 节点量完');

  // ── ③ shot-breakdown 节点
  记('=== ③ shot-breakdown 节点 ===');
  R.读数.拆解节点 = await 量节点('node-shot-breakdown');
  记('   ' + JSON.stringify({ 框: R.读数.拆解节点?.框, 全文: R.读数.拆解节点?.全文 }).slice(0, 700));
  记('   可点元素 ' + JSON.stringify(R.读数.拆解节点?.可点));
  await 扫危险('shot-breakdown 量完');

  // ── ④ 全页文字 vs 三组文案
  const 全 = await 全页文字(page, { 含透明: true });
  R.读数.全页文字 = 全;
  记(`   全页（含透明）文本 ${全.length} 条`);

  writeFileSync(HERE + 'batchFQ2-pages.json', JSON.stringify(全, null, 1));
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFQ2.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
