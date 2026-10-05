// ⭐⭐⭐⭐⭐ Batch FV-11：清理 FV-9 留下的节点 + 用精确文本定位重做 K1/K2
//
// 两件事：
//   ① ⛔ **清理**：FV-9 建出来的一个文本节点还留在主画布上（13 个了），必须删掉。
//      走资产管理抽屉的「⋯ → 删除」菜单（M-45 实测：可用、无确认框），
//      ⛔ 绝不按 Delete / Backspace。
//   ② K1/K2：连建两个文本节点，看它们是不是都拿 1。
//      FV-10 失败的原因是面板解析器**把「文本/图片/视频/音频」全过滤掉了**
//      —— 它用「祖先里有同名 innerText 就丢掉」来只留叶子，
//      而这四项外面都包着带图标的容器 ⇒ 全部被误杀。
//      ⭐ 教训：**「只留叶子」这个常见技巧，遇到带图标的菜单项就会连真项一起杀。**
//      本轮改成：innerText 精确等于目标词 + 尺寸合理 + 位于面板框内。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 断言: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFV11.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
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

const 点aria = async (名, 停 = 1200) => {
  const t = await page.evaluate((n) => {
    const e = document.querySelector(`[aria-label="${n}"]`);
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  }, 名);
  if (!t) { 记(`  ⛔ 找不到 aria="${名}"`); return false; }
  await page.mouse.click(t[0], t[1]);
  await page.waitForTimeout(停);
  return true;
};

