// ⭐⭐⭐⭐⭐ Batch FV-4：验一个可证伪的预测 —— 标题数字 = 该类型在「添加节点」面板里的序号
//
// FV-3 实拍主画布 12 个节点，标题数字是：
//     文本节点 1  音频节点 1  脚本 V2 1
//     图片节点 2
//     视频节点 3  智能剪辑 4  导演台 5
// ⇒ 数字**不唯一**（1 出现 5 次），所以「画布全局递增」被实测排除。
//
// ⭐⭐⭐ 但它排出了另一个极漂亮的规律：
//     文本 1 / 图片 2 / 视频 3 / 智能剪辑 4 / 导演台 5
//     —— **正好是「添加节点」面板里从上到下的第 N 项**（面板顺序见
//     M-85 实测：全部、文本、图片、视频、智能剪辑、导演台、逐帧拉片、音频、脚本、剧本）。
//
// 这是个**可证伪**的预测：打开添加节点面板读出真实顺序，比对即可。
// ⛔ 只读：打开面板 → 读文字 → Esc 关掉。不建任何节点，不点任何生成按钮。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFV4.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(14000);
  await closePromos(page);

  // 先关掉右侧可能开着的抽屉，免得它压住「添加节点」面板
  await page.evaluate(() => {
    for (const b of document.querySelectorAll('.mantine-Drawer-inner [aria-label="关闭"], .mantine-Drawer-close')) b.click();
  });
  await page.waitForTimeout(600);

  // 基线：面板不存在
  const 基线 = await page.evaluate(() => document.querySelectorAll('[role="menu"], [role="listbox"]').length);
  记(`基线：role=menu/listbox 元素 ${基线} 个`);

  // 打开添加节点面板：双击画布空白处（建节点不消耗积分，且双击只开面板）
  const 空白 = await page.evaluate(() => {
    // 找一个既没节点也没面板的点
    for (let x = 1200; x > 200; x -= 40) {
      for (let y = 700; y > 120; y -= 40) {
        const e = document.elementFromPoint(x, y);
        if (e && e.classList.contains('react-flow__pane')) return [x, y];
      }
    }
    return null;
  });
  if (!空白) { 记('⛔ 没找到画布空白处，放弃'); }
  else {
    记(`画布空白点：${空白.join(',')}`);
    await page.mouse.dblclick(空白[0], 空白[1]);
    await page.waitForTimeout(1200);

    const 面板 = await page.evaluate(() => {
      const out = [];
      for (const el of document.querySelectorAll('[role="menu"] *, [role="menuitem"], [class*="Dropdown"] *, [class*="Popover"] *')) {
        const s = (el.innerText || '').trim();
        if (!s || s.length > 30) continue;
        const r = el.getBoundingClientRect();
        if (r.width < 8 || r.height < 8) continue;
        out.push({ 文字: s, x: Math.round(r.x), y: Math.round(r.y), h: Math.round(r.height) });
      }
      // 同一行的只留最长的那条
      const seen = new Map();
      for (const o of out) {
        const key = o.y;
        if (!seen.has(key) || seen.get(key).文字.length < o.文字.length) seen.set(key, o);
      }
      return [...seen.values()].sort((a, b) => a.y - b.y);
    });
    R.读数.面板 = 面板;
    记(`\n添加节点面板读到 ${面板.length} 行：\n`);
    记('| # | 逐字 | y |');
    记('|---|---|---|');
    面板.forEach((p, i) => 记(`| ${i + 1} | \`${p.文字}\` | ${p.y} |`));

    const 关前 = 面板.length;
    await page.keyboard.press('Escape');
    await page.waitForTimeout(800);
    const 关后 = await page.evaluate(() => document.querySelectorAll('[role="menu"]').length);
    记(`\nEsc 后面板数 ${关前} → ${关后}（${关后 === 0 ? '✅ 关掉了' : '⛔ 没关掉'}）`);

    // ── 比对 ──
    记('\n=== 预测比对：标题数字 vs 面板序号 ===');
    const 实测 = { 文本: 1, 图片: 2, 视频: 3, 智能剪辑: 4, 导演台: 5, 音频: 1 };
    const 面板名 = 面板.map((p) => p.文字);
    let 对 = 0, 错 = [];
    for (const [类型, 数字] of Object.entries(实测)) {
      const i = 面板名.findIndex((n) => n.includes(类型));
      if (i === -1) { 错.push(`${类型}：面板里没有这一项`); continue; }
      const 预测 = i + 1;
      if (预测 === 数字) { 对++; 记(`✅ ${类型}：面板第 ${预测} 项，标题就是 \`${类型} ${数字}\``); }
      else { 错.push(`${类型}：面板第 ${预测} 项，但标题写 ${数字}`); 记(`❌ ${类型}：面板第 ${预测} 项，标题却是 ${数字}`); }
    }
    记(`\n对 ${对} / 错 ${错.length}`);
    if (错.length) 记('不一致项：\n  - ' + 错.join('\n  - '));
  }
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFV4.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
