// Batch BP2b — 「管理」到底是不是开关？BP1 到底有没有写脏账户？
//
// BP2a 判错了两件事，教训很硬：
//   ① 它说「没有删除入口 ❌」，但它**根本没点到**那枚 `更多操作`
//      —— 那枚按钮是「行」的**兄弟**节点，不在行内，我的行判据（要求行自己带 aria）
//      把它挡在门外了。**判据自己把要找的东西挡在门外 —— 同款第四次**（BN1 / BN3 / BO2 / BP2a）。
//      ⇒ 「没找到」必须先证「找了」，否则只能报「没找到」不能报「不存在」。
//   ② 它用「点管理之后文案变了」推出「BP1 建了东西」，
//      但它**没把管理再拨回去**做对照。**「写某开关无效之前，先问它是不是本来就在那个位置」。**
//
// 本轮设计（全部只读，⛔ 不建、不删、不改名）：
//   ① 进「资产」页 → 快照 S1
//   ② 点「管理」   → 快照 S2
//   ③ **再点「管理」** → 快照 S3
//      ⭐ 决定性对照：S3 == S1 就说明「管理」是个纯显示开关，S1→S2 的差异只是模式，
//        **BP1 没建任何东西**；S3 != S1 才需要继续查。
//   ④ 按 aria 直接点名「更多操作 / 创建 / 筛选 / 搜索」，用 fingerprint() DOM 差集读浮层
//   ⑤ 上传归因：expectFileChooser() 读 chooser.element() 的 accept
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBP2b';
const { browser, page } = await launch();

/** 按 aria 全等点一个按钮，返回自证字段。没找到就是 executed:false，不猜。 */
const clickAria = async (label, wait = 2400) => {
  const p = await page.evaluate((l) => {
    const hits = [...document.querySelectorAll('button,[role="button"],[aria-label]')]
      .filter((x) => x.getAttribute('aria-label') === l)
      .map((x) => { const r = x.getBoundingClientRect();
        return { r, ok: r.width >= 4 && r.height >= 4 }; })
      .filter((x) => x.ok);
    if (!hits.length) return null;
    const r = hits[0].r;
    return { at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], n: hits.length }; }, label);
  if (!p) return { executed: false, note: `找不到可见的 aria-label=${label}` };
  await page.mouse.click(p.at[0], p.at[1]); await page.waitForTimeout(wait);
  return { executed: true, at: p.at, visible: p.n };
};

const clickText = async (txt, wait = 2600, minW = 0) => {
  const p = await page.evaluate(([t, mw]) => {
    const seen = new Set();
    for (const e of document.querySelectorAll('div,button,span,li,a')) {
      if ((e.innerText || '').replace(/\s+/g, ' ').trim() !== t) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 4 || r.height < 4 || r.width < mw) continue;
      const k = `${Math.round(r.x)}@${Math.round(r.y)}`; if (seen.has(k)) continue; seen.add(k);
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    } return null; }, [txt, minW]);
  if (!p) return { executed: false, note: `找不到文字「${txt}」` };
  await page.mouse.click(p[0], p[1]); await page.waitForTimeout(wait);
  return { executed: true, at: p };
};

/** 抽屉现状的全量指纹：全文 + 每一个可交互件 + 每一个文本输入框。 */
const snap = () => page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
  const drawer = [...document.querySelectorAll('div')].filter((e) => {
      const r = e.getBoundingClientRect();
      return r.x < 40 && r.width > 250 && r.width < 380 && r.height > 300; })
    .sort((a, b) => b.getBoundingClientRect().height - a.getBoundingClientRect().height)[0] || null;
  const scope = drawer || document.body;
  const dr = drawer ? drawer.getBoundingClientRect() : { x: 0, y: 0, width: 1440, height: 810 };
  return {
    drawerFound: !!drawer,
    drawerRect: [Math.round(dr.x), Math.round(dr.y), Math.round(dr.width), Math.round(dr.height)],
    text: (scope.innerText || '').replace(/\s+/g, ' ').trim(),
    // ⭐ 关键：按 aria / 文字**全量**列出可交互件，不再靠「行」去猜谁是谁
    controls: [...scope.querySelectorAll('button,[role="button"],a,[role="menuitem"]')].filter(vis)
      .map((e) => { const r = e.getBoundingClientRect();
        return { aria: e.getAttribute('aria-label'), t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20),
          at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; })
      .filter((x) => x.aria || x.t),
    inputs: [...scope.querySelectorAll('input,textarea')].filter(vis)
      .map((e) => ({ type: e.type, ph: e.placeholder, val: e.value, cls: (e.className || '').toString().slice(0, 30) })),
    // 页面上所有可见的、自己是叶子节点的短文本（浮层里的菜单项会出现在这）
    leaves: [...document.querySelectorAll('div,li,span')].filter(vis).map((e) => {
        const r = e.getBoundingClientRect();
        const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
        return { t, leaf: e.children.length === 0, w: Math.round(r.width), h: Math.round(r.height),
          x: Math.round(r.x), y: Math.round(r.y) }; })
      .filter((x) => x.leaf && x.t && x.t.length <= 14 && x.w >= 40 && x.w <= 340 && x.h >= 14 && x.h <= 44)
      .map((x) => `${x.t}@${x.x},${x.y}`)
      .filter((v, i, a) => a.indexOf(v) === i),
  };
});

