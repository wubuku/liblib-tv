// ⭐⭐⭐⭐⭐ Batch FQ-5：改在**主画布**建三个节点（测试画布已判死）
//
// ⛔ FQ-4 的诊断 —— **测试画布 a4ef3de0… 是个坏画布，判死**：
//   21 个节点**几乎两两全部重叠**（重叠比 0.27~1.00），
//   `⌘0` 后 zoom 仍是 0.985（≈没缩）⇒ fit view 根本没把它们铺开。
//   「整理画布」也找不到入口（落点 null，它的文案/aria 与手册记的不一样）。
//   ⭐ 但 FQ-4 的**中心落点自证**工作正常：脚本 V2 节点中心属主读出
//     `v-k2vgxqBYjU`(video-clip, selected) ⇒ 诊断「被别的节点盖住」完全准确。
//     这条判据已经固化进 lib.mjs 的 `中心属主` / `拍节点` / `查重叠`。
//
// ⭐⭐⭐ 换主画布的**决定性理由**：FQ-1 读到的添加节点面板里本来就有
//   `视频 / 智能剪辑 Beta / 导演台 NEW / 逐帧拉片 🏷 SD 2.5 / 音频 / 脚本 › / 素材库 ›`
//   —— 「智能剪辑」和「逐帧拉片」**在主画布上一样能建**，主画布只是没建过。
//   而主画布节点整齐不重叠、`⌘0` 正常（zoom 0.4827）⇒ 截图干净。
//   （画布名字就叫「手册取证画布」，多三个节点是它的本职；基线会在 PROGRESS 更新。）
//
// ⛔ 安全边界：建节点**不消耗积分**（FQ-1 实测建完危险按钮 0 枚）；
//   建完一个生成按钮都不点，危险按钮只扫不点。
import { launch, closePromos, ORIGIN, 全页文字, 归一, 断言器, 找节点, 中心属主, 查重叠, 拍节点 } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const 主画布 = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 证据图: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFQ5.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = 断言器(记);

const 浏览器 = await launch();
const page = 浏览器.page;

const 危险 = ['批量生成分镜', '批量生视频', '一键合成全部提示词', '重新生成脚本', '批量生成资产图', '确认续写', '下载', '同意并使用', '开始生成', '开始拉片', '立即生成', '提交', '开始创作', '生成视频'];
async function 扫危险(标签) {
  const 命中 = await page.evaluate((黑) => {
    const 归 = (s) => (s || '').replace(/\s+/g, '');
    return [...document.querySelectorAll('button,[role="button"]')].map((b) => {
      const r = b.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) return null;
      const t = 归(b.innerText) || 归(b.getAttribute('aria-label')) || 归(b.title);
      if (!t || !黑.some((k) => t.includes(归(k)))) return null;
      const cs = getComputedStyle(b);
      return { 文字: t.slice(0, 20), 禁用: b.disabled === true, opacity: Number(cs.opacity).toFixed(2), cursor: cs.cursor };
    }).filter(Boolean);
  }, 危险);
  记(`   ⛔ ${标签}：危险按钮 ${命中.length} 枚 ${JSON.stringify(命中)}`);
  return 命中;
}

/** 在添加节点面板里点一行（带落点自证 + 点击后独占文案消失）。 */
async function 点添加节点行(关键词, { 记: 记f = 记 } = {}) {
  const 行 = await page.evaluate((kw) => {
    const 归 = (s) => (s || '').replace(/\s+/g, '');
    for (const el of document.querySelectorAll('div,button,[role="button"],[role="menuitem"]')) {
      const r = el.getBoundingClientRect();
      if (!(r.width > 100 && r.height > 20 && r.height < 60)) continue;
      const t = 归(el.innerText);
      if (!t.startsWith(kw) || t.length > kw.length + 8) continue;
      const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
      const hit = document.elementFromPoint(cx, cy);
      return {
        文字: t, 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 点: [cx, cy],
        命中文字: hit ? 归(hit.closest('div,button,[role="button"]')?.innerText || '').slice(0, 20) : null,
      };
    }
    return null;
  }, 关键词);
  记f('   「' + 关键词 + '」行 ' + JSON.stringify(行));
  断言(!!行, `添加节点面板里找得到「${关键词}」这一行`, 行);
  if (!行) return false;
  断言(行.命中文字 === 行.文字, `「${关键词}」行的落点属主就是它自己`, 行);
  await page.mouse.move(行.点[0] - 40, 行.点[1]); await page.waitForTimeout(300);
  await page.mouse.click(行.点[0], 行.点[1]);
  await page.waitForTimeout(2600);
  return true;
}

const 开添加节点 = async () => {
  const b = await page.evaluate(() => {
    for (const x of document.querySelectorAll('button,[role="button"]')) {
      if ((x.getAttribute('aria-label') || '') !== '添加节点') continue;
      const r = x.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0) || !(r.top > 700)) continue;
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    }
    return null;
  });
  if (!b) return false;
  await page.mouse.click(b[0], b[1]);
  await page.waitForTimeout(2000);
  return true;
};

