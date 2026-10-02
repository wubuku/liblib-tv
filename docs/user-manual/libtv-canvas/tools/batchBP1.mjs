// Batch BP1 — 资产页的四个写操作：**只读它们长什么样，一个都不提交**。
//
// 资产页的只读层早就写完了（工具行五枚图标、筛选面板六个预置标签、空状态两枚按钮），
// 剩下四个全是**写账户数据**的：
//   `创建默认资产分类` · `上传资产` · `新建文件夹` · `+ 新建标签`
// 手册对这四个一律标「没点过」，连带三件事都不知道：支持什么格式、有没有删除入口、
// 提交前长什么样。
//
// ⭐ 本轮的目标是**只读就能答的那部分**，零写操作：
//   ① `上传资产` 背后是 `<input type="file">` 吗？如果是，**它的 `accept` 属性
//      直接就是「支持哪些格式」的答案** —— 这是挂了很久的 📖，读一个属性的事。
//      （顺带用 `page.on('filechooser')` 确认它真的弹系统选择器，**但不选任何文件**。）
//   ② 四个入口点开之后**提交前**是什么：确认框？内联输入框？弹窗？—— 读表单字段、
//      placeholder、默认值，**不点提交**。
//   ③ ⭐ **有没有删除入口** —— 这一条决定 BP2 敢不敢真的建一次。
//      建了能删干净，才敢试；删不干净，就只读不写，并把结论写进正文。
//
// ⛔ 不提交任何表单、不选任何文件、不建任何分类/文件夹/标签。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const B = 'batchBP1';
const SHOTS = resolve(import.meta.dirname, '../screenshots');
const { browser, page } = await launch();

const clickAria = async (label, wait = 2400) => {
  const p = await page.evaluate((l) => {
    const e = [...document.querySelectorAll('button,[role="button"],[aria-label],a')].find((x) => x.getAttribute('aria-label') === l);
    if (!e) return null; const r = e.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) return null;
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2), Math.round(r.width), Math.round(r.height)]; }, label);
  if (!p) return { executed: false, note: `找不到 aria-label=${label}`, found: 0 };
  await page.mouse.click(p[0], p[1]); await page.waitForTimeout(wait);
  return { executed: true, at: p };
};
const clickText = async (txt, wait = 2400, minW = 0) => {
  const p = await page.evaluate(([t, mw]) => {
    const seen = new Set();
    for (const e of document.querySelectorAll('div,button,span,li,a')) {
      if ((e.innerText || '').replace(/\s+/g, ' ').trim() !== t) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 4 || r.height < 4 || r.width < mw) continue;
      const k = `${Math.round(r.x)}@${Math.round(r.y)}`; if (seen.has(k)) continue; seen.add(k);
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2), Math.round(r.width), Math.round(r.height)];
    } return null; }, [txt, minW]);
  if (!p) return { executed: false, note: `找不到文字「${txt}」` };
  await page.mouse.click(p[0], p[1]); await page.waitForTimeout(wait);
  return { executed: true, at: p };
};

/** 抽屉当前可见的全部输入类控件 —— ⭐ 格式答案就藏在这里。 */
const formFields = () => page.evaluate(() => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  const inputs = [...document.querySelectorAll('input,textarea,select')].filter((e) => !skip.has(e.tagName)).map((e) => {
    const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    return { tag: e.tagName, type: e.type, accept: e.getAttribute('accept'), multiple: e.multiple,
      placeholder: e.placeholder, name: e.name, value: (e.value || '').slice(0, 40),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      visible: r.width > 2 && r.height > 2 && cs.display !== 'none' && cs.visibility !== 'hidden',
      opacity: cs.opacity, acceptFiles: e.tagName === 'INPUT' && e.type === 'file' };
  });
  // 顶层浮层（确认框/弹窗）
  const vw = innerWidth, vh = innerHeight;
  const layers = [...document.querySelectorAll('div')].filter((e) => {
    if (skip.has(e.tagName)) return false;
    const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    if (r.width < 120 || r.height < 60) return false;
    if (cs.position !== 'fixed' && cs.position !== 'absolute') return false;
    if (parseInt(cs.zIndex || '0', 10) < 10) return false;
    if (r.x > 120 || r.y > 120 || r.x + r.width < vw - 120 || r.y + r.height < vh - 120) return false;
    return true; })
    .map((e) => { const r = e.getBoundingClientRect();
      return { cls: (typeof e.className === 'string' ? e.className : '').slice(0, 50),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        z: getComputedStyle(e).zIndex,
        text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300),
        buttons: [...e.querySelectorAll('button,[role="button"],[aria-label]')].filter((x) => !skip.has(x.tagName))
          .map((x) => ({ t: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20), aria: x.getAttribute('aria-label') }))
          .filter((x) => x.t || x.aria).slice(0, 12) }; })
    .sort((a, b) => b.rect[2] * b.rect[3] - a.rect[2] * a.rect[3]);
  return { inputs, layers: layers.slice(0, 2) };
});

