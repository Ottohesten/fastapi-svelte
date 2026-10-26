import { Node } from "@tiptap/core";
import { SUB_RECIPE_ATTRIBUTE } from "./sub-recipe-instructions";

export const SubRecipeInstructionNode = Node.create({
    name: "subRecipeInstructions",
    group: "block",
    atom: true,
    addAttributes() {
        return {
            recipeId: { default: "", rendered: false },
            title: { default: "Sub-recipe", rendered: false }
        };
    },
    parseHTML() {
        return [
            {
                tag: `div[${SUB_RECIPE_ATTRIBUTE}]`,
                getAttrs: (element) => ({
                    recipeId: element.getAttribute(SUB_RECIPE_ATTRIBUTE),
                    title: element.getAttribute("data-sub-recipe-title") ?? element.textContent
                })
            }
        ];
    },
    renderHTML({ node }) {
        return [
            "div",
            {
                [SUB_RECIPE_ATTRIBUTE]: node.attrs.recipeId,
                "data-sub-recipe-title": node.attrs.title,
                class: "rounded-lg border border-gray-300 p-3 dark:border-gray-700"
            },
            ["p", {}, ["strong", {}, node.attrs.title]],
            ["p", {}, "Linked instructions. Edit the sub-recipe to update them."]
        ];
    },
    renderText({ node }) {
        return node.attrs.title;
    }
});
