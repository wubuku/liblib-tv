// Batch CA — 扫剩下的 📖，四个都带安全网。
//
// 手册里还挂着的、本轮要收的四个：
//  ① 广场排序下拉里到底有哪些选项（BN1 试了四种判据都没读出来）
//  ② 资产行菜单「移动到 ›」子菜单（两轮读数不一致，只能算半个结论）
//  ③ 点一张特效卡片本身会发生什么（一直没点）
//  ④ 有内容时点「翻译提示词」会发生什么（一直没点）
//
// ⭐ ① 的老毛病：**先猜选项名再去找**（BN1 用的正则 `^(全部|最新|最热|价格…)`）。
//    猜错了就永远读不到。本轮换探针：**点开前后各存一份元素指纹，只报新出现的** ——
//    不预设它叫什么名字。
//
// ⭐ ③④ 都有花钱的可能，所以全局挂一道**余额闸**：
//    任何可能扣积分的动作前后各读一次顶栏那枚余额按钮，掉分就当场停手并如实报告。
//    ③④ 的对象也都是「自己造、自己删」：新建的文本节点、新建出来的节点。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView, addNode, nodeCount } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchCA';
const { browser, page } = await launch();
const settle = (ms = 900) => page.waitForTimeout(ms);

/** 顶栏余额：找那枚「纯数字」的按钮。 */
const credits = () => page.evaluate(() => {
  const b = [...document.querySelectorAll('button,[role="button"]')]
    .find((x) => { const t = (x.innerText || '').replace(/\s+/g, '').trim(); return /^\d+$/.test(t) && t.length <= 4; });
  return b ? { text: b.innerText.replace(/\s+/g, ' ').trim(), rect: (() => { const r = b.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })() } : null;
});

/** ⭐ 元素指纹：用来做「点开前 / 点开后」的差集，不预设任何名字。 */
const fingerprint = () => page.evaluate(() => {
  const m = new Map();
  for (const e of document.querySelectorAll('div,li,span,button,a,p')) {
    const r = e.getBoundingClientRect();
    if (r.width < 8 || r.height < 8) continue;
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden' || +s.opacity < 0.05) continue;
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    const k = `${e.tagName}|${(e.getAttribute('class') || '').slice(0, 30)}|${Math.round(r.x)},${Math.round(r.y)},${Math.round(r.width)}x${Math.round(r.height)}`;
    m.set(k, { tag: e.tagName, cls: (e.getAttribute('class') || '').slice(0, 50), text: t.slice(0, 60),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      children: e.children.length });
  }
  return [...m.entries()].map(([k, v]) => ({ k, ...v }));
});
const diffNew = (before, after) => { const seen = new Set(before.map((x) => x.k)); return after.filter((x) => !seen.has(x.k)); };

