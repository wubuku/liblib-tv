// Batch BI2 — ① 故事板视频列筛选三档逐个实点  ② 「翻译提示词」点下到底发生什么
//
// ① AUDIT 早先记了「成片」档会让视频列整行消失，「片段」档**没验**。
//    这轮把三档逐个点过去，每点一次都回读「列头文案 + 可见行数」，
//    ⭐ 并在每次读数时**把鼠标移开**（§30：悬停色与开启色只差 0.05 透明度）。
//    收尾必须点回「全部」复原。
//
// ② 「翻译提示词」（`文A`）此前只坐实了**按钮身份**（悬停读 tooltip），
//    「点下去会怎样」一直空着。
//    ⚠️ 安全边界：**只在提示词为空的节点上点**。AW 点「提示词优化」在空提示词下
//    只弹一句「提示词为空，请输入内容后点击」；翻译很可能同构。
//    但若它在**有内容**时会真的发翻译请求，那就不该由我点 ——
//    本轮不制造那种状态，也不碰任何生成按钮。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';

const SPACE = '10354929';
const B = 'batchBI2';
const { browser, page } = await launch();

/** 排掉 script/style/noscript/template 再读可见文案（BE 的硬规矩）。 */
const visText = () => page.evaluate(() => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  return [...document.querySelectorAll('body *')].filter((e) => !skip.has(e.tagName))
    .map((e) => ({ e, r: e.getBoundingClientRect() }))
    .filter((x) => x.r.width > 0 && x.r.height > 0)
    .filter((x) => ![...x.e.children].some((c) => c.getBoundingClientRect().width > 0))
    .map((x) => (x.e.innerText || '').replace(/\s+/g, ' ').trim())
    .filter((t) => t && t.length < 40);
});

