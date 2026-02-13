import type { ColumnDef } from "@tanstack/table-core";
import type { IngredientPublic } from "$lib/client";
import { renderComponent, renderSnippet } from "$lib/components/ui/data-table/index.js";
import IngredientActions from "./ingredient-actions.svelte";
import { createRawSnippet } from "svelte";
import type { SuperForm } from "sveltekit-superforms";
import type { Infer } from "sveltekit-superforms";
import type { IngredientUpdateSchema } from "$lib/schemas/schemas";

export const createColumns = (
    updateForm: SuperForm<Infer<typeof IngredientUpdateSchema>>
): ColumnDef<IngredientPublic>[] => [
    {
        accessorKey: "title",
        header: "Name"
    },
    {
        accessorKey: "calories",
        header: "Calories (per 100g)",
        cell: ({ row }) => {
            const calories = row.getValue("calories") as number;
            return `${calories} kcal`;
        }
    },
    {
        accessorKey: "weight_per_piece",
        header: "Weight per piece",
        cell: ({ row }) => {
            const weight = row.getValue("weight_per_piece") as number;
            return `${weight}g`;
        }
    },
    {
        id: "actions",
        header: () => {
            const actionsHeaderSnippet = createRawSnippet(() => {
                return {
                    render: () => '<div class="text-right"><span class="pr-2">Actions</span></div>'
                };
            });
            return renderSnippet(actionsHeaderSnippet, "");
        },
        enableHiding: false,
        cell: ({ row }) => {
            const ingredient = row.original;
            return renderComponent(IngredientActions, { ingredient, updateForm });
        }
    }
];
