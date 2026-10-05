// ⭐⭐⭐⭐⭐ Batch FQ-1：核实两件「文案表里有、手册一个字都没写」的功能
//
// 起因（缺陷 462 的规矩：动手前先 grep 账本）：
//   grep task-inventory.yml / AUDIT.md / PROGRESS.md ⇒ `scriptV2*`、`videoContinuation*`
//   三组**在账本里只有计数、没有功能级读数**。查回原文：
//   §141.2 记「`scriptV2*` 脚本 V2 | 42 | ⛔ 一个字都没有」—— 而实际表里是 **93 条**。
//   ⇒ 连「有多少条」都是手抄的错的。顺手做了 tools/i18n-census.py 重算，9 个分组 7 个错。
//
// 本轮目标（按「能不能真的用」排序）：
//   ① 「脚本 NEW」节点：能不能建？建出来长什么样？`scriptV2*` 93 条里哪些真在界面上？
//   ② 「智能续写」：视频节点上有没有入口？`videoContinuation*` 20 条里哪些真在界面上？
//
// ⛔ 安全边界（比平时更严，因为这两处都可能触发生成）：
//   ⛔ 不点「批量生成分镜」/「批量生视频」/「一键合成全部提示词」/「重新生成脚本」
//      /「批量生成资产图」/「生成」—— 每一个都消耗积分
//   ⛔ 不点「确认续写」—— `videoContinuationAgreementRequired = 请先阅读并同意 Seedance 协议`
//      ⇒ 确认续写会牵出 Seedance 承诺书签署（⛔ 本手册明确不代做）
//   ⛔ 不点「下载」
//   ⛔ 不删任何节点、不改模型、不点任何预设卡
//   ⛔ 建节点只在**一次性测试项目** a4ef3de0… 里做，主画布 34226ef1… 只读探测
import { launch, closePromos, ORIGIN, 全页文字, 归一, 断言器, 量浮层 } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const 主画布 = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const 测试画布 = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=a4ef3de0cdca4977ba45b373eb5165b5`;
const HERE = new URL('.', import.meta.url).pathname;
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFQ1.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = 断言器(记);

const 浏览器 = await launch();
const page = 浏览器.page;

/** ⛔ 危险按钮黑名单：只看不做。返回页面上**现在真实可点**的危险按钮清单。 */
const 危险 = [
  '批量生成分镜', '批量生视频', '一键合成全部提示词', '重新生成脚本',
  '批量生成资产图', '生成资产图', '确认续写', '下载', '同意并使用',
];

async function 扫危险按钮(标签) {
  const 命中 = await page.evaluate((黑) => {
    const 归 = (s) => (s || '').replace(/\s+/g, '');
    return [...document.querySelectorAll('button,[role="button"]')].map((b) => {
      const r = b.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) return null;
      const t = 归(b.innerText) || 归(b.getAttribute('aria-label')) || 归(b.title);
      if (!t || !黑.some((k) => t.includes(归(k)))) return null;
      const cs = getComputedStyle(b);
      return {
        文字: t, 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        禁用: b.disabled === true, opacity: cs.opacity, cursor: cs.cursor,
      };
    }).filter(Boolean);
  }, 危险);
  记(`   ⛔ ${标签}：页面上真实可点的危险按钮 ${命中.length} 枚 ${JSON.stringify(命中)}`);
  return 命中;
}

try {
  // ───────────────────────── 阶段 1：测试画布，建「脚本 NEW」节点
  记('=== 阶段 1：测试画布 a4ef3de0… 建脚本节点 ===');
  await page.goto(测试画布, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(13000);
  记('closePromos：' + JSON.stringify(await closePromos(page)).slice(0, 90));
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);

  R.读数.测试画布_进画布 = !!(await page.evaluate(() => /会话已过期|请刷新页面以继续编辑/.test(document.body.innerText || '')));
  断言(!R.读数.测试画布_进画布, '测试画布可以进（没被「单画布单编辑者」遮罩挡住）');

  R.读数.测试画布_建前节点 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')]
    .filter((n) => { const r = n.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
    .map((n) => n.getAttribute('data-id')));
  记('   建之前测试画布上的节点：' + JSON.stringify(R.读数.测试画布_建前节点));

  // 开「添加节点」面板（底栏 `添加节点`，aria-label 已知）
  const 加 = await page.evaluate(() => {
    for (const b of document.querySelectorAll('button,[role="button"]')) {
      if ((b.getAttribute('aria-label') || '') !== '添加节点') continue;
      const r = b.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0) || !(r.top > 700)) continue;
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    }
    return null;
  });
  记('   「添加节点」按钮落点 ' + JSON.stringify(加));
  if (加) { await page.mouse.click(加[0], 加[1]); await page.waitForTimeout(2200); }

  // 找「脚本」那一行（右侧有 ›），并断言落点属主就是它自己
  const 脚本行 = await page.evaluate(() => {
    const 归 = (s) => (s || '').replace(/\s+/g, '');
    for (const el of document.querySelectorAll('div,button,[role="button"],[role="menuitem"]')) {
      const r = el.getBoundingClientRect();
      if (!(r.width > 100 && r.height > 20 && r.height < 60)) continue;
      const t = 归(el.innerText);
      if (!t.startsWith('脚本')) continue;
      if (t.length > 12) continue;                     // 只要那一行，不要整个面板
      const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
      const hit = document.elementFromPoint(cx, cy);
      return {
        文字: t, 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        点: [cx, cy],
        命中文字: hit ? 归(hit.closest('div,button,[role="button"]')?.innerText || '').slice(0, 20) : null,
        有箭头: /›|>/.test(el.innerText || ''),
      };
    }
    return null;
  });
  R.读数.脚本行 = 脚本行;
  记('   「脚本」行 ' + JSON.stringify(脚本行));
  断言(!!脚本行, '添加节点面板里找得到「脚本」这一行', 脚本行);
  if (脚本行) {
    断言(脚本行.命中文字 === 脚本行.文字,
      `「脚本」行的落点属主就是它自己（没被别的浮层盖住）`, 脚本行);
    await page.mouse.move(脚本行.点[0] - 40, 脚本行.点[1]);
    await page.waitForTimeout(300);
    await page.mouse.click(脚本行.点[0], 脚本行.点[1]);
    await page.waitForTimeout(1800);
  }

  R.读数.子菜单 = await page.evaluate(() => {
    const 归 = (s) => (s || '').replace(/\s+/g, ' ');
    return [...document.querySelectorAll('div,ul')].filter((el) => {
      const r = el.getBoundingClientRect();
      const t = 归(el.innerText || '');
      return r.width > 80 && r.height > 30 && r.height < 200 &&
        /脚本\s*NEW|脚本（旧版）/.test(t) && t.length < 80;
    }).map((el) => {
      const r = el.getBoundingClientRect();
      return { 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 文字: 归(el.innerText) };
    });
  });
  记('   脚本子菜单：' + JSON.stringify(R.读数.子菜单));
  await 扫危险按钮('脚本子菜单打开时');

  // 点「脚本 NEW」建节点
  const 新 = await page.evaluate(() => {
    const 归 = (s) => (s || '').replace(/\s+/g, '');
    for (const el of document.querySelectorAll('div,button,[role="menuitem"]')) {
      const r = el.getBoundingClientRect();
      if (!(r.width > 40 && r.height > 15 && r.height < 60)) continue;
      const t = 归(el.innerText);
      if (!/^脚本NEW$/.test(t) && !/^脚本\s*NEW\s*$/i.test(t)) continue;
      return { 文字: t, 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
    }
    return null;
  });
  记('   「脚本 NEW」落点 ' + JSON.stringify(新));
  if (新) {
    await page.mouse.click(新.点[0], 新.点[1]);
    await page.waitForTimeout(6000);          // ⛔ 建完立刻等，看有没有自动开跑
    R.读数.建后文本 = (await 全页文字(page)).slice(0, 400);
    记('   建后页面前若干文本 ' + JSON.stringify(R.读数.建后文本.slice(0, 20)));
    const 在跑 = R.读数.建后文本.filter((t) => /生成中|初始化中|识别中|请先完成|积分/.test(t));
    记('   ⛔ 建完是否自动开跑：' + JSON.stringify(在跑));
    await 扫危险按钮('脚本节点建完');
    R.读数.建后节点 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')]
      .filter((n) => { const r = n.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
      .map((n) => { const r = n.getBoundingClientRect(); return { id: n.getAttribute('data-id'), 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 类: String(n.className || '').slice(0, 80) }; }));
    记('   建后节点 ' + JSON.stringify(R.读数.建后节点));
  }

  // ───────────────────────── 阶段 2：主画布只读，找「智能续写」入口
  记('=== 阶段 2：主画布只读，找智能续写入口 ===');
  await page.goto(主画布, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(13000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);

  R.读数.主画布_节点 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')]
    .filter((n) => { const r = n.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
    .map((n) => { const r = n.getBoundingClientRect(); return { id: n.getAttribute('data-id'), 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }));
  记('   主画布节点 ' + JSON.stringify(R.读数.主画布_节点));

  // 全文里找「续写」两个字在不在
  const 全 = await 全页文字(page, { 含透明: true });
  R.读数.主画布_含续写 = 全.filter((t) => /续写/.test(t));
  记('   主画布全页（含透明）里带「续写」的文本 ' + JSON.stringify(R.读数.主画布_含续写));

  记(`断言统计 ${JSON.stringify(断言.统计)}`);
  R.读数.断言 = 断言.统计;
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFQ1.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
