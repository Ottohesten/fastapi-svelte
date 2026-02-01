<script lang="ts">
	import Button from '$lib/components/ui/button/button.svelte';
	import { Pencil, Trash2, Shield, Plus, X } from 'lucide-svelte';
	import { enhance } from '$app/forms';
	import * as Dialog from '$lib/components/ui/dialog';
	import * as Sheet from '$lib/components/ui/sheet';
	import * as Select from "$lib/components/ui/select/index.js";
	import { Input } from '$lib/components/ui/input/index.js';
	import { Field, Control, Label, FieldErrors } from 'formsnap';
	import { zodClient } from 'sveltekit-superforms/adapters';
	import { UserUpdateSchema, UserAddRoleSchema } from '$lib/schemas/schemas.js';
	import SuperDebug from 'sveltekit-superforms/SuperDebug.svelte';

	import type { components } from '$lib/api/v1';
	import type { SuperForm } from 'sveltekit-superforms';
	import type { Infer } from 'sveltekit-superforms';

	let {
		user,
		userUpdateForm,
		permissions,
		userAddRoleForm,
		roles,
		availableScopes = []
	}: {
		user: components['schemas']['UserPublic'];
		userUpdateForm: SuperForm<Infer<typeof UserUpdateSchema>>;
		permissions: components['schemas']['UserWithPermissionsPublic'];
		userAddRoleForm: SuperForm<Infer<typeof UserAddRoleSchema>>;
		roles: components['schemas']['RolePublic'][];
		availableScopes?: string[];
	} = $props();

	// Destructure userUpdateForm
	const {
		form: userUpdateFormData,
		enhance: userUpdateEnhance,
		errors: userUpdateErrors,
		message: userUpdateMessage
	} = userUpdateForm;

	const {
		form: userAddRoleFormData,
		enhance: userAddRoleEnhance,
		errors: userAddRoleErrors,
		message: userAddRoleMessage
	} = userAddRoleForm;

	let editDialogOpen = $state(false);
	let permsOpen = $state(false);
	let selectedScope = $state(''); // For the add scope select

	function openPermissions() {
		$userAddRoleFormData.user_id = user.id;
		$userAddRoleFormData.role_id = ''; // Reset selected role
		selectedScope = ''; // Reset selected scope
		permsOpen = true;
	}

	let selectedRoleLabel = $derived(
		roles.find((r) => r.id.toString() === $userAddRoleFormData.role_id)?.name || 'Select a role'
	);

	// $inspect($userAddRoleFormData);
	// $inspect($userUpdateFormData);


	// Watch for form message changes to close dialog on success
	$effect(() => {
		if (userUpdateMessage && userUpdateErrors && editDialogOpen) {
			const currentMessage = $userUpdateMessage;
			const currentErrors = $userUpdateErrors;

			// If there's a success message and no errors, close the dialog
			if (currentMessage && typeof currentMessage === 'string' && currentMessage.length > 0) {
				// Check if there are no form errors (success condition)
				const hasErrors =
					currentErrors &&
					((currentErrors.email && currentErrors.email.length > 0) ||
						(currentErrors.full_name && currentErrors.full_name.length > 0) ||
						(currentErrors.password && currentErrors.password.length > 0) ||
						(currentErrors.confirm_password && currentErrors.confirm_password.length > 0) ||
						(currentErrors._errors && currentErrors._errors.length > 0));

				if (!hasErrors) {
					// Add a small delay to ensure the message is displayed
					setTimeout(() => {
						editDialogOpen = false;
					}, 100);
				}
			}
		}
	});

	function openEditDialog() {
		if (userUpdateForm && userUpdateFormData && userUpdateMessage) {
			// Clear any previous form messages
			userUpdateMessage.set('');

			// Pre-fill the form with current user data (all fields can be modified)
			userUpdateFormData.update(($form) => ({
				...$form,
				user_id: user.id,
				email: user.email,
				full_name: user.full_name || '',
				password: '', // Always start empty for security
				confirm_password: '', // Always start empty for security
				is_active: user.is_active,
				is_superuser: user.is_superuser
			}));
			editDialogOpen = true;
		}
	}

	// Function to close the edit dialog - this will be called from the parent
	export function closeEditDialog() {
		editDialogOpen = false;
	}
</script>

<!-- <SuperDebug {userUpdateForm} /> -->


