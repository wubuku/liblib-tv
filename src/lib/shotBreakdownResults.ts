export type ShotBreakdownDimension = "storyboard" | "motion" | "music";

export type ShotBreakdownMediaKind = "image" | "video" | "audio";

export interface ShotBreakdownResultItem {
  id: string;
  summary: string;
  imageUrl?: string;
  kind: ShotBreakdownMediaKind;
  resolution?: string;
}

export interface ShotBreakdownResultDefinition {
  key: string;
  category: ShotBreakdownDimension;
  title: string;
  dimensions: { width: number; height: number };
  items: ShotBreakdownResultItem[];
}

export const SHOT_BREAKDOWN_RESULT_DEFINITIONS: ShotBreakdownResultDefinition[] = [
  {
    key: "storyboard-01",
    category: "storyboard",
    title: "分镜组01｜出发探店·出门→咖啡",
    dimensions: { width: 1040, height: 680 },
    items: [
      {
        id: "S01",
        summary: "中景·固定｜出门微笑·引出人物",
        imageUrl: "/images/scene-coffee-1.png",
        kind: "image",
      },
      {
        id: "S02",
        summary: "中近景·平稳｜吧台接咖啡·建立场景",
        imageUrl: "/images/scene-coffee-3.png",
        kind: "image",
      },
      {
        id: "S03",
        summary: "近景·固定｜窗边捧杯看镜头·人物性格建立",
        imageUrl: "/images/scene-coffee-4.png",
        kind: "image",
      },
    ],
  },
  {
    key: "storyboard-02",
    category: "storyboard",
    title: "分镜组02｜抵达海边·逛街→沙滩漫步",
    dimensions: { width: 1040, height: 680 },
    items: [
      {
        id: "S04",
        summary: "中近景·侧面｜逛饰品店拍摄·展示探店过程",
        imageUrl: "/images/storyboard-2.png",
        kind: "image",
      },
      {
        id: "S05",
        summary: "中景·背面跟拍｜走向海边·进入新场景",
        imageUrl: "/images/scene-coffee-2.png",
        kind: "image",
      },
      {
        id: "S06",
        summary: "中景·侧前方｜弯腰捡贝壳·展示海边互动",
        imageUrl: "/images/scene-coffee-1.png",
        kind: "image",
      },
    ],
  },
  {
    key: "storyboard-03",
    category: "storyboard",
    title: "分镜组03｜海边时光·嬉闹→日落",
    dimensions: { width: 1040, height: 350 },
    items: [
      {
        id: "S07",
        summary: "中景·固定｜四人浅滩打水嬉闹·展示群体互动",
        imageUrl: "/images/scene-coffee-3.png",
        kind: "image",
      },
      {
        id: "S08",
        summary: "中近景·侧后逆光｜日落捧饮品望海·情绪收束",
        imageUrl: "/images/scene-coffee-4.png",
        kind: "image",
      },
    ],
  },
  {
    key: "motion",
    category: "motion",
    title: "动态｜运镜与动作参考",
    dimensions: { width: 1040, height: 680 },
    items: [
      {
        id: "M01",
        summary: "6s·中景跟拍｜走向海边捡贝壳",
        imageUrl: "/images/storyboard-2.png",
        kind: "video",
        resolution: "1280 × 720",
      },
      {
        id: "M02",
        summary: "6s·固定中景｜四人浅滩打水嬉闹",
        imageUrl: "/images/scene-coffee-3.png",
        kind: "video",
        resolution: "1280 × 720",
      },
      {
        id: "M03",
        summary: "4s·固定中近景｜日落沙滩静态收束",
        imageUrl: "/images/scene-coffee-4.png",
        kind: "video",
        resolution: "1280 × 720",
      },
    ],
  },
  {
    key: "music",
    category: "music",
    title: "音乐｜BGM参考片段",
    dimensions: { width: 324, height: 220 },
    items: [
      {
        id: "BGM",
        summary: "14.6s·轻快节奏｜旅行探店氛围",
        kind: "audio",
      },
    ],
  },
];
