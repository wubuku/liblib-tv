// 批次 160-f —— 钉死「导演台 + F」：先确认**选中的确实是导演台那个节点 id**，再按 F
//
// 🔴 160-e 连续踩了三个坑，这一轮逐个补上：
//   ① `[data-testid="node-toolbar"]` 命中的是**底部 dock 的音频生成面板**
//      （按钮逐字「创作类型: 音频生成 / 选择模型: SeedAudio 1.0 / 音色: 音色库 / 生成」），
//      且 `closest('.react-flow__node')` 读出 **null** ⇒ 它**不属于任何节点**。
//      ⇒ 差点把它当成导演台的浮动工具条，写出「手册说无工具条是错的」这种**反向错误结论**。
//      📌 立规 31：**读到 testid 先确认它属于谁** —— 用 `closest()` 验归属，
//        并把内容列出来对一眼，不要只看「有没有这个东西」。
//   ② `跳走` 的判据错了：拿 `按F前`（**没有 URL 字段**）去比每帧 URL ⇒ 恒为 true。
//      ⇒ 必须显式存一份 `按F前URL`。
//   ③ 只数了「选中数 = 1」，**没数选中的是哪一个** —— 于是点中的可能是压在上面的音频节点。
//      ⇒ 本轮断言 `selected` 的 `data-id` **等于**导演台的 id。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf } from './jimeng-b139-lib.mjs';

const rec = { 批次: '160f', 目的: '确认选中的是导演台节点本身，再判 F 是否导航' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b160f.json', import.meta.url), JSON.stringify(rec, null, 1));
const 出图 = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const 画布URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';

const { b, p } = await openCanvas();
const R = readers(p);
const 读节点 = (id) => p.evaluate((i) => {
  const n = document.querySelector('.react-flow__node[data-id="' + i + '"]');
  if (!n) return null;
  const r = n.getBoundingClientRect();
  return { 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
    中心在屏: r.x + r.width / 2 > 40 && r.x + r.width / 2 < innerWidth - 40 && r.y + r.height / 2 > 40 && r.y + r.height / 2 < innerHeight - 40 };
}, id);
const 工具态 = () => p.evaluate(() => { const t = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]'); if (!t) return null;
  const r = t.getBoundingClientRect(); return { aria: t.getAttribute('aria-label'), 落点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; });
const 切抓手 = async () => { const t = await 工具态(); if (t && !/抓手/.test(t.aria || '')) { await p.mouse.click(t.落点[0], t.落点[1]); await p.waitForTimeout(800); } };
const 切选择 = async () => { const t = await 工具态(); if (t && !/选择/.test(t.aria || '')) { await p.mouse.click(t.落点[0], t.落点[1]); await p.waitForTimeout(800); } };
const 选中的是谁 = () => p.evaluate(() => { const n = document.querySelector('.react-flow__node.selected');
  return n ? { id: n.getAttribute('data-id'), 逐字: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 70) } : null; });
const 清选中 = async () => { for (let k = 0; k < 3; k++) { if (await selCount(p) === 0) return true;
  const e = await p.evaluate(() => { const pane = document.querySelector('.react-flow__pane'); if (!pane) return null; const r = pane.getBoundingClientRect();
    for (const pt of [[r.x + 8, r.y + r.height - 8], [r.x + 12, r.y + 12]]) if (!document.elementFromPoint(pt[0], pt[1])?.closest('.react-flow__node')) return pt;
    return null; });
  if (e) { await p.mouse.click(e[0], e[1]); await p.waitForTimeout(800); } } return (await selCount(p)) === 0; };

