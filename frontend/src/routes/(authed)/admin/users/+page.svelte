<script lang="ts">
	let { data, form } = $props();
	import DataTable from '$lib/components/ui/data-table.svelte';
	import { columns } from './columns.js';
	import type { components } from '$lib/api/v1';
	import * as Dialog from '$lib/components/ui/dialog';
	import { Button } from '$lib/components/ui/button';
	import { enhance } from '$app/forms';
	import { invalidateAll } from '$app/navigation';
	// get usercreate type from components.schemas
	type UserCreate = components['schemas']['UserCreate'];
	let dialogOpen = $state(false);
	let email = $state('');
	let password = $state('');
	let confirmPassword = $state('');
	let fullName = $state('');
	let isActive = $state(true);
	let isSuperuser = $state(false);
	let passwordsMatch = $derived(password === confirmPassword && password.length > 0);
	let isSubmitting = $state(false);

	// Function to reset all form fields
	function resetForm() {
		email = '';
		password = '';
		confirmPassword = '';
		fullName = '';
		isActive = true;
		isSuperuser = false;
	}

	// Reset form when dialog closes
	$effect(() => {
		if (!dialogOpen) {
			resetForm();
			isSubmitting = false;
		}
	});
</script>

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
				<form
					action="?/createUser"
					method="POST"
					use:enhance={() => {
						isSubmitting = true;
						return async ({ result, update }) => {
							isSubmitting = false;
							if (result.type === 'success') {
								dialogOpen = false;
								// Reset form fields
								resetForm();
								// Invalidate all data to refresh the user list
								await invalidateAll();
							} else if (result.type === 'redirect') {
								dialogOpen = false;
								// Reset form fields
								resetForm();
								await update();
							} else if (result.type === 'failure') {
								// Keep dialog open on failure and update form
								await update();
							} else if (result.type === 'error') {
								console.error('Form submission error:', result.error);
								// Keep dialog open on error
							} else {
								await update();
							}
						};
					}}
					class="space-y-4"
				>
					{#if form?.error}
						<div class="rounded-md bg-red-50 p-4">
							<p class="text-sm text-red-800">{form.error}</p>
						</div>
					{/if}
					<div class="grid gap-4 py-4">
						<!-- Email Field -->
						<div class="space-y-2">
							<label for="email" class="text-sm font-semibold text-gray-700">
								Email Address *
							</label>
							<input
								type="email"
								id="email"
								name="email"
								required
								bind:value={email}
								class="w-full rounded-lg border-2 border-gray-300 bg-white px-4 py-2 text-base transition-colors hover:border-blue-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
								placeholder="user@example.com"
							/>
						</div>
						<!-- Password Field -->
						<div class="space-y-2">
							<label for="password" class="text-sm font-semibold text-gray-700"> Password * </label>
							<input
								type="password"
								id="password"
								name="password"
								required
								minlength="8"
								bind:value={password}
								class="w-full rounded-lg border-2 border-gray-300 bg-white px-4 py-2 text-base transition-colors hover:border-blue-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
								placeholder="Enter secure password"
							/>
						</div>

						<!-- Confirm Password Field -->
						<div class="space-y-2">
							<label for="confirm_password" class="text-sm font-semibold text-gray-700">
								Confirm Password *
							</label>
							<input
								type="password"
								id="confirm_password"
								name="confirm_password"
								required
								minlength="8"
								bind:value={confirmPassword}
								class="w-full rounded-lg border-2 border-gray-300 bg-white px-4 py-2 text-base transition-colors hover:border-blue-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100 {confirmPassword.length >
									0 && !passwordsMatch
									? 'border-red-400 focus:border-red-500 focus:ring-red-100'
									: ''}"
								placeholder="Confirm your password"
							/>
							{#if confirmPassword.length > 0 && !passwordsMatch}
								<p class="text-sm text-red-600">Passwords do not match</p>
							{/if}
							{#if passwordsMatch && password.length >= 8}
								<p class="text-sm text-green-600">Passwords match</p>
							{/if}
						</div>

						<!-- Full Name Field -->
						<div class="space-y-2">
							<label for="full_name" class="text-sm font-semibold text-gray-700"> Full Name </label>
							<input
								type="text"
								id="full_name"
								name="full_name"
								bind:value={fullName}
								class="w-full rounded-lg border-2 border-gray-300 bg-white px-4 py-2 text-base transition-colors hover:border-blue-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
								placeholder="John Doe"
							/>
						</div>

						<!-- Checkboxes -->
						<div class="space-y-3">
							<div class="flex items-center space-x-2">
								<input
									type="checkbox"
									id="is_active"
									name="is_active"
									bind:checked={isActive}
									class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500"
								/>
								<label for="is_active" class="text-sm font-medium text-gray-700">
									Active Account
								</label>
							</div>

							<div class="flex items-center space-x-2">
								<input
									type="checkbox"
									id="is_superuser"
									name="is_superuser"
									bind:checked={isSuperuser}
									class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500"
								/>
								<label for="is_superuser" class="text-sm font-medium text-gray-700">
									Superuser (Admin privileges)
								</label>
							</div>
						</div>
					</div>

					<Dialog.Footer class="flex flex-col gap-2 sm:flex-row">
						<Button
							type="button"
							variant="outline"
							class="w-full sm:w-auto"
							onclick={() => {
								dialogOpen = false;
							}}
						>
							Cancel
						</Button>
						<Button
							type="submit"
							class="w-full bg-blue-600 text-white hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
							disabled={!passwordsMatch || password.length < 8 || isSubmitting}
						>
							{#if isSubmitting}
								Creating...
							{:else}
								Create User
							{/if}
						</Button>
					</Dialog.Footer>
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
