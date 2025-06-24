<script lang="ts">
	import DataTable from '$lib/components/ui/data-table.svelte';
	import { columns } from './columns.js';
	import type { components } from '$lib/api/v1';
	import * as Dialog from '$lib/components/ui/dialog';
	import { Button } from '$lib/components/ui/button';
	import { superForm } from 'sveltekit-superforms';
	import SuperDebug from 'sveltekit-superforms';

	let { data } = $props();
	const { form, errors, message, constraints, enhance, submitting } = superForm(
		data.userCreateForm,
		{
			resetForm: true,
			onUpdated: ({ form }) => {
				if (form.valid) {
					dialogOpen = false;
				}
			}
		}
	);

	// const { form, errors, message, constraints, enhance } = superForm(data.userCreateForm, {
	// 	dataType: 'json'
	// });

	// get usercreate type from components.schemas
	type UserCreate = components['schemas']['UserCreate'];
	let dialogOpen = $state(false);
</script>

<SuperDebug data={$form} />

<div class="mx-auto max-w-7xl space-y-6 p-4 sm:p-6 lg:p-8">
	<!-- Header with Add User Button -->
	<div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
		<div>
			<h1 class="text-2xl font-bold text-gray-900 sm:text-3xl">User Management</h1>
			<p class="mt-1 text-sm text-gray-600">Manage user accounts and permissions</p>
		</div>

		<Dialog.Root bind:open={dialogOpen}>
			<Dialog.Trigger>
				<Button class="w-full sm:w-auto">Add User</Button>
			</Dialog.Trigger>
			<Dialog.Content class="sm:max-w-[500px]">
				<Dialog.Header>
					<Dialog.Title>Create New User</Dialog.Title>
					<Dialog.Description>
						Add a new user account to the system. All fields marked with * are required.
					</Dialog.Description>
				</Dialog.Header>
				<form action="?/createUser" method="POST" use:enhance class="space-y-4" autocomplete="off">
					<!-- Global Form Messages -->
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

					<div class="grid grid-cols-1 gap-4">
						<!-- Email Field -->
						<div>
							<label for="email" class="mb-1 block text-sm font-medium text-gray-700">Email *</label
							>
							<input
								type="email"
								name="email"
								aria-invalid={$errors.email ? 'true' : 'false'}
								id="email"
								class="w-full rounded-md border border-gray-300 p-2 focus:border-blue-500 focus:ring-blue-500"
								bind:value={$form.email}
								{...$constraints.email}
								required
								placeholder="Enter user email"
								autocomplete="off"
							/>
							{#if $errors.email}
								<p class="mt-1 text-sm text-red-600">{$errors.email}</p>
							{/if}
						</div>

						<!-- Full Name Field -->
						<div>
							<label for="full_name" class="mb-1 block text-sm font-medium text-gray-700"
								>Full Name *</label
							>
							<input
								type="text"
								name="full_name"
								aria-invalid={$errors.full_name ? 'true' : 'false'}
								id="full_name"
								class="w-full rounded-md border border-gray-300 p-2 focus:border-blue-500 focus:ring-blue-500"
								bind:value={$form.full_name}
								{...$constraints.full_name}
								required
								placeholder="Enter full name"
							/>
							{#if $errors.full_name}
								<p class="mt-1 text-sm text-red-600">{$errors.full_name}</p>
							{/if}
						</div>

						<!-- Password Field -->
						<div>
							<label for="password" class="mb-1 block text-sm font-medium text-gray-700"
								>Password *</label
							>
							<input
								type="password"
								name="password"
								aria-invalid={$errors.password ? 'true' : 'false'}
								id="password"
								class="w-full rounded-md border border-gray-300 p-2 focus:border-blue-500 focus:ring-blue-500"
								bind:value={$form.password}
								{...$constraints.password}
								required
								placeholder="Enter user password"
								autocomplete="new-password"
							/>
							{#if $errors.password}
								<p class="mt-1 text-sm text-red-600">{$errors.password}</p>
							{/if}
						</div>

						<!-- Confirm Password Field -->
						<div>
							<label for="confirm_password" class="mb-1 block text-sm font-medium text-gray-700"
								>Confirm Password *</label
							>
							<input
								type="password"
								name="confirm_password"
								aria-invalid={$errors.confirm_password ? 'true' : 'false'}
								id="confirm_password"
								class="w-full rounded-md border border-gray-300 p-2 focus:border-blue-500 focus:ring-blue-500"
								bind:value={$form.confirm_password}
								{...$constraints.confirm_password}
								required
								placeholder="Confirm user password"
								autocomplete="new-password"
							/>
							{#if $errors.confirm_password}
								<p class="mt-1 text-sm text-red-600">{$errors.confirm_password}</p>
							{/if}
						</div>

						<!-- Checkboxes -->
						<div class="space-y-3">
							<div class="flex items-center">
								<input
									type="checkbox"
									name="is_active"
									id="is_active"
									class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
									bind:checked={$form.is_active}
								/>
								<label for="is_active" class="ml-2 block text-sm text-gray-700">
									Active User
								</label>
							</div>
							{#if $errors.is_active}
								<p class="mt-1 text-sm text-red-600">{$errors.is_active}</p>
							{/if}

							<div class="flex items-center">
								<input
									type="checkbox"
									name="is_superuser"
									id="is_superuser"
									class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
									bind:checked={$form.is_superuser}
								/>
								<label for="is_superuser" class="ml-2 block text-sm text-gray-700">
									Superuser
								</label>
							</div>
							{#if $errors.is_superuser}
								<p class="mt-1 text-sm text-red-600">{$errors.is_superuser}</p>
							{/if}
						</div>
						<!-- Submit Button -->
						<div class="flex justify-end gap-3 pt-4">
							<Button type="button" variant="outline" onclick={() => (dialogOpen = false)}>
								Cancel
							</Button>
							<Button type="submit" disabled={$submitting}>
								{$submitting ? 'Creating...' : 'Create User'}
							</Button>
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
