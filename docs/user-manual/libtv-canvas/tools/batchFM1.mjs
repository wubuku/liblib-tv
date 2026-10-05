// ⭐⭐⭐⭐⭐ Batch FM-1：把 FK 那 8189 条文案里**最值钱的一组**拿到界面上逐条对账
//
// FL 已经证明「key 前缀不能当功能分组」，所以这一轮**不再按前缀推断**，
// 而是反过来：**拿着清单去界面上找**，一条一条对账，命中多少、没中多少，都报出来。
//
// 选「角色造型室」的理由：
//   · FK 统计里它是**最大的一组**（`characterStudio*` 799 条）
//   · 手册 `10-tasks/character-studio.md` 只写了「创建新角色」最浅的一层
//   · ⭐ **纯只读**：底栏第三枚按钮点开就是面板，不点任何卡片、不点「创建新角色」
//     （⛔ 创建角色会往画布上新建节点，不可逆）
//
// 对账方法：
//   ① 打开面板，dump 面板容器内**所有可见文字**（含 aria-label / title / placeholder）
//   ② 从 i18n-canvas.json 里取出 `characterStudio*` 的文案
//   ③ 逐条判断「这条文案在界面上找得到吗」
//   ④ ⭐ **同时报告反向的**：面板上出现了、但清单里没有的文字（可能是清单过时了）
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, readFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFM1.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

// 从清单里取文案（Node 侧读文件，不进浏览器）
const i18n = JSON.parse(readFileSync(EVID + 'i18n-canvas.json', 'utf8'));
const 清单 = Object.entries(i18n.表).filter(([k]) => k.startsWith('characterStudio')).map(([k, v]) => ({ k, v }));
记(`清单里 characterStudio* 共 ${清单.length} 条`);

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(13000);
  记('closePromos：' + JSON.stringify(await closePromos(page)).slice(0, 110));
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);

  // ① 点底栏「角色造型室」
  const 钮 = await page.evaluate(() => {
    for (const x of document.querySelectorAll('button')) {
      if ((x.getAttribute('aria-label') || '') === '角色造型室') {
        const r = x.getBoundingClientRect();
        if (r.width > 0) return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
      }
    }
    return null;
  });
  if (!钮) throw new Error('找不到「角色造型室」按钮');
  记('点底栏「角色造型室」' + JSON.stringify(钮));
  await page.mouse.click(钮[0], 钮[1]);
  await page.waitForTimeout(4500);

  // ② 找面板容器并 dump 全部可见文字
  const 面板 = await page.evaluate(() => {
    const 可见 = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    // ⭐ 找一个「大容器」：可见面积最大、且不是 body/html 的那个
    const 候选 = [...document.querySelectorAll('div,section,aside')].filter((el) => {
      if (!可见(el)) return false;
      if (el === document.body || el === document.documentElement) return false;
      const r = el.getBoundingClientRect();
      return r.width > 420 && r.height > 300;
    });
    候选.sort((a, b) => (b.getBoundingClientRect().width * b.getBoundingClientRect().height) - (a.getBoundingClientRect().width * a.getBoundingClientRect().height));
    const 根 = 候选[0] || document.body;
    const 文字 = new Set();
    const 节点 = [];
    for (const el of 根.querySelectorAll('*')) {
      if (!可见(el)) continue;
      // 只取叶子节点的直接文字
      for (const n of el.childNodes) {
        if (n.nodeType === 3) {
          const t = (n.textContent || '').replace(/\s+/g, ' ').trim();
          if (t) { 文字.add(t); 节点.push(t); }
        }
      }
      for (const a of ['aria-label', 'title', 'placeholder', 'alt']) {
        const v = (el.getAttribute && el.getAttribute(a)) || '';
        if (v && v.trim()) { 文字.add(v.trim()); 节点.push(v.trim()); }
      }
    }
    const r = 根.getBoundingClientRect();
    return { 容器class: (根.className || '').toString().slice(0, 80), 容器框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 文字: [...文字], 节点数: 节点.length };
  });
  记(`面板容器 ${JSON.stringify(面板.容器class)} 框 ${JSON.stringify(面板.容器框)}，可见文字 ${面板.文字.length} 条`);
  for (const w of 面板.文字.slice(0, 60)) 记('   · ' + w);
  await page.screenshot({ path: EVID + 'fm1-01-角色造型室.png' });
  R.读数.面板 = 面板;

  // ③ 对账：清单里有多少能在界面上找到
  const 界面集 = new Set(面板.文字);
  const 归一 = (s) => s.replace(/[\s　]+/g, '');
  const 界面归一 = new Set([...界面集].map(归一));
  const 命中 = [], 未命中 = [];
  for (const { k, v } of 清单) {
    (界面归一.has(归一(v)) ? 命中 : 未命中).push({ k, v });
  }
  记(`—— 对账：命中 ${命中.length} / ${清单.length}（${(100 * 命中.length / 清单.length).toFixed(1)}%）——`);
  for (const h of 命中.slice(0, 40)) 记('   ✅ ' + h.k + ' = ' + h.v);
  记('—— 前 25 条未命中（清单里有、界面上没找到）——');
  for (const h of 未命中.slice(0, 25)) 记('   ❌ ' + h.k + ' = ' + h.v);

  // ④ 反向：界面上有、清单里没有的
  const 清单集 = new Set(清单.map((x) => 归一(x.v)));
  const 反向 = [...界面集].filter((w) => !清单集.has(归一(w)) && w.length >= 2);
  记(`—— 反向：界面上出现但清单里没有的 ${反向.length} 条 ——`);
  for (const w of 反向.slice(0, 30)) 记('   ↩ ' + w);

  R.读数.对账 = { 清单条数: 清单.length, 命中: 命中.length, 未命中: 未命中.length, 命中率: Number((100 * 命中.length / 清单.length).toFixed(1)), 命中样本: 命中.slice(0, 30), 未命中样本: 未命中.slice(0, 20), 反向 };
} catch (e) {
  记('❌ 出错：' + (e && e.message ? e.message : String(e)));
} finally {
  try { await 浏览器.browser.close(); } catch (e) { /* 关 */ }
  记('done');
}
