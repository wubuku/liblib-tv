// 批次 196 e 轮：确认批次 195 的两条素材**到底删掉没有** —— 找对地方再看。
//
// 已知（d 轮）：`<文件名>: Upload complete` 挂在 **`DIV[role=status]`** 里，
//   屏上 `[-1,-1,1,1]` ⇒ 那是 ARIA 实时播报区，**不是素材列表**。
//   所以「在页面上抓到那串字」根本不构成「素材还在」的证据。
//
// 📌 要判断「素材还在不在」，得去**它应该待的地方**找。本轮两处都查：
//   ① 左栏「上传」入口点开后会露出什么（上传队列/历史？）
//   ② 资产库 dialog 的**每一级页签**（这次逐级点进去，不停在「主体」上——
//      b 轮就是因为没先点第一级，第二级页签全部无效，16 个时点全读到「主体」的文本）
//
// 收尾：若确认素材还在，顺手走通「删除素材」这条手册从未写过的路径。
import fs from 'node:fs';
import { openCanvas, readers, settle, endState } from './jimeng-b135-lib.mjs';

const MINE = ['jimeng-b195-test', 'jimeng-b195b-test', 'jimeng-b196-probe'];
const { b, p } = await openCanvas();
const R = readers(p);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
await settle(p, R);
const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b196e', 找的: MINE };

const 点左栏 = async (名字) => {
  const s = await p.evaluate((n) => { const e = Array.from(document.querySelectorAll('button'))
    .find((x) => (x.getAttribute('aria-label') || '') === n && x.getBoundingClientRect().width > 0);
    if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 名字);
  if (!s) return null; await p.mouse.click(s[0], s[1]); await p.waitForTimeout(2000); return s;
};

// ===== ① 点「上传」入口 =====
out.点上传后 = await 点左栏('上传');
out.上传后面板 = await p.evaluate((ns) => {
  const 浮 = Array.from(document.querySelectorAll('[role="dialog"],[role="menu"],[role="listbox"]')).filter((e) => e.getBoundingClientRect().width > 1);
  return { 浮层数: 浮.length,
    浮层: 浮.map((e) => ({ role: e.getAttribute('role'), testid: e.getAttribute('data-testid'),
      屏上: [e.getBoundingClientRect().x, e.getBoundingClientRect().y, e.getBoundingClientRect().width, e.getBoundingClientRect().height].map(Math.round),
      文本: e.innerText.replace(/\s+/g, ' ').trim().slice(0, 300) })),
    命中我的: ns.filter((x) => (document.body.innerText || '').includes(x)),
    body有我的: ns.filter((x) => (document.body.innerText || '').includes(x)) };
}, MINE);
log('点「上传」后：', JSON.stringify(out.上传后面板, null, 1));
await p.keyboard.press('Escape'); await p.waitForTimeout(1200);

// ===== ② 资产库：先点第一级「资产」，再逐个点第二级 =====
await 点左栏('资产库');
out.资产库_首屏 = await p.evaluate(() => { const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]');
  return d ? d.innerText.replace(/\s+/g, ' ').trim().slice(0, 300) : null; });
log('资产库首屏：', out.资产库_首屏);

const 一级 = await p.evaluate(() => { const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]'); if (!d) return [];
  return Array.from(d.querySelectorAll('button,[role="tab"]')).map((e) => { const r = e.getBoundingClientRect();
    return { 文字: (e.getAttribute('aria-label') || e.innerText || '').trim(), 屏上: [r.x, r.y, r.width, r.height].map(Math.round) }; })
    .filter((x) => ['资产', '主体'].includes(x.文字)); });
log('一级页签：', JSON.stringify(一级));
const 资产一级 = 一级.find((x) => x.文字 === '资产');
if (资产一级) { await p.mouse.click(资产一级.屏上[0] + 资产一级.屏上[2] / 2, 资产一级.屏上[1] + 资产一级.屏上[3] / 2); await p.waitForTimeout(1500); }
out.点资产一级后 = await p.evaluate(() => { const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]');
  return d ? d.innerText.replace(/\s+/g, ' ').trim().slice(0, 300) : null; });
log('点「资产」一级后：', out.点资产一级后);

const 二级 = await p.evaluate(() => { const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]'); if (!d) return [];
  return Array.from(d.querySelectorAll('button,[role="tab"]')).map((e) => { const r = e.getBoundingClientRect();
    return { 文字: (e.getAttribute('aria-label') || e.innerText || '').trim(), 屏上: [r.x, r.y, r.width, r.height].map(Math.round) }; })
    .filter((x) => ['图片', '视频', '音频', '文档', '时间'].includes(x.文字) && x.屏上[2] > 8 && x.屏上[3] > 8); });
log('二级页签：', JSON.stringify(二级));

out.逐个二级页签 = {};
for (const t of 二级) {
  await p.mouse.click(t.屏上[0] + t.屏上[2] / 2, t.屏上[1] + t.屏上[3] / 2); await p.waitForTimeout(1400);
  const r = await p.evaluate((ns) => { const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]'); if (!d) return null;
    const t = d.innerText.replace(/\s+/g, ' ');
    return { 空态: (t.match(/暂无[^ ]*素材|没有可用[^ ]*/) || [])[0] || null,
      命中我的: ns.filter((x) => t.includes(x)), img: d.querySelectorAll('img').length, video: d.querySelectorAll('video').length,
      文本: t.slice(0, 220) }; }, MINE);
  out.逐个二级页签[t.文字] = r;
  log(`  「${t.文字}」：`, JSON.stringify(r));
}
await p.keyboard.press('Escape'); await p.waitForTimeout(1000);

fs.writeFileSync('/tmp/b196e.json', JSON.stringify(out, null, 1));
out.收尾 = await endState(p, R, 基线);
log('收尾：', JSON.stringify(out.收尾));
await b.close();