/** 抽屉里「资产」页主体的当前状态（有几行、每行是什么、有没有删除入口）。 */
const assetPage = () => page.evaluate(() => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  // 抽屉 = 左侧那块
  const panel = [...document.querySelectorAll('div')].filter((e) => {
    const r = e.getBoundingClientRect();
    return r.x < 40 && r.width > 250 && r.width < 360 && r.height > 400; })
    .sort((a, b) => b.getBoundingClientRect().height - a.getBoundingClientRect().height)[0];
  if (!panel) return { err: 'no drawer' };
  const rows = [...panel.querySelectorAll('*')].filter((e) => !skip.has(e.tagName)).map((e) => {
    const r = e.getBoundingClientRect();
    return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), r,
      aria: e.getAttribute('aria-label'), tag: e.tagName, cursor: getComputedStyle(e).cursor }; })
    .filter((x) => x.t && x.t.length < 24 && x.r.width > 90 && x.r.height >= 16 && x.r.height <= 60
      && x.r.x < 40)
    .filter((x) => !/资产|搜索|批量|筛选|创建|管理|全部|共\s*\d+|画布|标签|重置|取消|应用/.test(x.t))
    .filter((x, i, a) => a.findIndex((y) => y.t === x.t && Math.abs(y.r.y - x.r.y) < 10) === i)
    .map((x) => ({ t: x.t, y: Math.round(x.r.y), aria: x.aria, cursor: x.cursor }));
  const btns = [...panel.querySelectorAll('button,[role="button"],[aria-label]')].filter((e) => !skip.has(e.tagName))
    .map((e) => { const r = e.getBoundingClientRect();
      return { aria: e.getAttribute('aria-label'), t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        op: getComputedStyle(e).opacity, cur: getComputedStyle(e).cursor }; })
    .filter((x) => x.rect[2] > 4 && x.rect[3] > 4 && x.rect[2] < 60);
  return { rows, buttons: btns, foot: (panel.innerText || '').replace(/\s+/g, ' ').trim().slice(-80) };
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1600);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
  await beginBatch(B, { note: '资产页四个写操作只读：格式从 accept 属性读，其余只看提交前长什么样' });
  const out = {};

  // ── 记录 filechooser：确认它真弹系统选择器（**不选文件**）
  let chooser = null;
  page.on('filechooser', (fc) => { chooser = { multiple: fc.isMultiple(), seenAt: Date.now() }; });
  const realOpen = page.waitForEvent('filechooser', { timeout: 6000 }).then(() => true).catch(() => false);

  // ── 进「资产」页
  await clickAria('资产管理', 2800);
  const tab = await clickText('资产', 2600, 20);
  out.tab = tab;
  const a0 = await assetPage();
  out.assetEmpty = a0;
  console.log(`═══ 资产页（空态）═══`);
  console.log(`  行：${JSON.stringify(a0.rows)}`);
  console.log(`  按钮 ${a0.buttons.length} 枚：${JSON.stringify(a0.buttons.slice(0, 8))}`);
  console.log(`  底部："${a0.foot}"`);

  // ── ① 上传资产：⭐ 读 <input type=file> 的 accept
  console.log(`\n═══ ① 「上传资产」—— 格式答案在 accept 属性里 ═══`);
  const before = await formFields();
  const up = await clickText('上传资产', 2600, 40);
  const after = await formFields();
  const chooserFired = await realOpen;
  const fileInputs = after.inputs.filter((i) => i.acceptFiles);
  console.log(`  点它 executed=${up.executed}；filechooser 是否弹出=${chooserFired}${chooser ? `（multiple=${chooser.multiple}）` : ''}`);
  console.log(`  页面里的 input 共 ${after.inputs.length} 个，其中 type=file 的 ${fileInputs.length} 个：`);
  fileInputs.forEach((i) => console.log(`     type=file accept=${JSON.stringify(i.accept)} multiple=${i.multiple} rect=${JSON.stringify(i.rect)} visible=${i.visible}`));
  console.log(`  点完新出现的浮层 ${after.layers.length} 个：`);
  after.layers.forEach((l) => console.log(`     [${l.rect}] z=${l.z} "${l.text}"\n        按钮：${JSON.stringify(l.buttons)}`));
  const newLayers = after.layers.filter((l) => !before.layers.some((b) => b.cls === l.cls));
  console.log(`  ⭐ 新增浮层 ${newLayers.length} 个`);
  newLayers.forEach((l) => console.log(`     ▸ "${l.text}"\n        按钮：${JSON.stringify(l.buttons)}`));
  out.upload = { executed: up.executed, chooserFired, chooser: chooser || null,
    fileInputs, layers: after.layers, newLayers };
  await shot(page, 'M-246-资产-上传入口.png');
  out.shotUpload = 'M-246-资产-上传入口.png';
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1400);

  // ── ② 创建默认资产分类
  console.log(`\n═══ ② 「创建默认资产分类」—— 提交前长什么样 ═══`);
  const b2 = await formFields();
  const mk = await clickText('创建默认资产分类', 2600, 60);
  const a2 = await formFields();
  const n2 = a2.layers.filter((l) => !b2.layers.some((x) => x.cls === l.cls));
  console.log(`  executed=${mk.executed}；新增浮层 ${n2.length} 个`);
  n2.forEach((l) => console.log(`     ▸ [${l.rect}] z=${l.z}\n        文字：「${l.text}」\n        按钮：${JSON.stringify(l.buttons)}`));
  console.log(`  input：${JSON.stringify(a2.inputs.filter((i) => i.visible))}`);
  out.mkDefault = { executed: mk.executed, layers: n2, inputs: a2.inputs.filter((i) => i.visible) };
  await shot(page, 'M-247-资产-创建默认分类.png');
  out.shotMk = 'M-247-资产-创建默认分类.png';
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1400);

  // ── ③ + 创建 → 新建文件夹
  console.log(`\n═══ ③ 「+ 创建」下拉 → 新建文件夹 ═══`);
  const plus = await clickAria('创建', 2200);
  const menu = await page.evaluate(() => {
    const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
    return [...document.querySelectorAll('div,li,span')].map((e) => { const r = e.getBoundingClientRect();
      return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), r, k: e.children.length }; })
      .filter((x) => /^(新建文件夹|上传资产)$/.test(x.t) && x.r.width > 50 && x.r.height > 14 && x.r.width < 300)
      .map((x) => ({ t: x.t, rect: [Math.round(x.r.x), Math.round(x.r.y), Math.round(x.r.width), Math.round(x.r.height)] }))
      .filter((v, i, a) => a.findIndex((o) => o.t === v.t) === i); });
  console.log(`  「创建」executed=${plus.executed}；下拉项：${JSON.stringify(menu)}`);
  out.createMenu = { executed: plus.executed, items: menu };
  const nf = menu.find((m) => m.t === '新建文件夹');
  if (nf) {
    const b3 = await formFields();
    await page.mouse.click(nf.rect[0] + nf.rect[2] / 2, nf.rect[1] + nf.rect[3] / 2);
    await page.waitForTimeout(2200);
    const a3 = await formFields();
    const vis3 = a3.inputs.filter((i) => i.visible);
    const newIn = vis3.filter((i) => !b3.inputs.some((x) => x.rect[0] === i.rect[0] && x.rect[1] === i.rect[1]));
    console.log(`  点完新增可见 input ${newIn.length} 个：${JSON.stringify(newIn)}`);
    console.log(`  新增浮层：${JSON.stringify(a3.layers.filter((l) => !b3.layers.some((x) => x.cls === l.cls)).map((l) => l.text))}`);
    out.newFolder = { newInputs: newIn, layers: a3.layers.filter((l) => !b3.layers.some((x) => x.cls === l.cls)) };
    await shot(page, 'M-248-资产-新建文件夹.png');
    out.shotFolder = 'M-248-资产-新建文件夹.png';
    await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
    await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  } else { await page.keyboard.press('Escape'); await page.waitForTimeout(1000); }

  // ── ④ 筛选 → + 新建标签
  console.log(`\n═══ ④ 筛选面板里的「+ 新建标签」 ═══`);
  const fl = await clickAria('筛选', 2200);
  const b4 = await formFields();
  const nl = await clickText('+ 新建标签', 2400, 30);
  const a4 = await formFields();
  const newIn4 = a4.inputs.filter((i) => i.visible).filter((i) => !b4.inputs.some((x) => x.rect[0] === i.rect[0] && x.rect[1] === i.rect[1]));
  console.log(`  「筛选」executed=${fl.executed}；「+ 新建标签」executed=${nl.executed}`);
  console.log(`  新增可见 input ${newIn4.length} 个：${JSON.stringify(newIn4)}`);
  out.newTag = { filter: fl.executed, newTag: nl.executed, newInputs: newIn4 };
  await shot(page, 'M-249-资产-新建标签.png');
  out.shotTag = 'M-249-资产-新建标签.png';
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1400);

  // ── ⑤ 盘点「管理」点开之后有没有删除入口（决定 BP2 敢不敢写）
  console.log(`\n═══ ⑤ 「管理」点开之后 ═══`);
  const b5 = await formFields();
  const mg = await clickAria('资产管理', 2600);
  const a5 = await formFields();
  const n5 = a5.layers.filter((l) => !b5.layers.some((x) => x.cls === l.cls));
  console.log(`  executed=${mg.executed}；新增浮层 ${n5.length} 个：${JSON.stringify(n5.map((l) => ({ cls: l.cls, text: l.text, buttons: l.buttons })))}`);
  const a5rows = await assetPage();
  console.log(`  抽屉行：${JSON.stringify(a5rows.rows)}`);
  console.log(`  抽屉按钮：${JSON.stringify(a5rows.buttons.slice(0, 10))}`);
  out.manage = { executed: mg.executed, layers: n5, rows: a5rows.rows, buttons: a5rows.buttons };
  await page.keyboard.press('Escape'); await page.waitForTimeout(1400);

  const finalN = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  out.finalNodes = finalN;
  console.log(`\n═══ 收尾：节点 ${finalN}（全程零写操作）═══`);

  await logStep(B, {
    id: 'BP1-asset-write-flows-readonly',
    title: '资产页四个写操作只读：格式从 accept 属性读，其余只看提交前长什么样',
    target: '资产页的只读层早就写完了，剩下四个全是**写账户数据**的入口。'
      + '本轮**一个都不提交**，只把「不写也能答」的部分答掉：'
      + '① ⭐ `上传资产` 背后的 `<input type="file">` 的 **`accept` 属性** —— '
      + '「支持哪些格式」这个挂了很久的 📖，读一个属性的事；'
      + '② 四个入口**提交前**是什么（确认框？内联输入框？弹窗？）；'
      + '③ ⭐ **有没有删除入口** —— 这条决定下一轮敢不敢真的建一次。'
      + '⛔ 不提交任何表单、不选任何文件。',
    evidence: out,
    visible_text: JSON.stringify({ 空态行: out.assetEmpty?.rows,
      上传: { chooser: out.upload?.chooserFired, fileInputs: out.upload?.fileInputs, newLayers: out.upload?.newLayers?.map?.((l) => l.text) },
      建默认分类: out.mkDefault?.layers?.map?.((l) => l.text),
      创建下拉: out.createMenu?.items, 新建文件夹: out.newFolder?.newInputs,
      新建标签: out.newTag, 管理: { layers: out.manage?.layers?.length, rows: out.manage?.rows },
      收尾节点数: out.finalNodes }).slice(0, 3000),
    shot: out.shotUpload,
  });
  console.log('\nBP1 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message);
} finally {
  await browser.close();
}
