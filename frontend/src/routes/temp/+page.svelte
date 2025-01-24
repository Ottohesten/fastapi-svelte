<script>
	let questions = $state([
		{
			id: 1,
			text: `Where did you go to school?`
		},
		{
			id: 2,
			text: `What is your mother's name?`
		},
		{
			id: 3,
			text: `What is another personal fact that an attacker could easily find with Google?`
		}
	]);

	let selected = $state();

	let answer = $state('');

	// @ts-ignore
	function handleSubmit(e) {
		e.preventDefault();

		alert(`answered question ${selected.id} (${selected.text}) with "${answer}"`);
	}

	$inspect(answer);
</script>

<div class="container">
	<h2>Insecurity questions</h2>

	<form class="" onsubmit={handleSubmit}>
		<select bind:value={selected} onchange={() => (answer = '')}>
			{#each questions as question}
				<option value={question}>
					{question.text}
				</option>
			{/each}
		</select>

		<input class="block border bg-gray-50 shadow" bind:value={answer} />

		<button
			class="bg-primary my-2 rounded-md p-2 font-medium text-white"
			disabled={!answer}
			type="submit"
		>
			Submit
		</button>
	</form>

	<p>
		selected question {selected ? selected.id : '[waiting...]'}
	</p>
</div>
