// OCR 辅助程序：供 scripts/audit-visible-text.py 调用，对截图做中文文字识别。
//
// 用法：ocr-visible <图片1> <图片2> ...   → stdout 输出 JSON：{路径: [识别到的文本行]}
//
// ★ 为什么单独用 Swift：macOS 自带的 Vision 框架能做中文识别，
//   而本机没有装 tesseract / pytesseract / easyocr（都实测过，import 均失败）。
//   Vision 是系统自带的，不需要联网也不需要装任何东西。
//
// ★ 三个已实测的坑（M225 踩过，写在这里是为了下一个用它的人别重踩）：
//   ① **它会把简体认成繁体**：实测把「空音频节点」认成「空音頻节点」、
//      把「主题模式」认成「主題模式」。所以比对前**必须做繁简归一**或放宽相似度。
//   ② **usesLanguageCorrection 必须关掉**：开着会把字"改正"，认出来的就不是图上写的那个字了。
//   ③ **认不出 placeholder 与极小文字**：实测「新建」徽标只有约 30x8 像素，整张图都没认出来，
//      放大 5 倍裁剪后才认到。**「OCR 没读到」绝不等于「图上没有」**——这是 M225 第 152 次否证的由来。
//   ④ ★ **认不出「深色底上的极小浅灰字」，尤其是被连线穿过的**：节点标题条上的
//      「文本 / 参考素材 / 双击编辑文字 / 生图」全是这种渲染。实测把 `文本` 那条
//      单独裁下来放大 4 倍（920x120，小到不会触发内部降采样），人眼清清楚楚看得见，
//      **Vision 返回 0 行**。这是 M225 第 153 次否证的由来。
//      ——所以本工具对**节点标题条**这一类天然不可靠，那不是清单的错。

import Foundation
import Vision
import AppKit

func ocrOne(_ path: String) -> [String] {
    guard let img = NSImage(contentsOfFile: path),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        return ["__LOAD_FAIL__"]
    }
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.recognitionLanguages = ["zh-Hans", "en-US"]
    req.usesLanguageCorrection = false
    let handler = VNImageRequestHandler(cgImage: cg, options: [:])
    do { try handler.perform([req]) } catch { return ["__ERR__ \(error)"] }
    // 先按 y 从上到下，同行再按 x 从左到右
    let obs = (req.results ?? []).sorted { a, b in
        let ay = a.boundingBox.midY, by = b.boundingBox.midY
        if abs(ay - by) > 0.01 { return ay > by }
        return a.boundingBox.minX < b.boundingBox.minX
    }
    return obs.compactMap { $0.topCandidates(1).first?.string }
}

var out: [String: [String]] = [:]
for p in CommandLine.arguments.dropFirst() {
    out[p] = ocrOne(p)
}
if let d = try? JSONSerialization.data(withJSONObject: out, options: [.prettyPrinted, .sortedKeys]),
   let s = String(data: d, encoding: .utf8) {
    print(s)
} else {
    for (k, v) in out { print(k, v) }
}
