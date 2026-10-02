// Batch BG — 连接口全量盘点 + 星级入口再扫 + 故事板筛选逐项验。
//
// BF 留下的 not_verified：节点星级入口。BF2/BF3 用面板差集法扫过音频节点，
// 卡片上 0 个、选中后带「星/评」字样的按钮 0 个。这轮换**别的节点类型**再扫，
// 并且多扫两处 BF 没碰的地方：
//   ① **资产管理列表的行内**（列表每行除了「定位到节点」和「更多操作」还有没有别的）
//   ② **节点的上下文菜单**（右击 / 长按会不会弹菜单）
// ⚠️ 右击会改浏览器行为，必须先验清 `contextmenu` 有没有被 preventDefault，
//    以及弹出的东西到底是应用菜单还是浏览器菜单。
//
// 这批的主目标是 **连接口（handle）全量盘点** —— connect-nodes 是手册的旗舰页面之一，
// 但正文讲的是「怎么连」，**没讲连接口长什么样、在哪、有几个**。
// ⭐ 关键判据：连接口在 React Flow 里是 `.react-flow__handle`，
//    且带 `data-handleid` / `data-nodeid` / `data-nodeType` ——
//    **认连接口要认结构属性，不要认 class 名字里有没有 Handle**
//    （§22：class 白名单不可信；BF2：整页按文本筛会混进一整页）。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBG1';
const { browser, page } = await launch();

/** ⭐ 画布坐标（BE 立的规矩：判位置一律用它，不读屏幕坐标）。 */
const flowPos = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(n).transform || '');
  const p = m ? m[1].split(',').map(Number) : null;
  return { id: n.getAttribute('data-id'), x: p ? Math.round(p[4]) : null, y: p ? Math.round(p[5]) : null };
}));

/** ⭐⭐ 连接口：认 React Flow 的**结构属性**，不认 class 名字。
 *  同时把「长什么样」（class/尺寸/背景）也读出来，供手册描述。 */
