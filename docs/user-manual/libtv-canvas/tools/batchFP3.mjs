// ⭐⭐⭐⭐⭐ Batch FP-3：**自我纠正** —— FP-2 对「预设面板」的解释是错的，而且几何和旧读数对不上
//
// 起因（缺陷 462）：我按「手册正文里没写这个面板」去补页，
// ⛔ **没先 grep `task-inventory.yml` 和 `AUDIT.md`** —— 那里面白纸黑字记着：
//   · batchAX1/AX2：面板 `[260,62,754×387]` z=602，「四列 11 项」
//   · batchBA1：**更正为三列 15 项**；⭐⭐ **15 条全部 `cursor: not-allowed`，
//     而悬停提示直接写出原因** ——「`调度故事板仅支持Lib Image模型`」
//     「`角色设定图仅支持Lib Image、General image Pro、General image V2模型`」
//     ⇒ **整片灰不是「节点里没图」，是当前模型不在支持名单里**
//   · batchBB1/BB2：换模型预设就变亮（`Lib Image 2.5 Pro` → 0 条可点 → `Lib Image` → 15 条全亮），
//     ⛔ 且换模型会改价格（⚡15 → ⚡18）
//   · batchBD4：全画面 5 个蓝点，预设里 3 个；**「蓝点 = 推荐/新功能」站不住**
//   · batchAZ2：② 那枚按钮是**`摄像机`**（无文字无 aria），tooltip 直接报当前设置
//
// ⛔ FP-2 犯了两个错：
//   ① 把「全灰」解释成「节点里没有图」—— 与 BA1 的读数**直接矛盾**
//   ② 几何读成「两栏 514×540」，与 BA1 的「三列 754×387」对不上
//
// 本轮就做两件事：把灰态的**真实原因**悬停读出来；把几何**重新量准**。
// ⛔ 安全边界：⛔ 不换模型（会改价格）；⛔ 不点任何卡片；只悬停 + 量。
import { launch, closePromos, ORIGIN, 全页文字, 归一, 断言器 } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFP3.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = 断言器(记);

const 浏览器 = await launch();
const page = 浏览器.page;

