export type DirectorModelLibraryCategoryId =
  | "convenience"
  | "home"
  | "outdoor"
  | "tools"
  | "my-models";

export type DirectorModelLibraryVisual =
  | "bottle"
  | "chair"
  | "lamp"
  | "plant"
  | "box";

export interface DirectorModelLibraryCategory {
  id: DirectorModelLibraryCategoryId;
  label: string;
}

export interface DirectorModelLibraryItem {
  id: string;
  categoryId: Exclude<DirectorModelLibraryCategoryId, "my-models">;
  name: string;
  visual: DirectorModelLibraryVisual;
  color: string;
}

export const DIRECTOR_MODEL_LIBRARY_CATEGORIES: DirectorModelLibraryCategory[] =
  [
    { id: "convenience", label: "便利生活" },
    { id: "home", label: "居家生活" },
    { id: "outdoor", label: "户外出行" },
    { id: "tools", label: "工具配件" },
    { id: "my-models", label: "我的模型" },
  ];

export const DIRECTOR_MODEL_LIBRARY_ITEMS: DirectorModelLibraryItem[] = [
  {
    id: "proxy-convenience-bottle",
    categoryId: "convenience",
    name: "饮料瓶",
    visual: "bottle",
    color: "#70a6c4",
  },
  {
    id: "proxy-convenience-cup",
    categoryId: "convenience",
    name: "咖啡杯",
    visual: "box",
    color: "#d5b28a",
  },
  {
    id: "proxy-convenience-basket",
    categoryId: "convenience",
    name: "购物篮",
    visual: "box",
    color: "#b48659",
  },
  {
    id: "proxy-home-chair",
    categoryId: "home",
    name: "餐椅",
    visual: "chair",
    color: "#9c7f75",
  },
  {
    id: "proxy-home-lamp",
    categoryId: "home",
    name: "台灯",
    visual: "lamp",
    color: "#d0a35b",
  },
  {
    id: "proxy-home-plant",
    categoryId: "home",
    name: "盆栽",
    visual: "plant",
    color: "#6f9b78",
  },
  {
    id: "proxy-outdoor-tent",
    categoryId: "outdoor",
    name: "帐篷",
    visual: "box",
    color: "#728ea1",
  },
  {
    id: "proxy-outdoor-flask",
    categoryId: "outdoor",
    name: "保温瓶",
    visual: "bottle",
    color: "#78959e",
  },
  {
    id: "proxy-outdoor-lantern",
    categoryId: "outdoor",
    name: "营灯",
    visual: "lamp",
    color: "#c5914f",
  },
  {
    id: "proxy-tools-hammer",
    categoryId: "tools",
    name: "锤子",
    visual: "box",
    color: "#8d9297",
  },
  {
    id: "proxy-tools-wrench",
    categoryId: "tools",
    name: "扳手",
    visual: "box",
    color: "#9babb3",
  },
  {
    id: "proxy-tools-toolbox",
    categoryId: "tools",
    name: "工具箱",
    visual: "box",
    color: "#8f6f55",
  },
];

export function getDirectorModelLibraryItems(
  categoryId: Exclude<DirectorModelLibraryCategoryId, "my-models">,
) {
  return DIRECTOR_MODEL_LIBRARY_ITEMS.filter(
    (item) => item.categoryId === categoryId,
  );
}
