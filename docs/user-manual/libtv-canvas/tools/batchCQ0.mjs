// Batch CQ-0：节点卡片上那一栏「尝试：」—— 手册从头到尾没写过它。
//
// CO 意外撞见的：每张节点卡片上都有一栏 `尝试：`，列着这个节点能被怎么用
// （智能剪辑 4 → 讲解视频/批量广告/口播视频/素材混剪；视频节点 3 → 5分钟超长视频/
// 首尾帧生成视频/首帧生成视频；文本节点 → 自己编写内容/文生视频/图片反推提示词/文字生音乐；
// 图片节点 → 图生图/图片高清；音频节点 → 音频生视频）。
//
// 本步：全量枚举每一张卡片的「尝试」栏 + 认它们是什么元素（tag / class / cursor /
// 尺寸 / 有没有 role）+ 悬停读气泡。
// ⛔ **一个都不点** —— 点下去要么生成（扣积分）、要么改节点设置。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const BASE = ['a-CUfJfmKzUJ', 'a-THmbuJXQj4', 'b-mfkcQNULC3', 'i-9nlG6HdjK2', 'i-sODTbgLUm1', 'n-56F19pXVB4', 't-2AK3Ukyxj3', 't-UtVx3lZmrV', 'v-eMpqKtiLlx', 'v-oZNpH99MtM', 'v-v2hlWY4Br3'];

const boot = async (page) => {
  await open(page, URL_);
  await closePromos(page);
  await page.waitForTimeout(1500);
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2800);
  for (let i = 0; i < 3; i += 1) {
    const d = page.locator('.mantine-Drawer-inner button[aria-label="关闭"]').first();
    if (await d.count()) await d.click({ timeout: 5000 }).catch(() => {});
    await page.waitForTimeout(600);
  }
};
const killPromo = async (page) => {
  const b = await page.evaluate(() => {
    const t = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '下次再说');
    if (!t) return null; const r = t.getBoundingClientRect(); return r.width > 0 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null;
  });
  if (!b) return false;
  await page.mouse.click(b[0], b[1]); await page.waitForTimeout(1200); return true;
};

// ⭐ 全量枚举：每张卡片上「尝试」栏里的每一项，带身份信息
const survey = (page) => page.evaluate(() => {
  const out = [];
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const id = n.getAttribute('data-id');
    const nr = n.getBoundingClientRect();
    if (nr.width === 0) continue;
    // 「尝试」二字所在的那个元素
    let 标 = null;
    for (const e of n.querySelectorAll('*')) {
      if (e.children.length) continue;
      if ((e.innerText || '').replace(/\s+/g, '').includes('尝试')) { 标 = e; break; }
    }
    const 记录 = { id, 卡片rect: [Math.round(nr.x), Math.round(nr.y), Math.round(nr.width), Math.round(nr.height)], 全文: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 90) };
    if (!标) { 记录.有尝试栏 = false; out.push(记录); continue; }
    记录.有尝试栏 = true;
    const sr = 标.getBoundingClientRect();
    记录.标rect = [Math.round(sr.x), Math.round(sr.y), Math.round(sr.width), Math.round(sr.height)];
    记录.标class = (标.className || '').toString().slice(0, 60);
    // 「尝试」栏容器：标往上一级
    let 栏 = 标.parentElement;
    for (let i = 0; i < 4 && 栏 && 栏 !== n; i += 1) 栏 = 栏.parentElement;
    if (栏) {
      const cr = 栏.getBoundingClientRect();
      记录.栏rect = [Math.round(cr.x), Math.round(cr.y), Math.round(cr.width), Math.round(cr.height)];
      记录.栏class = (栏.className || '').toString().slice(0, 70);
      记录.栏overflow = getComputedStyle(栏).overflow;
      记录.栏高度对得上内容 = Math.abs(cr.height - 栏.scrollHeight) < 3;
      记录.项 = [...栏.querySelectorAll('*')].filter((e) => e.children.length === 0 && (e.innerText || '').trim()).map((e) => {
        const r = e.getBoundingClientRect();
        return {
          文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20),
          tag: e.tagName.toLowerCase(), role: e.getAttribute('role'), cursor: getComputedStyle(e).cursor,
          class: (e.className || '').toString().slice(0, 48),
          在视口内: r.width > 0 && r.height > 0 && r.y >= 0 && r.y < 810,
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        };
      });
    }
    out.push(记录);
  }
  return out;
});
// 悬停某一项，读气泡 + 读它有没有变
const probe = (page, x, y) => page.mouse.move(x, y).then(() => page.waitForTimeout(1300)).then(() => page.evaluate(([px, py]) => {
  const el = document.elementFromPoint(px, py);
  if (!el) return { 无: true };
  const s = getComputedStyle(el);
  const r = el.getBoundingClientRect();
  const 链 = [];
  let a = el;
  for (let i = 0; i < 5 && a; i += 1, a = a.parentElement) {
    const st = getComputedStyle(a);
    链.push({ tag: a.tagName.toLowerCase(), cls: (a.className || '').toString().slice(0, 46), cursor: st.cursor, bg: st.backgroundColor, border: st.borderColor });
  }
  // 附近的小浮层文字（气泡）
  const 泡 = [];
  for (const e of document.querySelectorAll('body *')) {
    if (e.children.length) continue;
    const st = getComputedStyle(e); if (st.display === 'none' || +st.opacity === 0 || st.visibility === 'hidden') continue;
    const q = e.getBoundingClientRect(); if (!q.width || !q.height || q.width > 320 || q.height > 90) continue;
    if (Math.abs(q.x + q.width / 2 - px) > 200 || Math.abs(q.y + q.height / 2 - py) > 160) continue;
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (t && t.length <= 22) 泡.push({ 文字: t, rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] });
  }
  return { 文字: (el.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 18), tag: el.tagName.toLowerCase(), cursor: s.cursor, bg: s.backgroundColor, border: s.borderColor, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 链, 气泡: 泡 };
}, [x, y]));

