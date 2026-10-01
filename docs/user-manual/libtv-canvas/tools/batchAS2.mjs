// Batch AS2 —— AS 的三处修正与补测。
//
//   AS2a **AS 的缩放持久化判据是废的。**
//        AS 跑的时候起点 `z0` 已经是 `0.5`（AR 那轮留下的），
//        我又去点「缩放至50%」—— 设成了它本来的值，**什么都没变**。
//        然后 `afterReload === afterSet` 自然成立，于是 `persisted: true`。
//        这是**一个没有区分力的实验**：它无法区分「记住了」和「压根没变过」。
//        这次先读 `z0`，**只有在 `z0 !== 目标值` 时才继续** —— 否则这条判据不成立，
//        就把脚本报成 `skipped` 而不是硬凑一个 true。
//
//   AS2b `LibTV Plugin` 在 AS 里报「没有匹配的浮层」。到底是没反应，
//        还是我的正则（`Plugin|插件|安装|市场`）没覆盖它的文案？
//        用 **DOM 指纹差集**判：点之前拍一次，点之后拍一次，比多出来什么。
//        这跟资产管理那个指纹法是同一招（§14）。
//
//   AS2c 工具箱入口在 AS 里 `null` —— 页面上没有含「工具箱」字样的按钮。
//        它藏在「+」添加节点面板 →「素材库」子菜单里（正文 C-09 那张图有）。
//        顺着真实路径走一遍，顺便把素材库子菜单的文案读全。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { nodeCount } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAS2';
const { browser, page } = await launch();

