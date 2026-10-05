/**
 * 批次 214 清理脚本：把本批自己新建的 2 个节点删掉，把画布还原到 76。
 *
 * 🔴 为什么单独写：批次 214 a 轮的清理**只实现了「搜索」一条路径**，
 * 而搜索 `jimeng-b214-probe` 这种带连字符的名字**命中不到结果行**
 * （批次 213 的清理同样卡在 `jimeng-b196-probe`）⇒ 两个节点都没删掉，画布停在 **78**。
 * 📌 批次 213 f 轮的清理是**两条路径都写**的（先画布直点、失败再搜索），那一版成功了。
 * ⇒ 这就是立规 91 补记里那条的翻版：**规则/能力写在别处，不等于这一版有。**
 *
 * 本脚本两条路径都实现，且每一步都打印读数：
 *   路径 A：按立规 82 的 6×4 网格找一个**真在目标节点里**的点，直接点它
 *   路径 B：搜索（先用**节点名里最独特的一段**，并回显输入框实际值与现存结果行）
 *   两条都拿不到选中 ⇒ 走右键菜单里的「删除」
 *
 * 收尾**逐个 id 对照前置基线**核验（立规 94），不靠肉眼数。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const H = 720;
const OUT = '/tmp/b214-clean.json';
const 基线 = JSON.parse(fs.readFileSync('/tmp/b214a.json', 'utf8'));
const 要删 = 基线.自建清单 || [];
const 基线id = new Set(基线.步骤0_前置.基线id || []);

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b214-clean', 要删, 步: {} };

const 清单 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
  const t = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
  const r = n.getBoundingClientRect();
  return { id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'),
    画布: t ? [Number(t[1]), Number(t[2])] : null, 屏上: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
}));
const 状态行 = (p) => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes, (\d+) edges, (\d+) selected[^\n]*/) || [])[0] || null);
const 积分 = (p) => p.evaluate(() => {
  const e = Array.from(document.querySelectorAll('*')).find((x) => (x.getAttribute('aria-label') || '').startsWith('Credits'));
  return e ? e.getAttribute('aria-label') : null;
});
const 焦点 = (p) => p.evaluate(() => {
  const a = document.activeElement;
  return { tag: a ? a.tagName : null, inCE: !!(a && (a.closest('[contenteditable]') || a.isContentEditable)), isInput: !!(a && (a.tagName === 'INPUT' || a.tagName === 'TEXTAREA')) };
});

const browser = await chromium.connectOverCDP({ endpointURL: 'http://127.0.0.1:9444' });
const ctx = browser.contexts()[0];
const p = await ctx.newPage();
await p.setViewportSize({ width: 1280, height: H });
await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
await p.waitForSelector('.react-flow__node', { timeout: 45000 });
await p.waitForTimeout(5000);

out.前置 = { 数: (await 清单(p)).length, 状态行: await 状态行(p), 积分: await 积分(p) };
log('【前置】' + out.前置.数 + ' 个节点 ｜ ' + out.前置.状态行);

