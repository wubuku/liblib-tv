/**
 * 批次 295 · 「跳的是音频/视频」这条 kind 线索，撞上一个真正的判别集。
 *
 * 🔴 起意：前量全量转储（/tmp/b295-dump.json）拿到一件此前没人注意的事 ——
 *    **盒 320×320 跨了三个 kind**：文本×3、音频×68、外部×1（名「导演台」）。
 *    三者闭式**逐字相同**（1.75）。批次 294 测过其中两个（文本 1 不跳、音频 1 跳），
 *    第三个（外部）从没进过场 ⇒ 这是判别 kind 假说的**最干净的一格**：
 *    同盒、同闭式、第三个 kind，结果就能把「按 kind 走」从 5 样本线索推到跨类判定。
 *
 * 🔴 同时订正一处记账：批次 294 记的参照节点写的是「音频 68」，而它按前缀 `音频`
 *    实际找到的是 **`音频 node: 音频 1`（node_ay7f1jn45r）**。DOM 里 aria-label 的
 *    真实形态是 `<kind> node: <短名>`，而手册里满地的「音频 68」指的是
 *    **「节点 N」面板里的计数**（这一类 68 个）—— 字面相同、含义不同。
 *    本批把 音频 1 / 2 / 30 / 68 全部直接量一遍，把这句话本身也一并验明。
 *
 * 判据（写死）：
 *   P0 阳性对照：w=1212 上 音频 1 与 视频 1 必须**再次跳**（批次 293/294 已知）
 *      ⇒ 不跳 ⇒ 读数不可靠，**整组作废**（「没跳」不当发现）。
 *   P1 对照侧：w=1211 上 音频 1 与 外部 必须**不跳**（逐字命中闭式）
 *      ⇒ 跳了 ⇒ 阈值可能不在 1212，判据前提不成立，整组作废。
 *   P2 判决：按 kind 分组，**类内必须一致**（要么全跳、要么全不跳）；
 *      类内不一致 ⇒ kind 划分被推翻。
 *   P3 关注格：外部（320×320，闭式 1.75）跳不跳。
 *
 * 前提检查：轴向自检 / z0 > 闭式 硬门 / 落定自检 / 点击生效自检 / 参数写死 /
 *   盒与 id 一律现找现量（按 aria 精确匹配，不靠前缀、不靠记忆）/ 比较集固定。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b295.json';
const 放大键 = 'Meta+Equal';
const 按够 = 13;                      // 写死：1.2^13 ≈ 10.7，足以压过任何 vs 平台（参数写死）

// 臂表：只写 kind + 短名，id 与盒一律现找现量（前提：现量，不靠记忆）
const 臂表 = [
  { w: 1212, 键: '音频1',  kind: '音频', 名: '音频 1',  角色: 'P0 阳性对照：批次 293/294 已知跳' },
  { w: 1212, 键: '视频1',  kind: '视频', 名: '视频 1',  角色: 'P0 阳性对照：批次 293 已知跳' },
  { w: 1212, 键: '音频2',  kind: '音频', 名: '音频 2',  角色: 'P1 类内一致：第 2 个音频' },
  { w: 1212, 键: '音频30', kind: '音频', 名: '音频 30', 角色: 'P1 类内一致：中间那个' },
  { w: 1212, 键: '音频68', kind: '音频', 名: '音频 68', 角色: '🔴 订正：手册里那个「音频 68」到底是哪个节点' },
  { w: 1212, 键: '外部',   kind: '外部', 名: '导演台',   角色: '🔴 关注格：同盒 320×320 的第三个 kind' },
  { w: 1212, 键: '文本1',  kind: '文本', 名: '文本 1',  角色: '已知不跳（同盒对照）' },
  { w: 1212, 键: '图片',   kind: '图片', 名: 'b22-upload', 角色: '已知不跳' },
  { w: 1211, 键: '音频1@1211', kind: '音频', 名: '音频 1', 角色: 'P1 对照侧：1211 上必须不跳' },
  { w: 1211, 键: '外部@1211',  kind: '外部', 名: '导演台',   角色: 'P1 对照侧：1211 上必须不跳' },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b295',
  问: '同盒 320×320 跨三个 kind：文本不跳、音频跳，那第三个 kind（外部）跳不跳？',
  臂表, 臂: [], 判定: {},
};

// 🔴 批次 295 换掉「连常驻 CDP」这条路：
//    同一个上下文里，一个旧页有 76 节点、一个新页却是「登录以打开您的画布」，
//    且两页 document.cookie.length 分别是 1214 与 178 ⇒ **失败的页把会话 cookie 清掉了**
//    ⇒ 共享上下文里「开新页读数」这条路已经不可靠。
//    改为**每条臂自己 launch + storageState**（该路径已实测能出 76 节点 / 积分 813）。

const 屏上律 = (ww) => Math.max(100, ww - 532);
const 安全高 = (hh) => hh - 160;
const vf = (z) => Math.min(8, Math.max(0.08, z));

const 读 = (p) => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  return {
    scale: m ? Number(m[1]) : null,
    百分比: (document.querySelector('[data-testid="canvas-zoom-percent"]') || {}).textContent || null,
    选中: Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.dataset.id),
  };
});

for (const A of 臂表) {
  let br = null; let ctxA = null; let p = null;
  const 记 = { w: A.w, 键: A.键, kind: A.kind, 名: A.名, 角色: A.角色 };
  try {
    br = await chromium.launch({ headless: true });
    ctxA = await br.newContext({ storageState: STATE, viewport: { width: A.w, height: 720 } });
    p = await ctxA.newPage();
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 60000 });
    await p.waitForTimeout(6000);

    // 前提①：轴向自检
    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== A.w || 实际.h !== 720) throw new Error(`轴向自检失败：实测 ${实际.w}×${实际.h}`);

    // 前提②：按 aria **精确**匹配（DOM 真实形态是「<kind> node: <短名>」）
    const ariaWant = `${A.kind} node: ${A.名}`;
    const 目标 = await p.evaluate((aria) => {
      const e = document.querySelector(`.react-flow__node[data-id][aria-label="${aria}"]`)
        || Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
             .find((x) => x.getAttribute('aria-label') === aria);
      if (!e) return null;
      return { id: e.dataset.id, aria: e.getAttribute('aria-label'), W: e.offsetWidth, H: e.offsetHeight };
    }, ariaWant);
    if (!目标) throw new Error(`找不到 aria 为「${ariaWant}」的节点`);
    记.节点id = 目标.id;
    记.节点aria = 目标.aria;
    记.盒 = { W: 目标.W, H: 目标.H };        // 🔴 offsetWidth 即画布空间布局尺寸（立规 174，不再除 zoom）
    const 闭式 = +vf(Math.min(屏上律(A.w) / 目标.W, 安全高(720) / 目标.H)).toFixed(6);
    记.闭式 = 闭式;

    for (let i = 0; i < 按够; i++) { await p.keyboard.press(放大键); await p.waitForTimeout(380); }
    await p.waitForTimeout(1200);
    const z0 = await 读(p);
    记.z0 = z0.scale;
    if (z0.scale === null) throw new Error('读不到缩放');
    // 前提③：z0 > 闭式 硬门，否则读不到平台
    if (!(z0.scale > 闭式)) throw new Error(`z0(${z0.scale}) 不高于闭式(${闭式}) ⇒ 读不到平台`);

    const 钮 = await p.evaluate(() => {
      const b = document.querySelector('button[aria-label="搜索"]');
      if (!b) return null;
      const r = b.getBoundingClientRect();
      return { 中心: [r.x + r.width / 2, r.y + r.height / 2], 可见: r.width > 0 && r.height > 0 && r.y >= 0 && r.bottom <= innerHeight };
    });
    if (!钮 || !钮.可见) throw new Error('找不到可见的搜索钮');
    await p.mouse.click(钮.中心[0], 钮.中心[1]);
    await p.waitForTimeout(1600);

    // 候选查询名：先短名（用户真会输的），再完整 aria，再 kind
    let 行 = null, 用名 = null;
    for (const 名 of [A.名, ariaWant, A.kind]) {
      await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-search-panel"] input'); if (i) { i.focus(); i.select(); } });
      await p.keyboard.type(名, { delay: 80 });
      await p.waitForTimeout(2000);
      const sel = `[data-testid="canvas-search-result-node_${目标.id.replace(/^node_/, '')}"]`;
      let r = await p.evaluate((s) => {
        const e = document.querySelector(s);
        if (!e) return null;
        e.scrollIntoView({ block: 'center' });
        const b = e.getBoundingClientRect();
        return { 中心: [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)], 可见: b.width > 0 && b.height > 0 && b.y >= 0 && b.bottom <= innerHeight && b.x >= 0 && b.right <= innerWidth };
      }, sel);
      if (r && !r.可见) { await p.waitForTimeout(600); r = await p.evaluate((s) => { const e = document.querySelector(s); const b = e.getBoundingClientRect(); return { 中心: [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)], 可见: b.width > 0 && b.height > 0 && b.y >= 0 && b.bottom <= innerHeight && b.x >= 0 && b.right <= innerWidth }; }, sel); }
      if (r && r.可见) { 行 = r; 用名 = 名; break; }
    }
    if (!行) throw new Error(`搜不到「${A.名}」的可见结果行`);
    记.用名 = 用名;
    await p.mouse.click(行.中心[0], 行.中心[1]);
    await p.waitForTimeout(3000);
    const a1 = await 读(p);
    await p.waitForTimeout(2500);
    const a2 = await 读(p);
    记.z后1 = a1.scale;
    记.z后2 = a2.scale;
    记.落定 = a1.scale === a2.scale;               // 前提④：臂内落定自检
    记.选中 = a2.选中;
    记.点击生效 = a2.选中.includes(目标.id);        // 前提⑤：点击生效自检
    if (!记.点击生效) throw new Error(`点击未生效（选中=${JSON.stringify(a2.选中)}）`);
    记.vs实测 = a2.scale;
    记.跳了 = Math.abs(a2.scale - 闭式) > 2e-3;
    log(`${A.键.padEnd(9)}｜${A.w}｜${(A.kind + ' ' + A.名).padEnd(12)}｜盒 ${目标.W}×${目标.H}｜z0=${z0.scale}｜vs=${a2.scale}｜闭式 ${闭式}｜${记.跳了 ? '🔴 跳' : '✅ 不跳'}｜落定 ${记.落定 ? '✅' : '🔴'}｜用名「${用名}」`);
  } catch (e) {
    记.错误 = e.message;
    log(`${A.键.padEnd(9)}🔴 ${e.message}`);
  } finally {
    try { if (p) await p.close(); } catch (e) { /* 忽略 */ }
    try { if (br) await br.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

const 好 = out.臂.filter((x) => !x.错误 && x.点击生效 && x.vs实测 !== undefined);
log('\n════ 汇总 ════');
for (const x of 好) log(`  ${x.键.padEnd(9)} w=${x.w} ${(x.kind + ' ' + x.名).padEnd(12)} ${String(x.盒.W + '×' + x.盒.H).padEnd(10)} vs=${String(x.vs实测).padEnd(10)} 闭式=${String(x.闭式).padEnd(10)} ${x.跳了 ? '🔴 跳' : '✅ 不跳'}`);

// ── 判据 ──────────────────────────────────────────────
const 找 = (k) => 好.find((x) => x.键 === k);
const P0 = ['音频1', '视频1'].map(找).filter(Boolean);
const P1 = ['音频1@1211', '外部@1211'].map(找).filter(Boolean);
const 阳性 = P0.length === 2 && P0.every((x) => x.w === 1212 && x.跳了);
const 对照 = P1.length === 2 && P1.every((x) => !x.跳了);

// 按 kind 分组（只取 w=1212 这批可比集）
const 类 = {};
for (const x of 好.filter((y) => y.w === 1212)) {
  const k = (类[x.kind] ||= { 跳: 0, 不跳: 0, 成员: [], 值: [] });
  if (x.跳了) k.跳++; else k.不跳++;
  k.成员.push(x.名);
  k.值.push(x.vs实测);
}
const 矛盾 = Object.entries(类).filter(([, v]) => v.跳 > 0 && v.不跳 > 0);

if (!阳性 || !对照) {
  out.判定 = {
    前提: 'FAIL',
    结论: '🔴 **前提自检没过**（阳性对照或对照侧不符）⇒ 本组读数不可靠，「不跳/跳」都不能当发现，**整组作废**，不编',
    阳性, 对照,
  };
} else {
  const 跳的 = Object.entries(类).filter(([, v]) => v.跳 > 0).map(([k]) => k);
  const 不跳的 = Object.entries(类).filter(([, v]) => v.不跳 > 0).map(([k]) => k);
  out.判定 = {
    前提: 'PASS',
    有效臂: `${好.length}/${臂表.length}`,
    P0_阳性对照: `✅ 音频 1 与 视频 1 在 1212 上都再次跳`,
    P1_对照侧: `✅ 音频 1 与 外部 在 1211 上都不跳（逐字命中闭式）`,
    跳了的类: 跳的.join('、') || '（无）',
    不跳的类: 不跳的.join('、') || '（无）',
    按类: JSON.stringify(类),
    类内部不一致: 矛盾.length ? `🔴 ${矛盾.map(([k]) => k).join('、')}：同一个类里既有跳的也有不跳的 ⇒ kind 划分被推翻` : '✅ 每个类内部一致（要么全跳、要么全不跳）',
    结论: 矛盾.length
      ? `🔴 **kind 划分被推翻** —— ${矛盾.map(([k]) => k).join('、')} 类内不一致 ⇒ 跳变的真正判据还在别处，**不编**（立规 113）`
      : `✅ **kind 划分在 ${好.length} 个节点、${Object.keys(类).length} 个类上都类内一致** ⇒ 📌 **「跳变按 kind 走」从 5 样本线索升为跨类判定**；⚠️ **仍不等于成因** —— 下一步要问「音频/视频这一类在 w≥1212 上多出了什么」`,
  };
}
log('\n════ 判定 ════\n' + JSON.stringify(out.判定, null, 1));

const brz = await chromium.launch({ headless: true });
const ctxz = await brz.newContext({ storageState: STATE, viewport: { width: 1280, height: 720 } });
const pz = await ctxz.newPage();
try {
  await pz.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await pz.waitForSelector('.react-flow__node', { timeout: 60000 });
  await pz.waitForTimeout(6000);
  out.末态 = await pz.evaluate(() => ({
    节点数: document.querySelectorAll('.react-flow__node').length,
    状态行: (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null,
    积分: (document.querySelector('[data-testid="canvas-commerce-entry"]') || {}).textContent || null,
  }));
  log('末态独立复查：', JSON.stringify(out.末态));
} finally { try { await pz.close(); await brz.close(); } catch (e) { /* 忽略 */ } }

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入', OUT);
process.exit(0);
