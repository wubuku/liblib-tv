// ⭐⭐⭐⭐⭐ Batch FQ-3：三个「主画布上没有的节点」内部深挖 + 成品截图
//
// FQ-2 拿到的界面（全部实测，class 名即类型）：
//   ① script-v2        「脚本生成器」 尝试：剧本生成分镜脚本 / 角色生成分镜脚本 / 自己编写分镜脚本
//   ② video-clip       「智能剪辑」 4 空空如也，请连接视频节点后操作
//                      尝试：讲解视频 / 批量广告 / 口播视频 / 素材混剪
//   ③ shot-breakdown   「逐帧拉片 SD 2.5」 视频素材 上传视频后开始
//                      拆解维度 分镜 / 动态 / 音乐  「开始拉片」灰
//
// ⭐⭐⭐⭐ FQ-2 撞出的第四条灰态反例（推翻手册里「灰 = opacity 0.45」）：
//   「开始拉片」`disabled=true` + **`opacity: 1.00`** + `cursor: not-allowed`
//   ⇒ **`opacity` 不是灰的判据**，`disabled` + `cursor` 才是。
//
// ⛔ 安全边界：
//   ⛔ 不点「剧本生成分镜脚本」/「角色生成分镜脚本」—— 名字就写着「生成」，可能起任务
//   ⛔ 不点「上传视频后开始」—— 要真传文件，且拉片要消耗积分
//   ⛔ 不点「开始拉片」—— 本来就灰，但即使亮了也不点
//   ⛔ 不点「讲解视频 / 批量广告 / 口播视频 / 素材混剪」—— 都要连视频 + 起剪辑任务
//   ✅ 只点「自己编写分镜脚本」—— 字面语义是「自己写」，是个编辑器入口，
//      进编辑器只读、不输入、不提交；进去先量结构，出界用 Esc
import { launch, closePromos, ORIGIN, 全页文字, 归一, 断言器, 量浮层, shot } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const 测试画布 = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=a4ef3de0cdca4977ba45b373eb5165b5`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 证据图: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFQ3.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = 断言器(记);

const 浏览器 = await launch();
const page = 浏览器.page;

const 危险 = ['批量生成分镜', '批量生视频', '一键合成全部提示词', '重新生成脚本', '批量生成资产图', '生成资产图', '确认续写', '下载', '同意并使用', '开始生成', '开始拉片', '立即生成', '提交'];
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

/** 把一个节点单独圈出来截图（先高亮，再拍节点框 + 一点余量）。 */
async function 拍节点(类型, 文件) {
  const 框 = await page.evaluate((t) => {
    const n = [...document.querySelectorAll('.react-flow__node')].find((e) => String(e.className).includes(t));
    if (!n) return null;
    const r = n.getBoundingClientRect();
    return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
  }, 类型);
  if (!框) { 记('   ⛔ 找不到节点 ' + 类型); return null; }
  const clip = {
    x: Math.max(0, 框[0] - 24), y: Math.max(0, 框[1] - 24),
    width: Math.min(1440 - Math.max(0, 框[0] - 24), 框[2] + 48),
    height: Math.min(810 - Math.max(0, 框[1] - 24), 框[3] + 48),
  };
  await page.screenshot({ path: resolve(EVID, 文件), clip });
  R.证据图.push({ 文件, clip, 节点框: 框 });
  记(`   📷 ${文件}｜节点框 ${JSON.stringify(框)}｜裁剪 ${JSON.stringify(clip)}`);
  return { 框, clip };
}

try {
  await page.goto(测试画布, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(14000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);

  // ── ① 三个节点的证据图
  记('=== ① 拍三个节点的证据图 ===');
  await 拍节点('node-script-v2', 'fq3-1-脚本V2节点.png');
  await 拍节点('node-video-clip', 'fq3-2-智能剪辑节点.png');
  await 拍节点('node-shot-breakdown', 'fq3-3-逐帧拉片节点.png');
  // 全景（看三者在画布上的相对位置）
  await page.screenshot({ path: resolve(EVID, 'fq3-0-测试画布全景.png') });
  R.证据图.push({ 文件: 'fq3-0-测试画布全景.png' });
  记('   📷 fq3-0-测试画布全景.png');

  // ── ② 点「自己编写分镜脚本」进编辑器（⛔ 只读，不输入不提交）
  记('=== ② 脚本生成器 →「自己编写分镜脚本」 ===');
  const 独有 = '自己编写分镜脚本';
  const 前 = new Set((await 全页文字(page)).map(归一));
  断言(前.has(归一(独有)), `点之前「${独有}」在页面上`, [...前].filter((t) => t.includes('分镜脚本')));

  const b = await page.evaluate((t) => {
    const 归 = (s) => (s || '').replace(/\s+/g, '');
    for (const el of document.querySelectorAll('button,[role="button"]')) {
      const r = el.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) continue;
      if (归(el.innerText) !== 归(t) && 归(el.getAttribute('aria-label')) !== 归(t)) continue;
      const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
      const hit = document.elementFromPoint(cx, cy);
      return { 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 点: [cx, cy], 命中: hit ? 归(hit.closest('button,[role="button"]')?.innerText || '') : null };
    }
    return null;
  }, 独有);
  记('   「自己编写分镜脚本」' + JSON.stringify(b));
  断言(!!b && b.命中 === 归一(独有), '「自己编写分镜脚本」的落点属主就是它自己', b);

  if (b) {
    await page.mouse.move(b.点[0] - 50, b.点[1]); await page.waitForTimeout(250);
    await page.mouse.click(b.点[0], b.点[1]);
    await page.waitForTimeout(6000);
    const 后 = new Set((await 全页文字(page)).map(归一));
    断言(![...后].some((t) => t === 归一(独有)), `点掉之后独占文案「${独有}」消失（面板确实切了）`, [...后].filter((t) => t.includes('分镜脚本')));
    R.读数.编辑器文本 = [...后];
    记('   进编辑器后页面前 30 条文本 ' + JSON.stringify([...后].slice(0, 30)));
    await 扫危险('进编辑器后');
    R.读数.编辑器浮层 = await 量浮层(page, 'div');
    R.读数.编辑器浮层 = R.读数.编辑器浮层.filter((f) => f.z && f.z !== 'auto' && Number(f.z) >= 100).slice(0, 8);
    记('   高 z 浮层 ' + JSON.stringify(R.读数.编辑器浮层));
    await page.screenshot({ path: resolve(EVID, 'fq3-4-自己编写分镜脚本.png') });
    R.证据图.push({ 文件: 'fq3-4-自己编写分镜脚本.png' });
    记('   📷 fq3-4-自己编写分镜脚本.png');

    // ⛔ Esc 退出，断言独占文案回归
    await page.keyboard.press('Escape');
    await page.waitForTimeout(2500);
    const 回 = new Set((await 全页文字(page)).map(归一));
    断言(回.has(归一(独有)), `Esc 之后独占文案「${独有}」回来了（退出了编辑器）`, [...回].filter((t) => t.includes('分镜脚本')));
  }

  记(`断言统计 ${JSON.stringify(断言.统计)}`);
  R.读数.断言 = 断言.统计;
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFQ3.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
