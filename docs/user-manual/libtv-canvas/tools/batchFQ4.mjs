// ⭐⭐⭐⭐⭐ Batch FQ-4：修缺陷 463 重拍 —— FQ-3 拍出来是「张冠李戴」
//
// ⛔ FQ-3 的教训（缺陷 463，新立）：
//   我按「节点框 [721,403,345,345]」裁图，文件名写「脚本V2节点」，
//   结果**拍到的是智能剪辑节点** —— 因为
//     脚本 V2 节点  [721,403,345,345]
//     智能剪辑节点    [626,391,345,345]   ← 两者大面积重叠
//   且**被选中节点的 z-index = 1000**（未选中时没有 z）⇒ 它盖在别人上面。
//   ⇒ ⭐⭐⭐ **「框对了」不等于「拍到的是它」**。
//     与缺陷 449 同源（落点被浮层盖住），但这次盖住的是**另一个节点**。
//
// 本轮的修法（三条硬判据，拍前必过）：
//   ① 先用**产品自带的「整理画布」+「保留」**把重叠的节点错开
//      —— 这是画布复原铁律里三个合法入口之一，⛔ 不用拖拽硬挪
//   ② 点**节点标题栏**（不是按钮）来选中，⭐ 选中后才拍（选中 = 置顶 + 展开编辑区）
//   ③ ⭐ 拍前必验 `elementFromPoint(节点中心)` 的 `closest('.react-flow__node')`
//      **就是目标 id** —— 不通过就重拍，绝不将就
//
// ⛔ 安全边界：同 FQ-3，一个生成按钮都不点。
import { launch, closePromos, ORIGIN, 全页文字, 归一, 断言器, 量浮层 } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const 测试画布 = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=a4ef3de0cdca4977ba45b373eb5165b5`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 证据图: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFQ4.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = 断言器(记);

const 浏览器 = await launch();
const page = 浏览器.page;

/** ⭐ 节点中心点的落点属主（缺陷 463 的治法）。 */
async function 中心属主(id) {
  return page.evaluate((tid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${tid}"]`);
    if (!n) return null;
    const r = n.getBoundingClientRect();
    const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
    const hit = document.elementFromPoint(cx, cy);
    const owner = hit && hit.closest('.react-flow__node');
    return {
      中心: [cx, cy],
      框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      属主: owner ? owner.getAttribute('data-id') : null,
      属主类: owner ? String(owner.className).slice(0, 70) : null,
    };
  }, id);
}

/** 拍一个节点：先验属主，再拍。验不过就重拍，绝不将就。 */
async function 拍(类型, 文件, { 选 = true, 余量 = 26 } = {}) {
  const id = await page.evaluate((t) => {
    const n = [...document.querySelectorAll('.react-flow__node')].find((e) => String(e.className).includes(t));
    return n ? n.getAttribute('data-id') : null;
  }, 类型);
  if (!id) { 记('   ⛔ 找不到节点类型 ' + 类型); return null; }

  if (选) {
    // ⭐ 点**标题栏**（节点顶部 28px，那儿没有按钮）来选中
    const t = await page.evaluate((tid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${tid}"]`);
      const r = n.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + 14)];
    }, id);
    await page.mouse.click(t[0], t[1]);
    await page.waitForTimeout(2200);
  }

  const a = await 中心属主(id);
  记(`   中心落点自证 ${JSON.stringify(a)}`);
  const ok = 断言(!!a && a.属主 === id, `「${类型}」(${id}) 的中心落点属主就是它自己`, a);
  if (!ok) return { 失败: true, a };

  const clip = {
    x: Math.max(0, a.框[0] - 余量), y: Math.max(0, a.框[1] - 余量),
    width: Math.min(1440 - Math.max(0, a.框[0] - 余量), a.框[2] + 余量 * 2),
    height: Math.min(810 - Math.max(0, a.框[1] - 余量), a.框[3] + 余量 * 2),
  };
  await page.screenshot({ path: resolve(EVID, 文件), clip });
  R.证据图.push({ 文件, 节点id: id, clip });
  记(`   📷 ${文件}｜id ${id}｜裁剪 ${JSON.stringify(clip)}`);

  // 顺便把节点全文与可点元素读出来
  const 内 = await page.evaluate((tid) => {
    const 归 = (s) => (s || '').replace(/\s+/g, ' ');
    const n = document.querySelector(`.react-flow__node[data-id="${tid}"]`);
    if (!n) return null;
    const r = n.getBoundingClientRect();
    const 点 = [...n.querySelectorAll('button,[role="button"],[role="tab"],input,textarea,select')].map((b) => {
      const br = b.getBoundingClientRect();
      if (!(br.width > 0 && br.height > 0)) return null;
      const cs = getComputedStyle(b);
      return {
        文字: 归(b.innerText) || 归(b.getAttribute('aria-label')) || 归(b.title) || 归(b.placeholder) || '',
        框: [Math.round(br.x), Math.round(br.y), Math.round(br.width), Math.round(br.height)],
        禁用: b.disabled === true, opacity: Number(cs.opacity).toFixed(2), cursor: cs.cursor,
        tag: b.tagName.toLowerCase(),
      };
    }).filter(Boolean);
    return { 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 全文: 归(n.innerText).slice(0, 1200), 可点: 点 };
  }, id);
  return 内;
}

