// 批次 195 k 轮：收尾清理 —— 删掉本批自建的带媒体视频节点，视口复位 26%。
//
// 🔴 护栏：只删 `node_jhe3mm3ayg`（h 轮护栏拿到的上传差集 id），删前删后都比对节点数。
//    素材本身在 /tmp，不入 git；左栏资产库里的两条自建素材**本轮不删**（那是资产库 CRUD，
//    与画布节点分开，且批次 101 的收尾也只删节点）—— 📌 记为待办，不假装清干净了。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';

const SELF = 'node_jhe3mm3ayg';
const { b, p } = await openCanvas();
const R = readers(p);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
await settle(p, R);
const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b195k', 待删: SELF };

out.删前 = { 节点数: 基线.ids.length, 在不在: 基线.ids.includes(SELF), 积分: await R.credits() };
log('删前：', JSON.stringify(out.删前));

if (基线.ids.includes(SELF)) {
  await setZoom(p, 50);
  const pt = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
    const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height * 0.55)]; }, SELF);
  if (pt) {
    await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(1000);
    const 项 = await p.evaluate(() => { const it = Array.from(document.querySelectorAll('[role="menuitem"]')).find((e) => /^删除/.test(e.innerText.trim()));
      if (!it) return null; const r = it.getBoundingClientRect(); return { 文案: it.innerText.trim(), 坐标: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; });
    out.菜单项 = 项;
    if (项) { await p.mouse.click(项.坐标[0], 项.坐标[1]); await p.waitForTimeout(1600); }
    else { await p.keyboard.press('Escape'); out.跳过 = '菜单里没有删除项 ⇒ 不删'; }
  } else out.跳过 = '节点不在屏幕上 ⇒ 不删';
} else out.跳过 = '节点本来就不在';

out.删后 = { 节点数: (await R.ids()).length, 还在不在: (await R.ids()).includes(SELF) };
log('删后：', JSON.stringify(out.删后));
out.断言 = { 判据: '删后节点数 = 删前 - 1 且该 id 已消失', 通过: out.删后.还在不在 === false && out.删后.节点数 === out.删前.节点数 - 1 };
log('断言：', out.断言.通过 ? '✅' : '🔴 ' + JSON.stringify(out.删后));

await setZoom(p, 26);
out.收尾 = await endState(p, R, 基线);
log('收尾：', JSON.stringify(out.收尾));
out.遗留 = '左栏资产库里的 jimeng-b195-test / jimeng-b195b-test 两条自建素材**未删**（本轮只清画布节点）';
log('遗留：', out.遗留);
fs.writeFileSync('/tmp/b195k.json', JSON.stringify(out, null, 1));
await b.close();
