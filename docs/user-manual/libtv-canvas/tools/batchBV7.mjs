// Batch BV7 — ⛔ 先别点剪刀：得先知道线怎么接回去。
//
// ⚠️ BV6 的「点剪刀不能断线 ❌」是**假阴性**：三个节点对的 handle 全是 `null / null`，
//    造边没成功，于是 ③ 段**一次都没执行**，剪刀一下都没点。
//    ⭐ 这正是我记过的第 8 条判据缺陷的镜像：**空集让「全部通过」恒真，这里空集让「失败」恒真。**
//    分母是 0 的时候，输出里就不该出现「不能」——该出现的是「没测到」。
//
// ⭐ 本轮只做诊断，不做任何写入：
// ① handle 到底存不存在、长什么样（class / 尺寸 / 属性 / 是不是 hover 才出现）；
// ② 剪刀自己身上有没有事件处理器（`__reactProps$` 里的 onClick 之类）——
//    有的话说明「点它」在原理上可行；顺便看它有没有 aria/title（无障碍标签）。
// ③ 再顺手核一遍：**已有连线的中点在未悬停时是不是空的**，把「悬停才出现」这件事钉死。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBV7';
const { browser, page } = await launch();
const settle = (ms = 900) => page.waitForTimeout(ms);

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await settle(1800);
  await fitView(page); await settle(2500);
  await beginBatch(B, { note: '纯诊断：handle 是什么 + 剪刀身上有没有事件处理器' });
  const out = {};

  // ── ① handle 诊断
  console.log('═══ ① handle 诊断 ═══');
  const handles = await page.evaluate(() => {
    const res = {};
    res.byClass = {
      reactFlowHandle: document.querySelectorAll('.react-flow__handle').length,
      anyHandleWord: document.querySelectorAll('[class*="handle" i]').length,
      anySource: document.querySelectorAll('[class*="source" i]').length,
      anyTarget: document.querySelectorAll('[class*="target" i]').length,
      anyAnchor: document.querySelectorAll('[class*="anchor" i], [class*="Anchor"]').length,
      anyConnect: document.querySelectorAll('[class*="connect" i]').length,
      circle: document.querySelectorAll('.react-flow__node circle').length,
    };
    // 随便挑一个节点，把它里面所有「看起来像锚点」的小元素全列出来
    const n = document.querySelector('.react-flow__node[data-id="v-eMpqKtiLlx"]')
      || document.querySelector('.react-flow__node');
    res.probedNode = n ? n.getAttribute('data-id') : null;
    res.candidates = [];
    if (n) {
      const all = n.querySelectorAll('*');
      for (const e of all) {
        const r = e.getBoundingClientRect();
        if (r.width === 0 || r.height === 0) continue;
        if (r.width > 60 || r.height > 60) continue;   // 只看小圆点级别的东西
        const s = getComputedStyle(e);
        res.candidates.push({
          tag: e.tagName, cls: (e.getAttribute('class') || '').toString().slice(0, 70),
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          radius: s.borderRadius, bg: s.backgroundColor, cursor: s.cursor,
          opacity: s.opacity, pointerEvents: s.pointerEvents,
          attrs: [...e.attributes].map((a) => a.name).slice(0, 10),
        });
      }
    }
    return res;
  });
  out.handles = handles;
  console.log(`  全页统计：${JSON.stringify(handles.byClass)}`);
  console.log(`  探针节点：${handles.probedNode}｜里面小元素 ${handles.candidates.length} 个`);
  handles.candidates.slice(0, 12).forEach((c) => console.log(`     ${c.tag}.${c.cls || '(无)'} ${JSON.stringify(c.rect)} 圆角=${c.radius} bg=${c.bg} cursor=${c.cursor} op=${c.opacity} attrs=${JSON.stringify(c.attrs)}`));

  // ── ①b hover 之后再列一次（锚点常常要 hover 才挂载）
  const nb = await page.evaluate(() => { const n = document.querySelector('.react-flow__node[data-id="v-eMpqKtiLlx"]');
    if (!n) return null; const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (nb) {
    await page.mouse.move(nb[0], nb[1]); await settle(1600);
    const hovered = await page.evaluate(() => ({
      handles: document.querySelectorAll('.react-flow__handle').length,
      detail: [...document.querySelectorAll('.react-flow__node[data-id="v-eMpqKtiLlx"] .react-flow__handle')].map((h) => {
        const r = h.getBoundingClientRect();
        return { cls: (h.getAttribute('class') || ''), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          id: h.getAttribute('data-handleid'), type: h.getAttribute('data-handletype') };
      }),
    }));
    out.handlesHovered = hovered;
    console.log(`  ⭐ hover 该节点后：.react-flow__handle = ${hovered.handles} 个`);
    hovered.detail.slice(0, 6).forEach((d) => console.log(`     ${d.cls} ${JSON.stringify(d.rect)} id=${d.id} type=${d.type}`));
    await page.mouse.move(200, 780); await settle(600);
  }

  // ── ② 剪刀身上有没有事件处理器
  console.log('\n═══ ② 剪刀的事件处理器 ═══');
  const mids = await page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')].map((g) => {
    const p = g.querySelector('path'); let L = 0; try { L = p.getTotalLength(); } catch { L = 0; }
    const ctm = p && p.getScreenCTM(); let mid = null;
    if (ctm && L) { const q = p.getPointAtLength(L / 2); const s = new DOMPoint(q.x, q.y, 0, 1).matrixTransform(ctm); mid = [Math.round(s.x), Math.round(s.y)]; }
    return { id: g.getAttribute('data-id'), mid };
  }));
  out.mids = mids;
  const sc0 = await page.evaluate(() => document.querySelectorAll('.scissors-enter').length);
  console.log(`  未悬停时 .scissors-enter = ${sc0} 枚（钉死「悬停才出现」）`);
  const probe = [];
  for (const m of mids) {
    if (!m.mid) continue;
    await page.mouse.move(200, 780); await settle(500);
    await page.mouse.move(m.mid[0], m.mid[1]); await settle(1500);
    const info = await page.evaluate(() => {
      const els = [...document.querySelectorAll('.scissors-enter')].map((e) => {
        const r = e.getBoundingClientRect();
        const keys = Object.keys(e);
        const propKey = keys.find((k) => k.startsWith('__reactProps$'));
        const fiberKey = keys.find((k) => k.startsWith('__reactFiber$'));
        const props = propKey ? e[propKey] : null;
        const fns = props ? Object.keys(props).filter((k) => /^on[A-Z]/.test(k)) : [];
        const fiber = fiberKey ? e[fiberKey] : null;
        return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          html: e.outerHTML.slice(0, 260),
          aria: e.getAttribute('aria-label'), title: e.getAttribute('title'), role: e.getAttribute('role'),
          reactKeys: keys.filter((k) => k.startsWith('__react')),
          handlerProps: fns,
          handlerKinds: fns.map((k) => `${k}=${typeof props[k]}`),
          fiberTag: fiber ? (fiber.elementType ? (fiber.elementType.name || String(fiber.elementType).slice(0, 40)) : null) : null,
          innerCount: e.children.length,
          innerHtml: [...e.children].map((c) => c.tagName + '.' + ((c.getAttribute('class') || '').slice(0, 30))).join(' '),
        };
      });
      return els;
    });
    probe.push({ id: m.id, mid: m.mid, found: info.length, info });
    console.log(`  ${m.id}｜中点 ${JSON.stringify(m.mid)}｜scissors ${info.length} 枚`);
    info.forEach((i) => {
      console.log(`      aria=${i.aria || '-'} title=${i.title || '-'} role=${i.role || '-'} 子元素=${i.innerCount}（${i.innerHtml}）`);
      console.log(`      React 键：${JSON.stringify(i.reactKeys)}｜事件 props：${JSON.stringify(i.handlerKinds)}`);
      console.log(`      HTML：${i.html.replace(/\s+/g, ' ').slice(0, 200)}`);
    });
  }
  out.scissors = { idleCount: sc0, probe };

  // 悬停态拍一张：剪刀是这轮的实锤证据
  if (mids[0] && mids[0].mid) {
    await page.mouse.move(200, 780); await settle(500);
    await page.mouse.move(mids[0].mid[0], mids[0].mid[1]); await settle(1800);
    await shot(page, 'M-279-连线中点悬停出的那枚剪刀.png');
  }

  console.log(`\n═══ 本轮结论 ═══`);
  console.log(`  · 未悬停时剪刀数：${sc0}（>0 就说明「悬停才出现」是假的）`);
  console.log(`  · handle 类元素：${JSON.stringify(handles.byClass)}`);
  console.log(`  · 剪刀有 onClick 之类的处理器吗：${JSON.stringify(probe.map((p) => p.info.map((i) => i.handlerKinds)))}`);

  await logStep(B, {
    id: 'BV7-diagnose-handles-and-scissors-handlers',
    title: '⛔ 假阴性归零：BV6 的「点剪刀不能断线」是没测到；本轮只诊断不写入',
    target: '⚠️ BV6 打出「点剪刀不能断线 ❌」是**假阴性**：三个节点对的 handle 全 `null / null`，'
      + '造边没成功，③ 段**一次都没执行**。⭐ 空集让「全部通过」恒真，空集也让「失败」恒真——'
      + '分母是 0 时输出里不该出现「不能」。'
      + '⛔ **在搞清楚线怎么接回去之前不点剪刀**（回退动作必须先独立复核）。'
      + '本轮纯诊断：handle 到底存不存在、剪刀身上有没有 `onClick`。',
    evidence: out,
    visible_text: JSON.stringify({ handle: out.handles, hover后: out.handlesHovered, 剪刀: out.scissors }).slice(0, 3400),
    shot: 'M-279-连线中点悬停出的那枚剪刀.png',
  });
  console.log('\nBV7 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 5).join('\n'));
} finally {
  await browser.close();
}