const zoom = () => page.evaluate(() => {
  const v = document.querySelector('.react-flow__viewport');
  const m = v && /scale\(([\d.]+)\)/.exec(v.style.transform || '');
  const e = [...document.querySelectorAll('*')].find((x) => /^\d+%$/.test((x.innerText || '').trim())
    && x.getBoundingClientRect().width < 60 && x.getBoundingClientRect().y > 700);
  return { scale: m ? Number(m[1]) : null, label: e ? e.innerText.trim() : null };
});
const menuOpen = () => page.evaluate(() => [...document.querySelectorAll('[class*="Menu-dropdown"],[class*="Popover-dropdown"]')]
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 40 && r.height > 12; }).length > 0);
async function clickZoomPreset(label) {
  const trig = await page.evaluate(() => {
    const e = [...document.querySelectorAll('*')].find((x) => /^\d+%$/.test((x.innerText || '').trim())
      && x.getBoundingClientRect().width < 60 && x.getBoundingClientRect().y > 700);
    if (!e) return null;
    const b = (e.closest('button,[role="button"]') || e).getBoundingClientRect();
    return { cx: Math.round(b.x + b.width / 2), cy: Math.round(b.y + b.height / 2) };
  });
  if (!trig) return { err: '找不到百分比触发点' };
  if (await menuOpen()) { await page.mouse.click(trig.cx, trig.cy); await page.waitForTimeout(1100); }
  if (!(await menuOpen())) { await page.mouse.click(trig.cx, trig.cy); await page.waitForTimeout(1600); }
  const it = await page.evaluate((l) => {
    const m = [...document.querySelectorAll('[class*="Menu-dropdown"],[class*="Popover-dropdown"]')]
      .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 40 && r.height > 12; })[0];
    if (!m) return null;
    const el = [...m.querySelectorAll('button,div,li')].filter((e) => (e.innerText || '').trim() === l)
      .sort((a, b) => { const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
        return (ra.width * ra.height) - (rb.width * rb.height); })[0];
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
  }, label);
  if (!it) return { err: '菜单里没有「' + label + '」' };
  await page.mouse.click(it.cx, it.cy); await page.waitForTimeout(1900);
  return { ok: true, after: await zoom() };
}
const reload = async () => {
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => {});
  await page.waitForTimeout(4800);
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1400);
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '修 AS 的无区分力判据 + Plugin 面板指纹差集 + 工具箱真实入口' });

  // ── AS2a 缩放持久化：**先确认起点 ≠ 目标值，否则这条实验没有区分力**
  const as2a = { z0: await zoom() };
  const TARGET = 8;                                     // 800%，与 0.5 差得足够远
  if (as2a.z0.scale === TARGET) {
    as2a.skipped = `起点已经是 ${TARGET}，换个目标重试`;
    await clickZoomPreset('缩放至50%');
    await page.waitForTimeout(800);
  }
  const effectiveTarget = as2a.z0.scale === TARGET ? 0.5 : TARGET;
  const presetLabel = effectiveTarget === 8 ? '缩放至800%' : '缩放至50%';
  as2a.target = effectiveTarget; as2a.preset = presetLabel;
  as2a.startScale = (await zoom()).scale;
  as2a.meaningful = as2a.startScale !== effectiveTarget;   // ← 这次实验有没有区分力
  if (as2a.meaningful) {
    as2a.set = await clickZoomPreset(presetLabel);
    as2a.afterSet = await zoom();
    await shot(page, 'M-123-缩放-设为800.png');
    await reload(); as2a.reload1 = await zoom();
    await reload(); as2a.reload2 = await zoom();
    as2a.persisted = as2a.reload1.scale === effectiveTarget && as2a.reload2.scale === effectiveTarget;
    as2a.verdict = as2a.persisted
      ? `设成 ${presetLabel} 之后，**连续两次重载**读到的都是 ${as2a.reload1.label} —— 缩放是按画布持久化的`
      : `设成 ${presetLabel} 之后重载读到 ${as2a.reload1.label} / ${as2a.reload2.label}，**没有保持**，不能说它持久化`;
  } else {
    as2a.verdict = '起点就等于目标值，本轮实验无区分力，不下结论';
  }
  console.log('AS2a:', JSON.stringify(as2a));

  // ── AS2b LibTV Plugin：指纹差集
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(700);
  const before = await fingerprint(page);
  const pluginHit = await page.evaluate(() => {
    const el = [...document.querySelectorAll('button,[role="button"],[aria-label]')]
      .find((e) => (e.getAttribute('aria-label') || '').trim() === 'LibTV Plugin');
    if (!el) return { err: '抽屉里没有「LibTV Plugin」——可能抽屉没开' };
    const r = el.getBoundingClientRect();
    return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  });
  let as2b = { hit: pluginHit };
  if (!pluginHit.err) {
    // 抽屉可能没开：先找 TV Director 入口
    if (!(await page.evaluate(() => !!document.querySelector('.chat-welcome-root,[class*="chat-welcome"]')))) {
      const tv = await page.evaluate(() => {
        const b = [...document.querySelectorAll('button,[role="button"]')].find((e) => /TV\s*Director/i.test(e.getAttribute('aria-label') || ''));
        if (!b) return null; const r = b.getBoundingClientRect();
        return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
      });
      if (tv) { await page.mouse.click(tv.cx, tv.cy); await page.waitForTimeout(2400);
        as2b.reopenedDrawer = true; }
    }
    const hit2 = await page.evaluate(() => {
      const el = [...document.querySelectorAll('button,[role="button"],[aria-label]')]
        .find((e) => (e.getAttribute('aria-label') || '').trim() === 'LibTV Plugin');
      if (!el) return { err: '还是没有' };
      const r = el.getBoundingClientRect();
      return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
    });
    as2b.hit2 = hit2;
    if (!hit2.err) {
      const urlBefore = page.url();
      const nodesBefore = await nodeCount(page);
      const fpBefore = await fingerprint(page);
      await page.mouse.click(hit2.cx, hit2.cy);
      await page.waitForTimeout(3200);
      const fpAfter = await fingerprint(page);
      as2b.diff = diffPanels(fpBefore, fpAfter);
      as2b.urlChanged = page.url() !== urlBefore;
      as2b.nodesChanged = (await nodeCount(page)) !== nodesBefore;
      as2b.modals = await page.evaluate(() => [...document.querySelectorAll('[class*="Modal-inner"],[class*="Modal-content"],[role="dialog"]')]
        .map((e) => { const r = e.getBoundingClientRect();
          return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
            cls: (e.className || '').toString().slice(0, 80),
            text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400) }; })
        .filter((m) => m.rect[2] > 60 && m.rect[3] > 40));
      as2b.floats = await page.evaluate(() => [...document.querySelectorAll('[class*="Popover-dropdown"],[class*="Menu-dropdown"],[class*="Tooltip"]')]
        .map((e) => { const r = e.getBoundingClientRect();
          return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
            text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300) }; })
        .filter((m) => m.rect[2] > 40 && m.rect[3] > 20));
      as2b.toasts = await page.evaluate(() => [...document.querySelectorAll('[class*="Notification"],[class*="Toast"]')]
        .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()).filter(Boolean).slice(0, 5));
      await shot(page, 'M-126-LibTV-Plugin-点开之后.png');
    }
  }
  console.log('AS2b:', JSON.stringify(as2b).slice(0, 2200));

  // ── AS2c 工具箱：走「+」→「素材库」的真实路径
  await reload();
  const as2c = {};
  const addBtn = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button,[role="button"]')]
      .filter((x) => !x.innerText.trim() && x.getBoundingClientRect().width > 30 && x.getBoundingClientRect().height > 30)
      .map((x) => { const r = x.getBoundingClientRect();
        return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; })
      .filter((x) => x.cx > 800 && x.cx < 1100 && x.cy > 700);
    return addBtn0 = (b[0] || null);
  });
  as2c.addBtn = addBtn;
  if (addBtn) {
    await page.mouse.click(addBtn.cx, addBtn.cy); await page.waitForTimeout(2200);
    as2c.panelText = await page.evaluate(() => {
      const p = [...document.querySelectorAll('div')].filter((e) => { const r = e.getBoundingClientRect();
        return r.width > 150 && r.height > 150 && /素材库|脚本|图片|视频|音频/.test(e.innerText || ''); })
        .sort((a, b) => a.getBoundingClientRect().width - b.getBoundingClientRect().width)[0];
      return p ? (p.innerText || '').replace(/\s+/g, ' ').trim() : null; });
    // 悬停/点击「素材库」出子菜单
    const lib = await page.evaluate(() => {
      const el = [...document.querySelectorAll('div,button,li')]
        .filter((e) => (e.innerText || '').trim() === '素材库')
        .sort((a, b) => { const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
          return (ra.width * ra.height) - (rb.width * rb.height); })[0];
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
    });
    as2c.libItem = lib;
    if (lib) {
      await page.mouse.move(lib.cx, lib.cy); await page.waitForTimeout(1600);
      await page.mouse.move(lib.cx + 1, lib.cy); await page.waitForTimeout(1600);
      as2c.submenu = await page.evaluate(() => {
        const m = [...document.querySelectorAll('[class*="Menu-dropdown"],[class*="Popover-dropdown"]')]
          .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 90 && r.height > 40; });
        return m.map((e) => { const r = e.getBoundingClientRect();
          return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
            text: (e.innerText || '').replace(/\s+/g, ' ').trim() }; });
      });
      await shot(page, 'M-127-素材库子菜单.png');
      const tb = await page.evaluate(() => {
        const el = [...document.querySelectorAll('[class*="Menu-dropdown"],[class*="Popover-dropdown"] div,[class*="Menu-dropdown"] button')]
          .filter((e) => /打开工具箱/.test((e.innerText || '')))
          .sort((a, b) => { const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
            return (ra.width * ra.height) - (rb.width * rb.height); })[0];
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          t: (el.innerText || '').replace(/\s+/g, ' ').trim() };
      });
      as2c.toolboxBtn = tb;
      if (tb) {
        await page.mouse.click(tb.cx, tb.cy); await page.waitForTimeout(2800);
        await shot(page, 'M-128-工具箱弹窗.png');
        as2c.dialog = await page.evaluate(() => {
          const d = [...document.querySelectorAll('[class*="Modal-inner"],[role="dialog"]')]
            .map((e) => { const r = e.getBoundingClientRect();
              return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
                text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 600),
                buttons: [...e.querySelectorAll('button')].map((b) => {
                  const q = b.getBoundingClientRect();
                  return { t: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40),
                    aria: b.getAttribute('aria-label'), title: b.getAttribute('title'),
                    disabled: b.disabled === true, opacity: getComputedStyle(b).opacity,
                    rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] }; })
                .filter((b) => b.rect[2] > 0) }; })
            .filter((m) => m.rect[2] > 200 && m.rect[3] > 150);
          return d[0] || null;
        });
      }
    }
  }
  console.log('AS2c:', JSON.stringify(as2c).slice(0, 2200));

  await logStep(B, {
    id: 'AS2-fix-and-probe', title: '缩放持久化重做（带区分力检查）+ LibTV Plugin 指纹差集 + 工具箱真实入口',
    target: '**先验证实验有没有区分力**（起点 ≠ 目标值），再读结论；Plugin 用 DOM 指纹差集判「点完多出来什么」',
    evidence: { as2a, as2b, as2c },
    visible_text: `缩放持久化：${JSON.stringify(as2a)}。`
      + `\n\nLibTV Plugin：${JSON.stringify(as2b).slice(0, 1000)}。`
      + `\n\n工具箱：${JSON.stringify(as2c).slice(0, 1000)}`,
    shot: 'M-125-TV-Director-全局设置.png',
  });
  console.log('AS2 完成');
} finally {
  await browser.close();
}
