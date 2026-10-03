// 批次 137 · b 轮：护栏建一个**音频**节点 → 验 `audio-generation-form` → 删掉。
//
// （脚本由 a 轮复制而来，只改「左栏 aria」与期望的 testid；三档循环、护栏、取证函数逐字相同 ——
//   **两个面板的取证代码必须一模一样**，否则「对照」就不是对照了。）
//
// 🔑 靶子：`SOURCE_OBSERVATIONS.md` §3.82.4 记着一张三类生成表单的 testid 对照表：
//   视频 `video-generation-form` ／ **图片 `generation-form`（无类型前缀）** ／ 音频 `audio-generation-form`
//   —— 但**只有「图片」那一行在当前构建上被复现过**（批次 134），视频与音频两行是**沿用旧批次**的记述。
//
// 🔴 为什么值得专门验（批次 134 立过规）：**要推翻一条结论前先确认它当初的适用范围；
//   局部读数不自动等于全局规律。** 批次 134 正因为把「某个面板的读数」当成了「命名规律」，
//   差点反向误判手册有错。本轮是**反向自查**：手册那条规律自己站不站得住？
//   —— 特别是「图片无类型前缀」到底是**例外**还是**规律**。
//
// 🛡 建-删护栏在 `jimeng-b137-lib.mjs`，本轮**不写一遍**：护栏 ④ 用的是「**建后** ids」做差
//   （批次 134 那版算的是「本轮开始前」ids，恒为空集 ⇒ 门报 ⛔，清理本身却是成功的）。
import { writeFileSync } from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { 建删一轮 } from './jimeng-b137-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b' };
const save = () => writeFileSync(new URL('./_tmp-b137b.json', import.meta.url), JSON.stringify(out, null, 1));
const 断言 = (名, 条件, 详情) => { const ok = !!!!条件; (out.护栏 = out.护栏 || []).push({ 名, 通过: ok, 详情 });
  log(`  ${ok ? '✅' : '⛔'} 断言·${名}：${JSON.stringify(详情).slice(0, 300)}`); save(); return ok; };

out.手册对照表 = {
  来源: 'SOURCE_OBSERVATIONS.md §3.82.4（批次 63）',
  视频: 'video-generation-form',
  图片: 'generation-form（无类型前缀）',
  音频: 'audio-generation-form',
  本轮要验: '音频行（视频行已由 a 轮验成 video-generation-form）',
  注意: '图片行已由批次 134 在当前构建上复现；本轮是**反向自查这条规律站不站得住**',
};
log('手册对照表：', JSON.stringify(out.手册对照表, null, 1));
save();

