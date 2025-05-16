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

<SuperDebug data={$form} />

<div class="container">
	<div>
		<div>
			<!-- teams -->
			<h2 class="text-4xl font-bold">Teams:</h2>
			<div class="grid grid-cols-3 gap-4">
				{#if data.game_session.teams.length === 0}
					<p>No teams available.</p>
				{/if}

				{#each data.game_session.teams as team}
					<Team {team} />
				{/each}
			</div>
			<h2 class="text-4xl font-bold">Players:</h2>
			<div class="grid grid-cols-3 gap-4">
				{#if data.game_session.teams.length === 0}
					<p>No teams available.</p>
				{/if}
				{#if data.game_session.players.length === 0}
					<p>No players available.</p>
				{/if}
				{#each data.game_session.players as player}
					<Player {player} />
				{/each}
			</div>
		</div>

		<div class="mt-10">
			<h2 class="text-4xl font-bold">Create Team:</h2>
			<form method="POST" action="?/addTeam" enctype="multipart/form-data" use:enhance>
				{#if $message}<h3 class="text-center text-2xl">{$message}</h3>{/if}
				<div class="">
					<label class="" for="name">Team Name</label>
					<input
						class="w-full appearance-none rounded-md border bg-gray-50 p-2 text-gray-700 shadow"
						type="text"
						name="team_name"
						aria-invalid={$errors.name ? 'true' : undefined}
						bind:value={$form.name}
						{...$constraints.name}
						required
					/>
					{#if $errors.name}<span class="invalid">{$errors.name}</span>{/if}
				</div>
				<button
					type="submit"
					class="mt-4 rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-800"
					>Add Team
				</button>
			</form>
		</div>
		<div class="mt-10">
			<h2 class="text-4xl font-bold">Create Player:</h2>
			<form method="POST" action="?/addPlayer" enctype="multipart/form-data" use:playerEnhance>
				{#if $playerMessage}<h3 class="text-center text-2xl">{$playerMessage}</h3>{/if}
				<!-- {console.log($message)} -->
				<div class="">
					<label class="" for="name">Player Name</label>
					<input
						class="w-full appearance-none rounded-md border bg-gray-50 p-2 text-gray-700 shadow"
						type="text"
						name="player_name"
						aria-invalid={$playerErrors.name ? 'true' : undefined}
						bind:value={$playerForm.name}
						{...$playerConstraints.name}
						required
					/>
					{#if $playerErrors.name}<span class="invalid">{$playerErrors.name}</span>{/if}
				</div>
				<button
					type="submit"
					class="mt-4 rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-800"
					>Add Player
				</button>
			</form>
		</div>
	</div>
</div>
