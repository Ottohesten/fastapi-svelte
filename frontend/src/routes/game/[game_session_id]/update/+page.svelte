<script lang="ts">
	import { superForm, fileProxy } from 'sveltekit-superforms';
	import SuperDebug from 'sveltekit-superforms';
	import Team from '$lib/components/Team.svelte';
	import Player from '$lib/components/Player.svelte';
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

<div class="min-h-screen bg-linear-to-br from-blue-50 to-indigo-100 p-4 sm:p-6 lg:p-8">
	<div class="mx-auto max-w-7xl space-y-8">
		<!-- Header -->
		<div class="text-center">
			<h1 class="text-2xl font-bold text-gray-900 sm:text-3xl lg:text-4xl">Game Management</h1>
			<p class="mt-2 text-sm text-gray-600 sm:text-base">
				Manage teams and players for {data.game_session.title || 'your game session'}
			</p>
		</div>

		<!-- Teams Section -->
		<div class="rounded-2xl bg-white p-4 shadow-lg sm:p-6">
			<h2 class="mb-4 text-xl font-bold text-gray-900 sm:mb-6 sm:text-2xl lg:text-3xl">Teams</h2>
			<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
				{#if data.game_session.teams.length === 0}
					<div class="col-span-full text-center text-gray-500">
						<p class="text-sm sm:text-base">No teams available.</p>
					</div>
				{/if}

				{#each data.game_session.teams as team}
					<Team {team} />
				{/each}
			</div>
		</div>

		<!-- Players Section -->
		<div class="rounded-2xl bg-white p-4 shadow-lg sm:p-6">
			<h2 class="mb-4 text-xl font-bold text-gray-900 sm:mb-6 sm:text-2xl lg:text-3xl">Players</h2>
			<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
				{#if data.game_session.teams.length === 0}
					<div class="col-span-full text-center text-gray-500">
						<p class="text-sm sm:text-base">No teams available.</p>
					</div>
				{/if}
				{#if data.game_session.players.length === 0}
					<div class="col-span-full text-center text-gray-500">
						<p class="text-sm sm:text-base">No players available.</p>
					</div>
				{/if}
				{#each data.game_session.players as player}
					<Player {player} />
				{/each}
			</div>
		</div>
		<!-- Create Team Section -->
		<div class="rounded-2xl bg-white p-4 shadow-lg sm:p-6">
			<h2 class="mb-4 text-xl font-bold text-gray-900 sm:mb-6 sm:text-2xl lg:text-3xl">
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
					<div class="rounded-lg bg-blue-50 p-3 text-center">
						<h3 class="text-sm font-medium text-blue-800 sm:text-base">{$message}</h3>
					</div>
				{/if}
				<div class="space-y-2">
					<label class="text-sm font-semibold text-gray-700 sm:text-base" for="name"
						>Team Name</label
					>
					<input
						class="w-full rounded-lg border-2 border-gray-300 bg-white px-4 py-2 text-base transition-colors hover:border-blue-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100 sm:py-3"
						type="text"
						name="team_name"
						aria-invalid={$errors.name ? 'true' : undefined}
						bind:value={$form.name}
						{...$constraints.name}
						required
						placeholder="Enter team name"
					/>
					{#if $errors.name}
						<span class="text-sm text-red-600">{$errors.name}</span>
					{/if}
				</div>
				<button
					type="submit"
					class="w-full rounded-lg bg-blue-600 px-4 py-2 font-medium text-white transition-colors hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-100 sm:w-auto sm:px-6 sm:py-3"
				>
					Add Team
				</button>
			</form>
		</div>

		<!-- Create Player Section -->
		<div class="rounded-2xl bg-white p-4 shadow-lg sm:p-6">
			<h2 class="mb-4 text-xl font-bold text-gray-900 sm:mb-6 sm:text-2xl lg:text-3xl">
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
					<div class="rounded-lg bg-blue-50 p-3 text-center">
						<h3 class="text-sm font-medium text-blue-800 sm:text-base">{$playerMessage}</h3>
					</div>
				{/if}
				<div class="space-y-2">
					<label class="text-sm font-semibold text-gray-700 sm:text-base" for="name"
						>Player Name</label
					>
					<input
						class="w-full rounded-lg border-2 border-gray-300 bg-white px-4 py-2 text-base transition-colors hover:border-blue-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100 sm:py-3"
						type="text"
						name="player_name"
						aria-invalid={$playerErrors.name ? 'true' : undefined}
						bind:value={$playerForm.name}
						{...$playerConstraints.name}
						required
						placeholder="Enter player name"
					/>
					{#if $playerErrors.name}
						<span class="text-sm text-red-600">{$playerErrors.name}</span>
					{/if}
				</div>
				<div class="space-y-2">
					<label class="text-sm font-semibold text-gray-700 sm:text-base" for="team_id"
						>Team (Optional)</label
					>
					<select
						class="w-full cursor-pointer rounded-lg border-2 border-gray-300 bg-white px-4 py-2 text-base transition-colors hover:border-blue-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100 sm:py-3"
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
						<span class="text-sm text-red-600">{$playerErrors.team_id}</span>
					{/if}
				</div>
				<button
					type="submit"
					class="w-full rounded-lg bg-blue-600 px-4 py-2 font-medium text-white transition-colors hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-100 sm:w-auto sm:px-6 sm:py-3"
				>
					Add Player
				</button>
			</form>
		</div>
	</div>
</div>