const 危险 = ['批量生成分镜', '批量生视频', '一键合成全部提示词', '重新生成脚本', '批量生成资产图', '确认续写', '下载', '同意并使用', '开始生成', '开始拉片', '立即生成', '提交'];
async function 扫危险(标签) {
  const 命中 = await page.evaluate((黑) => {
    const 归 = (s) => (s || '').replace(/\s+/g, '');
    return [...document.querySelectorAll('button,[role="button"]')].map((b) => {
      const r = b.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) return null;
      const t = 归(b.innerText) || 归(b.getAttribute('aria-label')) || 归(b.title);
      if (!t || !黑.some((k) => t.includes(归(k)))) return null;
      const cs = getComputedStyle(b);
      return { 文字: t.slice(0, 20), 禁用: b.disabled === true, opacity: Number(cs.opacity).toFixed(2), cursor: cs.cursor };
    }).filter(Boolean);
  }, 危险);
  记(`   ⛔ ${标签}：危险按钮 ${命中.length} 枚 ${JSON.stringify(命中)}`);
  return 命中;
}

/** 关掉右侧那个 TV Director Drawer —— ⛔ 里面那枚「开启」是通知授权，绝不点。 */
async function 关抽屉() {
  const c = await page.evaluate(() => {
    const d = document.querySelector('.mantine-Drawer-inner');
    if (!d) return null;
    const r = d.getBoundingClientRect();
    // 找抽屉自己的关闭钮（aria-label 含 Close/关闭），⛔ 排除任何文字是「开启」的
    for (const b of d.querySelectorAll('button,[aria-label]')) {
      const t = (b.getAttribute('aria-label') || b.innerText || '').replace(/\s+/g, '').trim();
      if (/^(关闭|close|×|x)$/i.test(t)) {
        const br = b.getBoundingClientRect();
        if (br.width > 0 && br.height > 0) return { 文字: t, 点: [Math.round(br.x + br.width / 2), Math.round(br.y + br.height / 2)] };
      }
    }
    return { 无关闭钮: true, 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  });
  记('   抽屉关闭钮 ' + JSON.stringify(c));
  if (c && c.点) { await page.mouse.click(c.点[0], c.点[1]); await page.waitForTimeout(1500); }
  const 还在 = await page.evaluate(() => !!document.querySelector('.mantine-Drawer-inner'));
  记('   抽屉还在吗：' + 还在);
  return !还在;
}

try {
  await page.goto(测试画布, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(14000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);

  // ── ① 先量重叠有多严重（这是缺陷 463 的现场证据）
  记('=== ① 重叠检测 ===');
  R.读数.重叠 = await page.evaluate(() => {
    const ns = [...document.querySelectorAll('.react-flow__node')]
      .map((n) => { const r = n.getBoundingClientRect(); return { id: n.getAttribute('data-id'), 类: (String(n.className).match(/node-([a-z0-9-]+)/) || [, '?'])[1], z: getComputedStyle(n).zIndex, 框: [r.x, r.y, r.width, r.height] }; })
      .filter((n) => n.框[2] > 0 && n.框[3] > 0);
    const 重 = [];
    for (let i = 0; i < ns.length; i++) for (let j = i + 1; j < ns.length; j++) {
      const a = ns[i], b = ns[j];
      const ox = Math.min(a.框[0] + a.框[2], b.框[0] + b.框[2]) - Math.max(a.框[0], b.框[0]);
      const oy = Math.min(a.框[1] + a.框[3], b.框[1] + b.框[3]) - Math.max(a.框[1], b.框[1]);
      if (ox > 0 && oy > 0) {
        const 面积比 = (ox * oy) / Math.min(a.框[2] * a.框[3], b.框[2] * b.框[3]);
        if (面积比 > 0.25) 重.push({ a: a.类 + ':' + a.id + `(z=${a.z})`, b: b.类 + ':' + b.id + `(z=${b.z})`, 重叠比: Number(面积比.toFixed(2)) });
      }
    }
    return 重;
  });
  记('   ⭐ 重叠面积 >25% 的节点对：' + JSON.stringify(R.读数.重叠));
  断言(R.读数.重叠.length > 0, '测试画布上确实存在大面积重叠的节点（缺陷 463 的前提成立）', R.读数.重叠);

  // ── ② 用产品自带的「整理画布」错开
  记('=== ② 「整理画布」+「保留」 ===');
  const 整 = await page.evaluate(() => {
    for (const b of document.querySelectorAll('button,[role="button"]')) {
      const t = (b.innerText || b.getAttribute('aria-label') || '').replace(/\s+/g, '').trim();
      if (t !== '整理画布') continue;
      const r = b.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) continue;
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    }
    return null;
  });
  记('   「整理画布」落点 ' + JSON.stringify(整));
  if (整) {
    await page.mouse.click(整[0], 整[1]);
    await page.waitForTimeout(2500);
    const 弹 = await page.evaluate(() => [...document.querySelectorAll('button')].map((b) => (b.innerText || '').replace(/\s+/g, '').trim()).filter((t) => t && t.length <= 6));
    记('   弹窗里的短文案按钮：' + JSON.stringify(弹));
    const 保 = await page.evaluate(() => {
      for (const b of document.querySelectorAll('button,[role="button"]')) {
        const t = (b.innerText || b.getAttribute('aria-label') || '').replace(/\s+/g, '').trim();
        if (t !== '保留') continue;
        const r = b.getBoundingClientRect();
        if (!(r.width > 0 && r.height > 0)) continue;
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      }
      return null;
    });
    记('   「保留」落点 ' + JSON.stringify(保));
    if (保) { await page.mouse.click(保[0], 保[1]); await page.waitForTimeout(4000); }
  }
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);

  R.读数.整理后重叠 = await page.evaluate(() => {
    const ns = [...document.querySelectorAll('.react-flow__node')]
      .map((n) => { const r = n.getBoundingClientRect(); return { id: n.getAttribute('data-id'), 类: (String(n.className).match(/node-([a-z0-9-]+)/) || [, '?'])[1], 框: [r.x, r.y, r.width, r.height] }; })
      .filter((n) => n.框[2] > 0 && n.框[3] > 0);
    const 重 = [];
    for (let i = 0; i < ns.length; i++) for (let j = i + 1; j < ns.length; j++) {
      const a = ns[i], b = ns[j];
      const ox = Math.min(a.框[0] + a.框[2], b.框[0] + b.框[2]) - Math.max(a.框[0], b.框[0]);
      const oy = Math.min(a.框[1] + a.框[3], b.框[1] + b.框[3]) - Math.max(a.框[1], b.框[1]);
      if (ox > 0 && oy > 0 && (ox * oy) / Math.min(a.框[2] * a.框[3], b.框[2] * b.框[3]) > 0.25) 重.push(`${a.类}×${b.类}`);
    }
    return 重;
  });
  记('   整理后重叠：' + JSON.stringify(R.读数.整理后重叠));
  断言(R.读数.整理后重叠.length === 0, '「整理画布」之后没有大面积重叠了', R.读数.整理后重叠);

  await 关抽屉();
  await 扫危险('整理后');

  // ── ③ 逐个拍（选中态）
  记('=== ③ 逐个拍（选中态，含编辑区）===');
  R.读数.脚本V2 = await 拍('node-script-v2', 'fq4-1-脚本V2节点.png');
  记('   脚本 V2 全文 ' + JSON.stringify(R.读数.脚本V2?.全文).slice(0, 400));
  await 扫危险('脚本 V2 拍完');

  R.读数.智能剪辑 = await 拍('node-video-clip', 'fq4-2-智能剪辑节点.png');
  记('   智能剪辑 全文 ' + JSON.stringify(R.读数.智能剪辑?.全文).slice(0, 500));
  await 扫危险('智能剪辑拍完');

  R.读数.逐帧拉片 = await 拍('node-shot-breakdown', 'fq4-3-逐帧拉片节点.png');
  记('   逐帧拉片 全文 ' + JSON.stringify(R.读数.逐帧拉片?.全文).slice(0, 500));
  await 扫危险('逐帧拉片拍完');

  记(`断言统计 ${JSON.stringify(断言.统计)}`);
  R.读数.断言 = 断言.统计;
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFQ4.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