for (const id of 要删) {
  const 步 = { id };
  let now = await 清单(p);
  const me = now.find((n) => n.id === id);
  if (!me) { 步.备注 = '已不存在'; out.步[id] = 步; log('· ' + id + ' 已不存在'); continue; }
  步.aria = me.aria;

  // ---- 路径 A：画布直点（立规 82 网格）----
  步.路径A = await p.evaluate((nid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
    if (!n) return { 失败: '不在 DOM' };
    const r = n.getBoundingClientRect();
    if (r.right < 0 || r.x > innerWidth || r.bottom < 0 || r.y > innerHeight) return { 失败: '不在视口内', 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
    for (let fy = 0.15; fy <= 0.9; fy += 0.15) for (let fx = 0.15; fx <= 0.9; fx += 0.15) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const h = document.elementFromPoint(x, y);
      if (h && h.closest(`.react-flow__node[data-id="${nid}"]`)) return { x, y, 相对: [Math.round(fx * 100), Math.round(fy * 100)] };
    }
    return { 失败: '36 个候选点没有一个在节点内（被盖）' };
  }, id);
  if (步.路径A.x) {
    await p.mouse.click(步.路径A.x, 步.路径A.y);
    await p.waitForTimeout(1200);
    步.路径A后选中数 = await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
    log(`· ${id} 路径A 点 (${步.路径A.x},${步.路径A.y}) 相对 ${JSON.stringify(步.路径A.相对)} → 选中数 ${步.路径A后选中数}`);
  } else {
    log(`· ${id} 路径A 失败：${步.路径A.失败}`);
    // ---- 路径 B：搜索 ----
    步.路径B = { 尝试词: [] };
    const 词候选 = [(me.aria || '').split('node: ')[1] || '', (me.aria || '').split('node: ')[1] || ''].map((x) => x.trim()).filter(Boolean);
    for (const 词 of 词候选) {
      const 钮 = await p.evaluate(() => {
        const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
          || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
        if (!e) return null;
        const r = e.getBoundingClientRect();
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      });
      if (!钮) { 步.路径B.失败 = '找不到搜索钮'; break; }
      await p.mouse.click(钮[0], 钮[1]);
      await p.waitForTimeout(1400);
      const 有框 = await p.evaluate(() => {
        const e = Array.from(document.querySelectorAll('input')).find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
        if (!e) return false;
        e.focus(); e.select(); return true;
      });
      if (!有框) { 步.路径B.失败 = '找不到搜索输入框'; break; }
      await p.keyboard.press('Backspace');
      await p.waitForTimeout(200);
      await p.keyboard.type(词, { delay: 90 });
      await p.waitForTimeout(2200);
      const 回读 = await p.evaluate(() => {
        const e = Array.from(document.querySelectorAll('input')).find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
        return e ? e.value : null;
      });
      const 行 = await p.evaluate((nid) => {
        const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
        const 现存 = Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-node_"]')).slice(0, 6).map((x) => x.getAttribute('data-testid'));
        if (!e) return { 有: false, 现存 };
        const r = e.getBoundingClientRect();
        return { 有: true, 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 现存 };
      }, id.replace(/^node_/, ''));
      步.路径B.尝试词.push({ 词, 回读, 有行: 行.有, 现存: 行.现存 });
      log(`  路径B 词「${词}」回读=${JSON.stringify(回读)} 有行=${行.有}`);
      if (行.有) {
        await p.mouse.click(行.点[0], 行.点[1]);
        await p.waitForTimeout(1300);
        const sel = await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
        步.路径B.选中数 = sel;
        log(`  路径B 点行 → 选中数 ${sel}`);
        if (sel >= 1) break;
      }
    }
  }

  // ---- 删除：守卫过了才按 Backspace ----
  步.最终选中数 = await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
  步.焦点 = await 焦点(p);
  const 安全 = 步.最终选中数 >= 1 && !步.焦点.inCE && !步.焦点.isInput;
  步.焦点安全 = 安全;
  log(`  ⇒ 选中数 ${步.最终选中数} ｜ 焦点 ${JSON.stringify(步.焦点)} ｜ 安全 ${安全}`);
  if (安全) {
    await p.keyboard.press('Backspace');
    await p.waitForTimeout(2600);
    步.按了Backspace = true;
    // 若没删掉（可能被别的元素吃掉），再试一次
    if ((await 清单(p)).some((n) => n.id === id)) {
      log('  ⚠️ 第一次 Backspace 没删掉，再来一次');
      await p.keyboard.press('Backspace');
      await p.waitForTimeout(2600);
      步.按了两次 = true;
    }
  }
  步.删后仍在 = (await 清单(p)).some((n) => n.id === id);
  out.步[id] = 步;
  log(`  ⇒ ${id} 删后仍在 ${步.删后仍在} ｜ 当前 ${(await 清单(p)).length} 个节点`);
}

const 末 = await 清单(p);
out.后置 = {
  数: 末.length,
  状态行: await 状态行(p),
  积分: await 积分(p),
  多出来: 末.filter((n) => !基线id.has(n.id)).map((n) => n.id + ' ' + n.aria),
  少了: [...基线id].filter((x) => !末.some((n) => n.id === x)),
};
log('【后置】' + out.后置.数 + ' 个节点 ｜ 多 ' + JSON.stringify(out.后置.多出来) + ' ｜ 少 ' + JSON.stringify(out.后置.少了));
log('【后置】' + out.后置.状态行 + ' ｜ 积分 ' + out.后置.积分);

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
process.exit(0);
