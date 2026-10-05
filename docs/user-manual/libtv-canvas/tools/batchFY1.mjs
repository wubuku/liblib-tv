// ⭐⭐⭐⭐⭐ Batch FY-1：找画布上的新手引导（文案表里 134 条引导文案，手册一个字没写）
//
// 前提（缺陷 462 的规矩，开工前已跑）：`onboarding` / `第1/4步` / `跟着做` /
// `guideEditor` 四本账**全部命中 0** ⇒ 确实从未测过。
//
// 文案表里逐字写着的一整套：
//   onboardingStep1Title 第1/4步   onboardingStep1Desc 双击或右键创建新节点
//   onboardingStep2Title 第2/4步   onboardingStep2Desc 图片上方工具栏有高清、抠图、九宫格等功能
//   onboardingStep3Title 第3/4步   onboardingStep3Desc 拖拽一个或多个节点 + 进行连接
//   onboardingStep4Title 第4/4步   onboardingStep4Desc 把多个作品打组，打组后可排序和整组执行
//   guideDefaultSkipBarLabel 跟着做，快速上手
//   guideDefaultNextLabel 下一步 / guideDefaultPreviousLabel 上一步
//   guideDefaultSkipLabel 跳过 / guideDefaultDoneLabel 知道了
//
// ⭐ 三个入口假设，本轮逐个撞：
//   A. 新建一张空白画布 ⇒ 引导自动出现
//   B. URL 带 `guideDev=1`（文案表 `guideEditorPreviewLinkCopied` 提到这个参数）
//   C. 金刚位 `guideUrl`（`guideEditorProdLinkCopied` 说「粘到金刚位 guideUrl」）
//
// ⛔ 新建画布是 CRUD，允许。⛔ 建完只读引导，⛔ 不点「生成」。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const 主画布 = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 断言: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFY1.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = (名, 过, 明) => { R.断言.push({ 名, 过, 明 }); 记(`${过 ? '✅' : '❌'} ${名} —— ${明}`); };

// ⭐ 找引导的判据：文案表里那几句**逐字**。别用模糊的「浮层」判据（FT-3 栽过）。
const 探引导 = () => page.evaluate(() => {
  const 词 = ['第1/4步', '第2/4步', '第3/4步', '第4/4步', '跟着做，快速上手',
    '双击或右键创建新节点', '图片上方工具栏有高清', '拖拽一个或多个节点', '把多个作品打组',
    '下一步', '上一步', '跳过', '知道了', '先跟着引导完成这一步'];
  const 找到 = [];
  for (const w of 词) {
    for (const e of document.querySelectorAll('*')) {
      if (e.children.length) continue;                 // 只看叶子
      const t = (e.innerText || '').trim();
      if (t !== w && !(t.includes(w) && w.length >= 4)) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 4 || r.height < 4) continue;
      if (r.x < -200 || r.y < -200 || r.x > 2000 || r.y > 1200) continue;   // ⛔ 视口外的残留不算
      找到.push({ 词: w, tag: e.tagName, x: Math.round(r.x), y: Math.round(r.y),
        w: Math.round(r.width), h: Math.round(r.height) });
      break;                                          // 每个词只记第一处
    }
  }
  return 找到;
});

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });

  // ── A. 先在主画布上找（引导可能对老账号不显示）
  记('--- A 主画布上有没有引导 ---');
  await page.goto(主画布, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(6000);
  await closePromos(page);
  await page.waitForTimeout(4000);
  let 上 = -1, 稳 = 0;
  for (let i = 0; i < 20; i++) {
    const n = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
    if (n === 上) { 稳++; if (稳 >= 3) { 记(`  主画布稳定在 ${n} 个节点`); break; } } else 稳 = 0;
    上 = n; await page.waitForTimeout(1200);
  }
  const A = await 探引导();
  R.读数.主画布 = A;
  记(`  找到 ${A.length} 条引导文案：${A.length ? A.map((x) => `「${x.词}」@${x.x},${x.y}`).join(' / ') : '（无）'}`);
  await page.screenshot({ path: resolve(EVID, 'fy1-0-主画布.png') });

  // ── B. URL 带 guideDev=1
  记('\n--- B 主画布 + ?guideDev=1 ---');
  await page.goto(主画布 + '&guideDev=1', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  const B = await 探引导();
  R.读数.guideDev = B;
  记(`  找到 ${B.length} 条：${B.length ? B.map((x) => `「${x.词}」`).join(' / ') : '（无）'}`);
  await page.screenshot({ path: resolve(EVID, 'fy1-1-guideDev.png') });

  // ── C. 新建一张空白画布
  记('\n--- C 新建一张空白画布，看引导是否自动出现 ---');
  await page.goto(`${ORIGIN}/workspace?spaceId=${SPACE}`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(8000);
  await closePromos(page);
  await page.screenshot({ path: resolve(EVID, 'fy1-2-工作区.png') });
  const 全页文字 = await page.evaluate(() => document.body.innerText.slice(0, 1500));
  R.读数.工作区文字 = 全页文字;
  记(`  工作区首屏文字（前 300 字）：\n     ${全页文字.slice(0, 300).replace(/\n+/g, ' | ')}`);

  // 找「新建画布」入口
  const 新建 = await page.evaluate(() => {
    const o = [];
    for (const e of document.querySelectorAll('button, [role="button"], a, div, span')) {
      const t = (e.innerText || '').trim();
      if (!/新建画布|创建画布|新建项目|^\+ *新建/.test(t) || t.length > 12) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 20) continue;
      o.push({ 文字: t, tag: e.tagName, 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] });
    }
    return o;
  });
  R.读数.新建入口 = 新建;
  记(`  找到「新建画布」类入口 ${新建.length} 个：${新建.map((x) => `「${x.文字}」${x.tag}`).join(' / ')}`);

  if (!新建.length) {
    记('  ⛔ 工作区首页没有新建入口，本轮到此为止');
  } else {
    const b = 新建[0];
    const 落 = await page.evaluate(({ x, y }) => {
      const e = document.elementFromPoint(x, y);
      return e ? { tag: e.tagName, 文字: (e.innerText || '').trim().slice(0, 10) } : null;
    }, { x: b.中心[0], y: b.中心[1] });
    断言('落点属主是新建入口', !!落, `命中 ${落?.tag}「${落?.文字}」`);
    await page.mouse.click(b.中心[0], b.中心[1]);
    await page.waitForTimeout(2500);
    await page.screenshot({ path: resolve(EVID, 'fy1-3-点新建之后.png') });
    const D = await 探引导();
    R.读数.新建后 = D;
    记(`  点新建之后找到 ${D.length} 条引导文案：${D.length ? D.map((x) => `「${x.词}」@${x.x},${x.y}`).join(' / ') : '（无）'}`);
    记(`  当前 URL：${page.url()}`);
  }
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFY1.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
