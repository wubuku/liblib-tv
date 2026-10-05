// ⭐⭐⭐⭐⭐ Batch FQ-6：三个待解之谜
//
//   ① 「智能剪辑**4**」标题上那个 4 是什么？
//      FQ-5 建完节点后主画布上有 **2 个** video-clip 节点，
//      标题却是「智能剪辑 4」⇒ **不是同名实例计数**。
//      另一个候选：内部 4 个「尝试」项（讲解视频/批量广告/口播视频/素材混剪）。
//   ② 「剧本生成分镜脚本」/「角色生成分镜脚本」/「自己编写分镜脚本」点下去分别去哪？
//      FQ-3 试过「自己编写分镜脚本」，但那次**点击被另一个节点吃掉了**（缺陷 463），
//      面板其实没切 —— 读数是假的。必须在**中心落点自证通过**的前提下重试。
//   ③ 「首帧生成视频」/「首尾帧生成视频」这两枚可点按钮在哪、属于谁？
//      它们在危险扫描里冒出来过，`禁用:false` + `cursor:pointer`。
//      ⭐ 关联 `scriptV2BatchStepSelectVideoModel = 切换到支持「首帧生视频」的视频模型`
//
// ⛔ 安全边界：
//   ⛔ 不点「开始拉片」「首帧生成视频」「首尾帧生成视频」「开始创作」
//   ⛔ 不点「剧本生成分镜脚本」「角色生成分镜脚本」—— 名字写着「生成」
//   ✅ 只点「自己编写分镜脚本」（编辑器入口）—— 进去只量结构，不输入不提交，Esc 出来
import { launch, closePromos, ORIGIN, 全页文字, 归一, 断言器, 找节点, 中心属主, 量浮层 } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const 主画布 = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 证据图: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFQ6.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = 断言器(记);

const 浏览器 = await launch();
const page = 浏览器.page;

/** ⭐⭐ 点的落点自证：hit 的 closest(button) 的归一文字必须等于要找的文案。 */
async function 点自己核(文案, { 记: 记f = 记 } = {}) {
  const b = await page.evaluate((t) => {
    const 归 = (s) => (s || '').replace(/\s+/g, '');
    for (const el of document.querySelectorAll('button,[role="button"]')) {
      const r = el.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) continue;
      if (归(el.innerText) !== 归(t) && 归(el.getAttribute('aria-label')) !== 归(t)) continue;
      const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
      const hit = document.elementFromPoint(cx, cy);
      const owner = hit && hit.closest('button,[role="button"]');
      return {
        框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        点: [cx, cy],
        属主文字: owner ? 归(owner.innerText || owner.getAttribute('aria-label') || '') : null,
        属主类: owner ? String(owner.className || '').slice(0, 60) : null,
      };
    }
    return null;
  }, 文案);
  记f(`   点「${文案}」${JSON.stringify(b)}`);
  if (!b) { 断言(false, `页面上找得到「${文案}」`, null); return false; }
  if (!断言(b.属主文字 === 归一(文案), `「${文案}」的落点属主就是它自己（⛔ FQ-3 就栽在这）`, b)) return false;
  await page.mouse.move(b.点[0] - 50, b.点[1]); await page.waitForTimeout(300);
  await page.mouse.click(b.点[0], b.点[1]);
  await page.waitForTimeout(6000);
  return true;
}

