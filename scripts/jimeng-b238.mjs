/**
 * 批次 238：把 `时间线 1/2` 的**负结论框出边界** —— 与 `导演台` 对齐。
 *
 * 📌 为什么要做：立规 111 要求「负结论要写成带边界的结论」。批次 235/236 给 `导演台` 的
 *   负结论框到了 **`740`–`1235`**（`20` 臂），但 `时间线 2` 那条「❌ 没有带子」
 *   **一直没有边界** —— 它是批次 223 扫 `68` 档得出的，扫的是哪个区间没人写下来。
 *   ⇒ 同一张族表里两行负结论的**精度不一样**，而下一个人会以为它们一样可信。
 *
 * 📌 选 `时间线 2`（`z=20`）而不是 `时间线 1`（`z=1`）：`时间线 1` 画布坐标 x=`40.0555`
 *   几乎贴着左边缘，取景后可能落到视口外；`时间线 2` 在 `1282.76` 更靠中间，取景更稳。
 *   ⚠️ 这是**取样理由**，不是结论 —— 两个节点同为 `1200×207` / `timeline`，
 *   若结论要外推到整个族，得说明这一点。
 *
 * 🔴 纪律：
 *   · **粗扫只为框边界**，每档都记**正交读量**（节点中心 Y）——
 *     凹口左右两侧的 `scale` 都是 `0.5`，只看 `scale` 分不出分支（立规 104）；
 *   · **不自设下界**：`740` 以下不扫就在结论里写明「`740` 以下没测」；
 *   · 逐档写盘，跑到哪算哪。
 *
 * ⛔ 只点搜索结果行定位节点；不新建、不上传、不删除、不触发生成。
 *
 * 用法：node scripts/jimeng-b238.mjs [档位...]   （读数落盘 /tmp/b238.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const 靶 = { id: 'node_d4tjtpnatq', 名: '时间线 2', 词: ['时间线 2', '时间线'] };
// 批次 243：靶子切到「导演台」(`external` / `320×320` / `z=74`)。
// 📌 目的：批次 235/236 的 `740`–`1235` 是 **20px 步长**，而文本族那条异常带只有 **8px** 宽
//   ⇒ **理论上可能被整段跳过**。批次 242 把这条列成「未测」⇒ 本批改成**每 8px 一档**（`63` 档），
//   **任意 8px 宽的窗口必含至少一个采样点** ⇒ 「无遗漏覆盖」由构造保证，不靠运气。
const 靶导 = { id: 'node_pxvkay973v', 名: '导演台', 词: ['导演台', '导演'] };
const 用导 = process.env.B243 === '1';
// 批次 244：靶子切到「图片 b22-upload」（`image` / `568.875×320` / `z=10`）——
// **图像族是画布上最后一个没量过的族**（批次 236 普查：六种 kind 里 `image` 只有这 1 个节点）。
// 📌 取样按立规 121：带子最宽按文本族的 `8px` 计 ⇒ **每 `8px` 一档**（`600`–`1048`），
//   构造上保证「任意 `8px` 宽窗口必含 ≥1 采样点」⇒ 无遗漏，且比 `1px` 的 `449` 臂省一半。
const 靶图 = { id: 'node_gref4sw056', 名: 'b22-upload', 词: ['b22-upload', 'b22', 'upload'] };
const 用图 = process.env.B244 === '1';
// 批次 245：靶子切到「音频 68」（`audio` / `320×320` / `z=73`）—— 画布上唯一的音频样本之一。
// 📌 目的：音频族是**第四种形状**（指数斜坡、地板 `0.260267`＝画布默认缩放、带宽 `19px`），
//   既不服从 `scale = min(0.5, max(100, w−532)/W)`（公式在 `1212` 给 `2.125`→封顶，实测 `0.260267`），
//   也没有文本族那条 `692`–`699` 的异常带。
// 📌 本批先问一个便宜且决定性的问题：**音频在文本族那条异常带的同一位置（`692`–`699`）有没有带子？**
//   公式预言这三档都应是 `0.5`（因为 `532 + 320/2 = 692` 正是音频的封顶边界）。
//   有 ⇒ 异常带是普遍的、音频还有第二条；没有 ⇒ 音频那处凹口与文本那条**完全不是一回事**。
const 靶音 = { id: 'node_tadm1nyykc', 名: '音频 68', 词: ['音频 68', '音频'] };
const 用音 = process.env.B245 === '1';
// 批次 239：把目标换成「时间线 1」—— 与「时间线 2」同族同尺寸（1200×207 / timeline），
// 但画布坐标迥异（[40.06, 370.5] vs [1282.76, 998.61]）、z-index 也不同（1 vs 20）。
// 📌 目的：验证**族内两个节点是否逐字相同**（批次 238 只测了一个，没验证过族内一致性）。
const 靶1 = { id: 'node_cdwf8x6fbj', 名: '时间线 1', 词: ['时间线 1', '时间线'] };
const 用一 = process.env.B239 === '1';
// 批次 240：靶子切到「文本 3」（`320×320` / `text` / `z=3` / 画布 `[560.055, 319.375]`）。
// 📌 目的：批次 233/229 给它的负结论**只框了上界 `1004`**（「`1004`–`1300` 全封顶」），
//   **下界没框** ⇒ 与 `导演台`（`740`–`1235`）、`时间线`（`632`–`1132`）**精度不一致**。
//   📌 粗扫档位**自宽向窄**，找到第一个「未封顶」就停 —— 这是立规 119 说的「最便宜的路」。
const 靶文 = { id: 'node_5gftn3dnt1', 名: '测试文字样例', 词: ['测试文字样例', '文字样例', '测试'] };
const 用文 = process.env.B240 === '1';
// 批次 240b：靶子切到「文本 1」（`320×320` / `text` / `z=0` / 画布 `[480.055, 240]`），
// 用来判别 `692`–`698` 那条异常带是**文本族共有**还是**只属于「文本 3」这个节点**。
// 📌 侦察修正（`scripts/jimeng-b240b-recon.mjs` 只读实测）：空文本节点**在**搜索索引里，
//    但它们是按**节点名**（`文本 1`）匹配的，**不是**按占位文字「双击编辑文本」——
//    第一版探针用占位文字当词，5 臂全「候选词都没命中」，**差点写成「空文本节点搜不到」这个错结论**。
//    ⇒ 正确做法：搜 `文本`，再按 `data-testid` 挑中目标那一行。
const 靶文1 = { id: 'node_3bfb9r79qe', 名: '文本 1', 词: ['文本'] };
const 用文1 = process.env.B240B === '1';
// ⚠️ 声明顺序有讲究：`用一` / `靶节点` / `OUT` 都必须在**被用到之前** const，
//    否则是 TDZ（暂时性死区）运行期报错 —— 批次 239 第一版就踩了这个。
const 靶节点 = 用音 ? 靶音 : (用图 ? 靶图 : (用导 ? 靶导 : (用文1 ? 靶文1 : (用文 ? 靶文 : (用一 ? 靶1 : 靶)))));
const OUT = 用音 ? '/tmp/b245.json' : (用图 ? '/tmp/b244.json' : (用导 ? '/tmp/b243.json' : (用文1 ? '/tmp/b240b.json' : (用文 ? '/tmp/b240.json' : (用一 ? '/tmp/b239.json' : '/tmp/b238.json')))));
/** 与批次 235/236 的 `导演台` 负结论**用同一组档位**，两条才能直接对比。 */
const 默认档位 = [1235, 1215, 1200, 1180, 1160, 1140, 1120, 1100, 1080, 1060, 1040, 1020, 1000, 960, 920,
  900, 860, 820, 780, 740];
