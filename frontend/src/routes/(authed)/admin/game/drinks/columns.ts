import type { ColumnDef } from "@tanstack/table-core";
import type { DrinkPublic } from "$lib/client";
import { renderComponent, renderSnippet } from "$lib/components/ui/data-table/index.js";
import DrinkActions from "./drink-actions.svelte";
import { createRawSnippet } from "svelte";
import type { SuperForm, Infer } from "sveltekit-superforms";
import type { DrinkUpdateSchema } from "$lib/schemas/schemas";

export const createColumns = (
    updateForm: SuperForm<Infer<typeof DrinkUpdateSchema>>
): ColumnDef<DrinkPublic>[] => [
    {
        accessorKey: "name",
        header: "Name"
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
            const drink = row.original;
            return renderComponent(DrinkActions, { drink, updateForm });
        }
    }
];
