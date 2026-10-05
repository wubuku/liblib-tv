// ⭐⭐⭐⭐⭐ Batch FR-3：**去找 `VideoNodeToolbar`（视频节点悬浮工具条）**
//
// FR-2 在生产 bundle 里把「智能续写」的机制挖到底了：
//
//   ① 入口在 **`VideoNodeToolbar`** 这个组件的菜单里。读它的 props 就得到
//      **视频节点悬浮工具条的完整能力清单**（逐字）：
//        downloadOnly, onClipClick, onSegmentRemakeClick, segmentRemakeDisabled,
//        onCropClick, onDownloadClick, onEnhanceClick, onSeparateAvClick,
//        showParse, showEnhance, isCropping, isCropExporting, isSeparatingAv,
//        isVocalSplitting, isDownloading, onExpandClick, onVocalSplitClick,
//        vocalSplitDisabledReason, separateAvDisabledReason,
//        onContinuationClick, continuationDisabled,
//        onSubtitleEraseClick, subtitleEraseDisabledReason, subtitleEraseTooltip,
//        onPictureEditClick, pictureEditDisabledReason, onMattingClick,
//        onShotBreakdownClick, onOpeningClick, openingHasContent,
//        onDepthMapRefClick, depthMapRefDisabledReason,
//        onCaptureFirstFrame, onCaptureLastFrame, onCaptureCurrentFrame, ratingNodeId
//        ⭐⭐⭐ **21 个动作**（本手册此前一个都没见过）
//
//   ② ⭐⭐⭐⭐ 智能续写那一项的渲染条件是 **`onContinuationClick && …`**
//      —— 父组件**不传这个 prop，这一项压根不渲染**。
//      这就是主画布全页（含 opacity:0）读不到「续写」二字的原因：
//      **不是找不到入口，是当前状态下那一项没被传进来。**
//      ⇒ 因此「主画布上没有智能续写」是**正常状态**，不是手册漏了。
//
//   ③ ⭐⭐⭐ 机制：它**不是源视频上的一个模式，而是新建一个续写节点**：
//        planCreateVideoContinuation ⇒ 建 edge(source=源视频, target=新节点)
//        + extension { kind, version:1, sourceNodeId, sourceToTargetEdgeId, range }
//        守卫：三者任一为空就 throw "invalid_video_continuation_range"
//        三个判据：i(sourceDuration) && a(range) && range.endSec <= sourceDuration
//
//   ④ `eC` 菜单里有一项 label = `canvas:nodeTypeShotBreakdown`
//      ⇒ ⭐⭐⭐ **节点的「逐帧拉片」这个类型名就在这里**，
//      印证了「class 名 / featureId / 文案 key 三者对得上」。
//
// 本轮要做的：**把那条工具条在界面上找出来**。
// ⚠️ 关键：FR 之前所有批次都只看到视频节点的「尝试：」三项，
//    ⛔ 从没让鼠标**悬浮**到视频节点上 —— 工具条很可能是悬停才出现的。
//
// ⛔ 安全边界：
//   ⛔ 不点工具条上任何会消耗积分的动作（分离音视频 / 人声分离 / 增强 /
//      抽首帧尾帧 / 深度图 / 智能续写 —— 续写会**新建一个节点 + 一条连线**）
//   ⛔ 不点「删除」/ 不按 Delete/Backspace
//   ✅ 只悬浮、只读 DOM、只截图；菜单**可以点开看结构**（点菜单项本身才危险）
import { launch, closePromos, ORIGIN, 全页文字, 归一, 断言器, 找节点, 中心属主 } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const 主画布 = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 证据图: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFR3.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = 断言器(记);

const 浏览器 = await launch();
const page = 浏览器.page;

const 危险 = ['删除', '确认删除', '分离音视频', '人声分离', '增强', '抽首帧', '抽尾帧', '抽当前帧',
  '智能续写', '续写', '深度图', '字幕擦除', '抠图', '裁剪', '分离', '导出', '保存'];
