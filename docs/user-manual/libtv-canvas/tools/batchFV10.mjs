// ⭐⭐⭐⭐⭐ Batch FV-10：连建两个同类节点 + 清理，确认 `{index}` 是固定常量还是计数器
//
// FV-9 已坐实：**全新建的文本节点也是「文本节点 1」**，
// 而画布上已经有**两个**「文本节点 1」⇒ 它**不是**「画布上第几个同类节点」。
//
// 剩下唯一要分清的是：
//   K1「每种类型一个固定常量」—— 文本永远是 1、图片永远是 2…
//   K2「本次会话内的计数器」—— 连建两个会拿到 1 和 2
//
// ⭐ FV-9 的读数已经**同时命中**了 1、2、3、4、5 五种类型：
//     文本1  图片2  视频3  智能剪辑4  导演台5
// 而「音频节点 1」「脚本 V2 1」是**反例** —— 按添加节点面板顺序，音频该是 7。
// ⇒ K1 成立但**不完全**，所以这一轮要把音频也新建一个看它拿几号。
//
// 本轮做三件事：
//   ① 连建 **两个文本节点**（K1/K2 判据）
//   ② 建 **一个音频节点**（反例复核）
//   ③ 全部从资产管理抽屉的「⋯ → 删除」删掉，⛔ 绝不按 Delete / Backspace
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 断言: [], 待删: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFV10.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
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

// 打开添加节点面板，返回「面板容器」内某一类项的坐标
const 开面板 = async () => {
  const t = await page.evaluate(() => {
    const e = document.querySelector('[aria-label="添加节点"]');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  });
  if (!t) return null;
  await page.mouse.click(t[0], t[1]);
  await page.waitForTimeout(1200);
  return page.evaluate(() => {
    // 面板容器 = 含「智能剪辑」和「逐帧拉片」但不含「图片节点」的最内层 div
    const 候选 = [...document.querySelectorAll('div')].filter((d) => {
      const t = (d.innerText || '');
      return /智能剪辑/.test(t) && /逐帧拉片/.test(t) && /音频/.test(t) && !/图片节点/.test(t) && !/视频节点/.test(t);
    });
    候选.sort((a, b) => a.getBoundingClientRect().height - b.getBoundingClientRect().height);
    const box = 候选[0];
    if (!box) return null;
    const br = box.getBoundingClientRect();
    const 项 = [];
    for (const el of box.querySelectorAll('*')) {
      const s = (el.innerText || '').trim();
      if (!s || s.length > 20) continue;
      const r = el.getBoundingClientRect();
      if (r.width < 40 || r.height < 12) continue;
      if ([...el.querySelectorAll('*')].some((c) => c.innerText === s)) continue;  // 只留叶子
      项.push({ 文字: s, x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) });
    }
    const seen = new Set();
    return { 框: [Math.round(br.x), Math.round(br.y), Math.round(br.width), Math.round(br.height)],
      项: 项.filter((o) => { if (seen.has(o.文字)) return false; seen.add(o.文字); return true; }) };
  });
};

const 建节点 = async (类型) => {
  const p = await 开面板();
  if (!p) { 记('  ⛔ 面板没开'); return null; }
  const it = p.项.find((x) => x.文字 === 类型 || x.文字.startsWith(类型));
  if (!it) { 记(`  ⛔ 面板里没有「${类型}」，实有：${p.项.map((x) => x.文字).join('/')}`); return null; }
  const 落 = await page.evaluate(({ x, y }) => {
    const e = document.elementFromPoint(x, y);
    return e ? { tag: e.tagName, 文字: (e.innerText || '').trim().slice(0, 10) } : null;
  }, { x: it.x + Math.min(24, it.w / 2), y: it.y + it.h / 2 });
  记(`  面板项「${it.文字}」@${it.x},${it.y} ${it.w}×${it.h}；落点 ${落?.tag}「${落?.文字}」`);
  await page.mouse.click(it.x + Math.min(24, it.w / 2), it.y + it.h / 2);
  await page.waitForTimeout(1800);
  return true;
};

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(14000);
  await closePromos(page);

  const 前 = await 快照();
  R.读数.前 = 前;
  const 前id = 前.map((n) => n.id);
  断言('开跑前 12 个节点', 前.length === 12, `${前.length} 个`);
  记(`开跑前标题：${前.map((n) => n.标题).join(' / ')}`);

  // FV-9 留下的那个文本节点还在，先记下它的 id 一起清理
  // ── ① 连建两个文本节点
  记('\n--- ① 连建两个文本节点 ---');
  for (let i = 1; i <= 2; i++) {
    await 建节点('文本');
    const s = await 快照();
    const 新 = s.filter((n) => !前id.includes(n.id));
    R.读数[`文本第${i}次后`] = 新;
    记(`  第 ${i} 次建完，新增 ${新.length} 个：${新.map((n) => `\`${n.标题}\``).join(' ')}`);
    新.forEach((n) => { if (!R.待删.includes(n.id)) R.待删.push(n.id); });
  }
  const 两个 = R.读数['文本第2次后'] || [];
  if (两个.length >= 2) {
    断言('K1 固定常量', 两个[0].标题 === 两个[1].标题,
      `两次都建出 \`${两个.map((n) => n.标题).join('` / `')}\` ⇒ ${两个[0].标题 === 两个[1].标题 ? '固定常量' : '会话内递增'}`);
  } else 断言('K1 固定常量', false, `只建出 ${两个.length} 个`);

  // ── ② 建一个音频节点（反例复核）
  记('\n--- ② 建一个音频节点 ---');
  await 建节点('音频');
  const s2 = await 快照();
  const 新2 = s2.filter((n) => !前id.includes(n.id) && !R.待删.includes(n.id));
  R.读数.音频 = 新2;
  记(`  新增音频节点：${新2.map((n) => `\`${n.标题}\``).join(' ') || '（无）'}`);
  新2.forEach((n) => { if (!R.待删.includes(n.id)) R.待删.push(n.id); });
  await page.screenshot({ path: resolve(EVID, 'fv10-1-建完之后.png') });

  // ── ③ 清理：从资产管理抽屉的「⋯ → 删除」菜单逐个删
  记(`\n--- ③ 清理 ${R.待删.length} 个测试节点（⛔ 不用 Delete/Backspace）---`);
  记(`待删 id：${R.待删.join(', ')}`);
  R.读数.清理前 = await 快照();
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFV10.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
