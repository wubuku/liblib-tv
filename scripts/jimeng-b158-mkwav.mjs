// 批次 158：自造一个 **4 秒 440Hz 正弦波 WAV**（纯字节，无第三方依赖），放到 /tmp。
//
// 🔑 为什么自造：批次 101 已经证明「素材限制 ≠ 测不了」——
//    先问「需要什么素材」，再问「能不能自己造出来」。
//    本批要复现批次 110 的「音频播放失败」态，需要一个**能过上传、但取流可以被拦掉**的音频。
//
// 📐 WAV 结构（44 字节头 + PCM 数据）：
//    「RIFF」+size(4)+「WAVE」+「fmt 」+16+PCM(1)+声道(1)+采样率(4)+字节率(4)+块对齐(2)+位深(2)
//    +「data」+数据长度(4) + 采样点
// 44.1kHz / 单声道 / 16bit ⇒ 字节率 88200；4 秒 = 176400 字节数据。
import { writeFileSync } from 'node:fs';

const 采样率 = 44100, 秒 = 4, 频率 = 440;
const 点数 = 采样率 * 秒;
const 数据 = Buffer.alloc(点数 * 2);
for (let i = 0; i < 点数; i++) {
  // 头尾各 0.05 秒淡入淡出，避免爆音（爆音不影响能不能播，但会让人耳听着难受）
  const t = i / 采样率;
  const 包络 = Math.min(1, t / 0.05, (秒 - t) / 0.05);
  const v = Math.round(Math.sin(2 * Math.PI * 频率 * t) * 20000 * Math.max(0, 包络));
  数据.writeInt16LE(v, i * 2);
}
const 头 = Buffer.alloc(44);
头.write('RIFF', 0); 头.writeUInt32LE(36 + 数据.length, 4); 头.write('WAVE', 8);
头.write('fmt ', 12); 头.writeUInt32LE(16, 16); 头.writeUInt16LE(1, 20); 头.writeUInt16LE(1, 22);
头.writeUInt32LE(采样率, 24); 头.writeUInt32LE(采样率 * 2, 28); 头.writeUInt16LE(2, 32); 头.writeUInt16LE(16, 34);
头.write('data', 36); 头.writeUInt32LE(数据.length, 40);

const P = '/tmp/jimeng-b158-test-440hz-4s.wav';
writeFileSync(P, Buffer.concat([头, 数据]));
console.log('已生成', P, '|', 44 + 数据.length, '字节 |', 秒, '秒 |', 频率, 'Hz |', 采样率, 'Hz 单声道 16bit');
