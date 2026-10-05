// ⭐⭐⭐⭐⭐ Batch FV-8：按**结构**而不是按文本找「还原」按钮
//
// FV-7 报「找不到还原按钮」——但截图上那个浮层明明有「还原 / 保留」两个按钮。
// ⛔ 规矩：⛔ 不猜，必须看结构再点。
//
// 同时 FV-7 顺手交了一份大礼：**底栏与左下角 12 枚按钮的 aria 实名**。
//   底栏七枚：添加节点 / 移动 / 素材库 / 角色造型室 / 生成历史 / 快捷键 / 教程
//   左下五枚：整理画布（Option+Shift+F）/ 切换小地图 / 隐藏节点连线 / 网格吸附 / 缩放选项
// ⛔ 其中「移动」= 整理画布，**aria 名字与图标给人的印象完全不符** ——
//   FV-6 就是因为只按尺寸找、没读 aria，才把它当成了「添加节点」。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 断言: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFV8.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = (名, 过, 明) => { R.断言.push({ 名, 过, 明 }); 记(`${过 ? '✅' : '❌'} ${名} —— ${明}`); };

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(14000);
  await closePromos(page);

  // ── ① 先把「底栏按钮的 aria」正式记下来（这本身就是本批的交付物）
  const aria表 = await page.evaluate(() => {
    const out = [];
    for (const b of document.querySelectorAll('[aria-label]')) {
      const r = b.getBoundingClientRect();
      if (r.width < 18 || r.height < 18) continue;
      out.push({ aria: b.getAttribute('aria-label'), tag: b.tagName,
        x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) });
    }
    return out;
  });
  R.读数.全部aria = aria表;
  记(`全页带 aria-label 的可点元素 ${aria表.length} 枚\n`);
  const 底栏 = aria表.filter((a) => a.y >= 770 && a.y <= 800 && a.x < 400);
  const 底中 = aria表.filter((a) => a.y >= 770 && a.y <= 800 && a.x >= 500 && a.x < 1000);
  记('左下角工具行：');
  底栏.forEach((a) => 记(`   \`${a.aria}\` @${a.x},${a.y} ${a.w}×${a.h}`));
  记('\n底部中央工具行：');
  底中.forEach((a) => 记(`   \`${a.aria}\` @${a.x},${a.y} ${a.w}×${a.h}`));

  // ── ② 结构化找「还原 / 保留」那一对
  const 对 = await page.evaluate(() => {
    const 命中 = [];
    for (const e of document.querySelectorAll('button, [role="button"]')) {
      const t = (e.innerText || '').trim();
      if (t !== '还原' && t !== '保留') continue;
      const r = e.getBoundingClientRect();
      if (r.width < 20 || r.height < 15) continue;
      命中.push({ 文字: t, x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
        中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], tag: e.tagName,
        cls: (e.className || '').slice(0, 80) });
    }
    return 命中;
  });
  R.读数.按钮对 = 对;
  记(`\n结构化找「还原 / 保留」：命中 ${对.length} 个`);
  对.forEach((b) => 记(`   \`${b.文字}\` <${b.tag}> @${b.x},${b.y} ${b.w}×${b.h} cls=${b.cls}`));

  const 还原 = 对.find((b) => b.文字 === '还原');
  if (!还原) {
    记('⛔ 仍然没有找到，不点任何东西，留给人工');
  } else {
    const 前节点 = await page.evaluate(() =>
      [...document.querySelectorAll('.react-flow__node')].map((e) => (e.getAttribute('data-id') || '').trim()).sort());
    记(`\n点「还原」@${还原.中心.join(',')}`);
    await page.mouse.click(还原.中心[0], 还原.中心[1]);
    await page.waitForTimeout(1800);
    await page.screenshot({ path: resolve(EVID, 'fv8-1-还原之后.png') });

    const 后 = await page.evaluate(() => ({
      确认框: [...document.querySelectorAll('*')].some((e) => /是否保留此次整理结果/.test(e.innerText || '') && e.children.length === 0),
      缩放: (() => { const m = [...document.querySelectorAll('*')].find((e) => /^\d+%$/.test((e.innerText || '').trim()) && e.children.length === 0); return m ? m.innerText.trim() : ''; })(),
      节点: [...document.querySelectorAll('.react-flow__node')].map((e) => (e.getAttribute('data-id') || '').trim()).sort(),
    }));
    R.读数.后 = 后;
    断言('确认框消失', !后.确认框, `确认框 ${后.确认框 ? '还在' : '已消失'}`);
    断言('缩放回到 48%', 后.缩放 === '48%', `当前 ${后.缩放}%`);
    断言('节点 id 集合不变', JSON.stringify(后.节点) === JSON.stringify(前节点), `${后.节点.length} 个`);
  }
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFV8.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
