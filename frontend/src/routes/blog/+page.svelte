<script lang="ts">
	let { data } = $props();
</script>

<div class="container">
	<h1>blog</h1>
	<ul>
		{#each data.summaries as { slug, title }}
			<li><a href={`/blog/${slug}`}>{title}</a></li>
		{/each}
	</ul>
</div>
