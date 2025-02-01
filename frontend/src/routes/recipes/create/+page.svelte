<script lang="ts">
	import { superForm, fileProxy } from 'sveltekit-superforms';
	import SuperDebug from 'sveltekit-superforms';
	let { data } = $props();
	import * as Dialog from '$lib/components/ui/dialog/index.js';

	// const { form, errors, message, constraints, enhance } = superForm(data.form);

	const { form, errors, message, constraints, enhance } = superForm(data.form, {
		dataType: 'json'
	});

	// const file = fileProxy(form, 'image');

	// let selectedIngredients = $state<{ title: string; id: string }[]>([]);
	let selectedIngredient = $state<string>('');
	let open = $state(false);

	// $inspect(selectedIngredients);
	// $inspect(open);
	// $inspect($form.ingredients);
	// $inspect($form.image);
</script>

<!-- {JSON.stringify(data.ingredients)} -->

<SuperDebug data={$form} />

<div class="container">
	<div class="grid grid-cols-3 gap-4">
		<div class="col-span-2 w-full">
			{#if $message}<h3 class="text-center text-2xl">{$message}</h3>{/if}
			<form method="POST" action="" enctype="multipart/form-data" use:enhance>
				<div class="">
					<label class="" for="title">Title</label>
					<input
						class="w-full appearance-none rounded-md border bg-gray-50 p-2 text-gray-700 shadow"
						type="text"
						name="title"
						aria-invalid={$errors.title ? 'true' : undefined}
						bind:value={$form.title}
						{...$constraints.title}
						required
					/>
					{#if $errors.title}<span class="invalid">{$errors.title}</span>{/if}
				</div>
				<div class="mt-5">
					<label class="" for="description">Description</label>
					<input
						class="w-full appearance-none rounded-md border bg-gray-50 p-2 text-gray-700 shadow"
						type="text"
						name="description"
						aria-invalid={$errors.description ? 'true' : undefined}
						{...$constraints.description}
						bind:value={$form.description}
					/>
					{#if $errors.description}<span class="invalid">{$errors.description}</span>{/if}
				</div>
				<!-- <div class="mt-5">
					<label for="image">Image</label>
					<input type="file" name="image" accept="image/*" bind:files={$file} />
					{#if $errors.image}<span>{$errors.image}</span>{/if}
				</div> -->
				<div class="mt-5">
					<Dialog.Root bind:open>
						<Dialog.Trigger
							onclick={(event) => {
								// prevent triggering the form submit
								event.preventDefault();
								open = true;
								// $form.ingredients = [data.ingredients[0]];
							}}
							class="rounded-md bg-blue-600 px-4 py-2 text-white">Add Ingredient</Dialog.Trigger
						>
						<Dialog.Content>
							<Dialog.Header>
								<Dialog.Title>Adding Ingredient</Dialog.Title>
								<Dialog.Description>This will add an ingredient to the recipe.</Dialog.Description>
							</Dialog.Header>
							<!-- dropdown with ingredients as options. And a button you can click to save that ingredient to the list of ingredients -->
							<div>
								<select
									class="w-full appearance-none rounded-md border bg-gray-50 p-2 text-gray-700 shadow"
									bind:value={selectedIngredient}
								>
									{#each data.ingredients as ingredient}
										<option value={ingredient.id}>{ingredient.title}</option>
									{/each}
								</select>
							</div>
							<Dialog.Footer>
								<button
									class="rounded-md bg-blue-600 px-4 py-2 text-white"
									onclick={(event) => {
										event.preventDefault();
										// console.log('clicked add ingredient');

										// add the selected ingredient to the list of ingredients
										const ingredient = data.ingredients.find((i) => i.id === selectedIngredient); // This is just to find the ingredient object, from the ingredient id
										if (ingredient) {
											// add to form
											$form.ingredients = $form.ingredients.concat(ingredient);

											// remove ingredient from the dropdown (This is not really the way to do it, because if we come back later this will not work. We really just need to look at the ones already in $form.ingredients and compare with the ones in the dropdown)
											data.ingredients = data.ingredients.filter(
												(i) => i.id !== selectedIngredient
											);
											// close the dialog
											open = false;
										} else {
											// alert
											alert('Ingredient not found');
										}
										// else
									}}>Add Ingredient</button
								>
							</Dialog.Footer>
						</Dialog.Content>
					</Dialog.Root>
				</div>
				<div class="mt-5">
					<button
						class="rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-800"
						type="submit"
						onclick={() => {
							console.log($form.ingredients);
						}}
					>
						Submit
					</button>
				</div>
			</form>
		</div>
		<div class="rounded-md bg-gray-100 p-4">
			<h2 class="font-medium">Ingredients:</h2>
			{#each $form.ingredients as ingredient}
				<div class="flex items-center justify-between border-b border-gray-800">
					<p>{ingredient.title}</p>
					<button
						onclick={() => {
							// remove the ingredient from the list of selected ingredients
							$form.ingredients = $form.ingredients.filter((i) => i.id !== ingredient.id);
							// add the ingredient back to the dropdown
							data.ingredients = data.ingredients.concat(ingredient);
						}}
						class="">Remove</button
					>
				</div>
			{/each}
		</div>
	</div>
</div>

<style>
	.invalid {
		color: red;
	}
</style>
