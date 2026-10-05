// ⭐⭐⭐⭐⭐ Batch FT-4：量准「图片编辑区」浮层，并修 FT-3 的判据
//
// ⛔ FT-3 的判据错了：它按「innerText 含『上传图片输入文字指令』」筛 div，
//    结果**匹配到了 `<body>`**（框 = `[0,0,1440,810]`），
//    于是「找到编辑区浮层」和「完整落在视口内」两条断言都成了假绿灯。
//    ⭐ 而截图里浮层明明在 x≈-40（被裁了一半）—— **断言与截图直接矛盾**。
//    ⇒ 这是缺陷 474：**断言的判据太宽，命中了祖先节点**。
//
// FT-3 的日志 nonetheless 给出了**本手册从未描述过的完整读数**，逐字：
//   `参考` `标记` `风格`  ← 三枚胶囊按钮（`rounded-full px-2 py-1`）
//   占位：`可直接文字生图，或上传图片输入文字指令对图片进行编辑，如：将背景改为雪夜`
//   参数条：`Lib Image 2.5 Pro`▾ | `16:9 · 标准画质 · 2K · 1张`▾ |
//           `aria=预设`[1043,657] | 无名[1079,657] | 无名[1154,657] | 无名[1194,657] |
//           `⛭`[1274,657] **`disabled:true` + `cursor:not-allowed`** | `⤢`[1278,515]
//   ⭐⭐⭐ **「立即出图」那枚提交键是灰的**（`bg-btn-invert-bg` + `disabled`）
//        —— 这是本手册第一次读到它的禁用态
//   ⭐⭐⭐ 还有一个 `scroll` 出来的读数：`高级设置` 与
//        `智能引用 AutoLink` 两枚 —— ⛔ 手册未记
//
// 本轮把浮层的真实几何量准（用**最小命中**而不是最大命中），
// 并按 x 从大到小试，选一个能让浮层完整落在视口内的节点。
//
// ⛔ 安全边界：不点任何按钮；只选节点、只量、只截图。
import { launch, closePromos, ORIGIN, 断言器, 中心属主 } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const 主画布 = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 证据图: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFT4.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = 断言器(记);

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(主画布, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(14000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);

  const 图节点 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')]
    .map((n) => { const r = n.getBoundingClientRect(); return { id: n.getAttribute('data-id'), 类: (String(n.className).match(/node-([a-z0-9-]+)/) || [, '?'])[1], 框: [r.x, r.y, r.width, r.height] }; })
    .filter((n) => n.类 === 'image' && n.框[2] > 0)
    .sort((a, b) => b.框[0] - a.框[0]));
  记('   图片节点（x 降序）' + JSON.stringify(图节点));

  /** ⭐ 用**最小命中**：只取那个「恰好包住三枚胶囊按钮」的最深 div。 */
  const 量浮层 = async () => page.evaluate(() => {
    const 归 = (s) => (s || '').replace(/\s+/g, ' ').trim();
    const 命中 = [...document.querySelectorAll('div')].filter((el) => {
      const t = 归(el.innerText);
      if (!/^参考\s*标记\s*风格/.test(t)) return false;      // ⭐ 逐字前缀，只认这个浮层
      const r = el.getBoundingClientRect();
      return r.width > 200 && r.height > 80;
    });
    if (!命中.length) return null;
    // ⭐ 取**面积最小**的那个 —— 最大的会是它的祖先（body）
    命中.sort((a, b) => {
      const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
      return (ra.width * ra.height) - (rb.width * rb.height);
    });
    const el = 命中[0];
    const r = el.getBoundingClientRect();
    return {
      框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      class: String(el.className).slice(0, 160),
      父class: String(el.parentElement?.className || '').slice(0, 160),
      祖父class: String(el.parentElement?.parentElement?.className || '').slice(0, 160),
      命中个数: 命中.length,
      全文: 归(el.innerText).slice(0, 300),
      按钮: [...el.querySelectorAll('button,[role="button"]')].map((b) => {
        const br = b.getBoundingClientRect();
        if (!(br.width > 0 && br.height > 0)) return null;
        return {
          文字: 归(b.innerText), aria: b.getAttribute('aria-label') || '',
          框: [Math.round(br.x), Math.round(br.y), Math.round(br.width), Math.round(br.height)],
          禁用: b.disabled === true, cursor: getComputedStyle(b).cursor,
          class: String(b.className || '').slice(0, 70),
        };
      }).filter(Boolean),
    };
  });

  for (const n of 图节点.slice(0, 2)) {
    记(`=== 试节点 ${n.id} 框 ${JSON.stringify(n.框.map(Math.round))} ===`);
    const t = [Math.round(n.框[0] + n.框[2] / 2), Math.round(n.框[1] + 14)];
    await page.mouse.click(t[0], t[1]);
    await page.waitForTimeout(3000);
    const a = await 中心属主(page, n.id);
    断言(!!a && a.属主 === n.id, `${n.id} 中心落点属主就是它自己`, a);

    const 区 = await 量浮层();
    记('   ⭐ 最小命中浮层：' + JSON.stringify(区, null, 1).slice(0, 2200));
    断言(!!区, `选中 ${n.id} 后找得到编辑区浮层（最小命中）`, null);
    if (!区) continue;
    R.读数['浮层_' + n.id] = 区;

    const 完整 = 区.框[0] >= 0 && 区.框[0] + 区.框[2] <= 1440 && 区.框[1] >= 0 && 区.框[1] + 区.框[3] <= 810;
    记(`   完整落在视口内：${完整}（框 ${JSON.stringify(区.框)}）`);
    if (完整) {
      断言(true, `⭐ ${n.id} 的编辑区浮层完整落在视口内`, 区.框);
      R.读数.选中 = n.id;
      R.读数.目标浮层 = 区;
      const clip = { x: Math.max(0, 区.框[0] - 18), y: Math.max(0, 区.框[1] - 18), width: Math.min(1440 - Math.max(0, 区.框[0] - 18), 区.框[2] + 36), height: Math.min(810 - Math.max(0, 区.框[1] - 18), 区.框[3] + 36) };
      await page.screenshot({ path: resolve(EVID, 'ft4-0-图片编辑区浮层.png'), clip });
      R.证据图.push({ 文件: 'ft4-0-图片编辑区浮层.png', clip, 节点: n.id });
      记(`   📷 ft4-0-图片编辑区浮层.png｜裁剪 ${JSON.stringify(clip)}`);
      break;
    } else {
      断言(false, `⛔ ${n.id} 的编辑区浮层被视口裁掉了（框 ${JSON.stringify(区.框)}）—— 换节点`, 区.框);
    }
  }

  记(`断言统计 ${JSON.stringify(断言.统计)}`);
  R.读数.断言 = 断言.统计;
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFT4.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
