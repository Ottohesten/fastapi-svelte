<script lang="ts">
	let { data } = $props();
	import DataTable from './data-table.svelte';
	import { columns } from './columns.js';
</script>

<div class="mx-auto max-w-md">
	<DataTable data={data.users.data} {columns} />
</div>

<!-- <div>
	<p>
		Lorem ipsum dolor, sit amet consectetur adipisicing elit. Ratione at quo eveniet, nisi, placeat
		laborum distinctio autem provident rem reiciendis ex doloremque nobis, repellat dignissimos
		saepe accusantium eius neque assumenda!
	</p>
</div> -->

<!-- <div>
	<p>This is the admin users page</p>

	{JSON.stringify(data.users)}
</div> -->
