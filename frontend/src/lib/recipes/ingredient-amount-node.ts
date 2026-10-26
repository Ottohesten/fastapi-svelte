import { InputRule, Node } from "@tiptap/core";
import { Fragment, Slice, type Node as ProseMirrorNode } from "@tiptap/pm/model";
import { Plugin } from "@tiptap/pm/state";
import {
    AMOUNT_ATTRIBUTE,
    decodeAmountReference,
    encodeAmountReference,
    ingredientReferenceFromToken,
    referenceLabel,
    type AmountIngredient
} from "./ingredient-amounts";

export const IngredientAmountNode = Node.create<{ getIngredients: () => AmountIngredient[] }>({
    name: "ingredientAmount",
    group: "inline",
    inline: true,
    atom: true,
    addOptions() {
        return { getIngredients: () => [] };
    },
    addAttributes() {
        return { reference: { default: "", rendered: false } };
    },
    parseHTML() {
        return [
            {
                tag: `span[${AMOUNT_ATTRIBUTE}]`,
                getAttrs: (element) => {
                    const reference = element.getAttribute(AMOUNT_ATTRIBUTE);
                    return decodeAmountReference(reference) ? { reference } : false;
                }
            }
        ];
    },
    renderHTML({ node }) {
        const reference = decodeAmountReference(node.attrs.reference);
        return [
            "span",
            { [AMOUNT_ATTRIBUTE]: node.attrs.reference, class: "ingredient-amount-reference" },
            reference ? referenceLabel(reference) : "[Ingredient unavailable]"
        ];
    },
    renderText({ node }) {
        const reference = decodeAmountReference(node.attrs.reference);
        return reference ? referenceLabel(reference) : "[Ingredient unavailable]";
    },
    addInputRules() {
        return [
            new InputRule({
                find: /\{[^{}]+\}$/,
                handler: ({ state, range, match }) => {
                    const reference = ingredientReferenceFromToken(
                        match[0],
                        this.options.getIngredients()
                    );
                    if (!reference) return null;
                    state.tr.replaceWith(
                        range.from,
                        range.to,
                        this.type.create({ reference: encodeAmountReference(reference) })
                    );
                }
            })
        ];
    },
    addProseMirrorPlugins() {
        const transform = (fragment: Fragment): Fragment => {
            const nodes: ProseMirrorNode[] = [];
            fragment.forEach((node) => {
                if (node.type.spec.code || node.marks.some((mark) => mark.type.spec.code)) {
                    nodes.push(node);
                    return;
                }
                if (!node.isText) {
                    nodes.push(node.isLeaf ? node : node.copy(transform(node.content)));
                    return;
                }
                const text = node.text ?? "";
                let from = 0;
                for (const match of text.matchAll(/\{[^{}]+\}/g)) {
                    const reference = ingredientReferenceFromToken(
                        match[0],
                        this.options.getIngredients()
                    );
                    if (!reference) continue;
                    if (match.index > from) nodes.push(node.cut(from, match.index));
                    nodes.push(
                        this.type.create(
                            { reference: encodeAmountReference(reference) },
                            null,
                            node.marks
                        )
                    );
                    from = match.index + match[0].length;
                }
                if (from < text.length) nodes.push(node.cut(from));
            });
            return Fragment.fromArray(nodes);
        };
        return [
            new Plugin({
                props: {
                    transformPasted: (slice) =>
                        new Slice(transform(slice.content), slice.openStart, slice.openEnd)
                }
            })
        ];
    }
});
