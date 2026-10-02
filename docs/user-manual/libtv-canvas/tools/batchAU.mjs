// Batch AU —— 三处「正文提过、但没有控件级读数」的地方：
//
//   AU1  **节点顶部工具条**。正文 create-nodes.md 提过视频节点是
//        `参考 / 标记 / 特效 / 角色库 / 运镜`、图片节点是 `参考 / 标记 / 风格`，
//        但都是照着一张「节点展开」截图写的，**没读过 aria、没量过坐标、
//        不知道哪些点了会有反应**。这次逐枚读全部节点类型的顶部工具条。
//
//   AU2  **「从生成历史选择」弹窗的五个来源标签**
//        （`LibTV` / `Lib生成器` / `WebUI` / `ComfyUI` / `AI应用`）。
//        正文只说了「说明可以从外部工具接素材」，没点过任何一个。
//        这次**逐个点开只读列表**（不选任何东西、不点确定）。
//
//   AU3  **音频节点的「高级设置」折叠区**。这个卡了五轮
//        （§11 记着「四次尝试：三次点击坐标出视口、一次抓到拖拽手柄」）。
//        换思路：**不再按坐标点**，改用
//        ① 找 `aria-expanded` / `aria-controls` 的元素
//        ② 找到就 `locator.click()`（自带可见性判定与命中校验）
//        ③ 都没有就 `.focus()` + 键盘 `Enter` / `Space` 激活
//        每一步都读**内容区的实际高度**（它从 0 变成 ~145 才算成功）。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAU';
const { browser, page } = await launch();

