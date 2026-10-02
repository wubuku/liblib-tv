// Batch BH1 — 节点星级入口：前两轮判据全是误报，这轮改穷举 + 中文关键词。
//
// BG1/BG2 用 `/★|☆|星|评级|rating|star|favorite|收藏/i` 匹配
// `text + aria + title + class` 的拼接，结果 8~12 个「命中」全是
// `flex flex-col items-start gap-1` 这类**完全无关的 class** —— 纯误报。
//
// ✅ 这轮的判据换成两条**误报率极低**的：
//   ① 全量 dump 页面里**每一个** `button/[role=button]/[tabindex]/input` 的
//      `aria-label` / `title` / `innerText`，再用**中文关键词**筛：
//      `星级` `评分` `评级` `重要度` `优先级` `打分` `标记为`。
//      （不用英文 —— `star` 之类会撞上 `items-start`）
//   ② 直接看有没有 `★` / `☆` **这两个字符**出现在可见文字里。
//
// 再加三处 BG 没扫到的地方：
//   · **右键菜单**（用容器级读法，BG1 那次读出 101 条全是顶栏污染）
//   · **资产管理列表每一行**的完整可交互元素
//   · **顶栏 / 底栏**每个按钮的完整清单（万一评级是全局的）
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBH1';
const { browser, page } = await launch();

/** ⭐ 全量 dump 全部可交互元素的三个文案字段。**一条都不筛，先拿全量。 */
const allInteractive = () => page.evaluate(() => {
  const ok = (e) => !['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE'].includes(e.tagName);
  return [...document.querySelectorAll('button,[role="button"],[tabindex="0"],input,select,textarea,a[href]')]
    .filter(ok)
    .map((e) => {
      const r = e.getBoundingClientRect();
      if (r.width <= 0 || r.height <= 0) return null;
      return {
        tag: e.tagName, role: e.getAttribute('role'),
        aria: e.getAttribute('aria-label'), title: e.getAttribute('title'),
        text: (e.innerText || e.value || e.placeholder || '').replace(/\s+/g, ' ').trim().slice(0, 30),
        type: e.getAttribute('type'), tabindex: e.getAttribute('tabindex'),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        cls: (e.className || '').toString().slice(0, 46),
      };
    })
    .filter(Boolean);
});

/** ⭐ 中文关键词 + 星形字符 —— 低误报判据。 */
const kw = (s) => /星级|评分|评级|重要度|优先级|打分|标记为|收藏|★|☆/.test(s || '');

