import type { ColumnDef } from "@tanstack/table-core";


import type { components } from '$lib/api/v1';

export const columns: ColumnDef<components['schemas']["UserPublic"]>[] = [
    {
        accessorKey: "email",
        header: "Email",
    },
    {
        accessorKey: "is_superuser",
        header: "is_superuser",
    },
    {
        accessorKey: "is_active",
        header: "is_active",
    },
];