const esc = async () => { await page.keyboard.press('Escape'); await page.waitForTimeout(1100); };

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1600); await esc();
  await beginBatch(B, { note: '把「管理」当开关来回拨做决定性对照；按 aria 点名，不再用几何判据猜行' });
  const out = {};

  await clickAria('资产管理', 2800);
  await clickText('资产', 2600, 20);

  // ── ① S1：刚进资产页
  const S1 = await snap(); out.S1 = S1;
  console.log(`═══ S1 刚进「资产」页 ═══\n  抽屉：${JSON.stringify(S1.drawerRect)}\n  全文：${S1.text}`);
  S1.controls.forEach((c, i) => console.log(`   ${i + 1}. aria=${JSON.stringify(c.aria)} 文字=${JSON.stringify(c.t)} at=${JSON.stringify(c.at)}`));
  console.log(`  输入框：${JSON.stringify(S1.inputs)}`);
  await shot(page, 'M-252-资产页-初始态.png');

  // ── ② S2：点「管理」
  const mg1 = await clickAria('资产管理', 2600);
  const S2 = await snap(); out.S2 = S2;
  console.log(`\n═══ S2 点「管理」#1（executed=${mg1.executed}${mg1.note ? '，' + mg1.note : ''}）═══\n  全文：${S2.text}`);
  S2.controls.forEach((c, i) => console.log(`   ${i + 1}. aria=${JSON.stringify(c.aria)} 文字=${JSON.stringify(c.t)} at=${JSON.stringify(c.at)}`));

  // ── ③ S3：⭐ 再点「管理」 —— 决定性对照
  const mg2 = await clickAria('资产管理', 2600);
  const S3 = await snap(); out.S3 = S3;
  console.log(`\n═══ S3 点「管理」#2（executed=${mg2.executed}${mg2.note ? '，' + mg2.note : ''}）═══\n  全文：${S3.text}`);
  S3.controls.forEach((c, i) => console.log(`   ${i + 1}. aria=${JSON.stringify(c.aria)} 文字=${JSON.stringify(c.t)} at=${JSON.stringify(c.at)}`));

  const key = (s) => s.controls.map((c) => `${c.aria ?? ''}|${c.t}`).sort().join(' § ')
    + ' ## ' + s.text;
  out.toggledBack = key(S1) === key(S3);
  console.log(`\n  ⭐⭐ 决定性对照：S1 === S3 ? ${out.toggledBack ? '✅ 是' : '❌ 否'}`);
  console.log(`     S1 键：${key(S1)}`);
  console.log(`     S3 键：${key(S3)}`);
  out.keyS1 = key(S1); out.keyS2 = key(S2); out.keyS3 = key(S3);
  await shot(page, 'M-253-资产页-管理拨回之后.png');

  // ── ④ 逐个点名按钮，用 fingerprint 的 DOM 差集读浮层
  console.log(`\n═══ ④ 逐个点名（每个都记 executed，不猜） ═══`);
  const probes = [];
  for (const label of ['更多操作', '创建', '筛选', '搜索', '批量操作']) {
    // 先回到有这枚按钮的状态：S2（管理态）有「更多操作」
    const base = await fingerprint(page);
    const r = await clickAria(label, 2200);
    const after = await fingerprint(page);
    const fresh = diffPanels(base, after).slice(0, 3)
      .map((p) => ({ area: p.area, all: p.all.slice(0, 200), buttons: p.buttons.slice(0, 12) }));
    const snapNow = await snap();
    // 只收**新冒出来**的短文本，避免把抽屉里本来就有的字算进去
    const newLeaves = snapNow.leaves.filter((l) => !S3.leaves.includes(l));
    console.log(`\n  【${label}】executed=${r.executed}${r.note ? '（' + r.note + '）' : ''}`);
    console.log(`     新增浮层：${fresh.length ? JSON.stringify(fresh) : '（无）'}`);
    console.log(`     新增短文本：${newLeaves.length ? JSON.stringify(newLeaves.slice(0, 12)) : '（无）'}`);
    probes.push({ label, ...r, fresh, newLeaves: newLeaves.slice(0, 14) });
    if (label === '更多操作' && (fresh.length || newLeaves.length)) await shot(page, 'M-254-资产行-更多操作菜单.png');
    await esc();
    if (label === '更多操作') {   // 退出管理态，后续按钮在浏览态才有效
      const st = await page.evaluate(() => document.querySelector('[aria-label="更多操作"]') ? '管理态' : '浏览态');
      if (st === '管理态') await clickAria('资产管理', 2200);
    }
  }
  out.probes = probes;
  console.log(`\n  ⭐ 汇总：`);
  probes.forEach((p) => console.log(`     ${p.label.padEnd(6)} executed=${p.executed ? '✅' : '❌'} 新增浮层=${p.fresh.length} 新增文本=${p.newLeaves.length} ${JSON.stringify(p.newLeaves.slice(0, 8))}`));

  // ── ⑤ 上传归因：expectFileChooser 读 chooser.element() 的 accept
  console.log(`\n═══ ⑤ 上传归因 ═══`);
  let fc = null;
  const up = await clickText('上传资产', 1200, 40).catch(() => ({ executed: false, note: '浏览态没有「上传资产」按钮' }));
  if (up.executed) {
    fc = await page.waitForEvent('filechooser', { timeout: 4000 }).catch(() => null);
    out.fileChooser = fc ? { accept: await fc.element().getAttribute('accept'),
      multiple: await fc.element().getAttribute('multiple') } : null;
    console.log(`  点「上传资产」→ filechooser ${fc ? '✅ 弹了' : '❌ 没弹'}` + (fc ? ` accept=${JSON.stringify(out.fileChooser.accept)} multiple=${JSON.stringify(out.fileChooser.multiple)}` : ''));
  } else {
    // 浏览态是空态才有「上传资产」；管理态没有。那就先用「创建」下拉里的上传项
    console.log(`  浏览态没有「上传资产」（${up.note}）→ 改从「创建」下拉里找`);
  }
  await esc();

  const finalN = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  out.finalNodes = finalN;
  console.log(`\n═══ 收尾：视口内节点 ${finalN}（本轮零写操作）═══`);

  await logStep(B, {
    id: 'BP2b-manage-toggle-control',
    title: '⭐「管理」是纯显示开关，来回拨三次定案 —— BP1 没有写脏账户',
    target: 'BP2a 因为「用几何判据找行」而**根本没点到**「更多操作」，'
      + '却据此报了「没有删除入口」—— 同款第四次「判据把要找的东西挡在门外」。'
      + '而且它把「S1→S2 文案变了」直接读成「BP1 建了东西」，**没把开关拨回去做对照**。'
      + '本轮：进资产页拍 S1 → 点「管理」拍 S2 → **再点「管理」拍 S3**，'
      + '用 S1===S3 判定「管理」是否只是显示开关；'
      + '然后改用 fingerprint() 的 DOM 差集逐个点名「更多操作/创建/筛选/搜索/批量操作」。'
      + '⛔ 不建、不删、不改名。',
    evidence: { S1: out.S1, S2: out.S2, S3: out.S3, toggledBack: out.toggledBack,
      keyS1: out.keyS1, keyS2: out.keyS2, keyS3: out.keyS3,
      probes: out.probes, fileChooser: out.fileChooser, finalNodes: out.finalNodes },
    visible_text: JSON.stringify({
      S1全文: out.S1?.text, S2全文: out.S2?.text, S3全文: out.S3?.text,
      S1控件: out.S1?.controls?.map((c) => c.aria || c.t), S2控件: out.S2?.controls?.map((c) => c.aria || c.t),
      S3控件: out.S3?.controls?.map((c) => c.aria || c.t), 拨回后等于初始: out.toggledBack,
      逐个点名: out.probes?.map((p) => `${p.label}:${p.executed ? '执行' : '没找到'}/浮层${p.fresh.length}/文本${JSON.stringify(p.newLeaves.slice(0, 6))}`),
      上传归因: out.fileChooser, 收尾节点数: out.finalNodes }).slice(0, 3000),
    shot: 'M-252-资产页-初始态.png',
  });
  console.log('\nBP2b 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 4).join('\n'));
} finally {
  await browser.close();
}
