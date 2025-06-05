<script lang="ts">
	let { data } = $props();
	import { scaleLinear, scaleBand } from 'd3-scale';
	import { max as d3Max } from 'd3-array';
	import { schemeCategory10 } from 'd3-scale-chromatic';
	import type { components } from '$lib/api/v1';
	import { onMount } from 'svelte';

	// Use the actual API types instead of custom interfaces
	type GameSession = components['schemas']['GameSessionPublic'];
	type Team = components['schemas']['GameTeamPublic'];
	type Player = components['schemas']['GamePlayerPublic'];
	type DrinkLink = components['schemas']['GamePlayerDrinkLinkPublic'];

	// gameSession is derived from the 'data' prop's 'game_session' property
	let gameSession = $derived(data.game_session);

	// State for interactivity
	let hoveredPlayer: string | null = $state(null);
	let selectedTeam: string | null = $state(null);
	let showAnimation = $state(false);

	// 1. Process Data: Get all players with their total drinks
	let allPlayersData = $derived(
		gameSession?.players?.map((player) => ({
			name: player.name,
			playerId: player.id,
			teamName: player.team?.name || 'No Team',
			teamId: player.team_id,
			totalDrinks:
				player.drink_links?.reduce(
					(sum: number, drinkLink: DrinkLink) => sum + drinkLink.amount,
					0
				) || 0
		})) ?? []
	);

	// Filter data based on selected team
	let filteredPlayersData = $derived(
		selectedTeam && selectedTeam !== 'all'
			? allPlayersData.filter((p) => p.teamName === selectedTeam)
			: allPlayersData
	);
	// Get unique teams for filter dropdown
	let teams = $derived(Array.from(new Set(allPlayersData.map((p) => p.teamName))).sort());

	// Stable color assignment that preserves team colors when new teams are added
	let teamColorMap = $state(new Map<string, string>());

	// Color scale for teams with stable color assignment
	let colorScale = $derived.by(() => {
		const colors = schemeCategory10;

		// Assign colors to new teams while preserving existing assignments
		teams.forEach((team, index) => {
			if (!teamColorMap.has(team)) {
				// Find the next available color that's not already used
				let colorIndex = 0;
				let assignedColor = colors[colorIndex];

				// Check if this color is already used by another team
				const usedColors = Array.from(teamColorMap.values());
				while (usedColors.includes(assignedColor) && colorIndex < colors.length - 1) {
					colorIndex++;
					assignedColor = colors[colorIndex];
				}

				teamColorMap.set(team, assignedColor);
			}
		});

		// Return a function that gets the color for a team
		return (teamName: string) => teamColorMap.get(teamName) || schemeCategory10[0];
	});

	// 2. Dimensions, Margins & Scales
	const padding = { top: 40, right: 20, bottom: 80, left: 60 };
	let width = $state(800);
	let height = $state(500);

	let xScale = $derived(
		scaleBand<string>()
			.domain(filteredPlayersData.map((p) => p.name))
			.range([padding.left, width - padding.right])
			.padding(0.15)
	);

	let yScale = $derived(
		scaleLinear()
			.domain([0, d3Max(allPlayersData, (p) => p.totalDrinks) ?? 0])
			.range([height - padding.bottom, padding.top])
			.nice()
	);

	// For y-axis ticks
	let yTicks = $derived(yScale.ticks(6));
	// $inspect(yTicks);

	// Animation on mount
	onMount(() => {
		setTimeout(() => {
			showAnimation = true;
		}, 100);
	});

	// Helper functions

	function handleBarLeave() {
		hoveredPlayer = null;
	}
</script>

