<script lang="ts">
	import { superForm, fileProxy } from 'sveltekit-superforms';
	import SuperDebug from 'sveltekit-superforms';
	import Team from '$lib/components/Team.svelte';
	import Player from '$lib/components/Player.svelte';
	import { Input } from '$lib/components/ui/input';
	let { data } = $props();
	const { form, errors, message, constraints, enhance } = superForm(data.teamForm, {
		dataType: 'json'
	});

	const {
		form: playerForm,
		errors: playerErrors,
		message: playerMessage,
		constraints: playerConstraints,
		enhance: playerEnhance
	} = superForm(data.playerForm, {
		dataType: 'json'
	});
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
				<div class="space-y-2">
					<label
						class="text-sm font-semibold text-gray-700 sm:text-base dark:text-gray-200"
						for="name">Team Name</label
					>
					<Input
						type="text"
						name="team_name"
						aria-invalid={$errors.name ? 'true' : undefined}
						bind:value={$form.name}
						{...$constraints.name}
						required
						placeholder="Enter team name"
					/>
					{#if $errors.name}
						<span class="text-sm text-red-600 dark:text-red-400">{$errors.name}</span>
					{/if}
				</div>
				<button
					type="submit"
					class="w-full rounded-lg bg-blue-600 px-4 py-2 font-medium text-white transition-colors hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20 sm:w-auto sm:px-6 sm:py-3 dark:focus:ring-blue-400/30"
				>
					Add Team
				</button>
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
				<div class="space-y-2">
					<label
						class="text-sm font-semibold text-gray-700 sm:text-base dark:text-gray-200"
						for="name">Player Name</label
					>
					<Input
						type="text"
						name="player_name"
						aria-invalid={$playerErrors.name ? 'true' : undefined}
						bind:value={$playerForm.name}
						{...$playerConstraints.name}
						required
						placeholder="Enter player name"
					/>
					{#if $playerErrors.name}
						<span class="text-sm text-red-600 dark:text-red-400">{$playerErrors.name}</span>
					{/if}
				</div>
				<div class="space-y-2">
					<label
						class="text-sm font-semibold text-gray-700 sm:text-base dark:text-gray-200"
						for="team_id">Team (Optional)</label
					>
					<select
						class="w-full cursor-pointer rounded-lg border-2 border-gray-300 bg-white px-4 py-2 text-base transition-colors hover:border-blue-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100 sm:py-3 dark:border-gray-800 dark:bg-gray-900/40 dark:text-gray-100"
						name="team_id"
						bind:value={$playerForm.team_id}
						aria-invalid={$playerErrors.team_id ? 'true' : undefined}
					>
						<option value="">No Team</option>
						{#each data.game_session.teams as team}
							<option value={team.id}>{team.name}</option>
						{/each}
					</select>
					{#if $playerErrors.team_id}
						<span class="text-sm text-red-600 dark:text-red-400">{$playerErrors.team_id}</span>
					{/if}
				</div>
				<button
					type="submit"
					class="w-full rounded-lg bg-blue-600 px-4 py-2 font-medium text-white transition-colors hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500/20 sm:w-auto sm:px-6 sm:py-3 dark:focus:ring-blue-400/30"
				>
					Add Player
				</button>
			</form>
		</div>
	</div>
</div>
