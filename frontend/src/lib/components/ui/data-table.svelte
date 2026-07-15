<script lang="ts" generics="TData, TValue">
  import {
    type ColumnDef,
    type PaginationState,
    type SortingState,
    type ColumnFiltersState,
    getCoreRowModel,
    getPaginationRowModel,
    getSortedRowModel,
    getFilteredRowModel
  } from "@tanstack/table-core";
  import { createSvelteTable, FlexRender } from "$lib/components/ui/data-table/index.js";
  import * as Table from "$lib/components/ui/table/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import * as Select from "$lib/components/ui/select/index.js";
  import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, Search } from "@lucide/svelte";

  type DataTableProps<TData, TValue> = {
    columns: ColumnDef<TData, TValue>[];
    data: TData[];
    searchColumn?: string;
    searchPlaceholder?: string;
  };

  let { data, columns, searchColumn, searchPlaceholder }: DataTableProps<TData, TValue> = $props();

  let pagination = $state<PaginationState>({ pageIndex: 0, pageSize: 10 });
  let sorting = $state<SortingState>([]);
  let columnFilters = $state<ColumnFiltersState>([]);

  const table = createSvelteTable({
    get data() {
      return data;
    },
    // columns,
    get columns() {
      return columns;
    },
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onPaginationChange: (updater) => {
      if (typeof updater === "function") {
        pagination = updater(pagination);
      } else {
        pagination = updater;
      }
    },
    onSortingChange: (updater) => {
      if (typeof updater === "function") {
        sorting = updater(sorting);
      } else {
        sorting = updater;
      }
    },
    onColumnFiltersChange: (updater) => {
      if (typeof updater === "function") {
        columnFilters = updater(columnFilters);
      } else {
        columnFilters = updater;
      }
    },
    state: {
      get pagination() {
        return pagination;
      },
      get sorting() {
        return sorting;
      },
      get columnFilters() {
        return columnFilters;
      }
    }
  });

  let filteredRowCount = $derived(table.getFilteredRowModel().rows.length);
  let pageCount = $derived(table.getPageCount());
  let firstVisibleRow = $derived(
    filteredRowCount === 0 ? 0 : pagination.pageIndex * pagination.pageSize + 1
  );
  let lastVisibleRow = $derived(
    Math.min((pagination.pageIndex + 1) * pagination.pageSize, filteredRowCount)
  );
</script>

<div class="min-w-0 space-y-4">
  <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
    {#if searchColumn}
      <div class="relative w-full sm:max-w-sm">
        <Search
          aria-hidden="true"
          class="text-muted-foreground pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2"
        />
        <Input
          type="search"
          aria-label={searchPlaceholder ?? "Filter table"}
          placeholder={searchPlaceholder ?? "Filter..."}
          value={(table.getColumn(searchColumn)?.getFilterValue() as string) ?? ""}
          oninput={(event) => {
            table.getColumn(searchColumn)?.setFilterValue(event.currentTarget.value);
            table.setPageIndex(0);
          }}
          class="pl-9"
        />
      </div>
    {:else}
      <div></div>
    {/if}

    <p class="text-muted-foreground text-sm" aria-live="polite">
      {filteredRowCount}
      {filteredRowCount === 1 ? "result" : "results"}
    </p>
  </div>

  <div class="max-w-full overflow-x-auto rounded-lg border">
    <Table.Root class="min-w-[680px]">
      <Table.Header>
        {#each table.getHeaderGroups() as headerGroup (headerGroup.id)}
          <Table.Row>
            {#each headerGroup.headers as header (header.id)}
              <Table.Head>
                {#if !header.isPlaceholder}
                  <FlexRender
                    content={header.column.columnDef.header}
                    context={header.getContext()}
                  />
                {/if}
              </Table.Head>
            {/each}
          </Table.Row>
        {/each}
      </Table.Header>
      <Table.Body>
        {#each table.getRowModel().rows as row (row.id)}
          <Table.Row data-state={row.getIsSelected() && "selected"}>
            {#each row.getVisibleCells() as cell (cell.id)}
              <Table.Cell>
                <FlexRender content={cell.column.columnDef.cell} context={cell.getContext()} />
              </Table.Cell>
            {/each}
          </Table.Row>
        {:else}
          <Table.Row>
            <Table.Cell colspan={columns.length} class="h-24 text-center">No results.</Table.Cell>
          </Table.Row>
        {/each}
      </Table.Body>
    </Table.Root>
  </div>

  <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
    <p class="text-muted-foreground text-sm">
      Showing {firstVisibleRow}–{lastVisibleRow} of {filteredRowCount}
    </p>

    <div class="flex flex-col gap-3 sm:flex-row sm:items-center">
      <div class="flex items-center justify-between gap-2 sm:justify-start">
        <span class="text-muted-foreground text-sm">Rows per page</span>
        <Select.Root
          type="single"
          value={pagination.pageSize.toString()}
          onValueChange={(value) => {
            if (value) table.setPageSize(Number(value));
          }}
        >
          <Select.Trigger class="h-9 w-20" aria-label="Rows per page">
            {pagination.pageSize}
          </Select.Trigger>
          <Select.Content>
            {#each [10, 25, 50] as pageSize (pageSize)}
              <Select.Item value={pageSize.toString()} label={pageSize.toString()}>
                {pageSize}
              </Select.Item>
            {/each}
          </Select.Content>
        </Select.Root>
      </div>

      <div class="flex items-center justify-between gap-2 sm:justify-start">
        <span class="text-muted-foreground min-w-24 text-center text-sm">
          Page {filteredRowCount === 0 ? 0 : pagination.pageIndex + 1} of {pageCount}
        </span>
        <div class="flex items-center gap-1">
          <Button
            variant="outline"
            size="icon"
            class="hidden size-9 sm:inline-flex"
            aria-label="Go to first page"
            disabled={!table.getCanPreviousPage()}
            onclick={() => table.setPageIndex(0)}
          >
            <ChevronsLeft />
          </Button>
          <Button
            variant="outline"
            size="icon"
            class="size-9"
            aria-label="Go to previous page"
            disabled={!table.getCanPreviousPage()}
            onclick={() => table.previousPage()}
          >
            <ChevronLeft />
          </Button>
          <Button
            variant="outline"
            size="icon"
            class="size-9"
            aria-label="Go to next page"
            disabled={!table.getCanNextPage()}
            onclick={() => table.nextPage()}
          >
            <ChevronRight />
          </Button>
          <Button
            variant="outline"
            size="icon"
            class="hidden size-9 sm:inline-flex"
            aria-label="Go to last page"
            disabled={!table.getCanNextPage()}
            onclick={() => table.setPageIndex(Math.max(pageCount - 1, 0))}
          >
            <ChevronsRight />
          </Button>
        </div>
      </div>
    </div>
  </div>
</div>
