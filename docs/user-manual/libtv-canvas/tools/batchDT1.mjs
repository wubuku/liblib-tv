// Batch DT-1：把「baseType → 模型名」的对照表抓出来。
//
// ⭐ 背景（DS 批挖到的）：详情浮层里「首选推荐模型 / 其余适配模型」列的模型名
//   来自 `useMaterialPanelConfig()` 的 `styleModelList`，它按 **`baseType` 匹配**：
//     t.find(t => t.baseType === 卡.baseType[i])
//   ⇒ **一张卡 `baseType` 有 6 个值、浮层只列 5 个模型**（DS 批实测），
//     就是因为**有一个 baseType 在当前模型表里匹配不到**。
//
// ⭐⭐ 所以「这张风格支持哪几个模型」的权威答案 = **`styleModelList` 那张表**。
//   源码里只有一张 2 条的**兜底表**（线上走远程配置）：
//     styleModelList 兜底 = nebula-ultra→General image Pro(baseType 40)
//                        + qwen-image→Qwen Image(baseType 37)
//   ⇒ 真实表必须**从运行时抓**，这正是本轮要做的。
//
// ⭐ 判据：响应体里出现 `styleModelList` 这个 key。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = { 命中: [], 表: null, 校验: null };
const SAVE = () => writeFileSync(new URL('./batchDT1.json', import.meta.url), JSON.stringify(out, null, 2));

const { browser, page } = await launch();
const 见 = new Map(); // url -> 长度
page.on('response', async (resp) => {
  try {
    const u = resp.url();
    const t = await resp.text().catch(() => '');
    if (!t) return;
    if (!/styleModelList|lensModelList|materialPanelConfig/.test(t)) return;
    见.set(u, t.length);
    let j; try { j = JSON.parse(t); } catch { j = null; }
    out.命中.push({ url: u, 字节: t.length, 是JSON: !!j });
    // 就地找表
    const 挖 = (o) => {
      if (!o || typeof o !== 'object') return null;
      if (Array.isArray(o.styleModelList) || Array.isArray(o.lensModelList)) return o;
      for (const k of Object.keys(o)) { const r = 挖(o[k]); if (r) return r; }
      return null;
    };
    const cfg = j ? 挖(j) : null;
    if (cfg && !out.表) {
      out.表 = {
        来源: u,
        styleModelList: (cfg.styleModelList || []).map((x) => ({ modelKey: x.modelKey, modelName: x.modelName, baseType: x.baseType, styleType: x.styleType, maxCount: x.maxCount })),
        lensModelList: (cfg.lensModelList || []).map((x) => ({ modelKey: x.modelKey, modelName: x.modelName, baseType: x.baseType, modelType: x.modelType, maxCount: x.maxCount })),
      };
      LOG(`\n⭐⭐ 抓到配置！来源 ${u}`);
      LOG(`   styleModelList ${out.表.styleModelList.length} 条 / lensModelList ${out.表.lensModelList.length} 条`);
    }
  } catch { /* 忽略 */ }
});

await open(page, URL_);
await closePromos(page);
await page.waitForTimeout(3000);
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(3000);
// 多等一会儿：远程配置可能懒加载
for (let i = 0; i < 8; i += 1) {
  await page.waitForTimeout(2000);
  if (out.表) break;
}
LOG(`扫过的响应里含关键词的有 ${out.命中.length} 个`);
for (const h of out.命中.slice(0, 8)) LOG(`   ${h.字节} 字节 ${h.url.slice(0, 140)}`);

if (out.表) {
  LOG('\n══════ styleModelList（风格适配模型）══════');
  for (const m of out.表.styleModelList) LOG(`   baseType ${String(m.baseType).padStart(3)} → ${m.modelKey.padEnd(22)} ${m.modelName}  [${m.styleType || '-'}] maxCount=${m.maxCount}`);
  LOG('\n══════ lensModelList（特效适配模型）══════');
  for (const m of out.表.lensModelList) LOG(`   baseType ${String(m.baseType).padStart(3)} → ${m.modelKey.padEnd(22)} ${m.modelName}  modelType=${m.modelType} maxCount=${m.maxCount}`);
  // ⭐ 校验：DS 批那张 6 模型卡 baseType=[81,70,68,55,40,27] 有几个能匹配上
  const 卡 = [81, 70, 68, 55, 40, 27];
  const 命中 = 卡.map((b) => ({ baseType: b, 模型: out.表.styleModelList.filter((m) => m.baseType === b).map((m) => m.modelName) }));
  LOG('\n══════ ⭐ 校验：DS 批那张 6 模型卡 baseType=[81,70,68,55,40,27] ══════');
  for (const h of 命中) LOG(`   baseType ${String(h.baseType).padStart(3)} → ${h.模型.length ? h.模型.join(', ') : '⛔ 表里没有 ⇒ 这一项不渲染'}`);
  out.校验 = 命中;
} else {
  LOG('⛔ 响应体里没抓到配置（**阴性，不等于线上没有这张表**）');
}
SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDT1.json ===');
