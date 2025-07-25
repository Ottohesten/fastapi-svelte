import type { ColumnDef } from "@tanstack/table-core";
import type { components } from '$lib/api/v1';
import { renderComponent, renderSnippet } from '$lib/components/ui/data-table/index.js';
import UserBadge from "./user-badge.svelte";
import UserActions from "./user-actions.svelte";
import { createRawSnippet } from "svelte";
import type { SuperForm } from 'sveltekit-superforms';
import type { UserUpdateSchema } from '$lib/schemas/schemas.js';
import type { Infer } from 'sveltekit-superforms';

export function createColumns(userUpdateForm: SuperForm<Infer<typeof UserUpdateSchema>>): ColumnDef<components['schemas']["UserPublic"]>[] {
    return [
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
                return renderComponent(UserActions, { user, userUpdateForm });
            },
        }
    ];
}

// Keep the original columns export for backward compatibility
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
