<script lang="ts">
	import DataTable from '$lib/components/ui/data-table.svelte';
	import { columns } from './columns.js';
	import type { components } from '$lib/api/v1';
	import * as Dialog from '$lib/components/ui/dialog';
	import { Button } from '$lib/components/ui/button';
	import { superForm, type SuperValidated, type Infer } from 'sveltekit-superforms';

	import { zodClient } from 'sveltekit-superforms/adapters';
	import SuperDebug from 'sveltekit-superforms';
	import { Field, Control, Label, Description, FieldErrors } from 'formsnap';
	import { Input } from '$lib/components/ui/input/index.js';

	import { UserSchema, UserUpdateSchema } from '$lib/schemas/schemas.js';
	let { data } = $props();
	// let { data }: { data: { form: SuperValidated<Infer<FormSchema>> } } = $props();
	let dialogOpen = $state(false);

	const form = superForm(data.userCreateForm, {
		id: 'userCreateForm',
		validators: zodClient(UserSchema),
		onUpdated: ({ form }) => {
			console.log('Form updated - valid:', form.valid, 'message:', form.message);
			if (form.valid) {
				console.log('Form is valid, closing dialog');
				dialogOpen = false;
			}
		}
		// onResult: ({ result }) => {
		// 	console.log('Form result:', result);
		// 	if (result.type === 'success') {
		// 		console.log('Success result, closing dialog');
		// 		dialogOpen = false;
		// 	}
		// }
	});

	const updateForm = superForm(data.userUpdateForm, {
		id: 'userUpdateForm',
		validators: zodClient(UserUpdateSchema)
	});

	const { form: formData, enhance, errors, message } = form;
	// const { form, enhance } = superForm(data.form, {
	// 	// resetForm: true,
	// 	validators: zodClient(UserSchema)
	// 	// onUpdated: ({ form }) => {
	// 	// 	if (form.valid && form.message) {
	// 	// 		dialogOpen = false;
	// 	// 	}
	// 	// }
	// });
</script>

<!-- <SuperDebug data={$formData} /> -->
<!-- <SuperDebug data={$errors} /> -->
<!-- <SuperDebug data={$message} /> -->
<!-- <SuperDebug data={$constraints} /> -->