try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1000);
  const 建前 = await idsOf(p);
  rec.起点 = { 状态行: await R.status(), 节点数: 建前.length, 选中: await selCount(p), 积分: await R.credits() };
  rec.进场时选中的是谁 = await 选中的是谁();
  console.log('起点', JSON.stringify(rec.起点), '| 进场选中 =', JSON.stringify(rec.进场时选中的是谁));
  await 清选中();
  落盘();

  const 候选 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => ({
    id: n.getAttribute('data-id'), 逐字: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40) })).filter((z) => /导演台/.test(z.逐字)));
  const SELF = 候选[0]?.id || null;
  rec.SELF = SELF;
  断言('⓪ 画布上有且只有一个「导演台」节点', 候选.length === 1, { 候选 });

  if (SELF) {
    // ---- ① 平移到中心在视口内，且**四周留白**（避免压着别的节点）----
    await 切抓手();
    rec.平移 = [];
    for (let k = 0; k < 8; k++) {
      const cur = await 读节点(SELF);
      if (cur && cur.中心在屏) { rec.平移.push({ 轮: k, 中心: cur.中心, 注: '已在视口内' }); break; }
      const dx = Math.round(640 - cur.中心[0]), dy = Math.round(360 - cur.中心[1]);
      const 起 = [1150, 660], 终 = [Math.min(1272, 起[0] + dx), Math.min(712, 起[1] + dy)];
      if (终[0] === 起[0] && 终[1] === 起[1]) break;
      await p.mouse.move(起[0], 起[1]); await p.mouse.down(); await p.mouse.move(终[0], 终[1], { steps: 12 }); await p.mouse.up();
      await p.waitForTimeout(1100);
    }
    await 切选择();
    const 到位 = await 读节点(SELF);
    落盘();
    断言('① 节点中心已进视口', !!到位 && 到位.中心在屏, 到位);

    // ---- ② 找一个**压不到别的节点**的落点 ----
    const 落点搜索 = await p.evaluate((id) => {
      const n = document.querySelector('.react-flow__node[data-id="' + id + '"]'); if (!n) return null;
      const r = n.getBoundingClientRect();
      const 候选点 = [];
      for (let fx = 0.2; fx <= 0.81; fx += 0.1) for (let fy = 0.2; fy <= 0.81; fy += 0.1) {
        const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
        if (x < 8 || y < 8 || x > innerWidth - 8 || y > innerHeight - 8) continue;
        const hit = document.elementFromPoint(x, y)?.closest('.react-flow__node');
        候选点.push({ 点: [x, y], 命中id: hit ? hit.getAttribute('data-id') : null, 是本节点: hit ? hit.getAttribute('data-id') === id : false });
      }
      return { 节点盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)], 候选点,
        可用落点: 候选点.filter((z) => z.是本节点).slice(0, 6), 被别的节点挡住的点数: 候选点.filter((z) => !z.是本节点).length };
    }, SELF);
    rec.落点搜索 = 落点搜索;
    console.log('落点搜索 =', JSON.stringify({ 节点盒: 落点搜索?.节点盒, 可用: 落点搜索?.可用落点?.length, 被挡: 落点搜索?.被别的节点挡住的点数 }));
    落盘();
    断言('② 导演台节点上找得到**不被别的节点遮挡**的落点', (落点搜索?.可用落点?.length || 0) > 0, { 可用: 落点搜索?.可用落点?.length, 被挡: 落点搜索?.被别的节点挡住的点数 });

    const 用 = 落点搜索?.可用落点?.[0];
    if (用) {
      await p.mouse.click(用.点[0], 用.点[1]);
      await p.waitForTimeout(1900);
      rec.点的是 = 用.点;
      rec.点后选中 = await 选中的是谁();
      rec.点后选中数 = await selCount(p);
      console.log('点后选中 =', JSON.stringify(rec.点后选中));
      落盘();
      断言('③ **选中的就是导演台这个 id**（不是压在上面的音频节点）', rec.点后选中?.id === SELF, { 期望: SELF, 实际: rec.点后选中 });

      if (rec.点后选中?.id === SELF) {
        // ---- ④ 此时读工具条，并验归属 ----
        rec.选中后工具条 = await p.evaluate((id) => {
          const t = document.querySelector('[data-testid="node-toolbar"]');
          if (!t) return { 有: false };
          const r = t.getBoundingClientRect();
          const 挂 = t.closest('.react-flow__node');
          return { 有: true, 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
            挂在节点id: 挂 ? 挂.getAttribute('data-id') : null, 是本节点: 挂 ? 挂.getAttribute('data-id') === id : false,
            父testid: t.parentElement?.getAttribute('data-testid') || null,
            按钮数: t.querySelectorAll('button,[role=button]').length,
            前六个按钮aria: Array.from(t.querySelectorAll('button,[role=button]')).slice(0, 6).map((e) => e.getAttribute('aria-label')),
            逐字: (t.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120) };
        }, SELF);
        console.log('选中后工具条 =', JSON.stringify(rec.选中后工具条).slice(0, 600));
        落盘();
        rec.工具条属于本节点 = rec.选中后工具条.是本节点 === true;

        // ---- ⑤ 按 F，显式存基线 URL，密集采样 ----
        const 取景 = async () => p.evaluate((id) => {
          const n = document.querySelector('.react-flow__node[data-id="' + id + '"]');
          const 对话 = Array.from(document.querySelectorAll('[role=dialog]')).map((d) => (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 50));
          return { 节点逐字: n ? (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 100) : null,
            选中数: document.querySelectorAll('.react-flow__node.selected').length,
            开浮层: document.querySelectorAll('[data-state=open]').length, 对话框: 对话,
            不可用提示: Array.from(document.querySelectorAll('div')).filter((d) => d.children.length === 0 && /此快捷键当前不可用/.test(d.innerText || '')).length,
            工具条在: !!document.querySelector('[data-testid="node-toolbar"]'),
            全局元素: document.querySelectorAll('body *').length };
        }, SELF);
        rec.按F前URL = p.url();
        rec.按F前 = await 取景();
        rec.采样 = [];
        await p.keyboard.press('f');
        for (let i = 0; i < 16; i++) {
          await p.waitForTimeout(300);
          const s = await 取景(); s.毫秒 = (i + 1) * 300; s.URL = p.url();
          rec.采样.push(s);
        }
        rec.跳走 = rec.采样.some((z) => z.URL !== rec.按F前URL);
        rec.有变化的帧 = rec.采样.filter((s) => s.节点逐字 !== rec.按F前.节点逐字 || s.开浮层 !== rec.按F前.开浮层
          || s.对话框.length !== rec.按F前.对话框.length || s.不可用提示 !== rec.按F前.不可用提示
          || s.工具条在 !== rec.按F前.工具条在 || s.全局元素 !== rec.按F前.全局元素
          || s.选中数 !== rec.按F前.选中数).map((s) => ({ 毫秒: s.毫秒, 节点逐字: s.节点逐字, 开浮层: s.开浮层 }));
        rec.结论 = {
          按F前: rec.按F前,
          URL全程相同: [...new Set(rec.采样.map((s) => s.URL))].length === 1,
          跳走: rec.跳走,
          有变化的帧数: rec.有变化的帧.length,
          判定: rec.跳走 ? '跳走了' : (rec.有变化的帧.length ? '没跳走但界面变了' : '**完全静默**：URL 不变、节点逐字不变、无对话框、无「不可用」提示、无浮层、全局元素数不变'),
        };
        落盘();
        console.log('结论 =', JSON.stringify(rec.结论, null, 1));
        断言('④ **按 F 完全静默**（URL 不变 ＋ 界面零变化）', !rec.跳走 && rec.有变化的帧.length === 0, rec.结论);

        await p.evaluate((id) => { const n = document.querySelector('.react-flow__node[data-id="' + id + '"]'); if (!n) return false;
          const r = n.getBoundingClientRect(); const ov = document.createElement('div'); ov.id = '__hl__';
          ov.style.cssText = 'position:fixed;pointer-events:none;z-index:2147483647;border:3px solid rgb(255,146,48);border-radius:10px;box-sizing:border-box;left:' + (r.x - 4) + 'px;top:' + (r.y - 4) + 'px;width:' + (r.width + 8) + 'px;height:' + (r.height + 8) + 'px;';
          document.body.appendChild(ov); return true; }, SELF);
        await p.waitForTimeout(600);
        await p.screenshot({ path: new URL('./120-director-f-inert.png', 出图).pathname });
        rec.图 = 'screenshots/120-director-f-inert.png';
        await p.evaluate(() => { const e = document.getElementById('__hl__'); if (e) e.remove(); return true; });
        console.log('🖼 已拍 120');
        落盘();
      }
    }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