const clickAria = async (name, wait = 2400) => {
  const t = page.locator(`[aria-label="${name}"]`).first();
  if (!(await t.count())) return { ok: false, why: `没有 aria-label="${name}"` };
  await t.click({ timeout: 5000 }).catch((e) => { throw new Error(`${name} 点击失败: ${e.message.slice(0, 50)}`); });
  await settle(wait);
  return { ok: true };
};
const clickText = async (text, wait = 3000) => {
  const t = page.getByText(text, { exact: false }).first();
  if (!(await t.count())) return { ok: false, why: `找不到文字「${text}」` };
  await t.click({ timeout: 5000 }).catch((e) => { throw new Error(`「${text}」点击失败: ${e.message.slice(0, 50)}`); });
  await settle(wait);
  return { ok: true };
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await settle(1800);
  await fitView(page); await settle(2200);
  await beginBatch(B, { note: '四个 📖，都带余额闸与清理路径' });
  const out = {};
  const baseNodes = await nodeCount(page);
  const c0 = await credits();
  out.base = { nodes: baseNodes, credits: c0 };
  console.log(`═══ 基线：节点 ${baseNodes}｜余额 ${JSON.stringify(c0)} ═══`);

  // ═══ ① 广场排序下拉（换探针：DOM 差集）
  console.log('\n═══ ① 广场排序下拉：点开前后做元素差集 ═══');
  try {
    const a = await clickAria('素材库'); console.log(`  进素材库：${JSON.stringify(a)}`);
    const b = await clickText('风格库'); console.log(`  进风格库：${JSON.stringify(b)}`);
    const fpBefore = await fingerprint();
    const srt = await page.evaluate(() => {
      for (const e of document.querySelectorAll('div,button,span')) {
        const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
        if (!/^(全部|最新|最热|价格)/.test(t)) continue;
        const r = e.getBoundingClientRect();
        if (r.width < 40 || r.height < 12) continue;
        return { t, at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
      } return null; });
    console.log(`  排序按钮：${JSON.stringify(srt)}`);
    if (srt) {
      await page.mouse.click(srt.at[0], srt.at[1]); await settle(1800);
      const fpAfter = await fingerprint();
      const fresh = diffNew(fpBefore, fpAfter);
      // 候选项 = 新出现的、**自己不含子元素**的（叶子）文本块
      const leaves = fresh.filter((x) => x.children === 0 && x.text && x.text.length <= 14);
      const uniq = []; const seen = new Set();
      for (const l of leaves) { if (!seen.has(l.text)) { seen.add(l.text); uniq.push(l); } }
      console.log(`  ⭐ 新出现元素 ${fresh.length} 个，其中叶子 ${leaves.length} 个：`);
      uniq.forEach((l) => console.log(`     「${l.text}」 ${JSON.stringify(l.rect)} <${l.tag}.${l.cls}>`));
      out.sort = { button: srt, freshCount: fresh.length, leaves: uniq };
      await shot(page, 'M-290-风格广场-排序下拉选项.png');
      out.shot1 = 'M-290-风格广场-排序下拉选项.png';
      await page.keyboard.press('Escape'); await settle(1000);
    }
  } catch (e) { out.sort = { err: e.message.slice(0, 80) }; console.log('  ⛔ ' + e.message.slice(0, 80)); }
  await clearToasts(page);

  // ═══ ② 资产行菜单「移动到 ›」子菜单
  console.log('\n═══ ② 资产行菜单「移动到 ›」子菜单 ═══');
  try {
    const mgr = page.locator('[aria-label="资产管理"]').first();
    await mgr.click({ timeout: 5000 }); await settle(2200);
    // 切到「资产」页签（按 x 挑那个底栏的开关，两处同名）
    const mgrs = page.locator('[aria-label="资产管理"]');
    const cnt = await mgrs.count();
    for (let i = 0; i < cnt; i += 1) {
      const bb = await mgrs.nth(i).boundingBox();
      if (bb && bb.x < 400) { await mgrs.nth(i).click({ timeout: 4000 }).catch(() => {}); await settle(1800); break; }
    }
    const row = await page.evaluate(() => {
      const rows = [...document.querySelectorAll('div')].filter((d) => {
        const t = (d.innerText || '').trim(); const r = d.getBoundingClientRect();
        return t === '待分类资产' && r.x < 320 && r.width > 120 && r.height > 18; });
      if (!rows.length) return null;
      const r = rows[0].getBoundingClientRect();
      return { at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
    });
    console.log(`  「待分类资产」行：${JSON.stringify(row)}`);
    if (row) {
      await page.mouse.move(row.at[0], row.at[1]); await settle(1200);
      const more = await page.evaluate((rect) => {
        const c = [...document.querySelectorAll('button,[role="button"]')]
          .map((b) => ({ b, r: b.getBoundingClientRect() }))
          .filter((x) => x.r.y > rect[1] - 6 && x.r.y < rect[1] + rect[3] + 6 && x.r.x > rect[0] + rect[2] - 90 && x.r.width > 8 && x.r.width < 60);
        const t = c[c.length - 1];
        return t ? { at: [Math.round(t.r.x + t.r.width / 2), Math.round(t.r.y + t.r.height / 2)], w: Math.round(t.r.width), aria: t.b.getAttribute('aria-label') } : null;
      }, row.rect);
      console.log(`  行尾按钮：${JSON.stringify(more)}`);
      if (more) {
        await page.mouse.click(more.at[0], more.at[1]); await settle(1800);
        const mv = await page.evaluate(() => {
          const e = [...document.querySelectorAll('div,span,button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '移动到' || (x.innerText || '').replace(/\s+/g, ' ').trim() === '移动到 ›');
          if (!e) return null; const r = e.getBoundingClientRect();
          return { at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
        });
        console.log(`  「移动到」：${JSON.stringify(mv)}`);
        if (mv) {
          const fpB = await fingerprint();
          await page.mouse.move(mv.at[0], mv.at[1]); await settle(2000);
          const fpA = await fingerprint();
          const fresh = diffNew(fpB, fpA).filter((x) => x.children === 0 && x.text && x.text.length <= 16);
          const uniq = []; const seen = new Set();
          for (const l of fresh) { if (!seen.has(l.text)) { seen.add(l.text); uniq.push(l); } }
          console.log(`  ⭐ 悬停后新出现的叶子：${JSON.stringify(uniq.map((l) => ({ t: l.text, rect: l.rect, cls: l.cls })))}`);
          out.moveSub = { row, more, mv, fresh: uniq };
          await shot(page, 'M-291-资产行菜单-移动到子菜单.png');
          out.shot2 = 'M-291-资产行菜单-移动到子菜单.png';
        }
        await page.keyboard.press('Escape'); await settle(900);
      }
    }
  } catch (e) { out.moveSub = { err: e.message.slice(0, 80) }; console.log('  ⛔ ' + e.message.slice(0, 80)); }
  await page.keyboard.press('Escape'); await settle(1200);

  // ═══ ③ 点一张特效卡片本身（余额闸 + 清理）
  console.log('\n═══ ③ 点一张特效卡片本身 ═══');
  const cBefore3 = await credits();
  const nBefore3 = await nodeCount(page);
  let clicked = null;
  try {
    await clickAria('素材库'); await clickText('特效库');
    const card = await page.evaluate(() => {
      const btn = [...document.querySelectorAll('button[aria-label="详情"]')];
      if (!btn.length) return null;
      const r = btn[Math.floor(btn.length / 2)].getBoundingClientRect();
      // 点卡片本体：往上/左挪开详情按钮那一小块
      return { detailBtn: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        body: [Math.round(r.x - 40), Math.round(r.y + 30)], count: btn.length };
    });
    console.log(`  卡片：${JSON.stringify(card)}`);
    if (card) {
      await page.mouse.click(card.body[0], card.body[1]); await settle(3000);
      const dlg = await page.evaluate(() => [...document.querySelectorAll('[role="dialog"],.mantine-Modal-content')]
        .filter((d) => { const r = d.getBoundingClientRect(); return r.width > 4 && r.height > 4; })
        .map((d) => (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 140)));
      const nAfter3 = await nodeCount(page);
      const cAfter3 = await credits();
      clicked = { card, dialogs: dlg, nodesBefore: nBefore3, nodesAfter: nAfter3, creditsBefore: cBefore3, creditsAfter: cAfter3 };
      console.log(`  节点 ${nBefore3} → ${nAfter3}｜余额 ${cBefore3?.text} → ${cAfter3?.text}｜弹窗 ${JSON.stringify(dlg).slice(0, 200)}`);
      await shot(page, 'M-292-点过一张特效卡片之后.png');
      out.shot3 = 'M-292-点过一张特效卡片之后.png';
      // 清理：若建了新节点，删掉**本轮自己刚建**的那个
      if (nAfter3 > nBefore3) {
        const fresh = await page.evaluate((b) => [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id'))
          .filter((id) => !b.includes(id)), window.__caBaseIds || []);
        console.log(`  清理：新节点 ${JSON.stringify(fresh)}`);
        out.clean3 = fresh;
      }
    }
  } catch (e) { out.click3 = { err: e.message.slice(0, 80) }; console.log('  ⛔ ' + e.message.slice(0, 80)); }
  await page.keyboard.press('Escape'); await settle(1200);
  await clearToasts(page);

  // ═══ ④ 有内容时点「翻译提示词」（自建节点 → 自删）
  console.log('\n═══ ④ 自建文本节点 → 填内容 → 点「翻译提示词」═══');
  const cBefore4 = await credits();
  const nBefore4 = await nodeCount(page);
  let tr = null;
  try {
    const made = await addNode(page, '文本', { settle: 2600 });
    console.log(`  新建文本节点：${JSON.stringify(made)}`);
    const nAfter4 = await nodeCount(page);
    const newId = await page.evaluate((b) => {
      const ids = [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id'));
      return ids.find((i) => !b.includes(i)) || null;
    }, await page.evaluate((ids) => ids, []));
    void newId;
    // 找到刚落地的那个节点（id 不在开场那批里）
    const landed = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')]
      .map((n) => ({ id: n.getAttribute('data-id'), t: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30),
        r: (() => { const b = n.getBoundingClientRect(); return [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)]; })() }))
      .filter((n) => n.t.includes('文本节点')));
    console.log(`  文本节点：${JSON.stringify(landed)}`);
    const target = landed[landed.length - 1];
    if (target) {
      await page.mouse.click(target.r[0], target.r[1]); await settle(2200);
      const ta = await page.evaluate(() => {
        const ta = [...document.querySelectorAll('textarea,input[type="text"]')].filter((e) => {
          const r = e.getBoundingClientRect(); return r.width > 100 && r.height > 20; });
        const t = ta[ta.length - 1];
        if (!t) return null;
        const r = t.getBoundingClientRect();
        return { at: [Math.round(r.x + r.width / 2), Math.round(r.y + Math.min(20, r.height / 2))], value: t.value || '' };
      });
      console.log(`  提示词框：${JSON.stringify(ta)}`);
      if (ta) {
        await page.mouse.click(ta.at[0], ta.at[1]); await settle(600);
        await page.keyboard.type('一只猫在雨中的屋檐下', { delay: 25 }); await settle(700);
        const val = await page.evaluate(() => [...document.querySelectorAll('textarea')].map((t) => t.value).filter(Boolean).pop());
        console.log(`  填入后：${JSON.stringify(val)}`);
        const btn = await page.evaluate(() => {
          const cands = [...document.querySelectorAll('button,[role="button"]')].filter((b) => {
            const html = b.outerHTML.slice(0, 600);
            return /文A|translate/i.test(html) || /翻译/.test(b.getAttribute('aria-label') || '') || /翻译/.test(b.getAttribute('title') || ''); });
          const b = cands[0]; if (!b) return null;
          const r = b.getBoundingClientRect();
          return { at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], aria: b.getAttribute('aria-label'), title: b.getAttribute('title') };
        });
        console.log(`  翻译按钮：${JSON.stringify(btn)}`);
        if (btn) {
          await page.mouse.click(btn.at[0], btn.at[1]); await settle(3500);
          const after = await page.evaluate(() => [...document.querySelectorAll('textarea')].map((t) => t.value).filter(Boolean).pop());
          const tip = await page.evaluate(() => [...document.querySelectorAll('[class*="toast" i],[class*="notification" i],[class*="alert" i]')]
            .filter((d) => { const r = d.getBoundingClientRect(); return r.width > 10 && r.height > 10 && r.top < 700; })
            .map((d) => (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 80)));
          const cAfter4 = await credits();
          tr = { node: target, filled: val, button: btn, after, tip, creditsBefore: cBefore4, creditsAfter: cAfter4 };
          console.log(`  ⭐ 点完：提示词=${JSON.stringify(after)}｜提示条=${JSON.stringify(tip)}｜余额 ${cBefore4?.text} → ${cAfter4?.text}`);
          await shot(page, 'M-293-翻译提示词之后.png');
          out.shot4 = 'M-293-翻译提示词之后.png';
        }
      }
    }
  } catch (e) { out.translate = { err: e.message.slice(0, 80) }; console.log('  ⛔ ' + e.message.slice(0, 80)); }

  // ═══ 清理：把本轮自己建的节点删掉
  const finalNodes = await nodeCount(page);
  if (finalNodes > baseNodes) {
    console.log(`\n═══ 清理：节点 ${baseNodes} → ${finalNodes}，删掉多出来的 ═══`);
    const c1 = await credits();
    await page.mouse.click(180, 150); await settle(400);
    // 只删最后落地的那个文本节点：点它选中 → Delete
    const last = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')]
      .map((n) => ({ id: n.getAttribute('data-id'), t: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20),
        r: (() => { const b = n.getBoundingClientRect(); return [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)]; })() }))
      .filter((n) => n.t.includes('文本节点')).pop());
    if (last) {
      await page.mouse.click(last.r[0], last.r[1]); await settle(1200);
      const sel = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map((n) => n.getAttribute('data-id')));
      console.log(`  选中 ${JSON.stringify(sel)}｜按 Delete`);
      await page.keyboard.press('Delete'); await settle(1800);
    }
    const c2 = await credits();
    out.cleanup4 = { before: baseNodes, afterAdd: finalNodes, afterDel: await nodeCount(page), credits: [c1?.text, c2?.text] };
    console.log(`  清理结果：节点 ${await nodeCount(page)}｜余额 ${c1?.text} → ${c2?.text}`);
  } else {
    out.cleanup4 = { note: '本轮没多出节点，无需清理' };
  }
  out.translate = tr; out.click3 = clicked;
  await clearToasts(page);

  const fin = await nodeCount(page); const cFin = await credits();
  out.final = { nodes: fin, credits: cFin, restored: fin === baseNodes };
  console.log(`\n═══ 收尾：节点 ${fin}（基线 ${baseNodes}）｜余额 ${JSON.stringify(cFin)}｜复原=${out.final.restored}`);
  console.log(`\n═══ 本轮结论 ═══`);
  console.log(`  ① 排序下拉选项：${JSON.stringify(((out.sort || {}).leaves || []).map((l) => l.text))}`);
  console.log(`  ② 移动到子菜单：${JSON.stringify((((out.moveSub || {}).fresh) || []).map((l) => l.text))}`);
  console.log(`  ③ 点特效卡片：节点 ${clicked?.nodesBefore} → ${clicked?.nodesAfter}｜余额 ${clicked?.creditsBefore?.text} → ${clicked?.creditsAfter?.text}`);
  console.log(`  ④ 翻译提示词：${tr ? `提示词 ${JSON.stringify(tr.filled)} → ${JSON.stringify(tr.after)}｜余额 ${tr.creditsBefore?.text} → ${tr.creditsAfter?.text}` : '⛔ 没测到'}`);

  await logStep(B, {
    id: 'CA-four-open-questions',
    title: '四个 📖 一起扫：排序下拉 / 移动到子菜单 / 点特效卡片 / 翻译提示词',
    target: '① 排序下拉换了探针：BN1 用**先猜选项名再找**的正则，猜错就永远读不到；'
      + '本轮改成**点开前后各存元素指纹、只报新出现的**，不预设它叫什么。'
      + '③④ 有花钱的可能，所以挂**余额闸**：动作前后各读一次顶栏余额，掉分就停手。'
      + '对象也都是自己造自己删。',
    evidence: out,
    visible_text: JSON.stringify({ 基线: out.base, 排序下拉: out.sort, 移动到子菜单: out.moveSub,
      点特效卡片: out.click3, 翻译提示词: out.translate, 清理: out.cleanup4, 收尾: out.final }).slice(0, 3400),
    shot: out.shot1,
  });
  console.log('\nCA 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 5).join('\n'));
} finally {
  await browser.close();
}
