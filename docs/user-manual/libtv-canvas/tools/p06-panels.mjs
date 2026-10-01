// 探针 06 —— 逐个打开画布上的一级入口，把每个面板的真实内容拿全。
//
// 难点：这些面板不是 Mantine 浮层，选择器逐个猜必然漏（实测第一版只捞到画布下拉）。
// 做法：点击前拍一张「可见大元素」指纹，点击后取差集 —— 差集里带可见文本的就是新面板。
// 这样不依赖任何 class 名，也就不会漏掉自绘面板。
//
// 只读：面板开完即关，不创建节点、不提交表单、不触发任何生成。
import { launch, open, closePromos, shot } from './lib.mjs';
import { CANVAS_URL } from './test-project.mjs';

const { browser, page } = await launch();

async function clearToasts(p) {
  for (let i = 0; i < 3; i += 1) {
    const btn = p.getByRole('button', { name: '知道了', exact: true });
    const x = p.getByRole('button', { name: '关闭浏览器通知提示', exact: true });
    if (await btn.count()) await btn.first().click({ timeout: 2000 }).catch(() => {});
    await p.waitForTimeout(250);
    if (await x.count()) await x.first().click({ timeout: 2000 }).catch(() => {});
    await p.waitForTimeout(250);
    if (!(await btn.count()) && !(await x.count())) break;
  }
}

/** 可见、且有自身文本的「面板级」元素指纹（面积门槛排掉整页 body）。 */
const FINGERPRINT = () => {
  const vis = (el) => {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return r.width > 120 && r.height > 60 && s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity > 0.05;
  };
  const out = [];
  for (const el of document.querySelectorAll('div,section,aside,ul,nav,[role="dialog"],[role="menu"]')) {
    if (!vis(el)) continue;
    const own = [...el.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent.trim()).join('');
    const r = el.getBoundingClientRect();
    const sig = `${el.tagName}|${(el.className || '').toString().slice(0, 40)}|${Math.round(r.x)},${Math.round(r.y)}`;
    out.push({ sig, own, all: (el.innerText || '').replace(/\s+/g, ' ').slice(0, 1400), n: el.querySelectorAll('*').length, area: Math.round(r.width * r.height) });
  }
  return out;
};

async function snapshot() {
  return page.evaluate(FINGERPRINT);
}

function diff(before, after) {
  const seen = new Set(before.map((b) => b.sig));
  return after.filter((a) => !seen.has(a.sig)).sort((a, b) => a.area - b.area).slice(-3);
}

const ENTRIES = [
  ['添加节点', '添加节点', 'p06-add-node.png'],
  ['快捷键', '快捷键', 'p06-shortcuts.png'],
  ['素材库', '素材库', 'p06-asset-library.png'],
  ['角色造型室', '角色造型室', 'p06-character-studio.png'],
  ['生成历史', '生成历史', 'p06-gen-history.png'],
  ['缩放选项', '缩放选项', 'p06-zoom.png'],
  ['隐藏节点连线', '隐藏节点连线', 'p06-hide-edges.png'],
  ['切换小地图', '切换小地图', 'p06-minimap.png'],
  ['网格吸附', '网格吸附', 'p06-snap.png'],
  ['整理画布', '整理画布，Option+Shift+F', 'p06-tidy.png'],
  ['资产管理', '资产管理', 'p06-asset-manager.png'],
];

try {
  await open(page, CANVAS_URL, { settle: 3500 });
  await closePromos(page);
  await clearToasts(page);
  await page.waitForTimeout(800);
  await shot(page, 'p06-base-canvas.png');
  console.log('base:', await shot(page, 'p06-base-canvas.png'));

  for (const [name, aria, file] of ENTRIES) {
    const before = await snapshot();
    const loc = page.getByRole('button', { name: aria, exact: true }).first();
    const n = await loc.count();
    if (!n) { console.log(`\n######## ${name} —— 未找到按钮，跳过`); continue; }
    await loc.click({ timeout: 5000 }).catch((e) => console.log('  click warn:', e.message.slice(0, 60)));
    await page.waitForTimeout(1200);
    const after = await snapshot();
    const neu = diff(before, after);
    console.log(`\n######## ${name} —— 新增面板 ${neu.length} 个`);
    for (const d of neu) {
      console.log(`  [area=${d.area} children=${d.n}] ${d.all.slice(0, 1100)}`);
    }
    if (neu.length) await shot(page, file);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(600);
  }
} finally {
  await browser.close();
}
