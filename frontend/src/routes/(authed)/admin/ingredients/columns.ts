import type { ColumnDef } from "@tanstack/table-core";
import type { components } from '$lib/api/v1';
import { renderComponent, renderSnippet } from '$lib/components/ui/data-table/index.js';
import IngredientActions from "./ingredient-actions.svelte";
import { createRawSnippet } from "svelte";

export const columns: ColumnDef<components['schemas']["IngredientPublic"]>[] = [
    {
        accessorKey: "title",
        header: "Name",
    },
    {
        accessorKey: "calories",
        header: "Calories (per 100g)",
        cell: ({ row }) => {
            const calories = row.getValue("calories") as number;
            return `${calories} kcal`;
        },
    },
    {
        id: "actions",
        header: () => {
            const actionsHeaderSnippet = createRawSnippet(() => {
                return {
                    render: () => '<div class="text-right"><span class="pr-2">Actions</span></div>',
                }
            });
            return renderSnippet(actionsHeaderSnippet, "");
        },
        enableHiding: false,
        cell: ({ row }) => {
            const ingredient = row.original;
            return renderComponent(IngredientActions, { ingredient });
        },
    }
]
