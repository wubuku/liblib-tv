// Batch BF2 —— BF1 的三个目标全部因为「读数没定位到容器」而失真，这轮改用容器级读法。
//
// BF1 的教训（§22 的第三次翻车）：
//   · 缩放菜单三行全报「没找到「放大」」—— `clickText` 是在**整页**找的，
//     而菜单要么没开、要么整页里那三行的 `innerText` 被更大的父容器吃掉了。
//   · 画布下拉读出 **161 条**，里面混进了画布上的节点（「导演台 5」y=-320）
//     和顶栏的「开通会员 限时 45 折 20」—— 因为按文本+尺寸筛不构成容器边界。
//   · 行菜单读数同样被顶栏和画布内容污染。
//
// ✅ 正解就是 §22 已经写下的那条：**用 `fingerprint()` / `diffPanels()`
//    先定位到「点开之后新出现的那个面板」，再读它的 `innerText`。**
//    只看「可见 + 面积 + 位置」，不认 class，也不认文案。
//
// 三个目标：
//   1. 缩放菜单：定位到菜单容器 → 读它的**逐行**内容 → 再逐行点，看 scale 与菜单开关
//   2. 画布下拉：定位到下拉容器 → 读**完整**条目数（BF1 只读到视口内那截）
//   3. 节点星级：选中节点 → 对比选中前后的**面板差集**，找有没有星级 UI
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBF2';
const { browser, page } = await launch();

const snapScale = () => page.evaluate(() => {
  const v = document.querySelector('.react-flow__viewport');
  const m = v ? /scale\(([\d.]+)\)/.exec(v.style.transform || '') : null;
  return m ? +m[1] : null; });

/** ⭐ 找一个「可见 + 有面积 + 在视口内 + 不是画布/顶栏」的浮层容器，返回候选列表。 */
const overlays = () => page.evaluate(() => [...document.querySelectorAll('div,section,aside,ul')]
  .filter((e) => !['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE'].includes(e.tagName))
  .filter((e) => {
    if (e.closest('.react-flow')) return false;          // 画布里的容器不算
    if (e.closest('header, nav')) return false;          // 顶栏不算
    const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity <= 0.05) return false;
    if (r.width < 100 || r.height < 60) return false;
    if (r.x + r.width < 0 || r.x > 1440 || r.y + r.height < 0 || r.y > 810) return false;
    const txt = (e.innerText || '').replace(/\s+/g, ' ').trim();
    return txt.length > 0;
  })
  .map((e) => {
    const r = e.getBoundingClientRect();
    return { cls: (e.className || '').toString().slice(0, 60),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      z: getComputedStyle(e).zIndex, pos: getComputedStyle(e).position,
      area: Math.round(r.width * r.height),
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300) };
  })
  .sort((a, b) => a.area - b.area));   // 最内层优先

/** ⭐ 容器内逐行读：把直接子元素按 y 排一行一个。 */
const rowsIn = (pg, handle) => pg.evaluate(([h]) => {
  const all = [...document.querySelectorAll('div,section,aside,ul')]
    .filter((e) => !['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE'].includes(e.tagName))
    .filter((e) => { const r = e.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && !e.closest('.react-flow') && !e.closest('header, nav'); })
    .map((e) => { const r = e.getBoundingClientRect();
      return { cls: (e.className || '').toString().slice(0, 60),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        text: (e.innerText || '').replace(/\s+/g, ' ').trim() }; })
    .filter((e) => e.text && e.text.length < 60 && e.rect[2] > 30 && e.rect[3] > 6 && e.rect[3] < 60);
  // 找与 h 同位置的最小容器，再在里面取行
  const host = all.filter((e) => e.cls === h.cls && e.rect[0] === h.rect[0] && e.rect[1] === h.rect[1]);
  const box = host.length ? Math.min(...host.map((e) => e.rect[2] * e.rect[3])) : 0;
  const inside = all.filter((e) => e.rect[0] >= h.rect[0] && e.rect[1] >= h.rect[1]
    && e.rect[0] + e.rect[2] <= h.rect[0] + h.rect[2] + 2
    && e.rect[1] + e.rect[3] <= h.rect[1] + h.rect[3] + 2);
  const seen = new Set(); const out = [];
  for (const e of inside.sort((a, b) => a.rect[1] - b.rect[1] || a.rect[0] - b.rect[0])) {
    const k = `${e.rect[0]},${e.rect[1]}`;
    if (seen.has(k)) continue; seen.add(k);
    out.push({ text: e.text, rect: e.rect, cls: e.cls });
  }
  return { hostArea: box, rows: out };
}, [handle]);

