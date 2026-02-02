<script lang="ts">
	import { superForm, fileProxy } from 'sveltekit-superforms';
	import SuperDebug from 'sveltekit-superforms';
	import Team from '$lib/components/Team.svelte';
	import Player from '$lib/components/Player.svelte';
	import { Input } from '$lib/components/ui/input';
	import { Button } from '$lib/components/ui/button';
	import * as Select from "$lib/components/ui/select/index.js";
	import { Field, Control, Label, FieldErrors, Description } from 'formsnap';

	let { data } = $props();

	const teamForm = superForm(data.teamForm, {
		dataType: 'json'
	});
	const { form: teamFormData, errors, message, constraints, enhance } = teamForm;

	const playerForm = superForm(data.playerForm, {
		dataType: 'json'
	});
	const {
		form: playerFormData,
		errors: playerErrors,
		message: playerMessage,
		constraints: playerConstraints,
		enhance: playerEnhance
	} = playerForm;
</script>

<!-- <SuperDebug data={$form} /> -->
<!-- <SuperDebug data={$playerForm} /> -->

<div
	class="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-4 sm:p-6 lg:p-8 dark:from-gray-950 dark:to-gray-900"
>
	<div class="mx-auto max-w-7xl space-y-8">
		<!-- Header -->
		<div class="text-center">
			<h1 class="text-2xl font-bold text-gray-900 sm:text-3xl lg:text-4xl dark:text-gray-100">
				Game Management
			</h1>
			<p class="mt-2 text-sm text-gray-600 sm:text-base dark:text-gray-300">
				Manage teams and players for {data.game_session.title || 'your game session'}
			</p>
		</div>

		<!-- Teams Section -->
		<div class="surface-2 rounded-2xl p-4 sm:p-6">
			<h2
				class="mb-4 text-xl font-bold text-gray-900 sm:mb-6 sm:text-2xl lg:text-3xl dark:text-gray-100"
			>
				Teams
			</h2>
			<div class="grid grid-cols-1 gap-4 sm:grid-cols-3 xl:grid-cols-5">
				{#if data.game_session.teams.length === 0}
					<div class="col-span-full text-center text-gray-500 dark:text-gray-400">
						<p class="text-sm sm:text-base">No teams available.</p>
					</div>
				{/if}

				{#each data.game_session.teams as team}
					<Team {team} />
				{/each}
			</div>
		</div>

		<!-- Players Section -->
		<div class="surface-2 rounded-2xl p-4 sm:p-6">
			<h2
				class="mb-4 text-xl font-bold text-gray-900 sm:mb-6 sm:text-2xl lg:text-3xl dark:text-gray-100"
			>
				Players
			</h2>
			<div class="grid grid-cols-1 gap-4 sm:grid-cols-3 xl:grid-cols-5">
				{#if data.game_session.teams.length === 0}
					<div class="col-span-full text-center text-gray-500 dark:text-gray-400">
						<p class="text-sm sm:text-base">No teams available.</p>
					</div>
				{/if}
				{#if data.game_session.players.length === 0}
					<div class="col-span-full text-center text-gray-500 dark:text-gray-400">
						<p class="text-sm sm:text-base">No players available.</p>
					</div>
				{/if}
				{#each data.game_session.players as player}
					<Player {player} />
				{/each}
			</div>
		</div>
		<!-- Create Team Section -->
		<div class="surface-2 rounded-2xl p-4 sm:p-6">
			<h2
				class="mb-4 text-xl font-bold text-gray-900 sm:mb-6 sm:text-2xl lg:text-3xl dark:text-gray-100"
			>
				Create Team
			</h2>
			<form
				method="POST"
				action="?/addTeam"
				enctype="multipart/form-data"
				use:enhance
				class="space-y-4"
			>
				{#if $message}
					<div
						class="rounded-lg border border-blue-200 bg-blue-50 p-3 text-center dark:border-blue-900/40 dark:bg-blue-900/20"
					>
						<h3 class="text-sm font-medium text-blue-800 sm:text-base dark:text-blue-300">
							{$message}
						</h3>
					</div>
				{/if}
				<Field form={teamForm} name="name">
					<Control>
						{#snippet children({ props })}
							<Label class="text-sm font-semibold text-gray-700 sm:text-base dark:text-gray-200">
								Team Name
							</Label>
							<Input
								{...props}
								type="text"
								placeholder="Enter team name"
								bind:value={$teamFormData.name}
								required
							/>
						{/snippet}
					</Control>
					<FieldErrors class="text-sm text-red-600 dark:text-red-400" />
				</Field>
				<Button
					type="submit"
					class="w-full sm:w-auto"
				>
					Add Team
				</Button>
			</form>
		</div>

		<!-- Create Player Section -->
		<div class="surface-2 rounded-2xl p-4 sm:p-6">
			<h2
				class="mb-4 text-xl font-bold text-gray-900 sm:mb-6 sm:text-2xl lg:text-3xl dark:text-gray-100"
			>
				Create Player
			</h2>
			<form
				method="POST"
				action="?/addPlayer"
				enctype="multipart/form-data"
				use:playerEnhance
				class="space-y-4"
			>
				{#if $playerMessage}
					<div
						class="rounded-lg border border-blue-200 bg-blue-50 p-3 text-center dark:border-blue-900/40 dark:bg-blue-900/20"
					>
						<h3 class="text-sm font-medium text-blue-800 sm:text-base dark:text-blue-300">
							{$playerMessage}
						</h3>
					</div>
				{/if}
				<Field form={playerForm} name="name">
					<Control>
						{#snippet children({ props })}
							<Label class="text-sm font-semibold text-gray-700 sm:text-base dark:text-gray-200">
								Player Name
							</Label>
							<Input
								{...props}
								type="text"
								placeholder="Enter player name"
								bind:value={$playerFormData.name}
								required
							/>
						{/snippet}
					</Control>
					<FieldErrors class="text-sm text-red-600 dark:text-red-400" />
				</Field>
				<Field form={playerForm} name="team_id">
					<Control>
						{#snippet children({ props })}
							<Label class="text-sm font-semibold text-gray-700 sm:text-base dark:text-gray-200">
								Team (Optional)
							</Label>
							<select
								{...props}
								class="w-full cursor-pointer rounded-lg border-2 border-gray-300 bg-white px-4 py-2 text-base transition-colors hover:border-blue-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100 sm:py-3 dark:border-gray-800 dark:bg-gray-900/40 dark:text-gray-100"
								bind:value={$playerFormData.team_id}
							>
								<option value="">No Team</option>
								{#each data.game_session.teams as team}
									<option value={team.id}>{team.name}</option>
								{/each}
							</select>
						{/snippet}
					</Control>
					<FieldErrors class="text-sm text-red-600 dark:text-red-400" />
				</Field>
				<Button
					type="submit"
					class="w-full sm:w-auto"
				>
					Add Player
				</Button>
			</form>
		</div>
	</div>
</div>
