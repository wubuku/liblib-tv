// ⭐⭐⭐⭐⭐ Batch FI-1：解掉「我的收藏」的矛盾，并顺带解掉 `loadingMore` / `allLoaded` 的时序
//
// 手册里长期挂着一个**明确记下来但查不出原因**的矛盾（asset-library.md）：
//   「风格广场首屏那张 `Seedream 5.0 pro` **星是实心的、`aria-label="取消收藏"`**，
//     按理它就在收藏列表里；可是**两个广场的「我的收藏」页两次独立读数都是「暂无素材」**。」
//
// ⭐ 本轮把它拆成两个互斥的可能，一次实验就能分开：
//   假设 A：**加载时序** —— 收藏数据要等一会儿才到，所以第一次读是空的
//     预测：**刷新 / 等待之后**「我的收藏」里会出现那张卡
//   假设 B：**数据源不同** —— 收藏写在别处，「我的收藏」页读的不是那份数据
//     预测：**等再久、刷新再多次**也永远是「暂无素材」
//
// ⭐⭐⭐ 顺带解掉第二个 📖：`loadingMore` / `allLoaded` 这两个状态名一直没人说得清。
//   本轮在「我的收藏」页按固定间隔连续采样，读「有没有卡片 / 卡片数 / 空态文字」，
//   就能看出它到底有没有「先空、后满」这个过程。
//
// ⛔ 全部操作可逆、零风险：只做「打开面板 → 切标签 → 刷新 → 读」，
//   **不点任何卡片本体**（点卡片 = 新建节点）、不点收藏星（会改状态）。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFI1.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;

/** 打开「添加节点」面板并点进某个广场 */
const 开广场 = async (哪) => {
  // ⭐⭐ 走**底栏那枚独立的「素材库」按钮**（aria-label="素材库"，[660,757]）——
  //   它才是广场面板的入口。踩过两次坑：
  //   ① 底栏最左那枚是「资产管理」，不是「+」（位置条件会误命中它）
  //   ② 添加节点面板里那一项「素材库」是**上传素材的空态**（读出来是「空空如也」），
  //      不是广场。手册 10-tasks/asset-library.md 开头写得很清楚：「两个入口，同一个面板」，
  //      但实测走**底栏那枚**才出广场。
  const 加 = await page.evaluate(() => {
    for (const x of document.querySelectorAll('button')) {
      if ((x.getAttribute('aria-label') || '') === '素材库') {
        const r = x.getBoundingClientRect();
        if (r.width > 0 && r.top > 700) return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
      }
    }
    return null;
  });
  if (!加) { 记('   ⛔ 找不到底栏的 aria-label="素材库" 按钮'); return false; }
  记(`   点底栏「素材库」${JSON.stringify(加)}`);
  await page.mouse.click(加[0], 加[1]);
  await page.waitForTimeout(2600);
  // ⭐ 面板里的三项要先点那一行右边的 `›` 才展开（手册 10-tasks/asset-library.md 记的）
  const 找 = (名) => page.evaluate((n) => {
    for (const x of document.querySelectorAll('button,[role="menuitem"],li,div,span')) {
      const t = (x.innerText || '').replace(/\s+/g, ' ').trim();
      if (!t.startsWith(n)) continue;
      const r = x.getBoundingClientRect();
      if (r.width > 80 && r.height > 18 && r.height < 90) return { 文字: t.slice(0, 40), 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] };
    }
    return null;
  }, 名);
  let 项 = await 找(哪);
  if (!项) {
    const dump = await page.evaluate(() => {
      const 可见 = (el) => { const r = el.getBoundingClientRect(); return r.width > 4 && r.height > 4; };
      const out = [];
      for (const el of document.querySelectorAll('button,[role="menuitem"],[role="option"],li')) {
        const r = el.getBoundingClientRect();
        if (!可见(el) || r.width < 80 || r.height < 18) continue;
        const t = (el.innerText || '').replace(/\s+/g, ' ').trim();
        if (!t || t.length > 30) continue;
        out.push({ 文字: t, 框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
      }
      const seen = new Set();
      return out.filter((x) => { const k = x.框.join(','); if (seen.has(k)) return false; seen.add(k); return true; });
    });
    记('   —— 面板里宽度>80 的可见条目 ——');
    for (const d of dump) 记('      ' + JSON.stringify(d));
  }
  if (!项) { 记(`   ⛔ 面板里找不到「${哪}」`); return false; }
  记(`   点「${项.文字}」`);
  await page.mouse.click(项.中心[0], 项.中心[1]);
  await page.waitForTimeout(3200);
  return true;
};

/** 读一个广场页的完整状态 */
const 读页 = () => page.evaluate(() => {
  const 可见 = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const 正文 = document.body.innerText || '';
  // 三个标签
  const 标签 = [...document.querySelectorAll('button,[role="tab"]')]
    .filter((b) => ['风格广场', '特效广场', '我的收藏', '最近使用'].some((t) => (b.innerText || '').trim() === t))
    .map((b) => ({ 文字: (b.innerText || '').trim(), 高亮: (getComputedStyle(b).backgroundColor || '') !== 'rgba(0, 0, 0, 0)' }));
  // 收藏星：两态
  const 星 = [...document.querySelectorAll('[aria-label="收藏"],[aria-label="取消收藏"]')]
    .filter(可见)
    .map((b) => {
      const r = b.getBoundingClientRect();
      const p = b.querySelector('path');
      return { aria: b.getAttribute('aria-label'), 框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], path段数: b.querySelectorAll('path').length, d: p ? (p.getAttribute('d') || '').length : 0 };
    });
  // 卡片：带「详情」按钮的算风格卡
  const 详情 = [...document.querySelectorAll('[aria-label="详情"]')].filter(可见);
  // 空态
  const 空态 = /暂无素材|暂无收藏|还没有收藏|空空如也/.exec(正文);
  return {
    标签,
    收藏星: { 总数: 星.length, 已收藏: 星.filter((s) => s.aria === '取消收藏').length, 未收藏: 星.filter((s) => s.aria === '收藏').length, 样本: 星.slice(0, 4) },
    详情按钮数: 详情.length,
    空态: 空态 ? 空态[0] : null,
    含暂无: /暂无/.test(正文),
    正文字数: 正文.length,
  };
});

