<script lang="ts">
	import { superForm } from 'sveltekit-superforms/client';
	import SuperDebug from 'sveltekit-superforms';

	let { data } = $props(); // data: { form, player, all_drinks }

	const { form, errors, message, constraints, enhance } = superForm(data.form, {
		dataType: 'json'
	});
	function handleDrinkSelection(drinkId: string, isChecked: boolean) {
		const existingDrinkIndex = $form.drinks.findIndex((d) => d.drink_id === drinkId);

		// If the drink is checked, add it to the form if not already present
		if (isChecked) {
			if (existingDrinkIndex === -1) {
				$form.drinks = [...$form.drinks, { drink_id: drinkId, amount: 1 }];
			}

			// If the drink is unchecked, remove it from the form if present
		} else {
			if (existingDrinkIndex !== -1) {
				$form.drinks = $form.drinks.filter((_, index) => index !== existingDrinkIndex);
			}
		}
	}
	function handleAmountChange(drinkIndexInForm: number) {
		if ($form.drinks[drinkIndexInForm]) {
			let currentAmount = Number($form.drinks[drinkIndexInForm].amount);
			if (isNaN(currentAmount) || currentAmount < 0) {
				currentAmount = 0;
			}
			$form.drinks[drinkIndexInForm].amount = Math.floor(currentAmount);
		}
	}
</script>

<!-- <SuperDebug data={{ $form, $errors, $constraints, $message }} /> -->

<div class="container mx-auto p-4">
	<h1 class="mb-4 text-2xl font-bold">Edit Player: {data.player.name}</h1>

	{#if $message}
		<div class="mb-4 rounded-md bg-green-50 p-4 text-sm text-green-700" role="alert">
			{$message}
		</div>
		<!-- {console.log(message)} -->
	{/if}

	<form method="POST" use:enhance class="space-y-6">
		<div>
			<label for="name" class="block text-sm font-medium">Player Name</label>
			<input
				type="text"
				id="name"
				name="name"
				class="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
				bind:value={$form.name}
				aria-invalid={$errors.name ? 'true' : undefined}
				{...$constraints.name}
				required
			/>
			{#if $errors.name}
				<p class="mt-2 text-sm text-red-600">{$errors.name}</p>
			{/if}
		</div>

		<div>
			<h3 class="text-lg font-medium">Drinks</h3>
			<p class="mb-2 text-sm text-gray-500 dark:text-gray-400">
				Select the drinks and specify amounts for this player.
			</p>
			{#if typeof $errors.drinks === 'string'}
				<p class="mt-2 text-sm text-red-600">{$errors.drinks}</p>
			{/if}

			<div class="mt-4 space-y-2">
				{#if data.drinks && data.drinks.length > 0}
					{#each data.drinks as availableDrink (availableDrink.id)}
						<!-- Check i the drink is already in the form. If it is, it will return an index, otherwise -1 -->
						{@const currentSelectedDrinkIndex = $form.drinks.findIndex(
							(d) => d.drink_id === availableDrink.id
						)}
						<!-- If it is not -1 aka. exists in the list. we should check the box. -->
						{@const isChecked = currentSelectedDrinkIndex !== -1}

						<div
							class="flex items-center rounded-lg border border-gray-200 p-3 shadow-sm transition-shadow duration-150 hover:shadow-md"
						>
							<div class="flex-none">
								<input
									type="checkbox"
									id={`drink-checkbox-${availableDrink.id}`}
									checked={isChecked}
									onchange={(e) =>
										handleDrinkSelection(availableDrink.id, (e.target as HTMLInputElement).checked)}
									class="h-5 w-5 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
								/>
							</div>
							<div class="ml-3 grow">
								<label
									for={`drink-checkbox-${availableDrink.id}`}
									class="block text-sm font-medium"
								>
									{availableDrink.name}
									<!-- {#if availableDrink.description}
										<span class="block text-xs font-normal text-gray-500"
											>{availableDrink.description}</span
										>
									{/if} -->
								</label>
							</div>
							<!-- If the  -->
							{#if isChecked}
								<div class="ml-4 flex-none">
									<label for={`drink-amount-${availableDrink.id}`} class="sr-only"
										>Amount for {availableDrink.name}</label
									>
									<input
										type="number"
										min="0"
										step="1"
										id={`drink-amount-${availableDrink.id}`}
										name={`drinks[${currentSelectedDrinkIndex}].amount`}
										bind:value={$form.drinks[currentSelectedDrinkIndex].amount}
										oninput={() => handleAmountChange(currentSelectedDrinkIndex)}
										class="w-20 rounded-md border border-gray-300 p-1.5 text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
										placeholder="Amount"
									/>
								</div>
							{/if}
						</div>
						<!-- Error display for this specific drink object -->
						{#if $errors.drinks}
							{@const drinkError = $errors.drinks[currentSelectedDrinkIndex]}
							{#if drinkError}
								<div class="-mt-1 mb-1 pl-8 text-xs text-red-600">
									{#if typeof drinkError === 'string'}
										<p>{drinkError}</p>
									{:else if drinkError.amount}
										<p>Amount: {drinkError.amount.join(' ')}</p>
									{:else if drinkError.drink_id}
										<!-- In case drink_id was also part of the sub-schema and had errors -->
										<p>Drink ID: {drinkError.drink_id.join(' ')}</p>
									{/if}
								</div>
							{/if}
						{/if}
					{/each}
				{:else}
					<p class="text-sm text-gray-500">No drinks available to select.</p>
				{/if}
			</div>
		</div>

		<div>
			<button
				type="submit"
				class="flex w-full justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
			>
				Update Player
			</button>
		</div>
	</form>
</div>

<!-- Original content commented out -->
<!-- 
This is the main page for a player in a game. It will show the player's stats, achievements, and
other relevant information.

<div class="contain">
	<div class="grid grid-cols-1">
		<div class="">
		</div>
	</div>
</div>
-->