const out = {};
const { browser, page } = await launch();
await boot(page);
out.促销 = await killPromo(page);

out.枚举 = await survey(page);
console.log('=== 每张节点卡片的「尝试」栏 ===');
for (const n of out.枚举) {
  console.log(`\n${n.id}  ${JSON.stringify(n.卡片rect)}  有尝试栏=${n.有尝试栏}`);
  console.log(`  全文：${n.全文}`);
  if (!n.有尝试栏) continue;
  console.log(`  标「${n.标rect}」 class=${n.标class}`);
  console.log(`  栏 ${JSON.stringify(n.栏rect)} class=${n.栏class} overflow=${n.栏overflow} 高度对得上内容=${n.栏高度对得上内容}`);
  for (const it of (n.项 || [])) console.log(`     ${it.在视口内 ? '👁' : '·'} ${JSON.stringify(it.rect)} 「${it.文字}」 <${it.tag}> cursor=${it.cursor} role=${it.role}`);
}
out.有尝试栏的数量 = out.枚举.filter((n) => n.有尝试栏).length;
console.log(`\n⇒ 11 个节点里 ${out.有尝试栏的数量} 个带「尝试」栏`);

// 悬停探针：挑第一个在视口内的项
out.探针 = [];
for (const n of out.枚举) {
  const it = (n.项 || []).find((x) => x.在视口内);
  if (!it) continue;
  const [x, y, w, h] = it.rect;
  const p = await probe(page, x + w / 2, y + h / 2);
  out.探针.push({ 节点: n.id, 项: it.文字, 结果: p });
  console.log(`\n悬停 ${n.id} 的「${it.文字}」→ cursor=${p.cursor} 背景=${p.bg} 气泡=${JSON.stringify(p.气泡).slice(0, 200)}`);
  console.log(`   链: ${JSON.stringify(p.链).slice(0, 300)}`);
  await page.mouse.move(1400, 780);
  await page.waitForTimeout(500);
  if (out.探针.length >= 4) break;
}

// 拍一张「尝试栏」看得清的图
out.图 = 'cq0-节点卡片-尝试栏.png';
const 目标 = out.枚举.find((n) => n.有尝试栏 && (n.项 || []).some((x) => x.在视口内));
if (目标) {
  const [x, y, w, h] = 目标.卡片rect;
  console.log(`\n拍 ${目标.id} 的卡片：${JSON.stringify(目标.卡片rect)}`);
  await page.screenshot({ path: resolve(HERE, '.evidence', out.图), clip: { x: Math.max(0, x - 14), y: Math.max(0, y - 30), width: Math.min(1440 - Math.max(0, x - 14), w + 28), height: Math.min(810 - Math.max(0, y - 30), h + 44) } });
  console.log(`  已拍 ${out.图}`);
}

out.收尾节点 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { id: n.getAttribute('data-id'), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
}));
console.log('\n收尾节点数 =', out.收尾节点.length);
await browser.close();
{
  const { browser: b2, page: p2 } = await launch();
  await boot(p2);
  const r2 = await p2.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
    const r = n.getBoundingClientRect();
    return { id: n.getAttribute('data-id'), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  }));
  out.全新会话 = { 节点: r2.length, id一致: r2.length === BASE.length && BASE.every((x) => r2.some((n) => n.id === x)) };
  console.log('全新会话 节点', r2.length, ' id 一致 =', out.全新会话.id一致);
  await b2.close();
}
await writeFile(resolve(HERE, '.evidence/cq0-try-row.json'), JSON.stringify(out, null, 2));