/** 故事板视频列的行数：数「视频节点 N」这种行标题。 */
const videoRows = () => page.evaluate(() => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  const hits = [...document.querySelectorAll('body *')].filter((e) => !skip.has(e.tagName))
    .map((e) => ({ t: (e.innerText || '').replace(/\s+/g, ' ').trim(), r: e.getBoundingClientRect() }))
    .filter((x) => /^视频节点\s*\d+$/.test(x.t) && x.r.height > 10 && x.r.width > 20);
  const seen = new Set(); const rows = [];
  for (const h of hits) { const k = `${Math.round(h.r.x)},${Math.round(h.r.y)}`;
    if (!seen.has(k)) { seen.add(k); rows.push({ t: h.t, y: Math.round(h.r.y) }); } }
  return rows.sort((a, b) => a.y - b.y);
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await beginBatch(B, { note: '故事板三档筛选逐个实点 + 翻译提示词在空提示词下的效果' });

  const out = {};

  // ══════════ ① 故事板筛选三档
  console.log('══════ ① 故事板视频列筛选 ══════');
  const sb = page.getByRole('button', { name: '故事板', exact: true });
  if (await sb.count()) {
    await sb.first().click(); await page.waitForTimeout(3200);
    await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);

    const before = { rows: await videoRows() };
    console.log(`  进入故事板：视频列可见行 ${before.rows.length} 行 → ${JSON.stringify(before.rows.map((r) => r.t))}`);

    // 找那枚筛选按钮：正文是「全部」且带下拉的
    const pick = await page.evaluate(() => {
      const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
      const cands = [...document.querySelectorAll('button,[role="button"]')].filter((e) => !skip.has(e.tagName))
        .map((e) => ({ t: (e.innerText || '').replace(/\s+/g, ' ').trim(),
          r: e.getBoundingClientRect(), e }))
        .filter((x) => x.r.width > 20 && x.r.height > 10 && /^(全部|成片|片段)$/.test(x.t));
      // ⭐ 取最内层（面积最小）的那个，避免点到外层容器
      cands.sort((a, b) => a.r.width * a.r.height - b.r.width * b.r.height);
      const c = cands[0];
      if (!c) return null;
      return { text: c.t, rect: [Math.round(c.r.x), Math.round(c.r.y), Math.round(c.r.width), Math.round(c.r.height)],
        cx: Math.round(c.r.x + c.r.width / 2), cy: Math.round(c.r.y + c.r.height / 2), n: cands.length };
    });
    console.log('  筛选按钮：', JSON.stringify(pick));
    out.picker = pick;

    if (pick) {
      const steps = [];
      for (const want of ['成片', '片段', '全部']) {
        // ⭐ 落点归属校验：点上之前先确认那个点上确实是这枚按钮
        const own = await page.evaluate(([x, y]) => {
          const o = document.elementFromPoint(x, y);
          return { tag: o ? o.tagName : null, text: o ? (o.innerText || '').replace(/\s+/g, ' ').trim() : null };
        }, [pick.cx, pick.cy]);
        console.log(`\n  ── 点「${want}」：落点归属 ${own.tag} "${own.text}" ${own.text === pick.text ? '✅' : '⚠️'}`);

        await page.mouse.click(pick.cx, pick.cy); await page.waitForTimeout(1800);
        const fp1 = await fingerprint(page);
        // 读下拉里的三行
        const menu = await page.evaluate(() => {
          const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
          const rows = [...document.querySelectorAll('[class*="Menu-dropdown"],[class*="Popover-dropdown"]')]
            .filter((e) => e.getBoundingClientRect().width > 0)
            .map((e) => ({ cls: (e.className || '').toString().slice(0, 40),
              rect: (() => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })() }));
          const box = rows[0];
          if (!box) return { err: 'no dropdown' };
          const items = [...document.querySelectorAll('*')].filter((e) => !skip.has(e.tagName))
            .map((e) => { const r = e.getBoundingClientRect();
              return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), r }; })
            .filter((x) => x.t && x.t.length < 12 && x.r.width > 10 && x.r.height > 8
              && x.r.x >= box.rect[0] - 4 && x.r.x <= box.rect[0] + box.rect[2] + 4
              && x.r.y >= box.rect[1] - 4 && x.r.y <= box.rect[1] + box.rect[3] + 4)
            .filter((x) => [...x.r ? [] : []].length === 0)
            .filter((x) => !/^(全部|成片|片段)$/.test(x.t) || true);
          // 最内层去重
          const inner = items.filter((x) => ![...document.querySelectorAll('*')].some(() => false));
          const uniq = []; const seen = new Set();
          for (const x of items) { const k = `${x.t}@${Math.round(x.r.x)},${Math.round(x.r.y)}`; if (!seen.has(k)) { seen.add(k); uniq.push(x); } }
          return { box: box.rect, items: uniq.map((x) => ({ t: x.t, rect: [Math.round(x.r.x), Math.round(x.r.y), Math.round(x.r.width), Math.round(x.r.height)] })) };
        });
        console.log(`     下拉容器 ${JSON.stringify(menu.box)}；选项 ${menu.items?.length} 个：${JSON.stringify(menu.items?.map((m) => m.t))}`);

        // 找 want 那一行的坐标并点它
        const target = menu.items?.find((m) => m.t === want);
        if (!target) { console.log(`     ⚠️ 菜单里没有「${want}」`); steps.push({ want, err: 'not in menu' }); continue; }
        await page.mouse.click(target.rect[0] + target.rect[2] / 2, target.rect[1] + target.rect[3] / 2);
        await page.waitForTimeout(2200);
        // ⭐ 读完立刻把鼠标移开，再读 —— 否则读到的是悬停态
        await page.mouse.move(120, 780); await page.waitForTimeout(1400);

        const now = await page.evaluate(() => {
          const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
          const b = [...document.querySelectorAll('button,[role="button"]')].filter((e) => !skip.has(e.tagName))
            .map((e) => ({ t: (e.innerText || '').replace(/\s+/g, ' ').trim(), r: e.getBoundingClientRect() }))
            .filter((x) => /^(全部|成片|片段)$/.test(x.t) && x.r.width > 20);
          b.sort((a, x) => a.r.width * a.r.height - x.r.width * x.r.height);
          return b.length ? b[0].t : null;
        });
        const rows = await videoRows();
        console.log(`     点完：按钮文案 = ${JSON.stringify(now)}；视频列可见行 ${rows.length} 行 ${JSON.stringify(rows.map((r) => r.t))}`);
        steps.push({ want, landedOn: now, rows: rows.length, rowTitles: rows.map((r) => r.t), menuItems: menu.items?.map((m) => m.t) });
        if (want === '成片') await shot(page, 'M-202-故事板-成片筛选.png');
      }
      out.storyboard = steps;
      console.log('\n  ⭐ 三档汇总：');
      steps.forEach((s) => console.log(`     ${String(s.want).padEnd(4)} → 按钮「${s.landedOn}」，视频列 ${s.rows} 行`));
    }
    await shot(page, 'M-203-故事板-筛选复原.png');
    out.shot = ['M-202-故事板-成片筛选.png', 'M-203-故事板-筛选复原.png'];
  } else { console.log('  !! 顶栏没有「故事板」按钮'); out.storyboard = { err: 'no button' }; }

  // ══════════ ② 翻译提示词（只在空提示词节点上点）
  console.log('\n══════ ② 「翻译提示词」点下会发生什么 ══════');
  const mode = await page.getByRole('button', { name: '画布', exact: true }).count();
  if (mode) { await page.getByRole('button', { name: '画布', exact: true }).first().click(); await page.waitForTimeout(3000); }
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);

  // 找四类节点各自的「文A」按钮
  const scan = [];
  for (const id of ['t-UtVx3lZmrV', 'i-9nlG6HdjK2', 'v-eMpqKtiLlx', 'a-THmbuJXQj4']) {
    const pt = await page.evaluate((nid) => {
      const n = [...document.querySelectorAll('.react-flow__node')].find((x) => x.getAttribute('data-id') === nid);
      if (!n) return { err: 'no node' };
      const r = n.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    }, id);
    if (pt.err || !pt[0]) { console.log(`  ${id}: ${pt.err || '不在视口内'}`); scan.push({ id, ...pt }); continue; }
    await page.mouse.click(pt[0], pt[1]); await page.waitForTimeout(2600);

    const st = await page.evaluate(() => {
      const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
      // 参数条上的可交互元素
      const bar = [...document.querySelectorAll('button,[role="button"]')].filter((e) => !skip.has(e.tagName))
        .map((e) => { const r = e.getBoundingClientRect();
          return { e, t: (e.innerText || '').replace(/\s+/g, ' ').trim(), r,
            aria: e.getAttribute('aria-label'), title: e.getAttribute('title') }; })
        .filter((x) => x.r.width > 0 && x.r.height > 0 && x.r.y > window.innerHeight - 320);
      // 提示词框里有没有内容
      const ta = [...document.querySelectorAll('textarea,[contenteditable="true"],input[type="text"]')]
        .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 100 && r.height > 20; })
        .map((e) => ({ ph: e.getAttribute('placeholder') || '', val: (e.value || e.innerText || '').slice(0, 30),
          r: e.getBoundingClientRect() }));
      return { barCount: bar.length, bar: bar.map((x) => ({ t: x.t, aria: x.aria, title: x.title,
        rect: [Math.round(x.r.x), Math.round(x.r.y), Math.round(x.r.width), Math.round(x.r.height)] })),
        prompt: ta };
    });

    // 找那枚「文A」：靠**图形**认 —— 参数条里 rect 22~34 的方形按钮里，svg path 数最多且非 ⊙/⚙ 的
    const target = await page.evaluate(() => {
      const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
      const cand = [...document.querySelectorAll('button,[role="button"]')].filter((e) => !skip.has(e.tagName))
        .map((e) => { const r = e.getBoundingClientRect();
          const svg = e.querySelector('svg');
          return { e, r, paths: svg ? svg.querySelectorAll('path').length : 0,
            hasText: /[A-Za-z一-龥]/.test((e.innerText || '').trim()),
            aria: e.getAttribute('aria-label') }; })
        .filter((x) => x.r.width >= 20 && x.r.width <= 40 && x.r.y > window.innerHeight - 320);
      return cand.map((x) => ({ rect: [Math.round(x.r.x), Math.round(x.r.y), Math.round(x.r.width), Math.round(x.r.height)],
        paths: x.paths, hasText: x.hasText, aria: x.aria,
        cx: Math.round(x.r.x + x.r.width / 2), cy: Math.round(x.r.y + x.r.height / 2) }));
    });
    const name = (await page.evaluate(() => {
      const n = document.querySelector('.react-flow__node.selected');
      return n ? (n.innerText || '').replace(/\s+/g, ' ').trim().split(' ')[0] : null; }));
    console.log(`\n  ── ${name || id}：参数条可交互 ${st.barCount} 枚；提示词框 ${JSON.stringify(st.prompt)}`);
    console.log(`     20~40px 的方形按钮 ${target.length} 枚：${JSON.stringify(target)}`);
    scan.push({ id, name, barCount: st.barCount, prompt: st.prompt, candidates: target });
    await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  }
  out.translateScan = scan;

  await logStep(B, {
    id: 'BI2-storyboard-filter-and-translate',
    title: '故事板筛选三档逐个实点 + 定位「翻译提示词」按钮',
    target: 'AUDIT 记过「成片」会让视频列整行消失，但「片段」没验，这轮三档逐个点。'
      + '⭐ 每次点完先把鼠标移开再回读（§30 悬停色与开启色只差 0.05 透明度），收尾点回「全部」复原。'
      + '「翻译提示词」此前只坐实了按钮身份，本轮先把它在各类型节点参数条上的位置认出来 —— '
      + '⚠️ 只在空提示词上点，不制造有内容的状态，不碰任何生成按钮。',
    evidence: out,
    visible_text: JSON.stringify({ storyboard: out.storyboard?.map?.((s) => ({ 档: s.want, 按钮: s.landedOn, 行: s.rows })),
      picker: out.picker, translate: out.translateScan?.map?.((s) => ({ 节点: s.name, 条: s.barCount, 候选: s.candidates?.length })) }).slice(0, 3000),
    shot: 'M-202-故事板-成片筛选.png',
  });
  console.log('\nBI2 完成');
} finally {
  await browser.close();
}
