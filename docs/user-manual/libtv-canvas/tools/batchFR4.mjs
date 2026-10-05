// ⭐⭐⭐⭐⭐ Batch FR-4：打开视频节点的 **`⤢` 大编辑器**，找 `VideoNodeToolbar`
//
// FR-3 已排除一个假设：**工具条不是 hover 出现的**
//   （悬浮视频节点中部，节点外可点元素 68 → 68，一个都没多）。
//
// FR-2 的两条源码线索指向大编辑器：
//   · 导出名 `FLOATING_TOOLBAR_STYLE`
//   · 同一份导出清单里紧挨着的是 `PauseIcon` `PlayIcon` `ProgressSlider`
//     和一段**音量条**代码（`rgba(0,0,0,0.75)` 圆角小面板 + 竖直滑杆 + 静音按钮）
//   ⭐⭐ 那是一套**播放器**，不是画布卡片 ⇒ 它在 800×600 的大编辑器里。
//
// ⭐⭐ 手册此前只拍过大编辑器里的「参考 / 提示词框 / 底部参数条」三层，
//    **从没逐个枚举过里面的按钮** —— 而源码说那里有 21 个动作。
//
// ⛔ 安全边界：
//   ⛔ 不点大编辑器里任何会消耗积分或改内容的动作
//      （分离音视频 / 人声分离 / 增强 / 抽帧 / 智能续写 / 裁剪 / 抠图 …）
//   ⛔ 菜单**允许点开看结构**（点「⋯」「⌄」这类只开不开的），点菜单项本身才危险
//   ⛔ 不删节点、不按 Delete/Backspace、不改模型
import { launch, closePromos, ORIGIN, 全页文字, 归一, 断言器, 找节点, 中心属主 } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const 主画布 = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 证据图: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFR4.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = 断言器(记);

const 浏览器 = await launch();
const page = 浏览器.page;

const 危险 = ['删除', '确认删除', '分离音视频', '人声分离', '增强', '抽首帧', '抽尾帧', '抽当前帧',
  '智能续写', '续写', '深度图', '字幕擦除', '抠图', '裁剪', '分离', '导出', '保存', '生成'];
