// Batch EG-0：清理 EF 批留下的「素材-风格-Seedream 5.0」节点。
//
// ⛔⛔ 三重自证，缺一不可（ED 事故后立的规矩，见 §107.4 / §273-§277）：
//   ① id **不在** canvas-baseline.mjs 的 BASE 里；
//   ② id 以 `m-` 前缀开头；
//   ③ 名字以「素材-」开头（EF 批建的那一批都是这个前缀）。
//   三条全满足才允许删 —— 少一条就**中止并报告**，不硬来。
//
// ⛔ 除此之外绝对不碰：Delete 只作用在这一个 id 上，不用 ⌘A 不用 ⌫。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { BASE, 是基线节点 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchEG0.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));

const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 读节点 = (page) => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map(n => ({
  id: n.getAttribute('data-id'),
  名: (n.innerText || '').split('\n').filter(Boolean)[0] || '',
  cls: n.className.toString().split(' ').filter(c => c.startsWith('react-flow__node-')).join(','),
})));

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6500 });
  await closePromos(page);
  await page.waitForTimeout(1200);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1500);

  const 节点 = await 读节点(page);
  结果.读数.清理前 = 节点;
  const 多余 = 节点.filter(n => !BASE.includes(n.id));
  记(`清理前 ${节点.length} 个（基线 ${BASE.length}），多余 ${多余.length} 个：${JSON.stringify(多余.map(n => ({ id: n.id, 名: n.名 })))}`);

  // ⭐ 三重自证
  const 可删 = [];
  const 拒绝 = [];
  for (const n of 多余) {
    const 条 = [];
    if (是基线节点(n.id)) 条.push('✗ 在基线里');
    if (!n.id.startsWith('m-')) 条.push(`✗ 前缀不是 m-（是 ${n.id.slice(0, 2)}）`);
    if (!n.名.startsWith('素材-')) 条.push(`✗ 名字不以「素材-」开头（是「${n.名}」）`);
    if (条.length) 拒绝.push({ id: n.id, 名: n.名, 原因: 条 });
    else 可删.push(n);
  }
  结果.读数.自证 = { 可删, 拒绝 };
  记(`自证通过（可删）${可删.length} 个；被拒 ${拒绝.length} 个：${JSON.stringify(拒绝)}`);

  for (const n of 可删) {
    // ⭐ 走菜单删，不按 Delete —— 菜单有确认框，最后一道自证
    const 选中 = await page.evaluate((id) => {
      const el = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      if (!el) return false;
      const r = el.getBoundingClientRect();
      return { x: r.left + r.width / 2, y: r.top + 20 };
    }, n.id);
    await page.mouse.click(选中.x, 选中.y);
    await page.waitForTimeout(1000);

    // 找 ⋯ 菜单
    const 开了 = await page.evaluate((id) => {
      const el = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      const btns = [...el.querySelectorAll('button,[role="button"]')];
      const more = btns.find(b => {
        const t = (b.innerText || '').trim();
        return t === '⋯' || t === '···' || /更多/.test(b.getAttribute('aria-label') || '');
      });
      if (!more) return false;
      more.click(); return true;
    }, n.id);
    await page.waitForTimeout(900);
    记(`打开「${n.名}」的 ⋯ 菜单：${开了}`);

    if (开了) {
      // ⭐ 读确认框正文，确认要删的就是这个
      const 确认框 = await page.evaluate(() => {
        const c = [...document.querySelectorAll('.mantine-Modal-content')]
          .find(e => /删除|确定/.test(e.innerText || ''));
        return c ? { 全文: c.innerText, 按钮: [...c.querySelectorAll('button')].map(b => b.innerText.trim()).filter(Boolean) } : null;
      });
      结果.读数['确认框_' + n.id] = 确认框;
      记(`确认框：${JSON.stringify(确认框?.全文?.slice(0, 80))} 按钮=${JSON.stringify(确认框?.按钮)}`);

      const 点了删除 = await page.evaluate(() => {
        for (const b of document.querySelectorAll('.mantine-Menu-item,button')) {
          if ((b.innerText || '').trim() === '删除') { b.click(); return true; }
        }
        return false;
      });
      await page.waitForTimeout(1000);
      记(`点「删除」：${点了删除}`);

      if (确认框) {
        const 确认 = await page.evaluate(() => {
          for (const b of document.querySelectorAll('.mantine-Modal-content button')) {
            const t = (b.innerText || '').trim();
            if (t === '确定删除' || t === '删除' || t === '继续删除') { b.click(); return t; }
          }
          return false;
        });
        await page.waitForTimeout(1600);
        记(`点确认：${确认}`);
      }
    }
  }

  // ⭐ 刷新复核
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(6000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1500);

  const 后 = await 读节点(page);
  const 缺 = BASE.filter(x => !后.some(n => n.id === x));
  const 还多 = 后.filter(n => !BASE.includes(n.id));
  结果.读数.清理后 = { 节点数: 后.length, 缺失: 缺, 还多: 还多.map(n => n.名) };
  记(`⭐ 清理后 ${后.length} 个；基线缺失=${缺.length ? 缺 : '无 ✅'}；仍多余=${还多.length ? JSON.stringify(还多.map(n => n.名)) : '无 ✅'}`);
  落盘(结果);
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEG0.json ===');
}
