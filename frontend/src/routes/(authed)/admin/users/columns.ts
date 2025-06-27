import type { ColumnDef } from "@tanstack/table-core";
import type { components } from '$lib/api/v1';
import { renderComponent, renderSnippet } from '$lib/components/ui/data-table/index.js';
import UserBadge from "./user-badge.svelte";
import UserActions from "./user-actions.svelte";
import { createRawSnippet } from "svelte";

export const columns: ColumnDef<components['schemas']["UserPublic"]>[] = [
    {
        accessorKey: "email",
        header: "Email",
    },
    {
        accessorKey: "full_name",
        header: "Full Name"
    },
    {
        accessorKey: "is_superuser",
        header: "is superuser",
        cell: ({ row }) => {
            const isSuperuser = row.getValue("is_superuser") as boolean;
            return renderComponent(UserBadge, { isSuperuser });
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
            const user = row.original;
            return renderComponent(UserActions, { user });
        },

    }
];