/** 采样 n 次，每次间隔 ms，记录「我的收藏」页的卡片/空态变化 */
const 采样时序 = async (n, 间隔) => {
  const 序列 = [];
  for (let i = 0; i < n; i++) {
    const s = await 读页();
    序列.push({ t: i * 间隔, 详情按钮数: s.详情按钮数, 收藏星总数: s.收藏星.总数, 空态: s.空态, 含暂无: s.含暂无 });
    if (i < n - 1) await page.waitForTimeout(间隔);
  }
  return 序列;
};

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(13000);
  记('closePromos：' + JSON.stringify(await closePromos(page)).slice(0, 130));
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);

  // ——— ① 风格广场：先读首屏，找出哪些卡是「已收藏」 ———
  记('—— ① 进素材库（广场在这里面）——');
  if (!(await 开广场('素材库'))) throw new Error('进不去素材库');
  let s = await 读页();
  记(`   标签 ${JSON.stringify(s.标签)}`);
  记(`   收藏星：总数 ${s.收藏星.总数}｜已收藏 ${s.收藏星.已收藏}｜未收藏 ${s.收藏星.未收藏}`);
  记(`   详情按钮 ${s.详情按钮数} 枚｜空态 ${JSON.stringify(s.空态)}`);
  R.读数.风格广场首屏 = s;
  await page.screenshot({ path: EVID + 'fi1-01-风格广场首屏.png' });

  // ——— ② 切「我的收藏」，连续采样看时序 ———
  记('—— ② 切「我的收藏」，每 2s 采一次共 8 次 ——');
  const 收藏标签 = await page.evaluate(() => {
    for (const x of document.querySelectorAll('button,[role="tab"]')) {
      if ((x.innerText || '').trim() === '我的收藏') {
        const r = x.getBoundingClientRect();
        return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
      }
    }
    return null;
  });
  if (!收藏标签) { 记('   ⛔ 找不到「我的收藏」标签'); throw new Error('无标签'); }
  await page.mouse.click(收藏标签[0], 收藏标签[1]);
  const 序 = await 采样时序(8, 2000);
  for (const r of 序) 记(`   t+${r.t}ms：详情 ${r.详情按钮数}｜星 ${r.收藏星总数}｜空态 ${JSON.stringify(r.空态)}｜含暂无 ${r.含暂无}`);
  R.读数.收藏页时序_切换后 = 序;
  await page.screenshot({ path: EVID + 'fi1-02-我的收藏-切换后.png' });

  // ——— ③ ⭐ 刷新页面，再采一次（假设 A 的决定性检验）———
  记('—— ③ 刷新页面（不点任何东西），再连续采样 ——');
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(13000);
  await closePromos(page);
  // 刷新后广场窗口会关，需要重进
  const 重进 = await 开广场('素材库');
  记(`   刷新后重进广场：${重进}`);
  s = await 读页();
  记(`   刷新后风格广场首屏：收藏星 已收藏 ${s.收藏星.已收藏} / 共 ${s.收藏星.总数}｜详情 ${s.详情按钮数}`);
  R.读数.刷新后首屏 = { 已收藏: s.收藏星.已收藏, 总数: s.收藏星.总数, 详情按钮数: s.详情按钮数 };

  const 收藏标签2 = await page.evaluate(() => {
    for (const x of document.querySelectorAll('button,[role="tab"]')) {
      if ((x.innerText || '').trim() === '我的收藏') {
        const r = x.getBoundingClientRect();
        return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
      }
    }
    return null;
  });
  if (收藏标签2) {
    await page.mouse.click(收藏标签2[0], 收藏标签2[1]);
    const 序2 = await 采样时序(6, 2500);
    for (const r of 序2) 记(`   刷新后 t+${r.t}ms：详情 ${r.详情按钮数}｜星 ${r.收藏星总数}｜空态 ${JSON.stringify(r.空态)}｜含暂无 ${r.含暂无}`);
    R.读数.收藏页时序_刷新后 = 序2;
    await page.screenshot({ path: EVID + 'fi1-03-我的收藏-刷新后.png' });
  }

  // ——— ④ 判据 ———
  const 判 = (seq) => ({
    有卡片: seq.some((r) => r.详情按钮数 > 0 || r.收藏星总数 > 0),
    一直空: seq.every((r) => r.详情按钮数 === 0 && r.收藏星总数 === 0),
    空态字样: [...new Set(seq.map((r) => r.空态).filter(Boolean))],
    曾出现过内容: seq.some((r) => !r.含暂无),
  });
  记('—— 判据 ——');
  记('   切换后：' + JSON.stringify(判(序)));
  if (R.读数.收藏页时序_刷新后) 记('   刷新后：' + JSON.stringify(判(R.读数.收藏页时序_刷新后)));
  记(`   ⭐ 首屏「已收藏」的卡：${R.读数.风格广场首屏?.收藏星?.已收藏} 张（它们的星是实心、aria-label=取消收藏）`);
} catch (e) {
  记('❌ 出错：' + (e && e.message ? e.message : String(e)));
} finally {
  try { await page.waitForTimeout(8000); } catch (e) { /* 静置 */ }
  try { await 浏览器.browser.close(); } catch (e) { /* 关 */ }
  记('done');
}
