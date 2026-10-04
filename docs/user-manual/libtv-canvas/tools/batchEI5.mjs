// Batch EI-5：查清「打组」下拉菜单**到底是什么组件**（EI-4 用 .mantine-* 选择器读到 0 个，
// 但截图里菜单明明开了 ⇒ 是判据缺陷，不是功能缺失），并拿到一张没有右抽屉、没有通知条的干净图。
//
// ⭐ 本轮仍然只读：点开菜单 → dump 真实 DOM → Escape。不点任何菜单项。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEI5.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6500 });
  await closePromos(page);
  await page.waitForTimeout(1200);

  // ---- ① 先看清楚右抽屉到底是什么、关闭键在哪（EI-4 找错了标签：面板里没有「TV Director」字样的按钮）
  const 抽屉 = await page.evaluate(() => {
    const out = { 找到面板: false, 头部按钮: [], 全部小按钮: [] };
    // 面板根：含「让 TV Director 辅助」这段文案的最内层容器
    let 面板 = null;
    for (const el of document.querySelectorAll('div')) {
      if (/让\s*TV Director\s*辅助/.test(el.innerText || '') && el.getBoundingClientRect().width > 200) {
        if (!面板 || el.getBoundingClientRect().width < 面板.getBoundingClientRect().width) 面板 = el;
      }
    }
    if (!面板) return out;
    out.找到面板 = true;
    const r = 面板.getBoundingClientRect();
    out.面板box = [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)];
    for (const b of 面板.querySelectorAll('button')) {
      const rb = b.getBoundingClientRect();
      if (rb.width === 0) continue;
      out.头部按钮.push({
        文字: (b.innerText || '').trim().slice(0, 12),
        aria: b.getAttribute('aria-label') || '',
        box: [Math.round(rb.left), Math.round(rb.top), Math.round(rb.width), Math.round(rb.height)],
      });
    }
    return out;
  });
  结果.读数.抽屉 = 抽屉;
  记(`右抽屉：面板 box=${JSON.stringify(抽屉.面板box)}，内含按钮 ${抽屉.头部按钮.length} 个`);

  // 关闭键 = 面板**最上方一行**里最靠右的小方钮（截图上是「−」）
  const 关掉 = await page.evaluate(() => {
    let 面板 = null;
    for (const el of document.querySelectorAll('div')) {
      if (/让\s*TV Director\s*辅助/.test(el.innerText || '') && el.getBoundingClientRect().width > 200) {
        if (!面板 || el.getBoundingClientRect().width < 面板.getBoundingClientRect().width) 面板 = el;
      }
    }
    if (!面板) return '没找到面板';
    const 顶线 = 面板.getBoundingClientRect().top + 30;
    const 候选 = [...面板.querySelectorAll('button')].filter(b => {
      const r = b.getBoundingClientRect();
      return r.width > 0 && r.top < 顶线;                      // 面板顶部 30px 内
    });
    if (!候选.length) return '顶部没有按钮';
    const 右 = 候选.reduce((a, b) => (b.getBoundingClientRect().left > a.getBoundingClientRect().left ? b : a));
    右.click();
    return '已点最右上：' + (右.getAttribute('aria-label') || 右.innerText.trim() || '无名') + ' box=' + JSON.stringify((() => { const r = 右.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; })());
  });
  await page.waitForTimeout(1200);
  记(`关右抽屉：${关掉}`);

  // ---- ② 关掉「开启浏览器通知」蓝条
  const 关通知 = await page.evaluate(() => {
    const 蓝条 = [...document.querySelectorAll('div')].find(d => /开启浏览器通知/.test(d.innerText || '') && d.getBoundingClientRect().width < 700);
    if (!蓝条) return '没找到通知条';
    const x = [...蓝条.querySelectorAll('button, svg')].pop();
    if (!x) return '通知条里没有可点的 ×';
    (x.closest('button') || x).click();
    return '已点 ×';
  });
  await page.waitForTimeout(700);
  记(`关通知条：${关通知}`);

  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1600);

  // ---- ③ 框选
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
  await page.waitForTimeout(1800);

  const 选中 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
  结果.读数.选中 = 选中;
  记(`框选后：${JSON.stringify(选中)}`);

  // ---- ④ 工具条完整读数（含最左那枚无名按钮）
  const 工具条 = await page.evaluate(() => {
    const 在条上 = (el) => {
      const r = el.getBoundingClientRect();
      return r.top > 70 && r.top < 130 && r.left > 250 && r.left < 1000;
    };
    return [...document.querySelectorAll('button')].filter(b => !b.closest('.react-flow__node') && 在条上(b)).map(b => {
      const r = b.getBoundingClientRect();
      const cs = getComputedStyle(b);
      return {
        文字: (b.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 10),
        aria: b.getAttribute('aria-label') || '',
        title: b.getAttribute('title') || '',
        disabled: b.disabled,
        box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        子元素数: b.children.length,
        svg数: b.querySelectorAll('svg').length,
        背景: cs.backgroundColor,
      };
    });
  });
  结果.读数.工具条按钮 = 工具条;
  记(`工具条按钮：${JSON.stringify(工具条.map(t => [t.文字 || t.aria || '(无名)', ...t.box, '子' + t.子元素数]))}`);

  await page.screenshot({ path: EVID + 'ei5-多选工具条-干净.png' });
  记('✅ 已拍干净版工具条');

  // ---- ⑤ 点开「打组」下拉，dump 真实 DOM ⭐（EI-4 判据缺陷在这里查清）
  const 打组 = 工具条.find(t => t.文字.startsWith('打组'));
  if (!打组) { 记('❌ 工具条上找不到「打组」'); }
  else {
    await page.mouse.click(Math.round(打组.box[0] + 打组.box[2] / 2), Math.round(打组.box[1] + 打组.box[3] / 2));
    await page.waitForTimeout(1300);

    // ⭐ 阳性对照：先证明「页面里此刻确实多了一个浮层」，再去找它是谁
    const 浮层 = await page.evaluate(() => {
      // 任意 role=menu / [data-portal] / portal 容器，只要可见且不是工具条本身
      const 选 = [...document.querySelectorAll('[role="menu"],[role="listbox"],[data-portal],body > div:nth-last-child(1) > *')];
      return 选.map(e => {
        const r = e.getBoundingClientRect();
        const cs = getComputedStyle(e);
        return {
          role: e.getAttribute('role') || '', cls: (e.className || '').toString().slice(0, 90),
          文本: (e.innerText || '').replace(/\n/g, ' / ').slice(0, 90),
          box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
          可见: r.width > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && +cs.opacity > 0.05,
        };
      }).filter(x => x.可见 && x.box[0] > 500 && x.box[0] < 900 && x.box[1] > 100 && x.box[1] < 400);
    });
    结果.读数.浮层候选 = 浮层;
    记(`⭐ 打组附近可见浮层 ${浮层.length} 个：${JSON.stringify(浮层.map(f => f.role + '|' + f.cls.slice(0, 40)))}`);

    // 更宽松：全页扫「含『合并分镜组』的元素」，枚举所有含该关键词的元素、按尺寸升序取最小 ⇒ ⭐§283 法
    const 命中 = await page.evaluate(() => {
      const all = [...document.querySelectorAll('body *')].filter(e => /合并分镜组/.test(e.innerText || ''));
      return all.map(e => {
        const r = e.getBoundingClientRect();
        return {
          tag: e.tagName, cls: (e.className || '').toString().slice(0, 100),
          role: e.getAttribute('role') || '',
          文本: (e.innerText || '').trim().slice(0, 30),
          面积: Math.round(r.width * r.height),
          box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        };
      }).sort((p, q) => p.面积 - q.面积);
    });
    结果.读数.含合并分镜组的元素 = 命中;
    记(`含「合并分镜组」元素 ${命中.length} 个（按面积升序，最小的 3 个）：${JSON.stringify(命中.slice(0, 3))}`);

    // 从最小的那个往上爬两层，拿到浮层容器
    if (命中.length) {
      const 容器 = await page.evaluate(() => {
        const all = [...document.querySelectorAll('body *')].filter(e => /合并分镜组/.test(e.innerText || '') && e.getBoundingClientRect().width > 0);
        all.sort((p, q) => p.getBoundingClientRect().width * p.getBoundingClientRect().height - q.getBoundingClientRect().width * q.getBoundingClientRect().height);
        const 叶 = all[0];
        const 链 = [];
        let cur = 叶;
        for (let i = 0; i < 4 && cur; i++) {
          const r = cur.getBoundingClientRect();
          链.push({ 层: i, tag: cur.tagName, cls: (cur.className || '').toString().slice(0, 110), role: cur.getAttribute('role') || '', box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
          cur = cur.parentElement;
        }
        // 读这一层里所有可点的项
        let 宿主 = all[0];
        for (let i = 0; i < 3 && 宿主; i++) { if (宿主.querySelectorAll('[role="menuitem"],button,li').length >= 2) break; 宿主 = 宿主.parentElement; }
        const 项 = 宿主 ? [...宿主.querySelectorAll('[role="menuitem"],button,li')].map(e => {
          const r = e.getBoundingClientRect();
          return { 文本: (e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 20), role: e.getAttribute('role') || e.tagName, disabled: e.disabled === true || e.getAttribute('aria-disabled') === 'true', box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
        }).filter(x => x.box[2] > 0) : [];
        return { 祖先链: 链, 项 };
      });
      结果.读数.菜单结构 = 容器;
      记(`⭐ 菜单项：${JSON.stringify(容器.项.map(x => [x.文本, x.disabled ? '灰' : '亮', ...x.box]))}`);
      记(`祖先链：${JSON.stringify(容器.祖先链.map(c => c.tag + '.' + c.cls.slice(0, 46) + (c.role ? ' role=' + c.role : '')))}`);
    }

    await page.screenshot({ path: EVID + 'ei5-打组下拉.png' });
    记('已拍打组下拉');
    await page.keyboard.press('Escape');
    await page.waitForTimeout(800);
  }

  // ---- ⑥ 悬停**工具条上**那枚无名 32×32（限定 top∈[80,130]，EI-4 的过滤把顶栏也捞进来了）
  const 无名 = 工具条.filter(t => !t.文字 && t.box[2] === 32);
  结果.读数.工具条无名按钮 = 无名;
  记(`工具条上无名按钮：${JSON.stringify(无名.map(t => t.box))}`);
  for (const n of 无名) {
    const cx = Math.round(n.box[0] + 16), cy = Math.round(n.box[1] + 16);
    await page.mouse.move(cx - 40, cy + 60);
    await page.waitForTimeout(300);
    await page.mouse.move(cx, cy);
    await page.waitForTimeout(1500);
    const 气泡 = await page.evaluate(([bx, by]) => {
      // 只找出现在按钮附近的小浮层
      const all = [...document.querySelectorAll('[role="tooltip"],body > div > div,body > div:last-child > *')];
      const 命中 = all.map(e => {
        const r = e.getBoundingClientRect();
        return { 文本: (e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 40), cls: (e.className || '').toString().slice(0, 60), role: e.getAttribute('role') || '', box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
      }).filter(x => x.box[2] > 0 && x.box[2] < 300 && x.box[3] < 120 && Math.abs(x.box[0] - bx) < 260 && x.box[1] > by - 20 && x.box[1] < by + 160);
      return 命中;
    }, [cx, cy]);
    记(`悬停 [${n.box}] 后的小浮层：${JSON.stringify(气泡)}`);
    结果.读数['悬停_' + n.box[0]] = 气泡;
    await page.screenshot({ path: EVID + `ei5-悬停${n.box[0]}.png` });
  }
  落盘(结果);
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEI5.json ===');
}