/** 只读取证：所有候选 testid 的存在性、尺寸、逐字、按钮清单，以及三档缩放下的尺寸。 */
const 取证 = async (pg) => {
  const 快照 = () => pg.evaluate(() => {
    const box = (e) => { if (!e) return null; const r = e.getBoundingClientRect();
      return { w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10, x: Math.round(r.x), y: Math.round(r.y) }; };
    const q = (t) => document.querySelector(`[data-testid="${t}"]`);
    const 全部 = ['generation-form', 'video-generation-form', 'audio-generation-form', 'image-generation-form',
      'text-generation-form', 'node-toolbar', 'node-toolbar-feature-host', 'node-feature-chrome-host'];
    const 命中 = {};
    for (const t of 全部) { const e = q(t); if (e) 命中[t] = { 全部实例: document.querySelectorAll(`[data-testid="${t}"]`).length, 按面积最大: box(e) }; }
    // 全部实例逐个列出来（同一个 testid 可能有占位 + 真身）
    const 逐个 = {};
    for (const t of 全部) {
      const a = Array.from(document.querySelectorAll(`[data-testid="${t}"]`));
      if (a.length) 逐个[t] = a.map((e) => { const r = e.getBoundingClientRect();
        return { w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10, aria: e.getAttribute('aria-label'), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 80) }; });
    }
    const 面 = Array.from(document.querySelectorAll('[data-testid$="generation-form"], [data-testid="generation-form"]'))
      .map((e) => ({ testid: e.getAttribute('data-testid'), 矩形: box(e), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120),
        按钮: Array.from(e.querySelectorAll('button,[role=button]')).map((b) => ({ 逐字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24), aria: b.getAttribute('aria-label'),
          矩形: box(b) })) }));
    const 节点 = document.querySelector('.react-flow__node.selected');
    return { 命中, 逐个, generationForm族: 面,
      选中节点: 节点 ? { id: 节点.getAttribute('data-id'), 标题: (节点.querySelector('[data-testid="flow-node-title"]') || {}).innerText || null, 矩形: box(节点) } : null,
      节点class: 节点 ? 节点.className : null,
      全部testid含form: Array.from(new Set(Array.from(document.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')).filter((t) => /form/i.test(t)))) };
  });

  const r = { 各档: [] };
  // 🔴 第一版写的是 `if (pct !== 60) await setZoom(...)` —— 本意是「起始那档不用重设」，
  //   实际把**回程的 60% 档也跳过了** ⇒ 末档读到的其实是 40%（实测 scale 0.4）。
  //   **这与批次 135 d 轮是同一个 bug**：用一个「本该/不该做」的布尔条件去控制动作，
  //   循环里有重复值时就一定错。⇒ 改成**按实测 scale 判定**，不按「这一档是不是第一次」。
  const 实测 = async () => pg.evaluate(() => { const vp = document.querySelector('.react-flow__viewport');
    const m = vp ? /scale\(([-\d.]+)\)/.exec(vp.style.transform || '') : null; return m ? Math.round(parseFloat(m[1]) * 1000) / 1000 : null; });
  for (const pct of [60, 100, 40, 60]) {
    if (Math.abs((await 实测()) - pct / 100) > 0.002) {
      const z = await setZoom(pg, pct);
      r.setZoom记录 = r.setZoom记录 || []; r.setZoom记录.push({ 目标: pct, ...z });
    }
    const s = await 快照();
    const 实测scale = await pg.evaluate(() => { const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([-\d.]+)\)/.exec(vp.style.transform || '') : null; return m ? Math.round(parseFloat(m[1]) * 1000) / 1000 : null; });
    r.各档.push({ 目标: pct, 回读: await R.zoom(), 实测scale, 命中: Object.keys(s.命中), 快照: s });
    r.各档[r.各档.length - 1].占位 = s.逐个['node-toolbar'];
    log(`\n  ── 标称 ${pct}% ── aria «${await R.zoom()}»／**实测 scale ${实测scale}**`);
    log('     命中的 testid：', JSON.stringify(Object.keys(s.命中)));
    for (const t of Object.keys(s.命中)) log(`       ${t}: ${JSON.stringify(s.逐个[t])}`);
    log('     generation-form 族：', JSON.stringify(s.generationForm族.map((x) => ({ testid: x.testid, 矩形: x.矩形 }))));
    log('     选中节点：', JSON.stringify(s.选中节点), '｜class', s.节点class);
    log('     全部含 form 的 testid：', JSON.stringify(s.全部testid含form));
  }
  r.结论 = {
    音频行成立: r.各档.some((d) => d.命中.includes('audio-generation-form')),
    裸generationForm是否也在: r.各档.some((d) => d.命中.includes('generation-form')),
    出现的是哪一个form: r.各档[0].快照.命中,
    各档form尺寸: r.各档.map((d) => ({ 档: d.目标, 尺寸: d.快照.generationForm族.map((x) => [x.testid, x.矩形 && x.矩形.w + '×' + x.矩形.h]) })),
  };
  log('\n  🔑 结论：', JSON.stringify(r.结论, null, 1));
  return r;
};

log('\n=== 护栏循环：建「音频」节点 → 取证 → 删掉 ===');
const rec = await 建删一轮(p, 断言, '音频', 取证, 'batch-137b', 76);
out.本轮 = rec;
save();
save();
log('\n  护栏：', JSON.stringify((rec.护栏 || []).map((h) => [h.名, h.通过])));
log('  ok =', rec.ok);
断言('整轮护栏全过', rec.ok, { 护栏: (rec.护栏 || []).filter((h) => !h.通过) });
save(); save();
log('\n✅ b 轮完成 → ./_tmp-b137b.json');
await b.close();