async function exclusivePoint(pg, id) {
  return pg.evaluate((nid) => {
    const t = [...document.querySelectorAll('.react-flow__node')].find((n) => n.getAttribute('data-id') === nid);
    if (!t) return { err: 'no node' };
    const r = t.getBoundingClientRect();
    for (let fy = 0.2; fy <= 0.8; fy += 0.12) for (let fx = 0.06; fx <= 0.95; fx += 0.06) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const o = document.elementFromPoint(x, y);
      if (o && o.closest('.react-flow__node') === t) return { x, y };
    }
    return { err: 'no exclusive point' };
  }, id);
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1800);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '星级入口：穷举全部可交互元素 + 中文关键词（避开英文 class 误报）/ 右键菜单 / 列表行内' });

  const out = {};
  await page.mouse.move(720, 260); await page.waitForTimeout(800);

  // ═══ 1. 画布空白态：全量清单
  console.log('--- BH1-1 画布态全量可交互元素 ---');
  const all0 = await allInteractive();
  const hits0 = all0.filter((b) => kw(`${b.aria || ''} ${b.title || ''} ${b.text || ''}`));
  console.log(`  共 ${all0.length} 个可交互元素；中文关键词/星形命中 **${hits0.length}** 个`);
  hits0.forEach((b) => console.log(`    [${b.rect}] ${b.tag} aria=${b.aria} title=${b.title} text="${b.text}"`));
  out.idle = { total: all0.length, hits: hits0 };
  // 顺便把 aria 清单存下来（这是「有哪些按钮」的完整答案）
  const ariaList = [...new Set(all0.map((b) => b.aria || b.title || b.text).filter(Boolean))];
  console.log(`  去重后文案 ${ariaList.length} 条（前 30）：`);
  console.log('   ', ariaList.slice(0, 30).join(' | '));
  out.ariaList = ariaList;

  // ═══ 2. 逐类节点：选中后再扫
  console.log('\n--- BH1-2 逐类节点选中后 ---');
  const perType = [];
  for (const id of ['i-9nlG6HdjK2', 'v-eMpqKtiLlx', 't-UtVx3lZmrV', 'a-CUfJfmKzUJ', 'b-mfkcQNULC3']) {
    const pt = await exclusivePoint(page, id);
    if (pt.err) { console.log(`  ${id}: ${pt.err}`); continue; }
    const before = await fingerprint(page);
    await page.mouse.click(pt.x, pt.y); await page.waitForTimeout(2400);
    const after = await fingerprint(page);
    const added = diffPanels(before, after);
    const all = await allInteractive();
    const hits = all.filter((b) => kw(`${b.aria || ''} ${b.title || ''} ${b.text || ''}`));
    const newAria = [...new Set(all.map((b) => b.aria || b.title).filter(Boolean))]
      .filter((a) => !ariaList.includes(a));
    console.log(`  ${id}：可交互 ${all.length} 个；新增面板 ${added.length} 个；关键词命中 ${hits.length} 个；新增 aria ${JSON.stringify(newAria).slice(0, 200)}`);
    hits.forEach((b) => console.log(`      [${b.rect}] aria=${b.aria} title=${b.title} text="${b.text}"`));
    perType.push({ id, total: all.length, addedPanels: added.length, hits, newAria });
    await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  }
  out.perType = perType;
  out.starFound = perType.some((p) => p.hits.length > 0);

  // ═══ 3. 右键菜单（容器级读法）
  console.log('\n--- BH1-3 右键菜单 ---');
  const pt2 = await exclusivePoint(page, 'i-9nlG6HdjK2');
  if (pt2.err) { console.log('  ', pt2.err); out.ctx = { err: pt2.err }; }
  else {
    const beforeC = await fingerprint(page);
    await page.mouse.click(pt2.x, pt2.y, { button: 'right' });
    await page.waitForTimeout(2400);
    const afterC = await fingerprint(page);
    const addedC = diffPanels(beforeC, afterC);
    console.log(`  右键后新增面板 ${addedC.length} 个：`);
    addedC.forEach((a) => console.log(`    "${String(a.all || a.text || '').replace(/\s+/g, ' ').slice(0, 200)}"`));
    const allC = await allInteractive();
    const hitsC = allC.filter((b) => kw(`${b.aria || ''} ${b.title || ''} ${b.text || ''}`));
    console.log(`  右键后可交互 ${allC.length} 个；关键词命中 ${hitsC.length} 个`);
    const newAriaC = [...new Set(allC.map((b) => b.aria || b.title).filter(Boolean))].filter((a) => !ariaList.includes(a));
    console.log(`  右键后新增的 aria：${JSON.stringify(newAriaC)}`);
    out.ctx = { addedPanels: addedC.length, addedTexts: addedC.map((a) => String(a.all || a.text || '').replace(/\s+/g, ' ').slice(0, 200)),
      total: allC.length, hits: hitsC, newAria: newAriaC };
    await shot(page, 'M-197-节点右键菜单.png');
    out.shot = 'M-197-节点右键菜单.png';
    await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  }

  // ═══ 4. 资产管理抽屉：列表每一行 + 评级筛选器
  console.log('\n--- BH1-4 资产管理抽屉 ---');
  const dm = await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,[role="button"]')]
      .find((x) => x.getAttribute('aria-label') === '资产管理');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  if (!dm) { console.log('  没找到资产管理按钮'); out.drawer = { err: 'no btn' }; }
  else {
    await page.mouse.click(dm.x, dm.y); await page.waitForTimeout(2500);
    // 抽屉容器的完整 aria 清单
    const dAll = await page.evaluate(() => {
      const ok = (e) => !['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE'].includes(e.tagName);
      const dr = document.querySelector('.mantine-Drawer-content');
      const host = dr || document.body;
      return [...host.querySelectorAll('button,[role="button"],[tabindex="0"],input')]
        .filter(ok)
        .map((e) => { const r = e.getBoundingClientRect();
          return { aria: e.getAttribute('aria-label'), title: e.getAttribute('title'),
            text: (e.innerText || e.value || '').replace(/\s+/g, ' ').trim().slice(0, 20),
            placeholder: e.getAttribute('placeholder'),
            rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; })
        .filter((e) => e.rect[2] > 0 && e.rect[3] > 0);
    });
    const uniqAria = [...new Set(dAll.map((b) => b.aria || b.title || b.text).filter(Boolean))];
    console.log(`  抽屉里可交互 ${dAll.length} 个；去重文案 ${uniqAria.length} 条：`);
    uniqAria.forEach((a) => console.log(`    "${a}"`));
    const hitsD = dAll.filter((b) => kw(`${b.aria || ''} ${b.title || ''} ${b.text || ''}`));
    console.log(`  关键词命中 ${hitsD.length} 个：`, JSON.stringify(hitsD).slice(0, 300));
    out.drawer = { total: dAll.length, aria: uniqAria, hits: hitsD };

    // 点「所有评级」看六档（已知坐实过），但这次读**每一档的完整文案与可点性**
    const rate = dAll.find((b) => /所有评级|评级/.test(`${b.aria || ''}${b.title || ''}${b.text || ''}`));
    if (rate) {
      console.log(`  找到评级筛选器：[${rate.rect}] "${rate.aria || rate.title || rate.text}"`);
      await page.mouse.click(rate.rect[0] + rate.rect[2] / 2, rate.rect[1] + rate.rect[3] / 2);
      await page.waitForTimeout(2200);
      const opts = await page.evaluate(() => [...document.querySelectorAll('div,li,button,[role="option"]')]
        .filter((e) => !['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE'].includes(e.tagName))
        .map((e) => { const r = e.getBoundingClientRect();
          return { text: (e.innerText || '').replace(/\s+/g, ' ').trim(),
            cursor: getComputedStyle(e).cursor,
            rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; })
        .filter((e) => e.rect[2] > 20 && e.rect[3] > 6 && e.rect[3] < 50 && e.text && e.text.length < 12
          && /★|星|评级|^\d/.test(e.text)));
      console.log(`  下拉里与星级相关的 ${opts.length} 行：`);
      opts.forEach((o) => console.log(`    [${o.rect}] "${o.text}" cursor=${o.cursor}`));
      out.drawer.rateOptions = opts;
      await shot(page, 'M-198-评级筛选-六档.png');
      out.shot2 = 'M-198-评级筛选-六档.png';
      await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
    }
    await page.keyboard.press('Escape'); await page.waitForTimeout(1400);
  }

  await logStep(B, {
    id: 'BH1-star-entry-exhaustive',
    title: '星级入口：穷举全部可交互元素 + 中文关键词（避开英文 class 误报）',
    target: 'BG1/BG2 的星级扫描用 `/star|rating|星/i` 匹配 text+aria+title+class，'
      + '8~12 个「命中」全是 `flex flex-col items-start gap-1` 这类无关 class，纯误报。'
      + '这轮改用两条低误报判据：全量 dump 每个可交互元素的三个文案字段后，'
      + '只用**中文关键词**（星级/评分/评级/重要度/优先级/打分/标记为）加 ★☆ 两字符筛；'
      + '并补扫右键菜单与资产管理抽屉。',
    evidence: out,
    visible_text: JSON.stringify({ idle: { total: out.idle?.total, hits: out.idle?.hits?.length },
      perType: out.perType?.map((p) => ({ id: p.id, total: p.total, added: p.addedPanels, hits: p.hits.length, newAria: p.newAria })),
      starFound: out.starFound,
      ctx: { added: out.ctx?.addedPanels, hits: out.ctx?.hits?.length, newAria: out.ctx?.newAria },
      drawer: { total: out.drawer?.total, hits: out.drawer?.hits?.length, rateOptions: out.drawer?.rateOptions?.length } }).slice(0, 3000),
    shot: out.shot2 || out.shot,
  });
  console.log('\nBH1 完成');
} finally {
  await browser.close();
}
