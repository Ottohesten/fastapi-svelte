<script lang="ts">
	import { superForm } from 'sveltekit-superforms';
	import { zodClient } from 'sveltekit-superforms/adapters';
	import { LoginSchema } from '$lib/schemas/schemas';
	import { Field, Control, Label, FieldErrors } from 'formsnap';
	import { Input } from '$lib/components/ui/input';
	import { Button } from '$lib/components/ui/button';

	let { data } = $props();

	const form = superForm(data.form, {
		validators: zodClient(LoginSchema)
	});

	const { form: formData, enhance, message } = form;
</script>

<div class="container flex h-screen w-screen flex-col items-center justify-start mt-10">
	<div class="mx-auto flex w-full flex-col justify-center space-y-6 sm:w-[350px]">
		<div class="flex flex-col space-y-2 text-center">
			<h1 class="text-2xl font-semibold tracking-tight">Login</h1>
			<p class="text-sm text-muted-foreground">Enter your email and password below to login</p>
		</div>

		{#if $message}
			<div class="rounded bg-red-100 p-3 text-sm text-red-700">
				{$message}
			</div>
		{/if}

		<form method="POST" use:enhance class="grid gap-4">
			<Field {form} name="email">
				<Control>
					{#snippet children({ props })}
						<Label>Email</Label>
						<Input
							{...props}
							type="email"
							bind:value={$formData.email}
							placeholder="name@example.com"
						/>
					{/snippet}
				</Control>
				<FieldErrors />
			</Field>

			<Field {form} name="password">
				<Control>
					{#snippet children({ props })}
						<Label>Password</Label>
						<Input
							{...props}
							type="password"
							bind:value={$formData.password}
							placeholder="Password"
						/>
					{/snippet}
				</Control>
				<FieldErrors />
			</Field>

			<Button type="submit">Login</Button>
		</form>
	</div>
</div>
