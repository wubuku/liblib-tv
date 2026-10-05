// ⭐⭐⭐⭐⭐ Batch FV-5：FV-4 双击**没开出**添加节点面板，本轮先看截图再改判据
//
// FV-4 的断言（role=menu/listbox 计数）是**假绿灯**：
// 面板元素数始终 0，而断言写成「Esc 后面板数 0 → 0（✅ 关掉了）」——
// 0 → 0 只说明**前后都没有**，**不能证明打开过再关掉**。
// ⇒ 缺陷 488：**「计数不变」不能当「打开过又关掉」的证据**，
//    必须记 `executed` 自证字段（这正是 BK1 立的规矩，FV-4 又犯了一次）。
//
// ⭐ 而且 FV-4 选的双击点 (1200,700) 可能不在画布 pane 上 ——
// 那个坐标的 elementFromPoint 命中 `.react-flow__pane` 了，但双击可能落在别的层。
//
// 本轮：先按节点面板的**已知中文文案**去搜（缺陷 462：手册早写过这个面板，
// 元素名是「添加节点」/「双击画布 自由生成节点」），搜不到再截图看。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFV5.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(14000);
  await closePromos(page);
  await page.screenshot({ path: resolve(EVID, 'fv5-0-初始.png') });
  记('已拍初始画面');

  // 找顶栏「添加节点」入口的**所有候选**，按中文文案而不是 role
  const 候选 = await page.evaluate(() => {
    const out = [];
    for (const el of document.querySelectorAll('button, [role="button"], div, span')) {
      const s = (el.innerText || '').trim();
      if (!s || s.length > 12) continue;
      if (!/添加节点|新建节点|自由生成|^节点$/i.test(s)) continue;
      const r = el.getBoundingClientRect();
      if (r.width < 8 || r.height < 8) continue;
      out.push({ 文字: s, tag: el.tagName, role: el.getAttribute('role'),
        aria: el.getAttribute('aria-label'), x: Math.round(r.x), y: Math.round(r.y),
        w: Math.round(r.width), h: Math.round(r.height),
        中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] });
    }
    return out;
  });
  R.读数.候选 = 候选;
  记(`\n按文案搜到 ${候选.length} 个候选入口：`);
  候选.forEach((c) => 记(`   \`${c.文字}\` ${c.tag}${c.role ? ' role=' + c.role : ''} @${c.x},${c.y} ${c.w}×${c.h}`));

  if (!候选.length) {
    记('⛔ 顶栏没有「添加节点」字样的入口 —— 改用双击，但要**自证双击真的发生了**');
  } else {
    const c = 候选[0];
    记(`\n点候选「${c.文字}」…`);
    await page.mouse.click(c.中心[0], c.中心[1]);
    await page.waitForTimeout(1200);
    await page.screenshot({ path: resolve(EVID, 'fv5-1-点开之后.png') });
    const 面板 = await page.evaluate(() => {
      const out = [];
      for (const el of document.querySelectorAll('body *')) {
        const s = (el.innerText || '').trim();
        if (!s || s.length > 30) continue;
        const r = el.getBoundingClientRect();
        if (r.width < 20 || r.height < 10) continue;
        if (r.y < 60 || r.y > 700) continue;
        if (!/智能剪辑|逐帧拉片|导演台|音频|脚本|素材库/.test(s)) continue;
        out.push({ 文字: s, y: Math.round(r.y), x: Math.round(r.x) });
      }
      const seen = new Map();
      for (const o of out) if (!seen.has(o.y) || seen.get(o.y).文字.length < o.文字.length) seen.set(o.y, o);
      return [...seen.values()].sort((a, b) => a.y - b.y);
    });
    R.读数.面板 = 面板;
    记(`面板读到 ${面板.length} 行：`);
    面板.forEach((p, i) => 记(`   ${i + 1}. \`${p.文字}\` @y=${p.y}`));
  }
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFV5.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
