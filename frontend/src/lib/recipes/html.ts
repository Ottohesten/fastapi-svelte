import { type DefaultTreeAdapterMap } from "parse5";

export type HtmlNode = DefaultTreeAdapterMap["node"];
export type HtmlChild = DefaultTreeAdapterMap["childNode"];
export type HtmlElement = DefaultTreeAdapterMap["element"];
export type HtmlParent = DefaultTreeAdapterMap["parentNode"];
export type HtmlText = DefaultTreeAdapterMap["textNode"];

export function isElement(node: HtmlNode): node is HtmlElement {
    return "tagName" in node;
}

export function attribute(node: HtmlNode, name: string): string | undefined {
    return isElement(node) ? node.attrs.find((attr) => attr.name === name)?.value : undefined;
}

export function textContent(node: HtmlNode): string {
    if (node.nodeName === "#text") return (node as HtmlText).value;
    return "childNodes" in node ? node.childNodes.map(textContent).join("") : "";
}

export function escapeHtml(value: string): string {
    return value
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}
