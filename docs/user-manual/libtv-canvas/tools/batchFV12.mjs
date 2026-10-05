// ⭐⭐⭐⭐⭐ Batch FV-12：清掉 FV-9 留下的那一个测试节点，把主画布还原成 12 个
//
// 现状（FV-11 终态实测 13 个）：
//   原始 12 个（FQ 建过脚本节点）+ FV-9 留下的 1 个文本节点
//   FV-11 自己建的 2 个**已经删掉了**（它报「菜单里没找到删除」，
//   但画布 15 → 13，说明点「删除」时其实删掉了别的 ⇒ 又一个「报告与实际不符」，
//   记为缺陷 490：⛔ 必须以**画布实测**为准，不能以脚本自报的断言为准）
//
// ⛔ 本轮只做一件事：把多出来的那个删掉。
//   删除路径：左下角「资产管理」（⛔ 不是 aria，是**文字**）→ 抽屉里那行 → 「⋯」→ 「删除」
//   ⛔ 绝不按 Delete / Backspace。
//   ⛔ 删完逐条比对：节点 id 集合必须与 FV-3 的基线完全一致。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 断言: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFV12.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = (名, 过, 明) => { R.断言.push({ 名, 过, 明 }); 记(`${过 ? '✅' : '❌'} ${名} —— ${明}`); };

const 快照 = () => page.evaluate(() => {
  const out = [];
  for (const el of document.querySelectorAll('.react-flow__node')) {
    const cls = [...el.classList].find((c) => c.startsWith('react-flow__node-')) || '';
    const b = el.getBoundingClientRect();
    let 标题 = null;
    for (const t of el.querySelectorAll('*')) {
      if (t.children.length) continue;
      const s = (t.textContent || '').trim();
      if (!s || s.length > 24) continue;
      const r = t.getBoundingClientRect();
      if (r.top < b.top + 44 && (!标题 || r.top < 标题.top)) 标题 = { 文: s, top: r.top };
    }
    out.push({ id: (el.getAttribute('data-id') || '').trim(),
      类型: cls.replace('react-flow__node-', ''), 标题: 标题 ? 标题.文 : '' });
  }
  return out;
});

// FV-3 记录的原始 12 个节点（id 未知，但**类型+标题+数量**可作指纹）
const 指纹 = (s) => s.map((n) => `${n.类型}:${n.标题}`).sort().join(' | ');

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(14000);
  await closePromos(page);
  await page.screenshot({ path: resolve(EVID, 'fv12-0-开跑前.png') });

  const 前 = await 快照();
  R.读数.前 = 前;
  记(`开跑前 ${前.length} 个：`);
  前.forEach((n) => 记(`   ${n.id}  ${n.类型}  \`${n.标题}\``));

  // FV-3 的基线指纹
  const FV3指纹 = 'audio:音频节点 1 | audio:音频节点 1 | director-console-3d:导演台 5 | image:图片节点 2 | image:图片节点 2 | script-v2:脚本 V2 1 | shot-breakdown:逐帧拉片 | text:文本节点 1 | text:文本节点 1 | video-clip:智能剪辑 4 | video:视频节点 3 | video:视频节点 3';
  const 前指纹 = 指纹(前);
  const 多出 = 前.filter((n) => !FV3指纹.includes(`${n.类型}:${n.标题}`));
  记(`\n与 FV-3 基线相比，多出的：${多出.map((n) => `${n.id} ${n.类型}\`${n.标题}\``).join(' / ') || '（无）'}`);

  if (前.length <= 12) { 记('✅ 画布已经是 12 个或更少，不需要清理'); }
  else {
    // 候选：文本节点多于 2 个的那个就是 FV-9 留下的
    const 文本们 = 前.filter((n) => n.类型 === 'text');
    记(`\n文本节点共 ${文本们.length} 个：${文本们.map((n) => `${n.id}=${n.标题}`).join(' / ')}`);

    // 打开资产管理抽屉（按**文字**找，⛔ 不是 aria）
    const 开 = await page.evaluate(() => {
      for (const e of document.querySelectorAll('button, [role="button"], div, span')) {
        if (e.children.length) continue;
        if ((e.innerText || '').trim() !== '资产管理') continue;
        const r = e.getBoundingClientRect();
        if (r.width < 10 || r.height < 10) continue;
        return { x: Math.round(r.x), y: Math.round(r.y), 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
      }
      return null;
    });
    R.读数.资产管理 = 开;
    if (!开) { 记('❌ 找不到「资产管理」入口'); }
    else {
      记(`点「资产管理」@${开.中心.join(',')}`);
      await page.mouse.click(开.中心[0], 开.中心[1]);
      await page.waitForTimeout(1400);
      await page.screenshot({ path: resolve(EVID, 'fv12-1-抽屉开了.png') });

      // 抽屉里的行：每行有一个「⋯」按钮
      const 行 = await page.evaluate(() => {
        const out = [];
        for (const e of document.querySelectorAll('[aria-label^="更多操作"], [aria-label*="更多操作"]')) {
          const row = e.closest('[class*="group"], li, tr, div[class*="flex"]');
          const 行文 = (row?.innerText || '').trim().split('\n')[0];
          const r = e.getBoundingClientRect();
          if (r.width < 8) continue;
          out.push({ aria: e.getAttribute('aria-label'), 行文, 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] });
        }
        return out;
      });
      R.读数.抽屉行 = 行;
      记(`\n抽屉里带「更多操作」的行 ${行.length} 个：`);
      行.forEach((r) => 记(`   「${r.行文}」 aria=${r.aria}`));

      // 目标：文本节点那一行（第 4 个文本节点）
      const 目标 = 行.find((r) => /文本节点/.test(r.行文 || ''));
      if (!目标) { 记('⛔ 抽屉里没有文本节点那一行'); }
      else {
        记(`\n对「${目标.行文}」点「⋯」`);
        await page.mouse.click(目标.中心[0], 目标.中心[1]);
        await page.waitForTimeout(900);
        const 删项 = await page.evaluate(() => {
          const o = [];
          for (const e of document.querySelectorAll('*')) {
            if (e.children.length) continue;
            const t = (e.innerText || '').trim();
            if (t !== '删除') continue;
            const r = e.getBoundingClientRect();
            if (r.width < 20 || r.height < 10) continue;
            o.push({ x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width) });
          }
          return o;
        });
        R.读数.删除项 = 删项;
        记(`菜单里「删除」命中 ${删项.length} 处：${删项.map((d) => `@${d.x},${d.y} w=${d.w}`).join(' / ')}`);
        if (删项.length) {
          const d = 删项[0];
          await page.mouse.click(d.x + d.w / 2, d.y + 10);
          await page.waitForTimeout(1500);
          await page.screenshot({ path: resolve(EVID, 'fv12-2-删之后.png') });
        }
      }
    }
  }

  const 终 = await 快照();
  R.读数.终 = 终;
  断言('画布回到 12 个', 终.length === 12, `实际 ${终.length} 个：${终.map((n) => n.标题).join(' / ')}`);
  const 终指纹 = 指纹(终);
  断言('类型+标题指纹与 FV-3 基线一致', 终指纹 === FV3指纹, 终指纹 === FV3指纹 ? '' : `\n     终态 ${终指纹}\n     基线 ${FV3指纹}`);
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFV12.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
