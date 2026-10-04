// Batch EF-4：EF-3 看清了 —— 首张卡左上角是**模型徽标 `Seedream 5.0`**，不是「当前使用」。
// （我上一轮把别的卡左上角的字误认成它 —— 截图判读也得核对坐标。）
//
// 源码判据回顾：
//   W = typeof a === 'string' ? a === e.uuid : a?.has(e.uuid) ?? false
//   a = 当前节点正在用的风格 uuid
//   W ? 白底胶囊「✓ 当前使用」 : 空白占位
//
// ⭐ 本步先查**节点到底有没有在用风格**（读节点数据），
//    再决定要不要为了看到徽标而去设一个风格（那是写操作，需谨慎）。
//
// ⛔ 纯只读。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchEF4.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));

const 结果 = {};

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6000 });
  await closePromos(page);
  await page.waitForTimeout(1000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1600);

  // ⭐ 读 canvas store：每个节点的数据里有没有 styleId / styleUuid 之类
  const 节点数据 = await page.evaluate(() => {
    const out = [];
    for (const n of document.querySelectorAll('.react-flow__node')) {
      const id = n.getAttribute('data-id');
      // React Flow 把 __rf 挂在 DOM 上
      const rf = n[Object.keys(n).find(k => k.startsWith('__reactFiber'))];
      out.push({ id, cls: n.className.toString().split(' ').filter(c => c.startsWith('react-flow__node-')).join(',') });
    }
    return out;
  });
  console.log('节点:', JSON.stringify(节点数据, null, 1));
  结果.节点 = 节点数据;
  落盘(结果);

  // ⭐ 换一条路：抓接口响应（节点数据是后端下发的）
  const 响应 = [];
  page.on('response', async (r) => {
    const u = r.url();
    if (!/project|canvas|node|detail/i.test(u)) return;
    if (!r.ok()) return;
    try {
      const j = await r.json();
      const s = JSON.stringify(j);
      if (s.includes('styleId') || s.includes('styleUuid') || s.includes('styleCode')) {
        响应.push({ url: u.slice(0, 140), 长度: s.length });
      }
    } catch {}
  });

  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(6500);
  await closePromos(page);
  await page.waitForTimeout(1500);

  console.log('\n⭐ 含 styleId/styleUuid/styleCode 的接口响应:');
  for (const r of 响应) console.log('  ', r.url, '长度', r.长度);
  结果.响应 = 响应;
  落盘(结果);

  // ⭐ 更直接：读大编辑器里「风格」那一格当前显示什么
  const 节点 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map(n => {
    const r = n.getBoundingClientRect();
    return { id: n.getAttribute('data-id'), cls: n.className.toString(), box: [r.left, r.top, r.width, r.height] };
  }));
  for (const t of 节点.filter(x => /node-image|node-video\b/.test(x.cls)).slice(0, 3)) {
    await page.mouse.click(t.box[0] + t.box[2] / 2, t.box[1] + t.box[3] / 2);
    await page.waitForTimeout(1200);
    const 大编辑器 = await page.evaluate(() => {
      // 大编辑器通常是右侧/中央的大容器
      const cands = [...document.querySelectorAll('div')].filter(e => {
        const r = e.getBoundingClientRect();
        return r.width > 500 && r.height > 400 && /风格|参考|模型|Seed Audio|生成/.test(e.innerText || '');
      }).slice(-2);
      return cands.map(c => ({ cls: c.className.toString().slice(0, 60), 文本: (c.innerText || '').slice(0, 300) }));
    });
    console.log(`\n──── ${t.id} 的大编辑器 ────`);
    for (const c of 大编辑器) console.log('  ', JSON.stringify(c.文本));
    结果['大编辑器_' + t.id] = 大编辑器;
    await page.screenshot({ path: `.evidence/batchEF4-${t.id}-大编辑器.png` });
    落盘(结果);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(800);
  }
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEF4.json ===');
}