<div class="mx-auto max-w-7xl p-4 font-sans md:p-8">
	<div class="mb-8 border-b-2 border-gray-200 pb-6 text-center">
		<h1 class="mb-2 text-3xl font-bold text-gray-800 md:text-4xl">Game Session Dashboard</h1>
		<p class="text-lg text-gray-600">
			Session: <strong>{gameSession.title}</strong>
		</p>
	</div>

	<div class="mb-8 flex flex-col items-start justify-between gap-6 lg:flex-row lg:items-center">
		<div class="flex items-center gap-2">
			<label for="team-filter" class="font-semibold text-gray-700">Filter by Team:</label>
			<select
				id="team-filter"
				bind:value={selectedTeam}
				class="cursor-pointer rounded-lg border-2 border-gray-300 bg-white px-4 py-2 text-base transition-colors hover:border-blue-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
			>
				<option value="all">All Teams</option>
				{#each teams as team}
					<option value={team}>{team}</option>
				{/each}
			</select>
		</div>

		<div class="flex gap-4">
			<div
				class="rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 px-6 py-4 text-center text-white shadow-lg"
			>
				<div class="text-2xl font-bold">{filteredPlayersData.length}</div>
				<div class="mt-1 text-sm opacity-90">Players</div>
			</div>
			<div
				class="rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 px-6 py-4 text-center text-white shadow-lg"
			>
				<div class="text-2xl font-bold">
					{filteredPlayersData.reduce((sum, p) => sum + p.totalDrinks, 0)}
				</div>
				<div class="mt-1 text-sm opacity-90">Total Drinks</div>
			</div>
			<div
				class="rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 px-6 py-4 text-center text-white shadow-lg"
			>
				<div class="text-2xl font-bold">{teams.length}</div>
				<div class="mt-1 text-sm opacity-90">Teams</div>
			</div>
		</div>
	</div>

	<div class="mb-8 rounded-2xl bg-white p-6 shadow-xl md:p-8" bind:clientWidth={width}>
		<h2 class="mb-4 text-center text-2xl font-semibold text-gray-800">
			Drinks Consumed per Player
		</h2>

		{#if filteredPlayersData.length > 0}
			<svg {width} {height}>
				<!-- Background grid lines -->
				<g class="grid">
					{#each yTicks as tick}
						<line
							x1={padding.left}
							x2={width - padding.right}
							y1={yScale(tick)}
							y2={yScale(tick)}
							stroke="#f0f0f0"
							stroke-width="1"
						/>
					{/each}
				</g>

				<!-- Bars -->
				<g class="bars">
					{#each filteredPlayersData as player (player.playerId)}
						{@const barHeight = showAnimation ? yScale(0) - yScale(player.totalDrinks) : 0}
						<rect
							x={xScale(player.name)}
							y={yScale(player.totalDrinks)}
							width={xScale.bandwidth()}
							height={barHeight}
							fill={colorScale(player.teamName)}
							stroke={hoveredPlayer === player.name ? '#333' : 'rgba(255,255,255,0.8)'}
							stroke-width={hoveredPlayer === player.name ? '2' : '1'}
							opacity={hoveredPlayer && hoveredPlayer !== player.name ? 0.6 : 1}
							class="cursor-pointer drop-shadow-sm transition-all duration-300 ease-in-out hover:-translate-y-0.5 hover:drop-shadow-md"
							role="button"
							tabindex="0"
							onmouseenter={() => (hoveredPlayer = player.name)}
							onmouseleave={handleBarLeave}
							onfocus={() => (hoveredPlayer = player.name)}
							onblur={handleBarLeave}
						>
							<title>{player.name} ({player.teamName}): {player.totalDrinks} drinks</title>
						</rect>

						<!-- Value labels on top of bars -->
						{#if player.totalDrinks > 0}
							<text
								x={(xScale(player.name) ?? 0) + xScale.bandwidth() / 2}
								y={yScale(player.totalDrinks) - 5}
								text-anchor="middle"
								class="fill-gray-700 text-xs font-semibold transition-opacity duration-500"
								opacity={showAnimation ? 1 : 0}
							>
								{player.totalDrinks}
							</text>
						{/if}
					{/each}
				</g>
				<!-- Y-axis -->
				<g class="font-inherit">
					<!-- Axis line -->
					<line
						x1={padding.left}
						x2={padding.left}
						y1={padding.top}
						y2={height - padding.bottom}
						stroke="#333"
						stroke-width="2"
					/>

					{#each yTicks as tick}
						<g class="tick" transform="translate({padding.left}, {yScale(tick)})">
							<line x1="-6" x2="0" stroke="#333" stroke-width="1" />
							<text dy="0.32em" x="-10" text-anchor="end" class="fill-gray-700 text-sm">{tick}</text
							>
						</g>
					{/each}

					<!-- Y-axis label -->
					<text
						transform="rotate(-90)"
						y={padding.left - 40}
						x={-(height - padding.bottom + padding.top) / 2}
						text-anchor="middle"
						class="fill-gray-800 text-base font-semibold"
					>
						Total Drinks Consumed
					</text>
				</g>
				<!-- X-axis -->
				<g class="font-inherit">
					<!-- Axis line -->
					<line
						x1={padding.left}
						x2={width - padding.right}
						y1={height - padding.bottom}
						y2={height - padding.bottom}
						stroke="#333"
						stroke-width="2"
					/>

					{#each filteredPlayersData as player}
						<g
							class="tick"
							transform="translate({(xScale(player.name) ?? 0) + xScale.bandwidth() / 2}, {height -
								padding.bottom})"
						>
							<line y1="0" y2="6" stroke="#333" stroke-width="1" />
							<text
								y="20"
								text-anchor="middle"
								class="text-sm font-medium transition-all duration-200"
								fill={colorScale(player.teamName)}
								font-weight={hoveredPlayer === player.name ? 'bold' : 'normal'}
							>
								{player.name}
							</text>
							<text y="35" text-anchor="middle" class="fill-gray-600 text-xs opacity-70">
								{player.teamName}
							</text>
						</g>
					{/each}
				</g>
			</svg>
			<!-- Tooltip for hovered player -->
			{#if hoveredPlayer}
				{@const player = filteredPlayersData.find((p) => p.name === hoveredPlayer)}
				{#if player}
					<div
						class="pointer-events-none absolute left-1/2 top-1/2 z-50 -translate-x-1/2 -translate-y-1/2 rounded-lg bg-black/90 px-3 py-2 text-sm text-white shadow-lg"
					>
						<div class="mb-1 font-semibold">{player.name}</div>
						<div class="text-xs opacity-90">Team: {player.teamName}</div>
						<div class="text-xs opacity-90">Drinks: {player.totalDrinks}</div>
					</div>
				{/if}
			{/if}
		{:else}
			<div class="p-12 text-center text-gray-500">
				<p class="m-0 text-lg">No player data available for this game session.</p>
			</div>
		{/if}
	</div>
	<!-- Team Legend -->
	{#if teams.length > 1}
		<div class="rounded-2xl bg-white p-6 shadow-lg">
			<h3 class="mb-4 text-lg font-semibold text-gray-800">Teams</h3>
			<div class="flex flex-wrap gap-4">
				{#each teams as team}
					<div class="flex items-center gap-2 text-sm text-gray-700">
						<div
							class="h-4 w-4 rounded border border-black/10"
							style="background-color: {colorScale(team)}"
						></div>
						<span>{team}</span>
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div>