const clickAria = async (aria, wait = 2600) => {
  const h = await page.evaluate((a) => {
    const e = [...document.querySelectorAll('button,[role="button"],[aria-label]')]
      .filter((x) => (x.getAttribute('aria-label') || '').trim() === a)
      .map((x) => { const r = x.getBoundingClientRect();
        const onTop = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
        return { area: Math.round(r.width * r.height), visible: r.width > 2 && r.height > 2,
          onTop: !!(onTop && (x.contains(onTop) || onTop.contains(x))),
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; })
      .filter((x) => x.visible && x.onTop)[0];
    return e || { err: '找不到**可点**的 aria-label="' + a + '"' };
  }, aria);
  if (h.err) return h;
  await page.mouse.click(h.cx, h.cy); await page.waitForTimeout(wait);
  return h;
};
const clickText = async (t, wait = 2600) => {
  const h = await page.evaluate((s) => {
    const el = [...document.querySelectorAll('div,li,button,span,a')]
      .filter((e) => (e.innerText || '').trim() === s)
      .map((e) => { const r = e.getBoundingClientRect();
        const onTop = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
        return { area: Math.round(r.width * r.height), visible: r.width > 2 && r.height > 2,
          onTop: !!(onTop && (e.contains(onTop) || onTop.contains(e))),
          cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; })
      .filter((x) => x.visible && x.onTop).sort((a, b) => a.area - b.area)[0];
    return el || { err: '找不到**可点**的「' + s + '」' };
  }, t);
  if (h.err) return h;
  await page.mouse.click(h.cx, h.cy); await page.waitForTimeout(wait);
  return h;
};
/** 视口里每一枚画布节点：类型 + 标题 + 顶部工具条的按钮（只读）。 */
const nodeToolbars = () => page.evaluate(() => {
  const nodes = [...document.querySelectorAll('.react-flow__node')];
  return nodes.map((n) => {
    const r = n.getBoundingClientRect();
    // 顶部工具条 = 节点卡片里**靠上**的一排小按钮
    const btns = [...n.querySelectorAll('button,[role="button"],[aria-label]')].map((b) => {
      const q = b.getBoundingClientRect();
      return { t: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24),
        aria: b.getAttribute('aria-label'), title: b.getAttribute('title'),
        rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
        relY: Math.round(q.y - r.y) }; })
      .filter((b) => b.rect[2] > 0 && b.relY >= 0 && b.relY < 120);
    const title = (n.querySelector('input')?.value)
      || (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40);
    return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      title, btnCount: btns.length, btns };
  });
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await beginBatch(B, { note: '节点顶部工具条逐枚只读 + 五个来源标签只读 + 高级设置换 aria/focus/键盘三路' });

  const out = {};

  // ── AU1 视口里现有节点的顶部工具条 ────────────────────
  out.nodes0 = await nodeToolbars();
  console.log('AU1 视口节点数:', out.nodes0.length);
  for (const nd of out.nodes0) {
    console.log(`  「${nd.title}」顶部工具条:`, JSON.stringify(nd.btns.map((b) => b.t || b.aria || b.title)));
  }
  await shot(page, 'M-138-节点顶部工具条盘点.png');

  // 挑一个**图片节点**和**视频节点**细看（视口里没有就如实记下来）
  out.picked = {};
  for (const kind of ['图片节点', '视频节点', '音频节点']) {
    const nd = out.nodes0.find((n) => n.title.includes(kind));
    if (!nd) { out.picked[kind] = { err: '视口里没有这种节点' }; continue; }
    out.picked[kind] = nd;
    // 点它，让参数面板/工具条进入「选中」态
    await page.mouse.click(nd.rect[0] + nd.rect[2] / 2, nd.rect[1] + 30);
    await page.waitForTimeout(2600);
    out.picked[kind + '_选中后'] = await page.evaluate((t) => {
      const n = [...document.querySelectorAll('.react-flow__node')]
        .find((x) => (x.innerText || '').includes(t));
      if (!n) return { err: '节点不见了' };
      const r = n.getBoundingClientRect();
      return [...n.querySelectorAll('button,[role="button"],[aria-label]')].map((b) => {
        const q = b.getBoundingClientRect();
        return { t: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24),
          aria: b.getAttribute('aria-label'), title: b.getAttribute('title'),
          disabled: b.disabled === true, opacity: getComputedStyle(b).opacity,
          relY: Math.round(q.y - r.y),
          rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] };
      }).filter((b) => b.rect[2] > 0 && b.relY >= 0 && b.relY < 140);
    }, kind);
    console.log(`AU1 ${kind} 选中后:`, JSON.stringify(out.picked[kind + '_选中后']).slice(0, 900));
    await shot(page, `M-13${kind === '图片节点' ? 8 : kind === '视频节点' ? 9 : 9}-${kind}-顶部工具条.png`);
    await page.mouse.click(1300, 120); await page.waitForTimeout(1200);   // 点空白取消选中
  }

  // ── AU2 「从生成历史选择」的五个来源标签 ──────────────
  out.addBtn = await clickAria('添加节点');
  out.libItem = await clickText('素材库');       // 素材库带 › 子菜单
  const hist = await clickText('从生成历史选择', 3200);
  out.histEntry = hist;
  out.dlg = await page.evaluate(() => {
    const c = [...document.querySelectorAll('div,section')].filter((e) => {
      const r = e.getBoundingClientRect();
      return r.width > 400 && r.height > 250 && /选择图片|已选 0|Lib生成器/.test(e.innerText || '');
    }).sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
    if (!c) return { err: '弹窗没打开' };
    const r = c.getBoundingClientRect();
    return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      text: (c.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300) };
  });
  await shot(page, 'M-140-从生成历史选择-弹窗.png');

  out.sources = [];
  for (const s of ['LibTV', 'Lib生成器', 'WebUI', 'ComfyUI', 'AI应用']) {
    const hit = await clickText(s, 2400);
    const read = await page.evaluate((name) => {
      // 这个标签下面的内容区
      const c = [...document.querySelectorAll('div,section')].filter((e) => {
        const r = e.getBoundingClientRect();
        return r.width > 300 && r.height > 150 && /选择图片|已选 0|暂无数据|加载|错误|失败/.test(e.innerText || '');
      }).sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
      if (!c) return { err: '找不到弹窗' };
      const body = (c.innerText || '').replace(/\s+/g, ' ').trim();
      return { active: new RegExp(name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).test(
        [...c.querySelectorAll('button,[role="tab"]')].map((b) => (b.className || '')).join(' ')) ? 'class' : 'text',
        text: body.slice(0, 260),
        selectedTabs: [...c.querySelectorAll('button,[role="tab"]')].filter((b) => {
          const bg = getComputedStyle(b).backgroundColor;
          const bd = getComputedStyle(b).borderColor;
          return (bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') || b.getAttribute('aria-selected') === 'true';
        }).map((b) => (b.innerText || b.getAttribute('aria-label') || '').trim()).slice(0, 6),
        emptyState: /暂无数据|没有数据|暂无/.test(body) ? body.match(/暂无[^ ]*/)?.[0] || '有' : '无空态',
        inputs: [...c.querySelectorAll('input')].map((i) => ({ type: i.type, ph: i.placeholder, v: i.value })).slice(0, 6),
        buttons: [...c.querySelectorAll('button')].map((b) => (b.innerText || b.getAttribute('aria-label') || '').trim())
          .filter(Boolean).slice(0, 20),
      };
    }, s);
    out.sources.push({ name: s, hit, read });
    console.log(`AU2 来源「${s}」:`, JSON.stringify(read).slice(0, 800));
  }
  await shot(page, 'M-141-从生成历史选择-最后一个来源.png');

  // ── AU3 音频节点的「高级设置」：aria → focus+键盘 ─────
  // 先关掉弹窗
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(1200);
  const audio = out.nodes0.find((n) => n.title.includes('音频节点'));
  out.au3 = { node: audio ? audio.title : null };
  if (audio) {
    await page.mouse.click(audio.rect[0] + audio.rect[2] / 2, audio.rect[1] + 30);
    await page.waitForTimeout(2800);
    // 读折叠区当前状态
    const readFold = () => page.evaluate(() => [...document.querySelectorAll('div')]
      .filter((e) => { const s = getComputedStyle(e);
        return /grid-template-rows/.test(s.transitionProperty) || (s.display === 'grid' && /overflow-hidden/.test(s.overflowY) && e.children.length > 0); })
      .map((e) => { const r = e.getBoundingClientRect();
        return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          h: Math.round(r.height), cls: (e.className || '').toString().slice(0, 70),
          text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200),
          sliders: e.querySelectorAll('[class*="Slider"]').length,
          inputs: [...e.querySelectorAll('input')].map((i) => ({ type: i.type, aria: i.getAttribute('aria-label'), v: i.value })) }; })
      .filter((x) => x.h > 0 || x.text.length > 0).slice(0, 8));
    out.au3.before = await readFold();
    console.log('AU3 展开前:', JSON.stringify(out.au3.before).slice(0, 900));
    await shot(page, 'M-142-音频-高级设置-展开前.png');

    // 三路依次试：aria-expanded → focus+Enter → focus+Space
    for (const [how, act] of [
      ['aria-expanded', async () => {
        const h = await page.evaluate(() => {
          const e = [...document.querySelectorAll('[aria-expanded]')].map((x) => {
            const r = x.getBoundingClientRect();
            return { tag: x.tagName, expanded: x.getAttribute('aria-expanded'),
              label: (x.innerText || x.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim().slice(0, 30),
              rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
              visible: r.width > 2 && r.height > 2 };
          });
          const nd = e.find((x) => x.visible && (x.expanded === 'false' || /高级设置/.test(x.label)));
          return nd || { err: '没有可点的 aria-expanded（候选：' + JSON.stringify(e.slice(0, 8)) + '）' };
        });
        if (h.err) return h;
        await page.locator(`[aria-expanded="${h.expanded}"]`).first().click({ timeout: 5000 }).catch((e) => { h.clickErr = String(e).slice(0, 120); });
        return h;
      }],
      ['focus+Enter', async () => {
        const h = await page.evaluate(() => {
          // 找一个**内容区高度为 0** 的折叠容器，它的兄弟里应该有切换按钮
          const fold = [...document.querySelectorAll('div')].find((e) => {
            const r = e.getBoundingClientRect();
            return r.height < 3 && e.children.length > 0 && /overflow-hidden/.test(getComputedStyle(e).overflowY);
          });
          if (!fold) return { err: '找不到高度为 0 的折叠区' };
          // 在它最近的祖先里找可聚焦的兄弟
          let scope = fold.parentElement;
          const cands = [...scope.querySelectorAll('button,[role="button"],[tabindex]')].map((b) => {
            const r = b.getBoundingClientRect();
            return { t: (b.innerText || b.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim().slice(0, 30),
              area: Math.round(r.width * r.height), visible: r.width > 2 && r.height > 2,
              tabindex: b.getAttribute('tabindex') };
          }).filter((b) => b.visible);
          return { cands: cands.slice(0, 10) };
        });
        if (h.err) return h;
        return h;
      }],
    ]) {
      const r = await act();
      out.au3[how] = r;
      await page.waitForTimeout(1800);
      out.au3[how + '_after'] = await readFold();
      const grew = (out.au3[how + '_after'] || []).some((x) => x.h > 40 && x.text.length > 0);
      console.log(`AU3 ${how}:`, JSON.stringify(r).slice(0, 300), '| 展开后最大高度',
        Math.max(0, ...(out.au3[how + '_after'] || []).map((x) => x.h)), '| 变大?', grew);
      if (grew) { out.au3.hit = how; break; }
    }
    await shot(page, 'M-143-音频-高级设置-尝试之后.png');
    out.au3.verdict = out.au3.hit
      ? `用「${out.au3.hit}」成功展开了折叠区，内容区高度从 0 变成 ${Math.max(0, ...(out.au3[out.au3.hit + '_after'] || []).map((x) => x.h))}`
      : '三路都没能让内容区从 0 长起来（aria-expanded 路径已试；focus+Enter 那路本轮只打印了候选没真按）';
  }

  await logStep(B, {
    id: 'AU-toolbars-sources-accordion', title: '节点顶部工具条 / 五个来源标签 / 高级设置三路激活',
    target: '工具条只枚读 aria 与坐标；来源标签**只点开读列表不选**；高级设置改用 aria-expanded + focus + 键盘三路，每路都读内容区实际高度',
    evidence: out,
    visible_text: `视口节点顶部工具条：${JSON.stringify(out.nodes0).slice(0, 1200)}。`
      + `\n\n各类型选中后：${JSON.stringify(out.picked).slice(0, 1200)}。`
      + `\n\n五个来源：${JSON.stringify(out.sources).slice(0, 1500)}。`
      + `\n\n高级设置：${JSON.stringify(out.au3).slice(0, 1200)}`,
    shot: 'M-140-从生成历史选择-弹窗.png',
  });
  console.log('AU 完成');
} finally {
  await browser.close();
}