async function 扫危险(标签) {
  const 命中 = await page.evaluate((黑) => {
    const 归 = (s) => (s || '').replace(/\s+/g, '');
    return [...document.querySelectorAll('button,[role="button"]')].map((b) => {
      const r = b.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) return null;
      const t = 归(b.innerText) || 归(b.getAttribute('aria-label')) || 归(b.title);
      if (!t || !黑.some((k) => t.includes(归(k)))) return null;
      const cs = getComputedStyle(b);
      return { 文字: t.slice(0, 18), 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 禁用: b.disabled === true, cursor: cs.cursor };
    }).filter(Boolean);
  }, 危险);
  记(`   ⛔ ${标签}：危险按钮 ${命中.length} 枚 ${JSON.stringify(命中).slice(0, 500)}`);
  return 命中;
}

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(主画布, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(14000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);

  // 找一个**不与别的节点重叠**的视频节点（缺陷 463：重叠会把点击吃掉）
  const 候选 = await page.evaluate(() => {
    const ns = [...document.querySelectorAll('.react-flow__node')]
      .map((n) => { const r = n.getBoundingClientRect(); return { id: n.getAttribute('data-id'), 类: (String(n.className).match(/node-([a-z0-9-]+)/) || [, '?'])[1], 框: [r.x, r.y, r.width, r.height] }; })
      .filter((n) => n.框[2] > 0 && n.框[3] > 0);
    const 视频 = ns.filter((n) => n.类 === 'video');
    const 算重叠 = (a) => ns.filter((b) => {
      if (b.id === a.id) return false;
      const ox = Math.min(a.框[0] + a.框[2], b.框[0] + b.框[2]) - Math.max(a.框[0], b.框[0]);
      const oy = Math.min(a.框[1] + a.框[3], b.框[1] + b.框[3]) - Math.max(a.框[1], b.框[1]);
      return ox > 0 && oy > 0;
    }).length;
    return 视频.map((v) => ({ ...v, 重叠数: 算重叠(v) })).sort((a, b) => a.重叠数 - b.重叠数);
  });
  R.读数.视频候选 = 候选;
  记('   视频节点候选（按重叠数升序）：' + JSON.stringify(候选));
  断言(候选.length > 0, '画布上有 video 节点', 候选.length);
  if (!候选.length) throw new Error('没有视频节点');

  const 目标 = 候选[0];
  记(`   ⭐ 选重叠最少的：${目标.id} 框 ${JSON.stringify(目标.框.map(Math.round))} 与 ${目标.重叠数} 个节点相交`);

  // ── ① 悬浮到节点**中部**（不是标题栏），逐档试
  记('=== ① 悬浮视频节点，找工具条 ===');
  const 中 = [Math.round(目标.框[0] + 目标.框[2] / 2), Math.round(目标.框[1] + 目标.框[3] / 2)];
  const 基线 = await page.evaluate(() => document.querySelectorAll('button,[role="button"]').length);
  记(`   悬浮前全页可点元素 ${基线} 个`);

  await page.mouse.move(中[0] - 30, 中[1]);
  await page.waitForTimeout(400);
  await page.mouse.move(中[0], 中[1]);
  await page.waitForTimeout(1600);
  // ⭐ 工具条可能浮在节点**上方**，往四周各移一格试
  for (const dx of [0, -40, 40, -80, 80]) {
    await page.mouse.move(中[0] + dx, 中[1] - 30);
    await page.waitForTimeout(500);
  }
  await page.mouse.move(中[0], 中[1]);
  await page.waitForTimeout(1500);

  const 悬停后 = await page.evaluate(() => document.querySelectorAll('button,[role="button"]').length);
  记(`   悬浮后全页可点元素 ${悬停后} 个（基线 ${基线}，${悬停后 > 基线 ? '⭐ 变多了' : '没变'}）`);

  R.读数.工具条候选 = await page.evaluate(() => {
    const 归 = (s) => (s || '').replace(/\s+/g, ' ');
    return [...document.querySelectorAll('button,[role="button"],[data-feature-id]')].map((b) => {
      const r = b.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) return null;
      const n = b.closest('.react-flow__node');
      if (n && n.getAttribute('data-id') !== undefined) return null;   // 只看节点**外面**的
      return {
        文字: 归(b.innerText) || 归(b.getAttribute('aria-label')) || 归(b.title) || '',
        featureId: b.getAttribute('data-feature-id') || '',
        框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        父类: String(b.parentElement?.className || '').slice(0, 90),
        父父类: String(b.parentElement?.parentElement?.className || '').slice(0, 90),
      };
    }).filter(Boolean);
  });
  记(`   ⭐ 节点外的可点元素 ${R.读数.工具条候选.length} 枚`);
  R.读数.工具条候选.slice(0, 40).forEach((b, i) => 记(`   [${i}] ${JSON.stringify(b)}`));

  // ── ② 找一个稳定的浮层容器（class 含 toolbar / floating / z- 较高）
  R.读数.浮层 = await page.evaluate(() => {
    const 归 = (s) => (s || '').replace(/\s+/g, ' ');
    return [...document.querySelectorAll('div')].filter((el) => {
      const r = el.getBoundingClientRect();
      if (!(r.width > 120 && r.height > 24)) return false;
      const c = String(el.className || '');
      if (!/toolbar|floating|absolute|z-\[|z-\d/.test(c)) return false;
      return el.querySelectorAll('button,[role="button"]').length >= 2;
    }).slice(0, 6).map((el) => {
      const r = el.getBoundingClientRect();
      return {
        框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        z: getComputedStyle(el).zIndex, class: String(el.className).slice(0, 120),
        按钮数: el.querySelectorAll('button,[role="button"]').length,
        文字: 归(el.innerText).slice(0, 160),
      };
    });
  });
  记('   ⭐ 工具条浮层候选：' + JSON.stringify(R.读数.浮层, null, 1));

  await 扫危险('悬浮后');
  await page.screenshot({ path: resolve(EVID, 'fr3-0-视频节点悬浮全景.png') });
  R.证据图.push({ 文件: 'fr3-0-视频节点悬浮全景.png' });
  记('   📷 fr3-0-视频节点悬浮全景.png');

  记(`断言统计 ${JSON.stringify(断言.统计)}`);
  R.读数.断言 = 断言.统计;
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFR3.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
