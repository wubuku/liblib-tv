// Batch EI-6：把画面清干净后重拍 M-357（多选工具条）+ 补一张「打组」下拉图，
// 并查清「合并分镜组」在多选态下到底可不可用（EI-5 报的「亮」只看了 disabled 属性，可疑）。
//
// ⭐ 三处遮挡：①「Agent 已升级为 TV Director」升级卡（有「知道了」）②右抽屉（有「−」）③蓝色通知条（有 ×）
// ⭐ 判据纪律：禁用态不能只看 disabled 属性 —— 要看 opacity / 文字颜色 / class
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEI6.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

// 关掉一切浮层：点按钮文字精确匹配，失败就报出来（不做无声兜底）
const 关浮层 = async (page, 文字) => {
  const r = await page.evaluate((t) => {
    const b = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim() === t);
    if (!b) return '没找到「' + t + '」';
    b.click();
    return '已点「' + t + '」';
  }, 文字);
  await page.waitForTimeout(900);
  return r;
};

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6500 });
  await closePromos(page);
  await page.waitForTimeout(1500);

  记('① 升级卡：' + (await 关浮层(page, '知道了')));
  // 升级卡可能不止一层，连点两下（第二层没有就报「没找到」，符合预期）
  记('② 升级卡二次：' + (await 关浮层(page, '知道了')));

  // ③ 蓝通知条：按 class 找带 × 的那一条，精确点它自己的关闭键
  const 关条 = await page.evaluate(() => {
    const 条 = [...document.querySelectorAll('div')].filter(d => /开启浏览器通知/.test(d.innerText || ''));
    if (!条.length) return '没找到通知条';
    条.sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width);
    const 宿主 = 条[条.length - 1];
    const btn = [...宿主.querySelectorAll('button')].find(b => {
      const t = (b.innerText || '').trim();
      return t === '' || t === '×' || t === 'X';
    });
    if (!btn) return '通知条里没有空按钮；按钮文字=' + JSON.stringify([...宿主.querySelectorAll('button')].map(b => (b.innerText || '').trim()));
    const r = btn.getBoundingClientRect();
    btn.click();
    return '已点通知条 × box=' + JSON.stringify([Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]);
  });
  await page.waitForTimeout(900);
  记('③ 通知条：' + 关条);

  // ④ 右抽屉：找含「让 TV Director 辅助」的最外层固定面板，点它顶行最右的小方钮
  const 关抽屉 = await page.evaluate(() => {
    // ⭐ 阳性对照：先数一遍「新对话」标题有几个，避免又找错元素
    const 标题 = [...document.querySelectorAll('div,span,h1,h2,h3')].filter(e => (e.innerText || '').trim() === '新对话');
    let 面板 = null;
    for (const el of document.querySelectorAll('div')) {
      if (!/让\s*TV Director\s*辅助/.test(el.innerText || '')) continue;
      const r = el.getBoundingClientRect();
      if (r.width < 300 || r.width > 600) continue;               // 抽屉本体宽 366，高 600+
      if (!面板 || r.height > 面板.getBoundingClientRect().height) 面板 = el;
    }
    if (!面板) return '新对话标题 ' + 标题.length + ' 个，但没锁定面板';
    const r = 面板.getBoundingClientRect();
    const 顶线 = r.top + 28;
    const 候选 = [...面板.querySelectorAll('button')].filter(b => {
      const rb = b.getBoundingClientRect();
      return rb.width > 0 && rb.width < 40 && rb.top >= r.top && rb.top < 顶线;
    });
    if (!候选.length) {
      return '面板 box=' + JSON.stringify([Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]) + '，顶线 28px 内无小按钮';
    }
    const 右 = 候选.reduce((a, b) => (b.getBoundingClientRect().left > a.getBoundingClientRect().left ? b : a));
    const rr = 右.getBoundingClientRect();
    右.click();
    return `已点最右小钮（aria=${右.getAttribute('aria-label') || '无'}）box=` + JSON.stringify([Math.round(rr.left), Math.round(rr.top), Math.round(rr.width), Math.round(rr.height)]);
  });
  await page.waitForTimeout(1200);
  记('④ 右抽屉：' + 关抽屉);

  const 残留 = await page.evaluate(() => ({
    升级卡: [...document.querySelectorAll('button')].some(b => (b.innerText || '').trim() === '知道了'),
    通知条: /开启浏览器通知/.test(document.body.innerText || ''),
    抽屉: /让\s*TV Director\s*辅助/.test(document.body.innerText || ''),
  }));
  结果.读数.遮挡残留 = 残留;
  记(`残留复查：${JSON.stringify(残留)}`);

  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1800);

  // ⑤ 框选
  const 位置 = await page.evaluate(() => {
    const out = {};
    for (const id of ['i-9nlG6HdjK2', 'i-sODTbgLUm1']) {
      const el = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      const r = el.getBoundingClientRect();
      out[id] = [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)];
    }
    return out;
  });
  const a = 位置['i-9nlG6HdjK2'], b = 位置['i-sODTbgLUm1'];
  const x1 = Math.min(a[0], b[0]) - 20, y1 = Math.min(a[1], b[1]) - 10;
  const x2 = Math.max(a[0] + a[2], b[0] + b[2]) + 20, y2 = Math.max(a[1] + a[3], b[1] + b[3]) + 20;
  await page.mouse.move(x1, y1);
  await page.mouse.down();
  await page.mouse.move((x1 + x2) / 2, (y1 + y2) / 2, { steps: 12 });
  await page.mouse.move(x2, y2, { steps: 12 });
  await page.waitForTimeout(400);
  await page.mouse.up();
  // ⭐ 鼠标停在框选终点，会蹭到工具条左端 ⇒ 先把鼠标挪开再读数（否则 tooltip 污染读数，EI-5 就中过）
  await page.mouse.move(700, 700);
  await page.waitForTimeout(1800);

  const 选中 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
  结果.读数.选中 = 选中;
  记(`框选后：${JSON.stringify(选中)}`);

  const 工具条 = await page.evaluate(() => {
    const 在条上 = (el) => { const r = el.getBoundingClientRect(); return r.top > 70 && r.top < 130 && r.left > 250 && r.left < 1000; };
    return [...document.querySelectorAll('button')].filter(b => !b.closest('.react-flow__node') && 在条上(b)).map(b => {
      const r = b.getBoundingClientRect(); const cs = getComputedStyle(b);
      return { 文字: (b.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 10), aria: b.getAttribute('aria-label') || '', title: b.getAttribute('title') || '', box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 子元素数: b.children.length, html: b.innerHTML.replace(/\s+/g, ' ').slice(0, 150) };
    });
  });
  结果.读数.工具条按钮 = 工具条;
  记(`工具条 ${工具条.length} 个：${JSON.stringify(工具条.map(t => [(t.文字 || t.aria || '(无名)'), ...t.box, '子' + t.子元素数]))}`);

  await page.screenshot({ path: EVID + 'ei6-干净全图.png' });
  记('✅ 已拍干净全图');

  // ⑥ 裁一张只含工具条 + 选中节点的图（做减法：这张才是真正的主体）
  await page.screenshot({ path: EVID + 'ei6-工具条裁图.png', clip: { x: 250, y: 60, width: 700, height: 300 } });
  记('✅ 已拍工具条裁图 clip=[250,60,700,300]');

  // ⑦ 「打组」下拉：这一回把两项的**视觉态**全量读出来
  const 打组 = 工具条.find(t => t.文字.startsWith('打组'));
  if (!打组) 记('❌ 工具条上没有「打组」');
  else {
    await page.mouse.click(Math.round(打组.box[0] + 打组.box[2] / 2), Math.round(打组.box[1] + 打组.box[3] / 2));
    await page.waitForTimeout(1400);

    const 菜单 = await page.evaluate(() => {
      // ⭐ §283 法：按「含关键词」枚举 + 面积升序，取最小 ⇒ 不用事先知道它长什么样
      const all = [...document.querySelectorAll('body *')].filter(e => /合并分镜组/.test(e.innerText || '') && e.getBoundingClientRect().width > 0);
      all.sort((p, q) => p.getBoundingClientRect().width * p.getBoundingClientRect().height - q.getBoundingClientRect().width * q.getBoundingClientRect().height);
      const 叶 = all[0];
      let 宿主 = 叶; for (let i = 0; i < 3; i++) { if (宿主.querySelectorAll('button').length >= 2) break; 宿主 = 宿主.parentElement; }
      const 读一个 = (e) => {
        const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
        const sp = e.querySelector('span');
        return {
          文本: (e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 16),
          box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
          disabled属性: e.disabled === true,
          ariaDisabled: e.getAttribute('aria-disabled'),
          dataDisabled: e.getAttribute('data-disabled'),
          cursor: cs.cursor,
          按钮opacity: cs.opacity,
          文字色: sp ? getComputedStyle(sp).color : cs.color,
          文字opacity: sp ? getComputedStyle(sp).opacity : '',
          class: e.className.toString().slice(0, 120),
          子元素数: e.children.length,
        };
      };
      return { 浮层class: 宿主.className.toString().slice(0, 120), 项: [...宿主.querySelectorAll('button')].map(读一个) };
    });
    结果.读数.打组菜单 = 菜单;
    记(`⭐ 浮层 class：${菜单.浮层class}`);
    for (const it of 菜单.项) 记(`　项「${it.文本}」 disabled=${it.disabled属性} aria-dis=${it.ariaDisabled} data-dis=${it.dataDisabled} cursor=${it.cursor} 按钮opacity=${it.按钮opacity} 文字色=${it.文字色} 文字opacity=${it.文字opacity} 子${it.子元素数}`);

    await page.screenshot({ path: EVID + 'ei6-打组下拉-干净.png' });
    await page.screenshot({ path: EVID + 'ei6-打组下拉裁图.png', clip: { x: 530, y: 60, width: 300, height: 220 } });
    记('✅ 已拍打组下拉（干净 + 裁图）');
    await page.keyboard.press('Escape');
    await page.waitForTimeout(900);
  }

  // ⑧ 工具条上那枚无名按钮：先记录**未悬停**时的 DOM，再悬停再记一次 ⇒ 差分才是证据
  for (const t of 工具条.filter(x => !x.文字)) {
    const cx = Math.round(t.box[0] + t.box[2] / 2), cy = Math.round(t.box[1] + t.box[3] / 2);
    const 快照 = () => page.evaluate(() => [...document.querySelectorAll('body *')]
      .filter(e => e.children.length === 0 && (e.innerText || '').trim().length > 0 && (e.innerText || '').trim().length < 12)
      .map(e => { const r = e.getBoundingClientRect(); return { 文本: e.innerText.trim(), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] }; })
      .filter(x => x.box[2] > 0 && Math.abs(x.box[0] - cx) < 200 && Math.abs(x.box[1] - cy) < 120));
    await page.mouse.move(700, 700);
    await page.waitForTimeout(1200);
    const 前 = await 快照();
    await page.mouse.move(cx, cy);
    await page.waitForTimeout(1600);
    const 后 = await 快照();
    const 新增 = 后.filter(y => !前.some(x => x.文本 === y.文本));
    记(`悬停 [${t.box}] 前附近文本 ${前.length} 条；悬停后新出现 ${JSON.stringify(新增)}`);
    结果.读数['悬停前_' + t.box[0]] = 前;
    结果.读数['悬停后_' + t.box[0]] = 后;
    if (新增.length) await page.screenshot({ path: EVID + `ei6-悬停${t.box[0]}.png`, clip: { x: Math.max(0, cx - 180), y: Math.max(0, cy - 20), width: 400, height: 150 } });
  }
  落盘(结果);
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEI6.json ===');
}