const 悬停 = async (x, y) => {
  await page.mouse.move(x - 60, y);
  await page.waitForTimeout(250);
  await page.mouse.move(x, y);
  await page.waitForTimeout(1800);
  const 全部 = await page.evaluate(() => [...document.querySelectorAll('[class*="Tooltip"],[role="tooltip"]')]
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 30 && r.height > 10 && e.innerText && e.innerText.trim(); })
    .map((e) => { const r = e.getBoundingClientRect(); return { 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 文字: e.innerText.replace(/\s+/g, ' ').trim().slice(0, 120) }; }));
  // ⭐ 只取**离鼠标最近**的那一条 —— 常驻横幅的气泡会混进来（FP-2 读到过「按 ESC 退出」）
  return 全部.sort((a, b) => (Math.abs(a.框[0] + a.框[2] / 2 - x) + Math.abs(a.框[1] - y)) - (Math.abs(b.框[0] + b.框[2] / 2 - x) + Math.abs(b.框[1] - y)))[0] || null;
};

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(13000);
  记('closePromos：' + JSON.stringify(await closePromos(page)).slice(0, 70));
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);

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
  const 当前模型 = await page.evaluate(() => {
    const 归 = (s) => (s || '').replace(/\s+/g, ' ').trim();
    for (const el of document.querySelectorAll('button,[role="button"]')) {
      const t = 归(el.innerText);
      if (!/Lib Image|Seedream|General image|可灵/.test(t)) continue;
      const r = el.getBoundingClientRect();
      if (r.y < 600 || r.y > 800) continue;
      return { 名: t, 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
    }
    return null;
  });
  R.读数.当前模型 = 当前模型;
  记('   当前模型 ' + JSON.stringify(当前模型));

  const 预设钮 = await page.evaluate(() => {
    for (const el of document.querySelectorAll('button,[role="button"]')) {
      if (el.getAttribute('aria-label') !== '预设') continue;
      const r = el.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) continue;
      return { 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
    }
    return null;
  });
  await page.mouse.click(预设钮.点[0], 预设钮.点[1]);
  await page.waitForTimeout(2500);

  // ── ① 几何：逐个子元素量 x，按列聚类 ──
  记('—— ① 面板几何 ——');
  const 几何 = await page.evaluate(() => {
    const 归 = (s) => (s || '').replace(/\s+/g, ' ');
    let 壳 = null;
    for (const el of document.querySelectorAll('div')) {
      const t = 归(el.innerText);
      if (!t.includes('分镜叙事') || !t.includes('质感调节') || !t.includes('空间与机位')) continue;
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      const 候 = { 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], z: cs.zIndex, position: cs.position, class: String(el.className || '').slice(0, 120) };
      if (!壳 || (候.框[2] * 候.框[3]) < (壳.框[2] * 壳.框[3])) 壳 = 候;   // 取**最小**那个含全部文字的
    }
    // 卡片：h=52 的整块按钮，按左边缘聚类
    const 卡 = [];
    for (const el of document.querySelectorAll('button,[role="button"]')) {
      const r = el.getBoundingClientRect();
      if (Math.round(r.height) !== 52 || r.width < 150) continue;
      if (壳 && (r.x < 壳.框[0] - 5 || r.x + r.width > 壳.框[0] + 壳.框[2] + 5)) continue;
      卡.push({ 名: 归(el.innerText).slice(0, 40), x: Math.round(r.x), 宽: Math.round(r.width), y: Math.round(r.y) });
    }
    const 列 = {};
    for (const c of 卡) { (列[c.x] = 列[c.x] || []).push(c); }
    // 分组标题
    const 组 = [];
    for (const el of document.querySelectorAll('div,span,h3,p')) {
      const t = 归(el.innerText).trim();
      if (!['分镜叙事', '质感调节', '空间与机位', '设定图'].includes(t)) continue;
      const r = el.getBoundingClientRect();
      组.push({ 字: t, x: Math.round(r.x), y: Math.round(r.y) });
    }
    return { 壳, 卡, 列数: Object.keys(列).length, 列: Object.entries(列).map(([x, v]) => ({ x: Number(x), 宽: v[0].宽, 张数: v.length })), 组 };
  });
  R.读数.几何 = 几何;
  记('   外壳 ' + JSON.stringify(几何.壳));
  记('   ⭐ 列数 ' + 几何.列数 + '；列 ' + JSON.stringify(几何.列));
  记('   分组标题 ' + JSON.stringify(几何.组));
  断言(几何.卡.length === 15, '卡片 15 张', 几何.卡.length);
  断言(几何.列数 >= 2 && 几何.列数 <= 3, '⭐ 列数落在 2~3 之间（要能解释 BA1 的「三列」和我这次读到的几列）', 几何.列);

  // ── ② ⭐⭐ 灰态的真实原因：悬停读气泡 ──
  记('—— ② 灰态的真实原因 ——');
  const 读气泡 = [];
  for (const 名 of ['调度故事板', '故事板', '人像质感调节', '25宫格连贯分镜', '720全景', '角色脸部三视图']) {
    const c = 几何.卡.find((k) => k.名.startsWith(名));
    if (!c) { 记('   ⛔ 找不到卡片 ' + 名); continue; }
    const 泡 = await 悬停(c.x + c.宽 / 2, c.y + 26);
    读气泡.push({ 卡: 名, 气泡: 泡 });
    记(`   「${名}」→ ${泡 ? JSON.stringify(泡.文字) : '(无气泡)'}`);
  }
  R.读数.灰态原因 = 读气泡;
  const 带仅支持 = 读气泡.filter((x) => x.气泡 && /仅支持|不支持/.test(x.气泡.文字));
  断言(带仅支持.length > 0, '⭐⭐⭐ 悬停提示里写明了「仅支持…模型」—— 灰态是**模型不支持**，不是「没图」', 读气泡);
  await page.screenshot({ path: EVID + 'fp3-01-灰态原因悬停.png' });

  记(`—— 共跑了 ${断言.统计.次数} 条断言，失败 ${断言.统计.失败} 条 ——`);
} catch (e) {
  记('❌ ' + (e && e.message ? e.message : String(e)));
} finally {
  try { await 浏览器.browser.close(); } catch (e) { /* 关 */ }
  记('done');
}
