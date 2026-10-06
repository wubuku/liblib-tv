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
const OUT = '/tmp/b238.json';
const 靶 = { id: 'node_d4tjtpnatq', 名: '时间线 2', 词: ['时间线 2', '时间线'] };
/** 与批次 235/236 的 `导演台` 负结论**用同一组档位**，两条才能直接对比。 */
const 默认档位 = [1235, 1215, 1200, 1180, 1160, 1140, 1120, 1100, 1080, 1060, 1040, 1020, 1000, 960, 920,
  900, 860, 820, 780, 740];
const 档位 = process.argv.slice(2).map(Number).filter((n) => Number.isFinite(n) && n > 0);
const 要跑 = 档位.length ? 档位 : 默认档位;
const 封顶 = 0.5;
const 封顶容差 = 1e-4;

const log = (...a) => console.log(a.join(' '));
const out = fs.existsSync(OUT) ? JSON.parse(fs.readFileSync(OUT, 'utf8')) : { 轮次: 'b238', 靶: 靶.名, 臂: [] };
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

  const 短名 = 靶.id.replace(/^node_/, '');
  let 点 = null;
  for (const 词 of 靶.词) {
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
  }, 靶.id);
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