/** 点容器内某一行（按文本），并验落点归属。 */
const clickRow = async (pg, text) => pg.evaluate((t) => {
  const cands = [...document.querySelectorAll('div,button,li,span,a,[role="menuitem"]')]
    .filter((e) => !['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE'].includes(e.tagName))
    .filter((e) => { const r = e.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && !e.closest('.react-flow') && !e.closest('header, nav'); })
    .filter((e) => (e.innerText || '').replace(/\s+/g, ' ').trim() === t)
    .map((e) => { const r = e.getBoundingClientRect();
      return { e, x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2),
        w: Math.round(r.width), h: Math.round(r.height) }; });
  if (!cands.length) return { err: '没找到「' + t + '」' };
  cands.sort((a, b) => a.w * a.h - b.w * b.h);
  const c = cands[0];
  const at = document.elementFromPoint(c.x, c.y);
  return { x: c.x, y: c.y, n: cands.length,
    ownerOk: !!(at && (at === c.e || c.e.contains(at) || at.contains(c.e))),
    ownerTag: at ? at.tagName : null, ownerText: at ? (at.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20) : null };
}, text);

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1600);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '用容器级读法重做：缩放菜单逐行 / 画布下拉完整列表 / 节点星级面板差集' });

  const out = {};
  await page.mouse.move(720, 260); await page.waitForTimeout(800);

  // ═══ 1. 缩放菜单
  console.log('--- BF2-1 缩放菜单（容器级读法）---');
  const ov0 = await overlays();
  console.log('  打开前浮层候选：', ov0.length, JSON.stringify(ov0.map((o) => o.rect)).slice(0, 200));
  // 打开：点左下角「缩放选项」
  const zp = await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,[role="button"]')]
      .find((x) => x.getAttribute('aria-label') === '缩放选项');
    if (!e) return { err: '没找到缩放按钮' };
    const r = e.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2),
      text: (e.innerText || '').trim() };
  });
  if (zp.err) { console.log(' ', zp.err); out.zoom = zp; }
  else {
    console.log(`  缩放按钮正文 = "${zp.text}"`);
    await page.mouse.move(zp.x, zp.y); await page.waitForTimeout(300);
    await page.mouse.click(zp.x, zp.y); await page.waitForTimeout(2200);
    const ov1 = await overlays();
    const added = diffPanels(ov0.map((x) => x.rect), ov1.map((x) => x.rect));
    console.log(`  打开后浮层 ${ov1.length} 个；新增 ${added.length} 个`);
    ov1.slice(0, 6).forEach((o) => console.log(`    [${o.rect}] z=${o.z} "${o.text.slice(0, 70)}"`));
    out.zoom = { btn: zp, before: ov0.length, after: ov1.length, added, overlays: ov1.slice(0, 6) };

    // ⭐ 定位到菜单本体：文字里同时含「缩放至」和「适合屏幕」的那个最小容器
    const menuHost = ov1.find((o) => /适合屏幕/.test(o.text) && /缩放至|50%|100%/.test(o.text));
    if (!menuHost) { console.log('  ⚠️ 没定位到菜单容器'); out.zoom.host = null; }
    else {
      console.log(`  菜单容器 = [${menuHost.rect}] 面积 ${menuHost.area}："${menuHost.text.slice(0, 80)}"`);
      out.zoom.host = menuHost;
      const rows = await rowsIn(page, menuHost);
      console.log(`  容器内读到 ${rows.rows.length} 行：`);
      rows.rows.forEach((r) => console.log(`    [${r.rect}] "${r.text}"`));
      out.zoom.rows = rows.rows;
      await shot(page, 'M-191-缩放菜单-全貌.png');
      out.shot = 'M-191-缩放菜单-全貌.png';

      // 逐行动作项
      const actions = ['放大', '缩小', '适合屏幕'];
      const results = [];
      for (const label of actions) {
        // 菜单此刻还开着吗？用容器还在不在判断
        const still = (await overlays()).find((o) => o.cls === menuHost.cls
          && o.rect[0] === menuHost.rect[0] && o.rect[1] === menuHost.rect[1]);
        if (!still) {
          // 重新打开
          await page.mouse.click(zp.x, zp.y); await page.waitForTimeout(2000);
          console.log(`    （菜单已关，重新打开）`);
        }
        const s0 = await snapScale();
        const c = await clickRow(page, label);
        if (c.err) { results.push({ label, err: c.err }); console.log(`  ${label}: ${c.err}`); continue; }
        await page.mouse.click(c.x, c.y);
        await page.waitForTimeout(2300);
        const s1 = await snapScale();
        const ov2 = await overlays();
        const stillOpen = ov2.some((o) => o.cls === menuHost.cls
          && o.rect[0] === menuHost.rect[0] && o.rect[1] === menuHost.rect[1]);
        results.push({ label, hit: c, scaleBefore: s0, scaleAfter: s1,
          changed: s0 !== s1, menuStillOpen: stillOpen });
        console.log(`  ${label}：落点归属 ${c.ownerOk ? '✅' : `⚠️ ${c.ownerTag}`} "${c.ownerText}"；` +
          `scale ${s0} → ${s1} ${s0 !== s1 ? '(变了)' : '(没变)'}；菜单${stillOpen ? '还开着' : '关了'}`);
        await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
      }
      out.zoom.actions = results;
      // 复原
      await page.mouse.click(zp.x, zp.y); await page.waitForTimeout(2000);
      const inp = await page.evaluate(() => {
        const e = document.querySelector('input[aria-label="缩放比例"]');
        if (!e) return { err: '没找到缩放输入框' };
        e.focus(); return { ok: true }; });
      if (inp.ok) {
        await page.keyboard.press('Meta+a'); await page.keyboard.type('100');
        await page.keyboard.press('Enter'); await page.waitForTimeout(2200);
      }
      await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
      out.zoom.restored = await snapScale();
      console.log('  复原 scale =', out.zoom.restored);
    }
  }

  // ═══ 2. 顶栏画布下拉
  console.log('\n--- BF2-2 顶栏画布下拉（容器级读法）---');
  const cb = await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,[role="button"]')]
      .find((x) => /^画布\s*\d+$/.test((x.innerText || '').replace(/\s+/g, ' ').trim()));
    if (!e) return { err: '没找到「画布 N」' };
    const r = e.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2),
      text: (e.innerText || '').trim(), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  });
  if (cb.err) { console.log(' ', cb.err); out.canvasMenu = cb; }
  else {
    const ovA = await overlays();
    await page.mouse.move(cb.x, cb.y); await page.waitForTimeout(300);
    await page.mouse.click(cb.x, cb.y); await page.waitForTimeout(2400);
    const ovB = await overlays();
    console.log(`  打开后浮层 ${ovB.length} 个（打开前 ${ovA.length}）`);
    // 菜单本体：高度大、含多个「画布 N」
    const host = ovB.filter((o) => (o.text.match(/画布\s*\d+/g) || []).length >= 2)
      .sort((a, b) => a.area - b.area)[0];
    if (!host) { console.log('  ⚠️ 没定位到下拉容器'); out.canvasMenu = { btn: cb, err: 'no host' }; }
    else {
      console.log(`  下拉容器 = [${host.rect}] "${host.text.slice(0, 100)}"`);
      // 容器可能超出视口 —— 要读完整列表得先滚
      const full = await page.evaluate(([r]) => {
        const all = [...document.querySelectorAll('div,li,button')].filter((e) => {
          const q = e.getBoundingClientRect();
          return q.x >= r[0] - 4 && q.x + q.width <= r[0] + r[2] + 4
            && q.width > 30 && q.height > 8 && q.height < 60;
        });
        const seen = new Set(); const out2 = [];
        for (const e of all) {
          const q = e.getBoundingClientRect();
          const k = `${Math.round(q.x)},${Math.round(q.y)}`;
          if (seen.has(k)) continue; seen.add(k);
          const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
          if (t && t.length < 30) out2.push({ text: t,
            rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] });
        }
        return out2.sort((a, b) => a.rect[1] - b.rect[1]);
      }, [host.rect]);
      // 去重（父子同文）
      const uniq = []; const seenT = new Set();
      for (const f of full) { if (!seenT.has(f.text)) { seenT.add(f.text); uniq.push(f); } }
      console.log(`  下拉里读到 ${uniq.length} 个不同条目：`);
      uniq.forEach((i) => console.log(`    [${i.rect}] "${i.text}"`));
      out.canvasMenu = { btn: cb, host, items: uniq };
      await shot(page, 'M-192-画布下拉-列表.png');
      out.shot2 = 'M-192-画布下拉-列表.png';
      await page.keyboard.press('Escape'); await page.waitForTimeout(1600);
    }
  }

  // ═══ 3. 节点星级 —— 用「选中前后的面板差集」找
  console.log('\n--- BF2-3 节点星级（面板差集法）---');
  await fitView(page); await page.waitForTimeout(1600);
  const before = await fingerprint(page);
  const sel = await page.evaluate(() => {
    const ns = [...document.querySelectorAll('.react-flow__node')];
    for (const n of ns) {
      const r = n.getBoundingClientRect();
      for (let fy = 0.2; fy <= 0.8; fy += 0.15) for (let fx = 0.06; fx <= 0.95; fx += 0.06) {
        const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
        const o = document.elementFromPoint(x, y);
        if (o && o.closest('.react-flow__node') === n) return { x, y, id: n.getAttribute('data-id') };
      }
    }
    return { err: '没有独占点' }; });
  if (sel.err) { console.log(' ', sel.err); out.stars = sel; }
  else {
    await page.mouse.click(sel.x, sel.y); await page.waitForTimeout(2600);
    const after = await fingerprint(page);
    const added = diffPanels(before, after);
    console.log(`  选中 ${sel.id} 后新增面板 ${added.length} 个：`);
    added.forEach((a) => console.log(`    "${String(a.all || a.text || '').replace(/\s+/g, ' ').slice(0, 160)}"`));
    out.stars = { selected: sel.id, addedCount: added.length, added };
    // 选中后的所有按钮无障碍名（容器级）
    const barBtns = await page.evaluate(() => {
      const ok = (e) => !['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE'].includes(e.tagName);
      return [...document.querySelectorAll('button,[role="button"]')].filter(ok)
        .map((b) => { const r = b.getBoundingClientRect();
          return { aria: b.getAttribute('aria-label'), title: b.getAttribute('title'),
            text: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14),
            rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; })
        .filter((b) => b.rect[2] > 0 && b.rect[3] > 0 && b.rect[1] > 40 && b.rect[1] < 810)
        .filter((b) => /★|星|评|rating|star/i.test(`${b.aria || ''}${b.title || ''}${b.text}`));
    });
    console.log(`  选中后带「星/评」字样的按钮：${barBtns.length} 个`, JSON.stringify(barBtns).slice(0, 300));
    out.stars.starButtons = barBtns;
    await shot(page, 'M-193-节点星级-入口探查.png');
    out.shot3 = 'M-193-节点星级-入口探查.png';
  }

  await logStep(B, {
    id: 'BF2-container-scoped-reads',
    title: '容器级读法：缩放菜单逐行 / 画布下拉完整列表 / 节点星级面板差集',
    target: 'BF1 三个目标全部因为「在整页上按文本+尺寸筛」而失真：'
      + '缩放菜单三行全报「没找到」，画布下拉读出 161 条混进画布节点与顶栏元素。'
      + '这轮改用 §22 的正解：先用 fingerprint/diffPanels 定位到容器，再读容器的 innerText。',
    evidence: out,
    visible_text: JSON.stringify({ zoom: { host: out.zoom?.host?.rect, rows: out.zoom?.rows?.map((r) => r.text),
      actions: out.zoom?.actions?.map((a) => ({ label: a.label, changed: a.changed, menuStillOpen: a.menuStillOpen })), restored: out.zoom?.restored },
      canvasMenu: { host: out.canvasMenu?.host?.rect, n: out.canvasMenu?.items?.length },
      stars: { selected: out.stars?.selected, added: out.stars?.addedCount, starButtons: out.stars?.starButtons?.length } }).slice(0, 3000),
    shot: out.shot3 || out.shot2 || out.shot,
  });
  console.log('\nBF2 完成');
} finally {
  await browser.close();
}