try {
  await page.goto(主画布, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(14000);
  记('closePromos：' + JSON.stringify(await closePromos(page)).slice(0, 80));
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2800);

  R.读数.建前 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')]
    .filter((n) => { const r = n.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
    .map((n) => { const r = n.getBoundingClientRect(); return { id: n.getAttribute('data-id'), 类: (String(n.className).match(/node-([a-z0-9-]+)/) || [, '?'])[1], 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }));
  记('   建前主画布节点 ' + JSON.stringify(R.读数.建前));
  R.读数.建前重叠 = await 查重叠(page);
  记('   建前重叠对数 ' + R.读数.建前重叠.length);
  断言(R.读数.建前重叠.length === 0, '主画布建前没有大面积重叠（测试画布有 105 对）', R.读数.建前重叠.length);

  R.读数.zoom = await page.evaluate(() => document.querySelector('.react-flow__viewport')?.style.transform || null);
  记('   ⌘0 后 transform ' + JSON.stringify(R.读数.zoom));

  // ── 建「智能剪辑」
  记('=== 建「智能剪辑」节点 ===');
  await 开添加节点();
  if (await 点添加节点行('智能剪辑')) {
    await page.waitForTimeout(5000);
    await 扫危险('建智能剪辑后');
    const id = await 找节点(page, 'node-video-clip');
    记('   建出来的 video-clip 节点 id = ' + id);
    断言(!!id, '主画布上现在有 video-clip 节点了', id);
  }
  await page.keyboard.press('Escape');
  await page.waitForTimeout(1500);

  // ── 建「逐帧拉片」
  记('=== 建「逐帧拉片」节点 ===');
  await 开添加节点();
  if (await 点添加节点行('逐帧拉片')) {
    await page.waitForTimeout(5000);
    await 扫危险('建逐帧拉片后');
    const id = await 找节点(page, 'node-shot-breakdown');
    记('   建出来的 shot-breakdown 节点 id = ' + id);
    断言(!!id, '主画布上现在有 shot-breakdown 节点了', id);
  }
  await page.keyboard.press('Escape');
  await page.waitForTimeout(1500);

  // ── 建「脚本 NEW」
  记('=== 建「脚本 NEW」节点 ===');
  await 开添加节点();
  if (await 点添加节点行('脚本')) {
    const 新 = await page.evaluate(() => {
      const 归 = (s) => (s || '').replace(/\s+/g, '');
      for (const el of document.querySelectorAll('div,button,[role="menuitem"]')) {
        const r = el.getBoundingClientRect();
        if (!(r.width > 40 && r.height > 15 && r.height < 60)) continue;
        if (归(el.innerText) !== '脚本NEW') continue;
        return { 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
      }
      return null;
    });
    记('   「脚本 NEW」' + JSON.stringify(新));
    if (新) { await page.mouse.click(新.点[0], 新.点[1]); await page.waitForTimeout(5500); }
    await 扫危险('建脚本 V2 后');
    const id = await 找节点(page, 'node-script-v2');
    记('   建出来的 script-v2 节点 id = ' + id);
    断言(!!id, '主画布上现在有 script-v2 节点了', id);
  }
  await page.keyboard.press('Escape');
  await page.waitForTimeout(1800);

  // ── ⌘0 重新适配，然后量重叠
  记('=== 建完重新 ⌘0 并量重叠 ===');
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3200);
  R.读数.建后 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')]
    .filter((n) => { const r = n.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
    .map((n) => { const r = n.getBoundingClientRect(); return { id: n.getAttribute('data-id'), 类: (String(n.className).match(/node-([a-z0-9-]+)/) || [, '?'])[1], 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }));
  记('   建后节点 ' + JSON.stringify(R.读数.建后));
  R.读数.建后重叠 = await 查重叠(page);
  记('   ⛔ 建后重叠对：' + JSON.stringify(R.读数.建后重叠));
  R.读数.zoom2 = await page.evaluate(() => document.querySelector('.react-flow__viewport')?.style.transform || null);
  记('   建后 transform ' + JSON.stringify(R.读数.zoom2));

  // ── 拍三个节点（用 lib.mjs 的判据工具，自带中心落点自证）
  记('=== 拍三个新节点 ===');
  R.读数.拍_脚本 = await 拍节点(page, 'node-script-v2', 'fq5-1-脚本V2节点.png', { 记, 断言, 证据目录: EVID });
  R.读数.拍_剪辑 = await 拍节点(page, 'node-video-clip', 'fq5-2-智能剪辑节点.png', { 记, 断言, 证据目录: EVID });
  R.读数.拍_拉片 = await 拍节点(page, 'node-shot-breakdown', 'fq5-3-逐帧拉片节点.png', { 记, 断言, 证据目录: EVID });
  await 扫危险('拍完三个');

  await page.screenshot({ path: resolve(EVID, 'fq5-0-主画布建完全景.png') });
  R.证据图.push({ 文件: 'fq5-0-主画布建完全景.png' });
  记('   📷 fq5-0-主画布建完全景.png');

  记(`断言统计 ${JSON.stringify(断言.统计)}`);
  R.读数.断言 = 断言.统计;
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFQ5.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
