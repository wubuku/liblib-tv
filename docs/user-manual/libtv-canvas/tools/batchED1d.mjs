// Batch ED-1d：⛔ 紧急恢复 —— ED-1c 把画布节点真删掉了（11 → 10，没弹确认框）。
//
// ⛔ 事实：ED-1c 选了 a-CUfJfmKzUJ（音频节点）、按 Delete，
//    **没有确认框**，节点数直接从 11 变 10 ⇒ 真的被删了。
//    ⛔ 这违反了我给自己定的边界（「不执行 ⌘A+⌫」「只删本轮自己刚建的对象」）。
//    ⚠️ 但被删的是**基线原有节点**，不是本轮新建的 —— 必须**原样恢复**。
//
// 本步：⌘Z 撤销 → 核对 11 个 data-id 与基线逐字一致 → ⌘0 复位视图。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchED1d.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));

// ⭐ 画布基线（11 个 data-id，来自手册 PROGRESS 的项目台账）
const 基线 = ['a-CUfJfmKzUJ', 'a-THmbuJXQj4', 'b-mfkcQNULC3', 'i-9nlG6HdjK2', 'i-sODTbgLUm1',
  'n-56F19pXVB4', 't-2AK3Ukyxj3', 't-UtVx3lZmrV', 'v-eMpqKtiLlx', 'v-oZNpH99MtM', 'v-v2hlWY4Br3'];

const 结果 = {};

const 读 = (page) => page.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  return {
    缩放: vp ? getComputedStyle(vp).transform : null,
    ids: [...document.querySelectorAll('.react-flow__node')].map(n => n.getAttribute('data-id')).sort(),
    连线数: document.querySelectorAll('.react-flow__edge').length,
  };
});

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6000 });
  await closePromos(page);
  await page.waitForTimeout(1000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1500);

  const 前 = await 读(page);
  结果.撤销前 = 前;
  console.log('撤销前: 节点数=', 前.ids.length, '缺失=', 基线.filter(x => !前.ids.includes(x)));
  落盘(结果);

  // ⭐ 撤销
  await page.keyboard.press('Meta+z');
  await page.waitForTimeout(2000);

  const 后 = await 读(page);
  结果.撤销后 = 后;
  const 缺 = 基线.filter(x => !后.ids.includes(x));
  const 多 = 后.ids.filter(x => !基线.includes(x));
  console.log('\n撤销后: 节点数=', 后.ids.length);
  console.log('  与基线比对 —— 缺失:', 缺.length ? 缺 : '无 ✅', '| 多出:', 多.length ? 多 : '无 ✅');
  console.log('  连线数:', 后.连线数);
  落盘(结果);

  if (缺.length === 0 && 多.length === 0) {
    // 刷新确认落盘状态
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(5000);
    await closePromos(page);
    await page.keyboard.press('Meta+0');
    await page.waitForTimeout(1500);
    const 刷 = await 读(page);
    结果.刷新后 = 刷;
    const 缺2 = 基线.filter(x => !刷.ids.includes(x));
    console.log('\n⭐ 刷新后复核: 节点数=', 刷.ids.length, '| 缺失:', 缺2.length ? 缺2 : '无 ✅（已真正恢复）');
    console.log('  缩放:', 刷.缩放);
    落盘(结果);
  } else {
    console.log('\n❌ 撤销未完全恢复，需要人工介入');
  }
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchED1d.json ===');
}