<div class="flex items-center justify-end space-x-0">
	{#if permissions}
		<Sheet.Root bind:open={permsOpen}>
			<Button
				variant="ghost"
				title="View permissions"
				size="sm"
				class="p-2"
				onclick={() => (permsOpen = true)}
			>
				<Shield />
			</Button>
			<Sheet.Content side="right" class="w-full sm:max-w-xl">
				<div class="space-y-4">
					<div>
						<h2 class="text-lg font-semibold">User permissions</h2>
						<p class="text-muted-foreground text-sm">{user.email}</p>
					</div>
					<div class="space-y-2">
						<h3 class="text-sm font-medium">Roles</h3>
						{#if permissions.roles.length > 0}
							<div class="flex flex-wrap gap-2">
								{#each permissions.roles as r}
									<form action="?/removeRole" method="POST" use:enhance class="contents">
										<input type="hidden" name="user_id" value={user.id} />
										<input type="hidden" name="role_id" value={r.id} />
										<div class="inline-flex items-center rounded-full border px-2 py-0.5 text-xs">
											{r.name}
											<button
												type="submit"
												class="ml-1 -mr-1 rounded-full p-0.5 hover:bg-slate-200 hover:text-red-500"
												aria-label="Remove role {r.name}"
												title="Remove role"
											>
												<X class="h-3 w-3" />
											</button>
										</div>
									</form>
								{/each}
							</div>
						{:else}
							<p class="text-muted-foreground text-sm">No roles</p>
						{/if}
					</div>
					<!-- <SuperDebug data={$userAddRoleFormData} /> -->
					<!-- Select for roles -->
					<div class="space-y-2">
						<div>
							<h3 class="text-sm font-medium">Assign Role</h3>
							<form action="?/assignRole" method="POST" use:userAddRoleEnhance>
								<input type="hidden" name="user_id" value={user.id} />
								<Field form={userAddRoleForm} name="role_id">
									<Control>
										<Select.Root type="single" name="role_id" bind:value={$userAddRoleFormData.role_id}>
											<Select.Trigger class="w-full">
												{selectedRoleLabel}
											</Select.Trigger>
											<Select.Content>
												{#each roles as role}
													<Select.Item value={role.id.toString()} label={role.name}>
														{role.name}
													</Select.Item>
												{/each}
											</Select.Content>
										</Select.Root>
									</Control>
									<FieldErrors />
								</Field>
								<Button type="submit" class="mt-2" size="sm" disabled={!$userAddRoleFormData.role_id}>
									<Plus class="mr-2 h-4 w-4" /> Assign Role
								</Button>
							</form>
						</div>
					</div>

					<!-- Custom scopes -->
					<div class="space-y-2">
						<h3 class="text-sm font-medium">Custom scopes</h3>
						{#if permissions.custom_scopes.length > 0}
							<div class="flex max-h-24 flex-wrap gap-2 overflow-auto pr-1">
								{#each permissions.custom_scopes as s}
									<form action="?/removeScope" method="POST" use:enhance class="contents">
										<input type="hidden" name="user_id" value={user.id} />
										<input type="hidden" name="scope" value={s} />
										<div class="inline-flex items-center rounded-full border px-2 py-0.5 text-xs">
											{s}
											<button
												type="submit"
												class="ml-1 -mr-1 rounded-full p-0.5 hover:bg-slate-200 hover:text-red-500"
												title="Remove scope"
											>
												<X class="h-3 w-3" />
											</button>
										</div>
									</form>
								{/each}
							</div>
						{:else}
							<p class="text-muted-foreground text-sm">No custom scopes</p>
						{/if}

						<form action="?/addScope" method="POST" use:enhance class="mt-2 flex w-full items-center space-x-2">
							<input type="hidden" name="user_id" value={user.id} />
							<div class="flex-1">
								<Select.Root type="single" name="scope" bind:value={selectedScope}>
									<Select.Trigger class="h-8 text-xs w-full">
										{selectedScope || 'Select a scope'}
									</Select.Trigger>
									<Select.Content class="max-h-60 overflow-y-auto">
										{#each availableScopes as scope}
											<Select.Item value={scope} label={scope} class="text-xs">
												{scope}
											</Select.Item>
										{/each}
									</Select.Content>
								</Select.Root>
							</div>
							<Button type="submit" size="sm" variant="secondary" class="h-8 px-2" disabled={!selectedScope}>
								<Plus class="h-4 w-4" />
							</Button>
						</form>
					</div>
					<div class="space-y-2">
						<h3 class="text-sm font-medium">
							Effective scopes ({permissions.effective_scopes.length})
						</h3>
						<div class="max-h-64 overflow-auto rounded border p-2 text-xs leading-6">
							{#each permissions.effective_scopes as s}
								<div class="font-mono">{s}</div>
							{/each}
						</div>
					</div>
				</div>
			</Sheet.Content>
		</Sheet.Root>
	{/if}
	{#if userUpdateForm && userUpdateFormData && userUpdateEnhance}
		<Button variant="ghost" title="Edit user" size="sm" class="p-2" onclick={openEditDialog}>
			<Pencil class="" />
		</Button>

		<Dialog.Root bind:open={editDialogOpen}>
			<Dialog.Content class="sm:max-w-[500px]">
				<Dialog.Header>
					<Dialog.Title>Edit User</Dialog.Title>
					<Dialog.Description>
						Update user account details. Only modify the fields you want to change. Leave password
						fields empty to keep current password.
					</Dialog.Description>
				</Dialog.Header>
				{#if userUpdateFormData}
					<form action="?/updateUser" method="POST" use:userUpdateEnhance class="space-y-4">
						<input type="hidden" name="user_id" value={$userUpdateFormData?.user_id || user.id} />

						<div class="grid grid-cols-1 gap-2">
							<!-- Email Field -->
							<Field form={userUpdateForm} name="email">
								<Control>
									{#snippet children({ props })}
										<Label class="mb-1 block text-sm font-medium text-gray-700">Email</Label>
										<Input
											{...props}
											type="email"
											bind:value={$userUpdateFormData!.email}
											placeholder="Leave unchanged or enter new email"
										/>
									{/snippet}
								</Control>
								<FieldErrors />
							</Field>

							<!-- Full Name Field -->
							<Field form={userUpdateForm} name="full_name">
								<Control>
									{#snippet children({ props })}
										<Label class="mb-1 block text-sm font-medium text-gray-700">Full Name</Label>
										<Input
											{...props}
											type="text"
											bind:value={$userUpdateFormData!.full_name}
											placeholder="Leave unchanged or enter new full name"
										/>
									{/snippet}
								</Control>
								<FieldErrors />
							</Field>

							<!-- Password Field -->
							<Field form={userUpdateForm} name="password">
								<Control>
									{#snippet children({ props })}
										<Label class="mb-1 block text-sm font-medium text-gray-700">New Password (optional)</Label>
										<Input
											{...props}
											type="password"
											bind:value={$userUpdateFormData!.password}
											placeholder="Leave empty to keep current password"
											autocomplete="new-password"
										/>
									{/snippet}
								</Control>
								<FieldErrors />
							</Field>

							<!-- Confirm Password Field -->
							<Field form={userUpdateForm} name="confirm_password">
								<Control>
									{#snippet children({ props })}
										<Label class="mb-1 block text-sm font-medium text-gray-700">Confirm New Password</Label>
										<Input
											{...props}
											type="password"
											bind:value={$userUpdateFormData!.confirm_password}
											placeholder="Confirm new password"
											autocomplete="new-password"
										/>
									{/snippet}
								</Control>
								<FieldErrors />
							</Field>

							<!-- Checkboxes -->
							<div class="space-y-3">
								<Field form={userUpdateForm} name="is_active">
									<Control>
										{#snippet children({ props })}
											<div class="flex items-center">
												<input
													{...props}
													type="checkbox"
													bind:checked={$userUpdateFormData!.is_active}
													class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500/20"
												/>
												<Label class="ml-2 block text-sm text-gray-700">Active User</Label>
											</div>
										{/snippet}
									</Control>
									<FieldErrors />
								</Field>

								<Field form={userUpdateForm} name="is_superuser">
									<Control>
										{#snippet children({ props })}
											<div class="flex items-center">
												<input
													{...props}
													type="checkbox"
													bind:checked={$userUpdateFormData!.is_superuser}
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
								<Button type="button" variant="outline" onclick={() => (editDialogOpen = false)}>
									Cancel
								</Button>
								<Button type="submit">Update User</Button>
							</div>
						</div>
					</form>
				{/if}
			</Dialog.Content>
		</Dialog.Root>
	{:else}
		<Button variant="ghost" title="Edit user" size="sm" class="p-2">
			<Pencil class="" />
		</Button>
	{/if}

	<form action="?/deleteUser" method="POST" use:enhance>
		<input type="hidden" name="user_id" value={user.id} />
		<Button
			variant="ghost"
			title="Delete user"
			size="sm"
			class="p-2 text-red-600 hover:bg-red-100 hover:text-red-700"
			type="submit"
			onclick={(e) => {
				const confirmed = confirm(
					`Are you sure you want to delete user "${user.email}"? This action cannot be undone.`
				);
				if (!confirmed) {
					e.preventDefault();
				}
			}}
		>
			<Trash2 class="" />
		</Button>
	</form>
</div>