const 档位 = process.argv.slice(2).map(Number).filter((n) => Number.isFinite(n) && n > 0);
const 要跑 = 档位.length ? 档位 : 默认档位;
const 封顶 = 0.5;
const 封顶容差 = 1e-4;

const log = (...a) => console.log(a.join(' '));
const out = fs.existsSync(OUT) ? JSON.parse(fs.readFileSync(OUT, 'utf8')) : { 轮次: 用音 ? 'b245' : (用图 ? 'b244' : (用导 ? 'b243' : (用文1 ? 'b240b' : (用文 ? 'b240' : (用一 ? 'b239' : 'b238'))))), 靶: 靶节点.名, 臂: [] };
const 存 = () => fs.writeFileSync(OUT, JSON.stringify(out, null, 1));

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

async function 一臂(p, w) {
  await p.setViewportSize({ width: w, height: 720 });
  await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(4500);

  const 钮 = await p.evaluate(() => {
    const e = Array.from(document.querySelectorAll('button, [role="button"]'))
      .find((x) => (x.getAttribute('aria-label') || '') === '搜索');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
  });
  if (!钮) throw new Error('找不到搜索钮');
  await p.mouse.click(钮[0] + Math.round(钮[2] / 2), 钮[1] + Math.round(钮[3] / 2));
  await p.waitForTimeout(1500);
  const 有框 = await p.evaluate(() => {
    const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
    if (!inp) return false;
    inp.focus(); inp.select();
    return true;
  });
  if (!有框) throw new Error('找不到搜索输入框');

  const 短名 = 靶节点.id.replace(/^node_/, '');
  let 点 = null;
  for (const 词 of 靶节点.词) {
    await p.evaluate(() => {
      const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
      if (inp) { inp.focus(); inp.select(); }
    });
    await p.keyboard.type(词, { delay: 85 });
    await p.waitForTimeout(2200);
    const 读 = await p.evaluate((nid) => {
      const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
      const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
      return { 回读: inp ? inp.value : null, 有行: !!e };
    }, 短名);
    if (读.有行 && 读.回读 === 词) {
      点 = await p.evaluate((nid) => {
        const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
        if (!e) return null;
        const r = e.getBoundingClientRect();
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      }, 短名);
      if (点) { await p.mouse.click(点[0], 点[1]); await p.waitForTimeout(5000); break; }
    }
  }
  if (!点) throw new Error('候选词都没命中那一行');
  await p.keyboard.press('Escape');
  await p.waitForTimeout(600);
  await p.keyboard.press('Escape');
  await p.waitForTimeout(900);

  return await p.evaluate((nid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
    const vp = document.querySelector('.react-flow__viewport');
    const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
    const zbtn = document.querySelector('[data-testid="canvas-zoom-percent"]');
    const nr = n ? n.getBoundingClientRect() : null;
    return {
      scale: m ? Number(m[1]) : null,
      缩放按钮aria: zbtn ? zbtn.getAttribute('aria-label') : null,
      节点屏上: nr ? [Math.round(nr.width), Math.round(nr.height)] : null,
      节点中心: nr ? [Math.round(nr.x + nr.width / 2), Math.round(nr.y + nr.height / 2)] : null,
      状态行: (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null,
      innerW: window.innerWidth,
      URL没变: location.href.includes('/ai-canvas/'),
    };
  }, 靶节点.id);
}

for (const w of 要跑) {
  if (out.臂.some((r) => r.w === w)) { log(`【w=${w}】已跑过，跳过`); continue; }
  const p = await ctx.newPage();
  try {
    const 读 = await 一臂(p, w);
    const 封顶了 = 读.scale !== null && Math.abs(读.scale - 封顶) < 封顶容差;
    out.臂.push({ w, ...读, 封顶了 });
    log(`【w=${w}】落点 ${读.scale} ⇒ ${封顶了 ? '封顶 0.5' : '未封顶'}｜ 按钮 ${读.缩放按钮aria} ｜ 中心 ${JSON.stringify(读.节点中心)} ｜ 屏上 ${JSON.stringify(读.节点屏上)}`);
    if (!读.URL没变) log('   ⚠️ URL 已离开画布页');
  } catch (e) {
    out.臂.push({ w, 错误: e.message });
    log(`🔴 w=${w} ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
  }
  存();
  // 📌 只有跑**默认档位**（粗扫找边界）才在遇到未封顶时停；
  //   显式传档位 = 二分/定点复测，**不许早停**，否则后面几档永远跑不到。
  if (!档位.length && out.臂[out.臂.length - 1].封顶了 === false) {
    log('⇒ 出现未封顶 ⇒ 凹口存在，负结论不成立，停止粗扫');
    break;
  }
}

const 好的 = out.臂.filter((r) => r.scale !== null);
const 全封顶 = 好的.length > 0 && 好的.every((r) => r.封顶了);
if (全封顶) {
  const ws = 好的.map((r) => r.w);
  out.结论 = {
    负结论成立: true,
    实测区间: [Math.min(...ws), Math.max(...ws)],
    臂数: 好的.length,
    声明: `在 ${Math.min(...ws)}–${Math.max(...ws)} 实测区间内全封顶 0.5；更窄的宽度未测`,
  };
  log('⇒ ' + JSON.stringify(out.结论));
} else {
  const 未 = 好的.filter((r) => !r.封顶了).map((r) => r.w);
  out.结论 = { 负结论不成立: true, 未封顶档位: 未 };
  log('⇒ ' + JSON.stringify(out.结论));
}
存();
log('写入 ' + OUT);
await b.close();
