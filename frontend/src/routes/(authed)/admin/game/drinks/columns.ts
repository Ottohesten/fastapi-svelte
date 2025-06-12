import type { ColumnDef } from "@tanstack/table-core";
import type { components } from '$lib/api/v1';
import { renderComponent } from '$lib/components/ui/data-table/index.js';
import DrinkActions from "./drink-actions.svelte";


export const columns: ColumnDef<components['schemas']["DrinkPublic"]>[] = [
    {
        accessorKey: "name",
        header: "Name",
    }, {
        id: "actions",
        header: "Actions",
        enableHiding: false,
        cell: ({ row }) => {
            const drink = row.original;
            return renderComponent(DrinkActions, { drink });
        },
    }


]