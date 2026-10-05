// ⭐⭐⭐⭐⭐ Batch FZ-3：把「新建画布」的命名框读全 —— 确认按钮到底在哪
//
// FZ-2 已经坐实三件事：
//   ① ⭐ 点 `aria="新建画布"` 的加号 ⇒ **弹出命名框**，
//      框里 `aria="画布名称"` 的输入框 `value` **已经是 `画布 64`**
//   ② ⭐⭐ 建后下拉**真的多了一项 `画布 64`**（63 → 64）
//   ③ ⭐⭐⭐ **空的、崭新的画布上仍然没有新手引导**
//      URL：projectId=59c3c1187a244cfab3c578019f7143e3，节点数 0
//
// ⛔ FZ-2 的失误（缺陷 500）：它按「按钮文案 ∈ {确定,创建,确认,保存,完成}」
//    找确认按钮，**在 role=dialog 里一个都没找到**，
//    于是 fallback 到「第一个非 disabled 按钮」⇒ **点到了「感知画布开始创作」**
//    ——那是 TV Director 的入口，⛔ 本不该点。
//    好在那个动作只是打开导演对话，没有提交任何生成。
//
// 本轮只回答一个问题：**命名框的确认/取消按钮在哪、长什么样**。
// ⛔ 纯读。不点任何按钮。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
// ⭐ 用刚建好的那张空画布，避免再新建一张
const 新画布 = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=59c3c1187a244cfab3c578019f7143e3`;
const 主画布 = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 断言: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFZ3.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = (名, 过, 明) => { R.断言.push({ 名, 过, 明 }); 记(`${过 ? '✅' : '❌'} ${名} —— ${明}`); };

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(新画布, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(7000);
  await closePromos(page);
  await page.waitForTimeout(3500);

  记(`当前：${page.url()}`);
  const 节点 = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  记(`节点数 ${节点}`);
  await page.screenshot({ path: resolve(EVID, 'fz3-1-新画布全屏.png') });

  // 空画布上有没有「双击画布 自由生成节点」这类引导芯片
  记('\n--- 空画布上的文字全量 ---');
  const 文字 = await page.evaluate(() => document.body.innerText);
  R.读数.空画布文字 = 文字;
  记(`  ${文字.replace(/\n+/g, ' | ').slice(0, 600)}`);

  // ── 打开下拉读命名框的**完整结构**
  记('\n--- 打开下拉，定位「画布名称」输入框 ---');
  await page.mouse.click(200, 24);
  await page.waitForTimeout(1800);

  const 定位 = await page.evaluate(() => {
    const i = document.querySelector('input[aria-label="画布名称"]');
    if (!i) return { 错: '没找到画布名称输入框（说明命名框不是常驻的）' };
    const r = i.getBoundingClientRect();
    // 往上找它的行容器，再往下扫这一行下面的所有元素
    let 行 = i;
    for (let k = 0; k < 5 && 行; k++) {
      const rr = 行.getBoundingClientRect();
      if (rr.height > 28 && rr.height < 90) break;
      行 = 行.parentElement;
    }
    const lr = 行 ? 行.getBoundingClientRect() : r;
    const 附近 = [];
    for (const e of document.querySelectorAll('button, [role="button"], a, input, div')) {
      const b = e.getBoundingClientRect();
      if (b.width < 8 || b.height < 8) continue;
      if (b.y + b.height < lr.y - 4 || b.y > lr.y + lr.height + 90) continue;
      if (b.x + b.width < lr.x - 60 || b.x > lr.x + lr.width + 200) continue;
      附近.push({ tag: e.tagName, 文: (e.innerText || e.value || '').trim().slice(0, 14),
        aria: e.getAttribute('aria-label'), type: e.getAttribute('type'),
        disabled: e.disabled === true,
        框: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)] });
    }
    return { 输入框框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      行框: [Math.round(lr.x), Math.round(lr.y), Math.round(lr.width), Math.round(lr.height)],
      行cls: (行?.className || '').toString().slice(0, 90),
      附近 };
  });
  R.读数.命名框结构 = 定位;
  if (定位.错) { 记(`  ⛔ ${定位.错}`); }
  else {
    记(`  「画布名称」输入框 @${定位.输入框框.join(',')}`);
    记(`  它所在行 @${定位.行框.join(',')} cls=${定位.行cls}`);
    记(`\n  这一行上下 90px 内的所有元素（${定位.附近.length} 个）：`);
    定位.附近.forEach((e) => 记(`   <${e.tag}${e.type ? ' type=' + e.type : ''}> 文「${e.文}」aria=${e.aria} disabled=${e.disabled} ${e.框.join(',')}`));
  }
  await page.screenshot({ path: resolve(EVID, 'fz3-2-命名框区域.png') });
  const clip = 定位.错 ? undefined : { x: Math.max(0, 定位.行框[0] - 20), y: Math.max(0, 定位.行框[1] - 30),
    width: 定位.行框[2] + 220, height: 定位.行框[3] + 80 };
  if (clip) await page.screenshot({ path: resolve(EVID, 'fz3-3-命名框特写.png'), clip });

  // ⭐ 再扫一遍：**整个下拉容器**里所有可点元素（这次按容器框，不按固定范围）
  记('\n--- 下拉容器内所有可点元素（按容器框过滤）---');
  const 容器 = await page.evaluate(() => {
    let 最佳 = null;
    for (const e of document.querySelectorAll('div')) {
      const r = e.getBoundingClientRect();
      if (r.height < 200 || r.x < 100 || r.x > 400) continue;
      const t = e.innerText || '';
      if (!/切换到画布|画布 63/.test(t)) continue;
      if (!最佳 || r.height < 最佳.h) 最佳 = { h: r.height, 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
    }
    return 最佳;
  });
  R.读数.容器 = 容器;
  记(`  容器：${JSON.stringify(容器)}`);
  if (容器) {
    const 可点 = await page.evaluate((框) => {
      const o = [];
      for (const e of document.querySelectorAll('button,[role="button"],a,input')) {
        const r = e.getBoundingClientRect();
        if (r.width < 6 || r.height < 6) continue;
        if (r.x + r.width < 框[0] - 6 || r.x > 框[0] + 框[2] + 6) continue;
        if (r.y + r.height < 框[1] - 6 || r.y > 框[1] + 框[3] + 6) continue;
        const 文 = (e.innerText || e.value || '').trim();
        if (/^切换到画布|^画布 \d+$/.test(文)) continue;      // ⛔ 排除 63 行
        o.push({ tag: e.tagName, 文: 文.slice(0, 14), aria: e.getAttribute('aria-label'),
          type: e.getAttribute('type'), disabled: e.disabled === true,
          cls: (e.className || '').toString().slice(0, 60),
          框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
      }
      return o;
    }, 容器.框);
    R.读数.容器可点 = 可点;
    记(`  排除 63 行之后还剩 ${可点.length} 个：`);
    可点.forEach((e) => 记(`   <${e.tag}> 文「${e.文}」aria=${e.aria} type=${e.type} disabled=${e.disabled} ${e.框.join(',')}\n       cls=${e.cls}`));
  }
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFZ3.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