async function 扫危险(标签) {
  const 命中 = await page.evaluate((黑) => {
    const 归 = (s) => (s || '').replace(/\s+/g, '');
    return [...document.querySelectorAll('button,[role="button"]')].map((b) => {
      const r = b.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) return null;
      const t = 归(b.innerText) || 归(b.getAttribute('aria-label')) || 归(b.title);
      if (!t || !黑.some((k) => t.includes(归(k)))) return null;
      const cs = getComputedStyle(b);
      return { 文字: t.slice(0, 16), 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 禁用: b.disabled === true, cursor: cs.cursor };
    }).filter(Boolean);
  }, 危险);
  记(`   ⛔ ${标签}：危险按钮 ${命中.length} 枚 ${JSON.stringify(命中).slice(0, 400)}`);
  return 命中;
}

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(主画布, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(14000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);

  // 选重叠最少的视频节点
  const 目标 = await page.evaluate(() => {
    const ns = [...document.querySelectorAll('.react-flow__node')]
      .map((n) => { const r = n.getBoundingClientRect(); return { id: n.getAttribute('data-id'), 类: (String(n.className).match(/node-([a-z0-9-]+)/) || [, '?'])[1], 框: [r.x, r.y, r.width, r.height] }; })
      .filter((n) => n.框[2] > 0 && n.框[3] > 0);
    const 视频 = ns.filter((n) => n.类 === 'video');
    const 算 = (a) => ns.filter((b) => {
      if (b.id === a.id) return false;
      const ox = Math.min(a.框[0] + a.框[2], b.框[0] + b.框[2]) - Math.max(a.框[0], b.框[0]);
      const oy = Math.min(a.框[1] + a.框[3], b.框[1] + b.框[3]) - Math.max(a.框[1], b.框[1]);
      return ox > 0 && oy > 0;
    }).length;
    return 视频.map((v) => ({ ...v, 重叠数: 算(v) })).sort((a, b) => a.重叠数 - b.重叠数)[0] || null;
  });
  记('   目标视频节点 ' + JSON.stringify(目标));
  断言(!!目标, '有一个重叠最少的视频节点', 目标);

  // 点标题栏选中（缺陷 463：不点中心，中心可能被别的节点吃掉）
  const t = await page.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    const r = n.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + 14)];
  }, 目标.id);
  await page.mouse.click(t[0], t[1]);
  await page.waitForTimeout(2500);
  const a = await 中心属主(page, 目标.id);
  记('   选中后中心落点自证 ' + JSON.stringify(a));
  断言(!!a && a.属主 === 目标.id, `视频节点(${目标.id}) 中心落点属主就是它自己`, a);

  // ── 打开大编辑器（`⤢`）
  记('=== 打开 ⤢ 大编辑器 ===');
  const 放大 = await page.evaluate(() => {
    // ⛔ 用**绝对锚点**找参数条（y 600~800），别用「相对某个会变的框」
    for (const b of document.querySelectorAll('button,[role="button"]')) {
      const r = b.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) continue;
      if (!(r.top > 560 && r.top < 810)) continue;
      const cs = getComputedStyle(b);
      if (cs.cursor === 'not-allowed' || b.disabled) continue;
      // ⤢ 展开箭头的 class 形如 `absolute right-0.5 top-0.5 z-20 flex size-[15px]`
      const c = String(b.className || '');
      if (/size-\[15px\]|right-0\.5/.test(c)) {
        return { class: c.slice(0, 90), 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
      }
    }
    return null;
  });
  记('   ⤢ 落点 ' + JSON.stringify(放大));
  if (放大) {
    await page.mouse.move(放大.点[0] - 30, 放大.点[1]); await page.waitForTimeout(300);
    await page.mouse.click(放大.点[0], 放大.点[1]);
    await page.waitForTimeout(6000);
  }

  // ── 枚举大编辑器里所有可点元素
  R.读数.大编辑器按钮 = await page.evaluate(() => {
    const 归 = (s) => (s || '').replace(/\s+/g, ' ').trim();
    return [...document.querySelectorAll('button,[role="button"]')].map((b) => {
      const r = b.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) return null;
      const n = b.closest('.react-flow__node');
      const cs = getComputedStyle(b);
      return {
        文字: 归(b.innerText),
        aria: b.getAttribute('aria-label') || '',
        title: b.getAttribute('title') || '',
        框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
        在节点内: !!n,
        禁用: b.disabled === true, cursor: cs.cursor, opacity: Number(cs.opacity).toFixed(2),
        class: String(b.className || '').slice(0, 80),
      };
    }).filter(Boolean);
  });
  const 在浮层 = R.读数.大编辑器按钮.filter((b) => !b.在节点内);
  记(`   ⭐ 全页可点元素 ${R.读数.大编辑器按钮.length} 个，其中**不在节点内**的 ${在浮层.length} 个`);
  在浮层.forEach((b, i) => 记(`   [${i}] ${JSON.stringify(b)}`));

  // ⭐⭐ 对账源码里的 21 个动作
  const 源码动作 = ['下载', '裁剪', '增强', '分离音视频', '人声分离', '展开', '智能续写', '字幕擦除',
    '图片编辑', '抠图', '分镜拆解', '开场', '深度图', '抽首帧', '抽尾帧', '抽当前帧', '评分', '片段重剪', '片段截取'];
  R.读数.对账 = {};
  for (const w of 源码动作) {
    const 命中 = 在浮层.filter((b) => [b.文字, b.aria, b.title].some((s) => s && s.includes(w)));
    if (命中.length) R.读数.对账[w] = 命中.map((b) => b.框);
  }
  记('   ⭐ 源码里 19 个动作，在大编辑器里对上的：' + JSON.stringify(R.读数.对账, null, 1));
  断言(Object.keys(R.读数.对账).length > 0, '大编辑器里对上了至少一个源码动作', Object.keys(R.读数.对账));

  await 扫危险('大编辑器打开后');
  await page.screenshot({ path: resolve(EVID, 'fr4-0-视频节点大编辑器.png') });
  R.证据图.push({ 文件: 'fr4-0-视频节点大编辑器.png' });
  记('   📷 fr4-0-视频节点大编辑器.png');

  记(`断言统计 ${JSON.stringify(断言.统计)}`);
  R.读数.断言 = 断言.统计;
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFR4.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