try {
  await page.goto(主画布, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(14000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);

  // ── ① 标题上那个数字
  记('=== ① 每个节点的标题文本 ===');
  R.读数.标题 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')]
    .filter((n) => { const r = n.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
    .map((n) => {
      const r = n.getBoundingClientRect();
      // 标题 = 节点里第一个有文字的子元素，或节点自身文本的前 20 字
      const 头 = [...n.children].find((c) => (c.innerText || '').trim().length > 0 && c.getBoundingClientRect().height < 40);
      return {
        id: n.getAttribute('data-id'),
        类: (String(n.className).match(/node-([a-z0-9-]+)/) || [, '?'])[1],
        框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        标题: (头 ? 头.innerText : n.innerText).replace(/\s+/g, ' ').trim().slice(0, 30),
        文本前30: n.innerText.replace(/\s+/g, ' ').trim().slice(0, 30),
      };
    }));
  记('   ' + JSON.stringify(R.读数.标题, null, 1));

  const 剪辑们 = R.读数.标题.filter((t) => t.类 === 'video-clip');
  记(`   ⭐ video-clip 节点 ${剪辑们.length} 个，标题分别是 ` + JSON.stringify(剪辑们.map((t) => t.标题)));
  断言(剪辑们.length >= 2, `主画布上现在有 ${剪辑们.length} 个智能剪辑节点（建前 1 个 + FQ-5 建 1 个）`, 剪辑们.length);
  const 数字集 = [...new Set(剪辑们.map((t) => (t.标题.match(/智能剪辑\s*(\d+)/) || [])[1]).filter(Boolean))];
  记('   ⭐ 标题里的数字集合 = ' + JSON.stringify(数字集));
  断言(数字集.length === 0 || 数字集.every((d) => d === String(剪辑们.length)),
    `标题数字不是「同名实例序号」（有 ${剪辑们.length} 个节点，数字却是 ${JSON.stringify(数字集)}）`,
    { 节点数: 剪辑们.length, 数字: 数字集 });

  // ── ② 点「自己编写分镜脚本」（这次带落点自证）
  记('=== ② 「自己编写分镜脚本」===');
  const 脚本id = await 找节点(page, 'node-script-v2');
  记('   script-v2 节点 id = ' + 脚本id);
  const 前 = new Set((await 全页文字(page)).map(归一));
  断言(前.has(归一('自己编写分镜脚本')), '点之前「自己编写分镜脚本」在页面上', [...前].filter((t) => t.includes('分镜')));

  if (await 点自己核('自己编写分镜脚本')) {
    const 后 = new Set((await 全页文字(page)).map(归一));
    断言(![...后].some((t) => t === 归一('自己编写分镜脚本')),
      '点掉之后独占文案「自己编写分镜脚本」消失（面板确实切了）',
      [...后].filter((t) => t.includes('分镜脚本')));
    R.读数.编辑器文本 = [...后];
    记('   进编辑器后新增文本 ' + JSON.stringify([...后].filter((t) => !前.has(t)).slice(0, 40)));
    R.读数.浮层 = (await 量浮层(page, 'div')).filter((f) => Number(f.z) >= 90).slice(0, 10);
    记('   高 z 浮层 ' + JSON.stringify(R.读层 || R.读数.浮层));
    await page.screenshot({ path: resolve(EVID, 'fq6-1-自己编写分镜脚本.png') });
    R.证据图.push({ 文件: 'fq6-1-自己编写分镜脚本.png' });
    记('   📷 fq6-1-自己编写分镜脚本.png');

    // Esc 退出，断言独占文案回归
    await page.keyboard.press('Escape');
    await page.waitForTimeout(2800);
    const 回 = new Set((await 全页文字(page)).map(归一));
    断言(回.has(归一('自己编写分镜脚本')), 'Esc 之后「自己编写分镜脚本」回来了（退出了编辑器）',
      [...回].filter((t) => t.includes('分镜')));
  }

  // ── ③ 「首帧生成视频」/「首尾帧生成视频」在哪
  记('=== ③ 找「首帧生成视频」「首尾帧生成视频」===');
  R.读数.首帧 = await page.evaluate(() => {
    const 归 = (s) => (s || '').replace(/\s+/g, '');
    return [...document.querySelectorAll('button,[role="button"]')]
      .map((b) => {
        const r = b.getBoundingClientRect();
        if (!(r.width > 0 && r.height > 0)) return null;
        const t = 归(b.innerText) || 归(b.getAttribute('aria-label'));
        if (!/首帧|首尾帧/.test(t)) return null;
        const n = b.closest('.react-flow__node');
        const cs = getComputedStyle(b);
        return {
          文字: t, 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          所属节点: n ? n.getAttribute('data-id') : null,
          所属类: n ? (String(n.className).match(/node-([a-z0-9-]+)/) || [, '?'])[1] : null,
          禁用: b.disabled === true, cursor: cs.cursor,
          外层文字: 归(b.parentElement?.parentElement?.innerText || '').slice(0, 90),
        };
      }).filter(Boolean);
  });
  记('   ⭐ ' + JSON.stringify(R.读数.首帧, null, 1));
  断言(R.读数.首帧.length > 0, '「首帧/首尾帧生成视频」两枚按钮真实存在', R.读数.首帧.length);

  记(`断言统计 ${JSON.stringify(断言.统计)}`);
  R.读数.断言 = 断言.统计;
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFQ6.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