try { await 切选择(); } catch (e) {}
try {
  if (p.url() !== 画布URL) { await p.goto(画布URL, { waitUntil: 'domcontentloaded', timeout: 90000 }); await p.waitForTimeout(9000); }
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
} catch (e) {}
rec.清选中成功 = await 清选中();
try {
  const mm = await R.minimap();
  if (!mm || mm.ariaPressed !== 'true') {
    const t = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-display-toggle-minimap"]'); if (!e) return null;
      const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    if (t) { await p.mouse.click(t[0], t[1]); await p.waitForTimeout(1400); }
  }
} catch (e) {}
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(), zoom: await R.zoom(), 积分: await R.credits(), 工具: await 工具态() };
rec.断言全过 = 断言过; 落盘();
console.log('收尾', JSON.stringify(rec.收尾));
断言('⑤ 收尾回到基线：76 / 0 选中 / 0 浮层 / 60% / 选择工具 / 积分不变',
  rec.收尾.节点数 === 76 && rec.收尾.选中 === 0 && rec.收尾.浮层 === 0 && /选择/.test(String(rec.收尾.工具?.aria || '')) && String(rec.收尾.积分) === String(rec.起点.积分),
  { 起点: rec.起点, 收尾: rec.收尾 });
rec.断言全过 = 断言过; 落盘();
console.log('断言全过 =', rec.断言全过);
process.exit(0);
