// Batch EG-0c：素材节点画布上没有 ⋯ 菜单 —— 只有一枚 `aria="更换风格"` 按钮（11×11）。
// ⇒ 删它的入口在**资产管理抽屉**里（organize-canvas.md 记过：资产行有 ⋯ 菜单，含「删除」）。
//
// ⛔ 三重自证同 EG-0；本轮只删那一个 m- 前缀的「素材-」节点。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { BASE, 是基线节点 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchEG0c.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 目标名 = '素材-风格-Seedream 5.0 pro';

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6500 });
  await closePromos(page);
  await page.waitForTimeout(1200);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1500);

  const 前 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map(n => n.getAttribute('data-id')));
  const 多余 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')]
    .map(n => ({ id: n.getAttribute('data-id'), 名: (n.innerText || '').split('\n').filter(Boolean)[0] || '' }))
    .filter(n => n.名.startsWith('素材-风格-Seedream 5.0 pro')));
  结果.读数.目标 = 多余;
  记(`画布 ${前.length} 个；待删目标：${JSON.stringify(多余)}`);

  // ⭐ 三重自证
  for (const n of 多余) {
    const 条件 = { 不在基线: !是基线节点(n.id), m前缀: n.id.startsWith('m-'), 素材命名: n.名.startsWith('素材-') };
    记(`自证 ${n.id}：${JSON.stringify(条件)}`);
    if (!(条件.不在基线 && 条件.m前缀 && 条件.素材命名)) {
      记('⛔ 自证不全 → 中止，不删');
      break;
    }
  }
  if (!多余.length) { 记('没有待删对象'); }

  // ① 开资产管理抽屉
  const 开抽屉 = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim() === '资产管理' || /资产管理/.test(x.getAttribute('aria-label') || ''));
    if (!b) return false; b.click(); return true;
  });
  await page.waitForTimeout(1600);
  记(`开「资产管理」抽屉：${开抽屉}`);

  // ② 找那一行
  const 行 = await page.evaluate((名) => {
    const drawer = document.querySelector('.mantine-Drawer-content');
    if (!drawer) return { 错: '没有抽屉' };
    const 页签 = [...drawer.querySelectorAll('button')].map(b => b.innerText.trim()).filter(Boolean).slice(0, 8);
    for (const el of [...drawer.querySelectorAll('*')]) {
      if (el.children.length > 0) continue;
      if ((el.innerText || '').trim() !== 名) continue;
      const r = el.getBoundingClientRect();
      return { 找到: true, 页签, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
    }
    return { 找到: false, 页签 };
  }, 目标名);
  结果.读数.抽屉 = 行;
  记(`抽屉里找「${目标名}」：${JSON.stringify(行)}`);

  if (行.找到) {
    await page.mouse.move(行.box[0] + 行.box[2] / 2, 行.box[1] + 行.box[3] / 2);
    await page.waitForTimeout(800);
    // ③ ⭐ AUDIT.md:66 记过：「更多操作」是**行的兄弟节点**，不在行内 ⇒ 按坐标扫那一带所有按钮
    const 附近 = await page.evaluate((box) => {
      const [x, y, w, h] = box;
      const out = [];
      for (const b of document.querySelectorAll('button,[role="button"]')) {
        const r = b.getBoundingClientRect();
        if (r.width === 0) continue;
        // 在那一行的水平范围内、垂直重合
        const 同水平 = r.right > x - 20 && r.left < x + w + 20;
        const 同垂直 = Math.abs((r.top + r.height / 2) - (y + h / 2)) < 14;
        if (!同水平 || !同垂直) continue;
        out.push({ aria: b.getAttribute('aria-label') || '', text: (b.innerText || '').trim().slice(0, 12), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
      }
      return out;
    }, 行.box);
    结果.读数.同行按钮 = 附近;
    记(`那一行附近的按钮：${JSON.stringify(附近)}`);

    // ③ ⭐ 那一行有三个按钮，「定位到节点」占前两个 ⇒ 必须按 aria-label 精确点「更多操作」
    const 点了 = await page.evaluate(() => {
      const b = [...document.querySelectorAll('button,[role="button"]')]
        .find(x => (x.getAttribute('aria-label') || '') === '更多操作');
      if (!b) return false;
      b.click();
      return true;
    });
    await page.waitForTimeout(1100);
    记(`点「更多操作」：${点了}`);

    // ④ 读菜单 + 点删除
    const 菜单 = await page.evaluate(() => {
      const d = document.querySelector('.mantine-Menu-dropdown');
      return d ? [...d.querySelectorAll('.mantine-Menu-item')].map(x => x.innerText.trim()) : null;
    });
    结果.读数.菜单 = 菜单;
    记(`菜单项：${JSON.stringify(菜单)}`);

    if (菜单 && 菜单.includes('删除')) {
      const 点了删除 = await page.evaluate(() => {
        for (const x of document.querySelectorAll('.mantine-Menu-item')) {
          if (x.innerText.trim() === '删除') { x.click(); return true; }
        }
        return false;
      });
      await page.waitForTimeout(1000);
      记(`点「删除」：${点了删除}`);

      const 确认框 = await page.evaluate(() => {
        const c = [...document.querySelectorAll('.mantine-Modal-content')].find(e => /删除/.test(e.innerText || ''));
        return c ? { 全文: c.innerText, 按钮: [...c.querySelectorAll('button')].map(b => b.innerText.trim()).filter(Boolean) } : null;
      });
      结果.读数.确认框 = 确认框;
      记(`⭐ 确认框正文：${JSON.stringify(确认框?.全文)}`);

      const 确认 = await page.evaluate(() => {
        for (const b of document.querySelectorAll('.mantine-Modal-content button')) {
          if (/删除/.test(b.innerText) && !/取消/.test(b.innerText)) { b.click(); return b.innerText.trim(); }
        }
        return false;
      });
      await page.waitForTimeout(2000);
      记(`点确认：${确认}`);
    }
  }

  // ⑤ 刷新复核
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(6000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1500);
  const 后 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map(n => ({
    id: n.getAttribute('data-id'), 名: (n.innerText || '').split('\n').filter(Boolean)[0] || '',
  })));
  const 缺 = BASE.filter(x => !后.some(n => n.id === x));
  const 还多 = 后.filter(n => !BASE.includes(n.id));
  结果.读数.清理后 = { 数: 后.length, 缺失: 缺, 还多: 还多.map(n => n.名) };
  记(`⭐ 清理后 ${后.length} 个；基线缺失=${缺.length ? 缺 : '无 ✅'}；仍多余=${还多.length ? JSON.stringify(还多.map(n => n.名)) : '无 ✅'}`);
  落盘(结果);
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEG0c.json ===');
}