const handles = () => page.evaluate(() => {
  const nodes = [...document.querySelectorAll('.react-flow__node')];
  const out = [];
  for (const n of nodes) {
    const nid = n.getAttribute('data-id');
    const name = ((n.innerText || '').replace(/\s+/g, ' ').trim().split(' ')[0] || '').slice(0, 12);
    const list = [...n.querySelectorAll('[data-handleid],[data-handleid] > *, .react-flow__handle')]
      .map((e) => {
        const r = e.getBoundingClientRect();
        const cs = getComputedStyle(e);
        return {
          handleId: e.getAttribute('data-handleid'),
          nodeId: e.getAttribute('data-nodeid'),
          nodeType: e.getAttribute('data-nodeType'),
          isConnectable: e.getAttribute('isConnectable'),
          connectionMode: e.getAttribute('connectionMode'),
          pos: e.getAttribute('data-handlepos') || (cs.position || ''),
          tag: e.tagName,
          cls: (e.className || '').toString().slice(0, 70),
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          bg: cs.backgroundColor, border: cs.borderColor, radius: cs.borderRadius,
          cursor: cs.cursor, opacity: cs.opacity, z: cs.zIndex,
        };
      })
      // 只保留带 React Flow 结构属性的（真正的口），再按坐标排
      .filter((h) => h.handleId !== null || /handle/i.test(h.cls));
    out.push({ id: nid, name, nHandles: list.length, handles: list });
  }
  return out;
});

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
  await beginBatch(B, { note: '连接口按 data-handleid 全量盘点 / 星级换类型再扫 + 列表行内 + 右键菜单' });

  const out = {};
  await page.mouse.move(720, 260); await page.waitForTimeout(800);

  // ═══ 1. 连接口全量盘点
  console.log('--- BG1-1 连接口全量盘点 ---');
  const hs = await handles();
  const withH = hs.filter((n) => n.nHandles > 0);
  const noH = hs.filter((n) => n.nHandles === 0);
  console.log(`  ${hs.length} 个节点；**有连接口的 ${withH.length} 个、没有的 ${noH.length} 个**`);
  console.log(`  没有连接口的：${noH.map((n) => `${n.id}(${n.name})`).join(', ') || '（无）'}`);
  for (const n of withH) {
    console.log(`  ${n.id} ${n.name}：${n.nHandles} 个口`);
    for (const h of n.handles) {
      console.log(`    [${h.rect}] id=${h.handleId} nodeType=${h.nodeType} connectable=${h.isConnectable} ` +
        `mode=${h.connectionMode} ${h.w}×${h.h} r=${h.radius} cursor=${h.cursor} bg=${h.bg}`);
    }
  }
  out.handles = { total: hs.length, withHandles: withH.length, noHandles: noH.map((n) => n.id), list: withH };
  await shot(page, 'M-194-连接口-全量盘点.png');
  out.shot = 'M-194-连接口-全量盘点.png';

  // ═══ 2. 连接口悬停读提示（BF 的老手段）
  console.log('\n--- BG1-2 连接口悬停提示 ---');
  const tips = [];
  for (const n of withH) {
    for (const h of n.handles.slice(0, 2)) {
      const [x, y, w, hh] = h.rect;
      if (w < 4 || hh < 4) continue;
      const cx = x + w / 2, cy = y + hh / 2;
      // 落点归属校验（AZ 的硬闸）
      const own = await page.evaluate(([px, py, hid]) => {
        const o = document.elementFromPoint(px, py);
        return { tag: o ? o.tagName : null,
          handleId: o ? (o.getAttribute('data-handleid') || o.closest('[data-handleid]')?.getAttribute('data-handleid') || null) : null,
          want: hid };
      }, [cx, cy, h.handleId]);
      await page.mouse.move(cx, cy); await page.waitForTimeout(1400);
      const tip = await page.evaluate(() => [...document.querySelectorAll('[class*="Tooltip-tooltip"]')]
        .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
        .map((e) => { const r = e.getBoundingClientRect();
          return { text: (e.innerText || '').replace(/\s+/g, ' ').trim(),
            d: Math.round(Math.hypot(r.x + r.width / 2 - window.__mx, r.y + r.height / 2 - window.__my)) }; })
        .filter((t) => !/按 ESC 退出|^新功能/.test(t.text))
        .sort((a, b) => a.d - b.d)[0] || null);
      await page.evaluate(([px, py]) => { window.__mx = px; window.__my = py; }, [cx, cy]);
      await page.waitForTimeout(300);
      const tip2 = await page.evaluate(() => [...document.querySelectorAll('[class*="Tooltip-tooltip"]')]
        .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
        .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim())
        .filter((t) => !/按 ESC 退出|^新功能/.test(t)));
      tips.push({ node: n.id, name: n.name, handleId: h.handleId, ownerOk: own.handleId === h.handleId, owner: own, tip: tip2 });
      console.log(`  ${n.name} 的「${h.handleId}」：落点归属 ${own.handleId === h.handleId ? '✅' : '⚠️'}；提示 ${JSON.stringify(tip2)}`);
    }
    if (tips.length >= 8) break;
  }
  out.handleTips = tips;

  // ═══ 3. 星级：换类型再扫 + 资产管理列表行内 + 右键菜单
  console.log('\n--- BG1-3 星级入口再扫 ---');
  const scan = [];
  for (const id of ['i-9nlG6HdjK2', 'v-eMpqKtiLlx', 't-UtVx3lZmrV']) {
    const pt = await exclusivePoint(page, id);
    if (pt.err) { console.log(`  ${id} 无独占点`); continue; }
    const before = await fingerprint(page);
    await page.mouse.click(pt.x, pt.y); await page.waitForTimeout(2400);
    const after = await fingerprint(page);
    const added = diffPanels(before, after);
    // 选中后页面里所有「像星级」的东西
    const starish = await page.evaluate(() => {
      const ok = (e) => !['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE'].includes(e.tagName);
      return [...document.querySelectorAll('body *')].filter(ok)
        .map((e) => { const r = e.getBoundingClientRect();
          return { tag: e.tagName, cls: (e.className || '').toString().slice(0, 50),
            text: (e.innerText || e.textContent || '').trim().slice(0, 10),
            aria: e.getAttribute('aria-label'), title: e.getAttribute('title'),
            rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; })
        .filter((e) => e.rect[2] > 0 && e.rect[3] > 0
          && /★|☆|星|评级|rating|star|favorite|收藏/i.test(`${e.text}${e.aria || ''}${e.title || ''}${e.cls}`));
    });
    scan.push({ id, addedPanels: added.length, starish });
    console.log(`  选中 ${id}：新增面板 ${added.length} 个；「星/评/收藏」相关元素 ${starish.length} 个`);
    starish.slice(0, 6).forEach((e) => console.log(`    [${e.rect}] ${e.tag} "${e.text}" aria=${e.aria} cls=${e.cls}`));
    await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  }
  out.starScan = scan;

  // 3b. 右键菜单
  console.log('\n  右键（contextmenu）探测：');
  const pt2 = await exclusivePoint(page, 'i-9nlG6HdjK2');
  if (pt2.err) { console.log('   无独占点'); out.ctx = { err: pt2.err }; }
  else {
    const beforeC = await fingerprint(page);
    await page.mouse.click(pt2.x, pt2.y, { button: 'right' });
    await page.waitForTimeout(2200);
    const afterC = await fingerprint(page);
    const addedC = diffPanels(beforeC, afterC);
    const menu = await page.evaluate(() => {
      const ok = (e) => !['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE'].includes(e.tagName);
      return [...document.querySelectorAll('div,li,button')].filter(ok)
        .map((e) => { const r = e.getBoundingClientRect();
          return { text: (e.innerText || '').replace(/\s+/g, ' ').trim(),
            rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; })
        .filter((e) => e.rect[2] > 40 && e.rect[3] > 6 && e.rect[3] < 50 && e.text && e.text.length < 18
          && e.rect[0] > 0 && e.rect[1] > 0);
    });
    console.log(`   右键后新增面板 ${addedC.length} 个；可见菜单行 ${menu.length} 个`);
    menu.slice(0, 14).forEach((m) => console.log(`     [${m.rect}] "${m.text}"`));
    out.ctx = { added: addedC.length, rows: menu };
    await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  }

  // 3c. 资产管理列表行内还有没有别的按钮
  console.log('\n  资产管理列表行内元素：');
  const dm = await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,[role="button"]')]
      .find((x) => x.getAttribute('aria-label') === '资产管理');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  if (dm) {
    await page.mouse.click(dm.x, dm.y); await page.waitForTimeout(2400);
    const rows = await page.evaluate(() => {
      const rows = [...document.querySelectorAll('*')]
        .filter((e) => (e.innerText || '').trim().startsWith('定位到节点') && e.getBoundingClientRect().height > 20)
        .map((e) => ({ rect: (() => { const r = e.getBoundingClientRect();
          return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })() }));
      if (!rows.length) return { err: 'no rows' };
      const y0 = rows[0].rect[1];
      return { nRows: rows.length, row0Y: y0, inRow0: [...document.querySelectorAll('button,[role="button"]')]
        .map((b) => { const r = b.getBoundingClientRect();
          return { aria: b.getAttribute('aria-label'), title: b.getAttribute('title'),
            text: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 12),
            rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; })
        .filter((b) => b.rect[2] > 0 && b.rect[3] > 0 && b.rect[0] < 330 && Math.abs(b.rect[1] - y0) < 30) }; });
    console.log(`   ${rows.nRows} 行；第 1 行内可点元素：`, JSON.stringify(rows.inRow0));
    out.drawerRow = rows;
    await page.keyboard.press('Escape'); await page.waitForTimeout(1400);
  }

  await logStep(B, {
    id: 'BG1-handles-star-rescan',
    title: '连接口按 data-handleid 全量盘点 / 星级换类型再扫 + 右键 + 列表行内',
    target: 'connect-nodes 讲的是「怎么连」，没讲连接口长什么样。在线上有几个、在哪、能不能点。'
      + '⭐ 认连接口认 React Flow 的结构属性（data-handleid/data-nodeid/data-nodeType），'
      + '不认 class 名字里有没有 Handle —— §22 与 BF2 的教训。'
      + '星级换图片/视频/文本三类节点再扫一遍，并补两处 BF 没碰的地方：右键菜单、资产管理列表行内。',
    evidence: out,
    visible_text: JSON.stringify({ handles: { total: out.handles?.total, with: out.handles?.withHandles,
      detail: out.handles?.list?.map((n) => ({ name: n.name, n: n.nHandles,
        ids: n.handles.map((h) => `${h.handleId}:${h.w}×${h.h}:${h.cursor}`) })) },
      tips: out.handleTips?.filter((t) => t.tip?.length)?.map((t) => `${t.name}/${t.handleId}=${t.tip.join('|')}`),
      star: out.starScan?.map((s) => ({ id: s.id, panels: s.addedPanels, starish: s.starish.length })),
      ctx: { added: out.ctx?.added, rows: out.ctx?.rows?.length } }).slice(0, 3000),
    shot: out.shot,
  });
  console.log('\nBG1 完成');
} finally {
  await browser.close();
}
