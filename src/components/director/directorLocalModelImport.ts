import type {
  DirectorLocalModelLibraryItem,
  DirectorModelLibraryVisual,
} from "@/components/director/directorModelLibrary";

const LOCAL_MODEL_EXTENSION_RE = /\.(fbx|obj)$/i;

const LOCAL_MODEL_COLORS: Record<DirectorModelLibraryVisual, string> = {
  bottle: "#78959e",
  chair: "#9c7f75",
  lamp: "#d0a35b",
  plant: "#6f9b78",
  box: "#8f6f55",
};

function readFileAsDataUrl(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.addEventListener("load", () => {
      if (typeof reader.result === "string") {
        resolve(reader.result);
        return;
      }
      reject(new Error("模型文件读取失败"));
    });
    reader.addEventListener("error", () =>
      reject(reader.error ?? new Error("模型文件读取失败")),
    );
    reader.readAsDataURL(file);
  });
}

function inferVisual(fileName: string): DirectorModelLibraryVisual {
  const normalized = fileName.toLocaleLowerCase("en-US");
  if (/(bottle|cup|can|flask|jar|kettle|water|饮料|水壶|杯|罐)/u.test(normalized)) {
    return "bottle";
  }
  if (/(chair|stool|seat|sofa|椅|凳|沙发)/u.test(normalized)) {
    return "chair";
  }
  if (/(lamp|lantern|light|台灯|营灯|灯)/u.test(normalized)) {
    return "lamp";
  }
  if (/(plant|tree|flower|cactus|盆栽|植物|仙人掌)/u.test(normalized)) {
    return "plant";
  }
  return "box";
}

function createLocalModelId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `director-local-model-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export async function readDirectorLocalModelFiles(
  files: FileList | File[],
): Promise<DirectorLocalModelLibraryItem[]> {
  const validFiles = Array.from(files).filter((file) =>
    LOCAL_MODEL_EXTENSION_RE.test(file.name),
  );

  return Promise.all(
    validFiles.map(async (file) => {
      const visual = inferVisual(file.name);
      return {
        id: createLocalModelId(),
        categoryId: "my-models",
        name: file.name.replace(LOCAL_MODEL_EXTENSION_RE, ""),
        fileName: file.name,
        dataUrl: await readFileAsDataUrl(file),
        mimeType:
          file.type ||
          (file.name.toLocaleLowerCase("en-US").endsWith(".obj")
            ? "text/plain"
            : "application/octet-stream"),
        sizeBytes: file.size,
        lastModified: file.lastModified,
        visual,
        color: LOCAL_MODEL_COLORS[visual],
      } satisfies DirectorLocalModelLibraryItem;
    }),
  );
}