<div class="mx-auto max-w-7xl space-y-6 p-4 sm:p-6 lg:p-8">
	<!-- Header with Add User Button -->
	<div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
		<div>
			<h1 class="text-2xl font-bold text-gray-900 sm:text-3xl">User Management</h1>
			<p class="mt-1 text-sm text-gray-600">Manage user accounts and permissions</p>
		</div>
		{#if $message}
			<div class="rounded-md border border-green-200 bg-green-50 p-3">
				<p class="text-sm text-green-800">{$message}</p>
			</div>
		{/if}

		{#if $errors._errors}
			<div class="rounded-md border border-red-200 bg-red-50 p-3">
				{#each $errors._errors as error}
					<p class="text-sm text-red-800">{error}</p>
				{/each}
			</div>
		{/if}

		<Dialog.Root bind:open={dialogOpen}>
			<Dialog.Trigger
				class="bg-primary text-primary-foreground ring-offset-background hover:bg-primary/90 focus-visible:ring-ring inline-flex h-10 w-full items-center justify-center whitespace-nowrap rounded-md px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 sm:w-auto"
			>
				Add User
			</Dialog.Trigger>
			<Dialog.Content class="sm:max-w-[500px]">
				<Dialog.Header>
					<Dialog.Title>Create New User</Dialog.Title>
					<Dialog.Description>
						Add a new user account to the system. All fields marked with * are required.
					</Dialog.Description>
				</Dialog.Header>
				<form action="?/createUser" method="POST" use:enhance class="space-y-4">
					<!-- Global Form Messages -->
					<!-- {#if $message}
						<div class="rounded-md border border-green-200 bg-green-50 p-3">
							<p class="text-sm text-green-800">{$message}</p>
						</div>
					{/if}

					{#if $errors._errors}
						<div class="rounded-md border border-red-200 bg-red-50 p-3">
							{#each $errors._errors as error}
								<p class="text-sm text-red-800">{error}</p>
							{/each}
						</div>
					{/if} -->
					<div class="grid grid-cols-1 gap-2">
						<!-- Email Field -->
						<Field {form} name="email">
							<Control>
								{#snippet children({ props })}
									<Label class="mb-1 block text-sm font-medium text-gray-700">Email *</Label>
									<input
										{...props}
										type="email"
										bind:value={$formData.email}
										placeholder="Enter user email"
										class="w-full rounded-md border border-gray-300 p-2 transition-colors focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
									/>
								{/snippet}
							</Control>
							<FieldErrors />
						</Field>
						<!-- <input type="email" placeholder="Enter user email" class="w-full rounded-lg border-2 border-gray-300 bg-white px-4 py-2 text-base transition-colors hover:border-blue-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100 sm:py-3" /> -->

						<!-- Full Name Field -->
						<Field {form} name="full_name">
							<Control>
								{#snippet children({ props })}
									<Label class="mb-1 block text-sm font-medium text-gray-700">Full Name *</Label>
									<input
										{...props}
										type="text"
										bind:value={$formData.full_name}
										placeholder="Enter full name"
										class="w-full rounded-md border border-gray-300 p-2 transition-colors focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
									/>
								{/snippet}
							</Control>
							<FieldErrors />
						</Field>
						<!-- Password Field -->
						<Field {form} name="password">
							<Control>
								{#snippet children({ props })}
									<Label class="mb-1 block text-sm font-medium text-gray-700">Password *</Label>
									<input
										{...props}
										type="password"
										bind:value={$formData.password}
										placeholder="Enter user password"
										autocomplete="new-password"
										class="w-full rounded-md border border-gray-300 p-2 transition-colors focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
									/>
								{/snippet}
							</Control>
							<FieldErrors />
						</Field>

						<!-- Confirm Password Field -->
						<Field {form} name="confirm_password">
							<Control>
								{#snippet children({ props })}
									<Label class="mb-1 block text-sm font-medium text-gray-700"
										>Confirm Password *</Label
									>
									<input
										{...props}
										type="password"
										bind:value={$formData.confirm_password}
										placeholder="Confirm user password"
										autocomplete="new-password"
										class="w-full rounded-md border border-gray-300 p-2 transition-colors focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
									/>
								{/snippet}
							</Control>
							<FieldErrors />
						</Field>

						<!-- Checkboxes -->
						<div class="space-y-3">
							<Field {form} name="is_active">
								<Control>
									{#snippet children({ props })}
										<div class="flex items-center">
											<input
												{...props}
												type="checkbox"
												bind:checked={$formData.is_active}
												class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500/20"
											/>
											<Label class="ml-2 block text-sm text-gray-700">Active User</Label>
										</div>
									{/snippet}
								</Control>
								<FieldErrors />
							</Field>

							<Field {form} name="is_superuser">
								<Control>
									{#snippet children({ props })}
										<div class="flex items-center">
											<input
												{...props}
												type="checkbox"
												bind:checked={$formData.is_superuser}
												class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500/20"
											/>
											<Label class="ml-2 block text-sm text-gray-700">Superuser</Label>
										</div>
									{/snippet}
								</Control>
								<FieldErrors />
							</Field>
						</div>
						<!-- Submit Button -->
						<div class="flex justify-end gap-3 pt-4">
							<Button type="button" variant="outline" onclick={() => (dialogOpen = false)}>
								Cancel
							</Button>
							<Button type="submit">Create User</Button>
						</div>
					</div>
				</form>
			</Dialog.Content>
		</Dialog.Root>
	</div>

	<!-- Data Table -->
	<div class="rounded-2xl bg-white shadow-lg">
		<DataTable data={data.users.data} {columns} />
	</div>
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
