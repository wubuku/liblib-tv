export function isMalformedBase64DataImageUrl(value: string): boolean {
  if (!value.startsWith("data:image/")) return false;

  const commaIndex = value.indexOf(",");
  if (commaIndex < 0) return true;

  const metadata = value
    .slice(5, commaIndex)
    .toLocaleLowerCase("en-US");
  if (!metadata.includes(";base64")) return false;

  const payload = value.slice(commaIndex + 1).replace(/\s+/g, "");
  return (
    payload.length === 0 ||
    payload.length % 4 === 1 ||
    !/^[a-z0-9+/]*={0,2}$/i.test(payload)
  );
}