const 开面板并找 = async (词) => page.evaluate((w) => {
  // 面板 = 一个「窄条状容器」，里面同时含 智能剪辑 / 逐帧拉片 / 素材库
  const 候选 = [...document.querySelectorAll('div')].filter((d) => {
    const t = (d.innerText || '');
    return /智能剪辑/.test(t) && /逐帧拉片/.test(t) && /素材库/.test(t) && !/视频节点/.test(t) && !/图片节点/.test(t);
  });
  候选.sort((a, b) => a.getBoundingClientRect().height - b.getBoundingClientRect().height);
  const box = 候选[0];
  if (!box) return { 错: '没找到面板容器' };
  const br = box.getBoundingClientRect();
  const out = [];
  for (const el of box.querySelectorAll('*')) {
    if ((el.innerText || '').trim() !== w) continue;      // ⭐ 精确等于，不做「只留叶子」
    const r = el.getBoundingClientRect();
    if (r.width < 30 || r.height < 10) continue;
    out.push({ x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) });
  }
  out.sort((a, b) => a.y - b.y);
  return { 框: [Math.round(br.x), Math.round(br.y), Math.round(br.width), Math.round(br.height)], 命中: out };
}, 词);

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(14000);
  await closePromos(page);

  const 前 = await 快照();
  R.读数.前 = 前;
  断言('开跑前节点数（应为 13，含 FV-9 留下的）', 前.length === 13, `${前.length} 个`);
  记(`开跑前：${前.map((n) => n.标题).join(' / ')}`);

  // ── ① 先做 K1/K2，趁节点还在
  记('\n--- ① 连建两个文本节点（K1 固定常量 vs K2 会话内递增）---');
  const 建的 = [];
  for (let i = 1; i <= 2; i++) {
    const ok = await 点aria('添加节点');
    if (!ok) { 记('  ⛔ 添加节点按钮找不到'); break; }
    const f = await 开面板并找('文本');
    if (f.错 || !f.命中 || !f.命中.length) { 记(`  ⛔ ${f.错 || '面板里定位不到「文本」'}`); await page.keyboard.press('Escape'); await page.waitForTimeout(500); continue; }
    const it = f.命中[0];
    const 落 = await page.evaluate(({ x, y }) => {
      const e = document.elementFromPoint(x, y);
      return e ? { tag: e.tagName, 文字: (e.innerText || '').trim().slice(0, 8) } : null;
    }, { x: it.x + Math.min(30, it.w / 2), y: it.y + it.h / 2 });
    记(`  面板框 ${f.框.join(',')}；「文本」${f.命中.length} 处，取 @${it.x},${it.y} ${it.w}×${it.h}；落点 ${落?.tag}「${落?.文字}」`);
    断言('落点属主就是「文本」', 落?.文字 === '文本', `命中「${落?.文字}」`);
    await page.mouse.click(it.x + Math.min(30, it.w / 2), it.y + it.h / 2);
    await page.waitForTimeout(1900);
    const s = await 快照();
    const 新 = s.filter((n) => !前.some((o) => o.id === n.id));
    记(`  第 ${i} 次建完，画布共 ${s.length} 个，新增：${新.map((n) => `\`${n.标题}\``).join(' ') || '（无）'}`);
    建的.push(...新);
    if (i === 1) await page.screenshot({ path: resolve(EVID, 'fv11-1-第一次建完.png') });
  }
  R.读数.建的 = 建的;
  const 文本建的 = 建的.filter((n) => n.类型 === 'text');
  if (文本建的.length >= 2) {
    断言('K1 固定常量', 文本建的[0].标题 === 文本建的[1].标题,
      `两次都建出「${文本建的[0].标题}」与「${文本建的[1].标题}」⇒ ${文本建的[0].标题 === 文本建的[1].标题 ? '固定' : '递增'}`);
  } else 断言('K1 固定常量', false, `只建出 ${文本建的.length} 个文本节点`);

  // ── ② 清理
  const 需删 = 建的.map((n) => n.id);
  记(`\n--- ② 清理 ${需删.length} 个本轮建出来的节点（⛔ 不用 Delete/Backspace）---`);
  记(`待删：${需删.join(', ')}`);
  for (const id of 需删) {
    const ok = await 点aria('资产管理');
    if (!ok) { 记('  ⛔ 找不到「资产管理」'); break; }
    await page.waitForTimeout(900);
    const r = await page.evaluate((nid) => {
      // 找画布上那个节点，抽屉里应该有同名行
      const el = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      if (!el) return { 错: '画布上找不到该节点' };
      const b = el.getBoundingClientRect();
      return { 中心: [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)] };
    }, id);
    if (r.错) { 记(`  ${id}：${r.错}`); continue; }
    // 选中它，抽屉里那行会高亮，行尾出现「⋯」
    await page.mouse.click(r.中心[0], r.中心[1]);
    await page.waitForTimeout(900);
    const 更多 = await page.evaluate(() => {
      for (const e of document.querySelectorAll('[aria-label^="更多操作"], [aria-label*="更多"]')) {
        const s = (e.getAttribute('aria-label') || '');
        if (!e.closest('[class*="Drawer"], aside')) continue;
        const r = e.getBoundingClientRect();
        if (r.width < 8) continue;
        return { aria: s, 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
      }
      return null;
    });
    if (!更多) { 记(`  ${id}：抽屉里没找到「更多操作」按钮 —— ⛔ 不猜，留给人工`); continue; }
    await page.mouse.click(更多.中心[0], 更多.中心[1]);
    await page.waitForTimeout(800);
    const 删 = await page.evaluate(() => {
      for (const e of document.querySelectorAll('*')) {
        if (e.children.length) continue;
        if ((e.innerText || '').trim() !== '删除') continue;
        const r = e.getBoundingClientRect();
        if (r.width < 20 || r.height < 10) continue;
        if (r.x < 400) continue;   // ⛔ 只认抽屉那一侧（x>400），不碰画布上的东西
        return { 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
      }
      return null;
    });
    if (!删) { 记(`  ${id}：菜单里没找到「删除」—— ⛔ 不猜`); await page.keyboard.press('Escape'); continue; }
    await page.mouse.click(删.中心[0], 删.中心[1]);
    await page.waitForTimeout(1200);
    const 后 = await 快照();
    断言(`${id} 已删`, !后.some((n) => n.id === id), `画布现有 ${后.length} 个`);
  }
  await page.screenshot({ path: resolve(EVID, 'fv11-2-清理之后.png') });
  const 终 = await 快照();
  R.读数.终 = 终;
  断言('回到 FV-9 之前的 13 个', 终.length === 13, `实际 ${终.length} 个`);
  记(`\n终态：${终.map((n) => n.标题).join(' / ')}`);
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFV11.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
