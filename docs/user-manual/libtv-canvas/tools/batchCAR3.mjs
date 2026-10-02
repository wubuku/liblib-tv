// Batch CA-R3 — 把顶替节点拖回被误删那个原来的位置，然后收口。
//
// 现状核对（CA-R2 之后）：节点 11 个、组成正确（2 文本 / 2 音频 / 2 图片 / 2 视频 /
// 1 拉片 / 1 导演台 —— ⚠️ 原本就只有 **2 个**文本节点，CA-R2 脚本里写的「目标 3」是我数错了）、
// 连线 2 条未动。唯一没复原的是**位置**：顶替节点 `t-2AK3Ukyxj3` 落在「添加节点」面板的锚点上，
// 被误删的 `t-xVGmDWNLaZ` 原来在左下 `[150,671]`。
//
// 本轮只做一件事：把它拖回那个坐标，然后复核。
// ⭐ 拖之前先记下**两边的坐标**，拖完再读一次 —— 凭「看起来差不多了」不算复原。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, beginBatch, logStep } from './scenario.mjs';
import { fitView, nodeCount } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchCAR3';
const NEW_ID = 't-2AK3Ukyxj3';
const OLD_POS = [150, 671];          // 被误删节点的原屏幕坐标
const { browser, page } = await launch();
const settle = (ms = 900) => page.waitForTimeout(ms);
const ids = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')));
const boxOf = (id) => page.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null; const r = n.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; }, id);
const edgeAria = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')].map((e) => e.getAttribute('aria-label')));

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await settle(1800);
  await fitView(page); await settle(2200);
  await beginBatch(B, { note: '把顶替节点拖回原位置' });
  const out = {};

  const start = await ids();
  out.start = { count: start.length, has: start.includes(NEW_ID) };
  const box0 = await boxOf(NEW_ID);
  out.before = box0;
  console.log(`═══ 现状：节点 ${start.length}｜${NEW_ID} 在不在=${out.start.has}`);
  console.log(`  顶替节点当前矩形：${JSON.stringify(box0)}｜目标左上角：${JSON.stringify(OLD_POS)}`);

  if (!box0) { console.log('⛔ 顶替节点不在视口里，本轮到此为止'); }
  else {
    // 从节点标题那条（上方 1/4 处）起拖，避开内部可点区域
    const grab = [box0[0] + Math.round(box0[2] / 2), box0[1] + 14];
    const delta = [OLD_POS[0] - box0[0], OLD_POS[1] - box0[1]];
    console.log(`  起手点 ${JSON.stringify(grab)}｜位移 ${JSON.stringify(delta)}`);
    await page.mouse.move(grab[0], grab[1]); await settle(700);
    await page.mouse.down(); await settle(400);
    for (let s = 1; s <= 10; s += 1) {
      await page.mouse.move(grab[0] + delta[0] * (s / 10), grab[1] + delta[1] * (s / 10));
      await settle(130);
    }
    await page.mouse.up(); await settle(2200);
    const box1 = await boxOf(NEW_ID);
    out.after = box1;
    out.moved = { delta, offBy: box1 ? [box1[0] - OLD_POS[0], box1[1] - OLD_POS[1]] : null };
    console.log(`  拖完矩形：${JSON.stringify(box1)}｜与目标的偏差：${JSON.stringify(out.moved.offBy)}`);
  }

  const fin = await ids();
  out.final = { count: fin.length, ids: fin, edges: await edgeAria() };
  console.log(`\n═══ 收口 ═══`);
  console.log(`  节点 ${fin.length}｜连线 ${JSON.stringify(out.final.edges)}`);
  console.log(`  id 清单：${JSON.stringify(fin)}`);
  console.log(`\n═══ 本轮结论 ═══`);
  console.log(`  · 位置复原：${out.after ? `偏差 ${JSON.stringify(out.moved.offBy)} 像素` : '未测到'}`);
  console.log(`  · 节点数 11：${fin.length === 11 ? '✅' : '❌'}`);

  await logStep(B, {
    id: 'CA-repair-part3-position',
    title: '顶替节点拖回原位置，收口',
    target: 'CA-R2 之后只剩**位置**没复原：顶替节点落在「添加节点」面板锚点上。'
      + '拖之前先记坐标、拖完再读一次 —— 凭「看起来差不多」不算复原。'
      + '⚠️ 顺带更正 CA-R2 脚本里我自己数错的目标值：原本就只有 **2 个**文本节点，不是 3 个。',
    evidence: out,
    visible_text: JSON.stringify({ 现状: out.start, 拖前: out.before, 拖后: out.after, 收口: out.final }).slice(0, 2500),
  });
  console.log('\nCA-R3 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 5).join('\n'));
} finally {
  await browser.close();
}
