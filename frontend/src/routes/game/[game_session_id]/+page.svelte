<script lang="ts">
	let { data } = $props();
	import { schemeCategory10, schemeSet3 } from 'd3-scale-chromatic';
	import { scaleLinear, scaleBand, scaleOrdinal } from 'd3-scale';
	import { max as d3Max } from 'd3-array';
	import type { components } from '$lib/api/v1';
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import Button from '$lib/components/ui/button/button.svelte';
	import { Pencil, Trash2 } from 'lucide-svelte';
	import { enhance } from '$app/forms';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { Input } from '$lib/components/ui/input';
	// Use the actual API types instead of custom interfaces
	type GameSession = components['schemas']['GameSessionPublic'];
	type Team = components['schemas']['GameTeamPublic'];
	type Player = components['schemas']['GamePlayerPublic'];
	type DrinkLink = components['schemas']['GamePlayerDrinkLinkPublic'];

	// Default values for dashboard state
	const DEFAULT_VIEW_MODE: 'overview' | 'charts' | 'players' | 'teams' = 'charts';
	const DEFAULT_CHART_TYPE: 'drinks' | 'players' = 'drinks';
	// gameSession is derived from the 'data' prop's 'game_session' property
	let gameSession = $derived(data.game_session);

	// State for interactivity - initialize from URL parameters
	let selectedTeam: string | null = $state(null);
	let selectedPlayer: string | null = $state(null);
	let showAnimation = $state(false);
	let viewMode: 'overview' | 'charts' | 'players' | 'teams' = $state(DEFAULT_VIEW_MODE);
	let chartType: 'drinks' | 'players' = $state(DEFAULT_CHART_TYPE);
	let hoveredSegment: string | null = $state(null);
	let open = $state(false);

	// Function to update URL with current state
	function updateURL() {
		if (!browser) return;

		const searchParams = new URLSearchParams();

		if (selectedTeam && selectedTeam !== 'all') {
			searchParams.set('team', selectedTeam);
			// console.log(`Selected team: ${selectedTeam}`);
		}
		if (selectedPlayer) {
			searchParams.set('player', selectedPlayer);
		}
		if (viewMode !== DEFAULT_VIEW_MODE) {
			searchParams.set('view', viewMode);
		}
		if (chartType !== DEFAULT_CHART_TYPE) {
			searchParams.set('chart', chartType);
		}

		const newUrl = `${window.location.pathname}${searchParams.toString() ? '?' + searchParams.toString() : ''}`;
		if (newUrl !== window.location.pathname + window.location.search) {
			goto(newUrl, { replaceState: true, noScroll: true });
		}
	}
	// Function to restore state from URL
	function restoreFromURL() {
		if (!browser) return;

		const urlParams = new URLSearchParams(window.location.search);
		const teamParam = urlParams.get('team');
		selectedTeam = teamParam === 'all' || !teamParam ? null : teamParam;
		selectedPlayer = urlParams.get('player') || null;
		viewMode = (urlParams.get('view') as typeof viewMode) || DEFAULT_VIEW_MODE;
		chartType = (urlParams.get('chart') as typeof chartType) || DEFAULT_CHART_TYPE;
	}
	// Tooltip state
	let tooltip = $state({
		visible: false,
		x: 0,
		y: 0,
		content: {
			title: '',
			subtitle: '',
			amount: 0,
			percentage: 0,
			color: '',
			details: [] as { name: string; value: number }[]
		}
	});

	// Process player data with drink breakdowns
	let allPlayersData = $derived(
		gameSession?.players?.map((player) => {
			const drinkBreakdown = new Map<string, { name: string; amount: number }>();

			player.drink_links?.forEach((drinkLink: DrinkLink) => {
				const drinkName = drinkLink.drink?.name || 'Unknown Drink';
				if (drinkBreakdown.has(drinkName)) {
					drinkBreakdown.get(drinkName)!.amount += drinkLink.amount;
				} else {
					drinkBreakdown.set(drinkName, { name: drinkName, amount: drinkLink.amount });
				}
			});

			return {
				name: player.name,
				playerId: player.id,
				teamName: player.team?.name || 'No Team',
				teamId: player.team_id,
				totalDrinks:
					player.drink_links?.reduce(
						(sum: number, drinkLink: DrinkLink) => sum + drinkLink.amount,
						0
					) || 0,
				drinkBreakdown: Array.from(drinkBreakdown.values()).sort((a, b) => b.amount - a.amount)
			};
		}) ?? []
	);
	// Process team data with aggregations and drink breakdowns
	let teamsData = $derived(() => {
		const teamMap = new Map<
			string,
			{
				name: string;
				id: string | null;
				totalDrinks: number;
				playerCount: number;
				players: typeof allPlayersData;
				drinkBreakdown: { name: string; amount: number }[];
			}
		>();

		allPlayersData.forEach((player) => {
			const teamName = player.teamName;
			if (!teamMap.has(teamName)) {
				teamMap.set(teamName, {
					name: teamName,
					id: player.teamId || null,
					totalDrinks: 0,
					playerCount: 0,
					players: [],
					drinkBreakdown: []
				});
			}

			const team = teamMap.get(teamName)!;
			team.totalDrinks += player.totalDrinks;
			team.playerCount += 1;
			team.players.push(player);
		});

		// Calculate drink breakdowns for each team
		teamMap.forEach((team) => {
			const drinkMap = new Map<string, number>();
			team.players.forEach((player) => {
				player.drinkBreakdown.forEach((drink) => {
					drinkMap.set(drink.name, (drinkMap.get(drink.name) || 0) + drink.amount);
				});
			});
			team.drinkBreakdown = Array.from(drinkMap.entries())
				.map(([name, amount]) => ({ name, amount }))
				.sort((a, b) => b.amount - a.amount);
		});

		return Array.from(teamMap.values()).sort((a, b) => b.totalDrinks - a.totalDrinks);
	});

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

	// Get all unique drinks across all teams for consistent coloring
	let allDrinks = $derived(() => {
		const drinkSet = new Set<string>();
		teamsData().forEach((team) => {
			team.drinkBreakdown.forEach((drink) => drinkSet.add(drink.name));
		});
		return Array.from(drinkSet).sort();
	});

	// Color scale for drinks
	let drinkColorScale = $derived(scaleOrdinal<string>().domain(allDrinks()).range(schemeSet3));

	// Color scale for players within teams
	let playerColorScale = $derived(
		scaleOrdinal<string>()
			.domain(allPlayersData.map((p) => p.name))
			.range(schemeCategory10)
	);

	// Chart dimensions
	const chartMargin = { top: 20, right: 20, bottom: 60, left: 60 };
	let chartWidth = $state(800);
	let chartHeight = $state(400);

	// Chart scales
	let xScale = $derived(
		scaleBand<string>()
			.domain(teamsData().map((team) => team.name))
			.range([chartMargin.left, chartWidth - chartMargin.right])
			.padding(0.2)
	);

	let yScale = $derived(
		scaleLinear()
			.domain([0, d3Max(teamsData(), (team) => team.totalDrinks) || 0])
			.range([chartHeight - chartMargin.bottom, chartMargin.top])
			.nice()
	);

	let yTicks = $derived(yScale.ticks(6));
	// Animation on mount
	onMount(() => {
		// Restore state from URL first
		restoreFromURL();

		setTimeout(() => {
			showAnimation = true;
		}, 100);
	});

	// Reactive effects to update URL when state changes
	$effect(() => {
		// Update URL whenever state changes (after initial load)
		if (browser) {
			updateURL();
		}
	}); // Helper functions
	function getTopDrinks(drinkBreakdown: { name: string; amount: number }[], limit: number = 3) {
		return drinkBreakdown.slice(0, limit);
	}

	function formatPercentage(value: number, total: number): string {
		return total > 0 ? `${Math.round((value / total) * 100)}%` : '0%';
	}

	// Get top players for a specific drink within a team
	function getTopPlayersForDrink(teamName: string, drinkName: string, limit: number = 3) {
		const teamData = teamsData().find((team) => team.name === teamName);
		if (!teamData) return [];

		const playersWithDrink = teamData.players
			.map((player) => {
				const drinkAmount =
					player.drinkBreakdown.find((drink) => drink.name === drinkName)?.amount || 0;
				return { name: player.name, value: drinkAmount };
			})
			.filter((player) => player.value > 0)
			.sort((a, b) => b.value - a.value)
			.slice(0, limit);

		return playersWithDrink;
	}

	// Get top drinks for a specific player
	function getTopDrinksForPlayer(playerName: string, limit: number = 3) {
		const player = allPlayersData.find((p) => p.name === playerName);
		if (!player) return [];

		return player.drinkBreakdown
			.slice(0, limit)
			.map((drink) => ({ name: drink.name, value: drink.amount }));
	} // Tooltip functions
	function showTooltip(event: MouseEvent, segment: any, teamTotal: number) {
		// Only update tooltip if it's not already showing the same segment
		const segmentKey =
			chartType === 'drinks'
				? `${segment.team}-${segment.drink}`
				: `${segment.team}-${segment.player}`;

		if (hoveredSegment === segmentKey && tooltip.visible) {
			return; // Don't recalculate if same segment
		}

		hoveredSegment = segmentKey;

		const containerRect = (event.target as SVGElement)
			.closest('.chart-container')
			?.getBoundingClientRect();
		if (containerRect) {
			// Get the center of the hovered bar segment for stable positioning
			const rect = (event.target as SVGElement).getBoundingClientRect();
			const centerX = rect.left + rect.width / 2 - containerRect.left;
			const centerY = rect.top + rect.height / 2 - containerRect.top;

			// Tooltip dimensions
			const tooltipWidth = 280;
			const tooltipHeight = 200;
			const padding = 15;

			// Start with tooltip positioned above and centered on the bar
			let adjustedX = centerX - tooltipWidth / 2;
			let adjustedY = centerY - tooltipHeight - padding;

			// Horizontal bounds checking
			if (adjustedX < padding) {
				adjustedX = padding;
			}
			if (adjustedX + tooltipWidth > containerRect.width - padding) {
				adjustedX = containerRect.width - tooltipWidth - padding;
			}

			// Vertical bounds checking
			if (adjustedY < padding) {
				// Position below the bar instead
				adjustedY = centerY + rect.height / 2 + padding;

				// If still doesn't fit, position in middle
				if (adjustedY + tooltipHeight > containerRect.height - padding) {
					adjustedY = Math.max(padding, (containerRect.height - tooltipHeight) / 2);
				}
			}

			tooltip.visible = true;
			tooltip.x = adjustedX;
			tooltip.y = adjustedY;
			if (chartType === 'drinks') {
				const topPlayers = getTopPlayersForDrink(segment.team, segment.drink, 3);
				tooltip.content = {
					title: segment.drink,
					subtitle: `Team: ${segment.team}`,
					amount: segment.amount,
					percentage: Math.round((segment.amount / teamTotal) * 100),
					color: segment.color,
					details: topPlayers
				};
			} else {
				const topDrinks = getTopDrinksForPlayer(segment.player, 3);
				tooltip.content = {
					title: segment.player,
					subtitle: `Team: ${segment.team}`,
					amount: segment.amount,
					percentage: Math.round((segment.amount / teamTotal) * 100),
					color: segment.color,
					details: topDrinks
				};
			}
		}
	}

	function hideTooltip() {
		tooltip.visible = false;
		hoveredSegment = null;
	}

	// Create stacked data for drinks
	function createStackedDrinkData() {
		return teamsData().map((team) => {
			let runningTotal = 0;
			const segments = team.drinkBreakdown.map((drink) => {
				const segment = {
					drink: drink.name,
					team: team.name,
					amount: drink.amount,
					y0: runningTotal,
					y1: runningTotal + drink.amount,
					color: drinkColorScale(drink.name)
				};
				runningTotal += drink.amount;
				return segment;
			});
			return { team: team.name, segments, total: team.totalDrinks };
		});
	}

	// Create stacked data for players
	function createStackedPlayerData() {
		return teamsData().map((team) => {
			let runningTotal = 0;
			const segments = team.players
				.sort((a, b) => b.totalDrinks - a.totalDrinks)
				.map((player) => {
					const segment = {
						player: player.name,
						team: team.name,
						amount: player.totalDrinks,
						y0: runningTotal,
						y1: runningTotal + player.totalDrinks,
						color: playerColorScale(player.name)
					};
					runningTotal += player.totalDrinks;
					return segment;
				});
			return { team: team.name, segments, total: team.totalDrinks };
		});
	}

	let stackedDrinkData = $derived(createStackedDrinkData());
	let stackedPlayerData = $derived(createStackedPlayerData());
</script>

<div class="mx-auto max-w-7xl p-4 font-sans md:p-8">
	<!-- Header -->
	<div class="mb-8 border-b-2 border-gray-200 pb-6 text-center">
		<h1 class="mb-2 text-3xl font-bold text-gray-800 md:text-4xl">Game Session Dashboard</h1>
		<p class="text-lg text-gray-600">
			Session: <strong>{gameSession.title}</strong>
		</p>
	</div>

	<!-- Controls -->
	<div class="mb-8 flex flex-col items-start justify-between gap-6 lg:flex-row lg:items-center">
		<div class="flex flex-wrap items-center gap-4">
			<div class="flex items-center gap-2">
				<label for="team-filter" class="font-semibold text-gray-700">Filter by Team:</label>
				<select
					id="team-filter"
					value={selectedTeam || 'all'}
					onchange={(e) =>
						(selectedTeam =
							(e.target as HTMLSelectElement).value === 'all'
								? null
								: (e.target as HTMLSelectElement).value)}
					class="cursor-pointer rounded-lg border-2 border-gray-300 bg-white px-4 py-2 text-base transition-colors hover:border-blue-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
				>
					<option value="all">All Teams</option>
					{#each teams as team}
						<option value={team}>{team}</option>
					{/each}
				</select>
			</div>

			<div class="flex items-center gap-2">
				<label for="view-mode" class="font-semibold text-gray-700">View:</label>
				<select
					id="view-mode"
					bind:value={viewMode}
					class="cursor-pointer rounded-lg border-2 border-gray-300 bg-white px-4 py-2 text-base transition-colors hover:border-blue-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
				>
					<option value="overview">Overview</option>
					<option value="charts">Team Charts</option>
					<option value="players">Players Detail</option>
					<option value="teams">Teams Detail</option>
				</select>
			</div>
		</div>

		<!-- Summary Stats -->
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

	<!-- Main Content -->
	{#if viewMode === 'overview'}
		<!-- Overview Mode -->
		<div class="space-y-8">
			<!-- Teams Overview -->
			<div class="rounded-2xl bg-white p-6 shadow-xl">
				<h2 class="mb-6 text-2xl font-semibold text-gray-800">Teams Overview</h2>
				<div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
					{#each teamsData() as team}
						<!-- {console.log(selectedTeam === team.name)} -->
						<div
							class="cursor-pointer rounded-lg border-2 border-gray-200 p-4 transition-all hover:border-blue-400 hover:shadow-lg {selectedTeam ===
							team.name
								? '-translate-y-2 border-black shadow-lg'
								: ''}"
							style="border-left: 4px solid {colorScale(team.name)}"
							role="button"
							tabindex="0"
							onclick={() => (selectedTeam = selectedTeam === team.name ? null : team.name)}
							onkeydown={(e) => {
								if (e.key === 'Enter' || e.key === ' ') {
									e.preventDefault();
									selectedTeam = selectedTeam === team.name ? null : team.name;
								}
							}}
						>
							<h3 class="mb-2 text-lg font-semibold" style="color: {colorScale(team.name)}">
								{team.name}
							</h3>
							<div class="space-y-2 text-sm text-gray-600">
								<div class="flex justify-between">
									<span>Players:</span>
									<span class="font-medium">{team.playerCount}</span>
								</div>
								<div class="flex justify-between">
									<span>Total Drinks:</span>
									<span class="font-medium">{team.totalDrinks}</span>
								</div>
								<div class="flex justify-between">
									<span>Avg per Player:</span>
									<span class="font-medium">{(team.totalDrinks / team.playerCount).toFixed(1)}</span
									>
								</div>
							</div>
							{#if team.drinkBreakdown.length > 0}
								<div class="mt-3 border-t border-gray-200 pt-3">
									<div class="mb-2 text-xs font-medium text-gray-500">Top Drinks:</div>
									{#each getTopDrinks(team.drinkBreakdown, 3) as drink}
										<div class="flex justify-between text-xs text-gray-600">
											<span>{drink.name}</span>
											<span>{drink.amount}</span>
										</div>
									{/each}
								</div>
							{/if}
						</div>
					{/each}
				</div>
			</div>

			<!-- Top Players -->
			<div class="rounded-2xl bg-white p-6 shadow-xl">
				<h2 class="mb-6 text-2xl font-semibold text-gray-800">Top Players</h2>
				<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
					{#each filteredPlayersData
						.sort((a, b) => b.totalDrinks - a.totalDrinks)
						.slice(0, 8) as player}
						<div
							class="cursor-pointer rounded-lg border-2 border-gray-200 p-4 transition-all hover:border-blue-400 hover:shadow-lg"
							class:border-blue-500={selectedPlayer === player.name}
							role="button"
							tabindex="0"
							onclick={() => (selectedPlayer = selectedPlayer === player.name ? null : player.name)}
							onkeydown={(e) => {
								if (e.key === 'Enter' || e.key === ' ') {
									e.preventDefault();
									selectedPlayer = selectedPlayer === player.name ? null : player.name;
								}
							}}
						>
							<h3 class="mb-2 font-semibold text-gray-800">{player.name}</h3>
							<div class="space-y-1 text-sm">
								<div class="flex justify-between">
									<span class="text-gray-600">Team:</span>
									<span style="color: {colorScale(player.teamName)}" class="font-medium"
										>{player.teamName}</span
									>
								</div>
								<div class="flex justify-between">
									<span class="text-gray-600">Drinks:</span>
									<span class="text-lg font-bold">{player.totalDrinks}</span>
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
	{:else if viewMode === 'charts'}
		<!-- Charts Mode -->
		<div class="space-y-8">
			<!-- Chart Controls -->
			<div class="rounded-2xl bg-white p-6 shadow-xl">
				<div class="mb-4 flex items-center justify-between">
					<h2 class="text-2xl font-semibold text-gray-800">Team Stacked Bar Charts</h2>
					<div class="flex items-center gap-2">
						<label for="chart-type" class="font-semibold text-gray-700">Chart Type:</label>
						<select
							id="chart-type"
							bind:value={chartType}
							class="cursor-pointer rounded-lg border-2 border-gray-300 bg-white px-4 py-2 text-base transition-colors hover:border-blue-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
						>
							<option value="drinks">By Drink Type</option>
							<option value="players">By Player Contribution</option>
						</select>
					</div>
				</div>
				<!-- Chart Container -->
				<div class="chart-container relative overflow-x-auto" bind:clientWidth={chartWidth}>
					<svg width={chartWidth} height={chartHeight}>
						<!-- Background grid -->
						<g class="grid">
							{#each yTicks as tick}
								<line
									x1={chartMargin.left}
									x2={chartWidth - chartMargin.right}
									y1={yScale(tick)}
									y2={yScale(tick)}
									stroke="#f0f0f0"
									stroke-width="1"
								/>
							{/each}
						</g>

						<!-- Stacked Bars -->
						<g class="bars">
							{#if chartType === 'drinks'}
								{#each stackedDrinkData as teamData}
									{#each teamData.segments as segment}
										<rect
											x={xScale(teamData.team)}
											y={showAnimation ? yScale(segment.y1) : yScale(0)}
											width={xScale.bandwidth()}
											height={showAnimation ? yScale(segment.y0) - yScale(segment.y1) : 0}
											fill={segment.color}
											stroke="white"
											stroke-width="1"
											opacity={hoveredSegment &&
											hoveredSegment !== `${segment.team}-${segment.drink}`
												? 0.6
												: 1}
											class="cursor-pointer transition-all duration-300"
											role="button"
											tabindex="0"
											onmouseenter={(e) => {
												hoveredSegment = `${segment.team}-${segment.drink}`;
												showTooltip(e, segment, teamData.total);
											}}
											onmouseleave={hideTooltip}
										></rect>
									{/each}
								{/each}
							{:else}
								{#each stackedPlayerData as teamData}
									{#each teamData.segments as segment}
										<rect
											x={xScale(teamData.team)}
											y={showAnimation ? yScale(segment.y1) : yScale(0)}
											width={xScale.bandwidth()}
											height={showAnimation ? yScale(segment.y0) - yScale(segment.y1) : 0}
											fill={segment.color}
											stroke="white"
											stroke-width="1"
											opacity={hoveredSegment &&
											hoveredSegment !== `${segment.team}-${segment.player}`
												? 0.6
												: 1}
											class="cursor-pointer transition-all duration-300"
											role="button"
											tabindex="0"
											onmouseenter={(e) => {
												hoveredSegment = `${segment.team}-${segment.player}`;
												showTooltip(e, segment, teamData.total);
											}}
											onmouseleave={hideTooltip}
										></rect>
									{/each}
								{/each}
							{/if}
						</g>

						<!-- Y-axis -->
						<g class="y-axis">
							<line
								x1={chartMargin.left}
								x2={chartMargin.left}
								y1={chartMargin.top}
								y2={chartHeight - chartMargin.bottom}
								stroke="#333"
								stroke-width="2"
							/>
							{#each yTicks as tick}
								<g transform="translate({chartMargin.left}, {yScale(tick)})">
									<line x1="-6" x2="0" stroke="#333" stroke-width="1" />
									<text dy="0.32em" x="-10" text-anchor="end" class="fill-gray-700 text-sm"
										>{tick}</text
									>
								</g>
							{/each}
							<text
								transform="rotate(-90)"
								y={chartMargin.left - 40}
								x={-(chartHeight - chartMargin.bottom + chartMargin.top) / 2}
								text-anchor="middle"
								class="fill-gray-800 text-base font-semibold"
							>
								Total Drinks
							</text>
						</g>

						<!-- X-axis -->
						<g class="x-axis">
							<line
								x1={chartMargin.left}
								x2={chartWidth - chartMargin.right}
								y1={chartHeight - chartMargin.bottom}
								y2={chartHeight - chartMargin.bottom}
								stroke="#333"
								stroke-width="2"
							/>
							{#each teamsData() as team}
								<g
									transform="translate({(xScale(team.name) || 0) +
										xScale.bandwidth() / 2}, {chartHeight - chartMargin.bottom})"
								>
									<line y1="0" y2="6" stroke="#333" stroke-width="1" />
									<text y="20" text-anchor="middle" class="text-sm font-medium">
										{team.name}
									</text>
									<text y="35" text-anchor="middle" class="fill-gray-600 text-xs">
										{team.totalDrinks} total
									</text>
								</g>
							{/each}
						</g>
					</svg>
					<!-- Tooltip -->
					{#if tooltip.visible}
						<div
							class="pointer-events-none absolute z-50 min-w-56 rounded-lg border border-gray-300 bg-white px-4 py-3 shadow-xl transition-all duration-150 ease-out"
							style="left: {tooltip.x}px; top: {tooltip.y}px; transform: translateZ(0);"
						>
							<div class="mb-2 flex items-center gap-2">
								<div
									class="h-4 w-4 rounded border border-gray-200"
									style="background-color: {tooltip.content.color}"
								></div>
								<div class="text-base font-bold text-gray-900">{tooltip.content.title}</div>
								<div class="rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-600">
									{chartType === 'drinks' ? '🍹' : '👤'}
								</div>
							</div>
							<div class="mb-2 text-sm text-gray-600">{tooltip.content.subtitle}</div>
							<div class="mb-3 flex items-baseline gap-2">
								<span class="text-xl font-bold text-blue-600">
									{tooltip.content.amount}
								</span>
								<span class="text-sm text-gray-600">drinks</span>
								<span class="ml-auto text-sm font-semibold text-green-600">
									{tooltip.content.percentage}%
								</span>
							</div>
							<!-- Detailed breakdown -->
							{#if tooltip.content.details.length > 0}
								<div class="border-t border-gray-200 pt-2">
									<div class="mb-2 flex items-center gap-1 text-xs font-semibold text-gray-500">
										{#if chartType === 'drinks'}
											👥 Top Players:
										{:else}
											🍹 Top Drinks:
										{/if}
									</div>
									<div class="space-y-1">
										{#each tooltip.content.details as detail}
											<div class="flex items-center justify-between text-sm">
												<span class="max-w-32 truncate text-gray-700">{detail.name}</span>
												<span class="ml-2 font-semibold text-gray-900">{detail.value}</span>
											</div>
										{/each}
									</div>
								</div>
							{/if}
						</div>
					{/if}
				</div>

				<!-- Legend -->
				<div class="mt-6 border-t border-gray-200 pt-4">
					<h4 class="mb-3 text-sm font-semibold text-gray-700">
						{chartType === 'drinks' ? 'Drink Types' : 'Players'}
					</h4>
					<div class="flex flex-wrap gap-3">
						{#if chartType === 'drinks'}
							{#each allDrinks() as drink}
								<div class="flex items-center gap-2 text-sm">
									<div
										class="h-3 w-3 rounded"
										style="background-color: {drinkColorScale(drink)}"
									></div>
									<span class="text-gray-700">{drink}</span>
								</div>
							{/each}
						{:else}
							{#each allPlayersData.slice(0, 10) as player}
								<div class="flex items-center gap-2 text-sm">
									<div
										class="h-3 w-3 rounded"
										style="background-color: {playerColorScale(player.name)}"
									></div>
									<span class="text-gray-700">{player.name}</span>
								</div>
							{/each}
							{#if allPlayersData.length > 10}
								<div class="text-sm text-gray-500">
									... and {allPlayersData.length - 10} more players
								</div>
							{/if}
						{/if}
					</div>
				</div>
			</div>
		</div>
	{:else if viewMode === 'players'}
		<!-- Players Detail Mode -->
		<div class="rounded-2xl bg-white p-6 shadow-xl">
			<h2 class="mb-6 text-2xl font-semibold text-gray-800">Player Details</h2>
			<div class="space-y-6">
				{#each filteredPlayersData.sort((a, b) => b.totalDrinks - a.totalDrinks) as player}
					<div class="rounded-lg border border-gray-200 p-6 shadow-sm">
						<div class="mb-4 flex items-start justify-between">
							<div>
								<h3 class="text-xl font-semibold text-gray-800">{player.name}</h3>
								<p class="text-sm" style="color: {colorScale(player.teamName)}">
									Team: {player.teamName}
								</p>
							</div>
							<div class="text-right">
								<div class="text-2xl font-bold text-gray-800">{player.totalDrinks}</div>
								<div class="text-sm text-gray-600">Total Drinks</div>
							</div>
						</div>

						{#if player.drinkBreakdown.length > 0}
							<div class="mt-4">
								<h4 class="mb-3 font-medium text-gray-700">Drink Breakdown:</h4>
								<div class="space-y-2">
									{#each player.drinkBreakdown as drink}
										<div class="flex items-center justify-between rounded bg-gray-50 px-3 py-2">
											<span class="font-medium text-gray-700">{drink.name}</span>
											<div class="flex items-center gap-3">
												<span class="text-lg font-bold text-gray-800">{drink.amount}</span>
												<span class="text-sm text-gray-500">
													({formatPercentage(drink.amount, player.totalDrinks)})
												</span>
											</div>
										</div>
									{/each}
								</div>
							</div>
						{:else}
							<div class="mt-4 text-center text-gray-500">
								<p>No drinks recorded for this player</p>
							</div>
						{/if}
					</div>
				{/each}
			</div>
		</div>
	{:else if viewMode === 'teams'}
		<!-- Teams Detail Mode -->
		<div class="rounded-2xl bg-white p-6 shadow-xl">
			<h2 class="mb-6 text-2xl font-semibold text-gray-800">Team Details</h2>
			<div class="space-y-8">
				{#each teamsData() as team}
					<div
						class="rounded-lg border-2 border-gray-200 p-6 shadow-sm"
						style="border-left: 6px solid {colorScale(team.name)}"
					>
						<div class="mb-6 flex items-start justify-between">
							<div>
								<h3 class="text-2xl font-semibold" style="color: {colorScale(team.name)}">
									{team.name}
								</h3>
								<div class="mt-2 flex gap-6 text-sm text-gray-600">
									<span><strong>{team.playerCount}</strong> players</span>
									<span><strong>{team.totalDrinks}</strong> total drinks</span>
									<span
										><strong>{(team.totalDrinks / team.playerCount).toFixed(1)}</strong> avg per player</span
									>
								</div>
							</div>
							<div class="text-right">
								<div class="text-3xl font-bold text-gray-800">{team.totalDrinks}</div>
								<div class="text-sm text-gray-600">Total Drinks</div>
							</div>
						</div>

						<!-- Team Drink Breakdown -->
						{#if team.drinkBreakdown.length > 0}
							<div class="mb-6">
								<h4 class="mb-3 font-medium text-gray-700">Team Drink Breakdown:</h4>
								<div class="grid gap-2 md:grid-cols-2 lg:grid-cols-3">
									{#each team.drinkBreakdown as drink}
										<div class="flex items-center justify-between rounded bg-gray-50 px-3 py-2">
											<span class="font-medium text-gray-700">{drink.name}</span>
											<div class="flex items-center gap-2">
												<span class="text-lg font-bold text-gray-800">{drink.amount}</span>
												<span class="text-xs text-gray-500">
													({formatPercentage(drink.amount, team.totalDrinks)})
												</span>
											</div>
										</div>
									{/each}
								</div>
							</div>
						{/if}

						<!-- Team Players -->
						<div>
							<h4 class="mb-3 font-medium text-gray-700">Team Players:</h4>
							<div class="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
								{#each team.players.sort((a, b) => b.totalDrinks - a.totalDrinks) as player}
									<div class="rounded border border-gray-200 bg-white p-3 shadow-sm">
										<div class="flex items-center justify-between">
											<span class="font-medium text-gray-800">{player.name}</span>
											<span class="text-lg font-bold text-gray-700">{player.totalDrinks}</span>
										</div>
										{#if player.drinkBreakdown.length > 0}
											<div class="mt-2 space-y-1">
												{#each getTopDrinks(player.drinkBreakdown, 2) as drink}
													<div class="flex justify-between text-xs text-gray-600">
														<span>{drink.name}</span>
														<span>{drink.amount}</span>
													</div>
												{/each}
											</div>
										{/if}
									</div>
								{/each}
							</div>
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Team Legend (always visible) -->
	{#if teams.length > 1}
		<div class="mt-8 rounded-2xl bg-white p-6 shadow-lg">
			<h3 class="mb-4 text-lg font-semibold text-gray-800">Team Colors</h3>
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

	<!-- update button, go to {gamesessionid/update} -->
	{#if data.authenticatedUser?.is_superuser}
		<div class="mt-6">
			<Dialog.Root bind:open>
				<Dialog.Trigger>
					<Button>Add Drink to Player</Button>
				</Dialog.Trigger>
				<Dialog.Content class="sm:max-w-[425px]">
					<Dialog.Header>
						<Dialog.Title>Add New Drink</Dialog.Title>
						<Dialog.Description>Select a player and enter add a drink and amount</Dialog.Description
						>
					</Dialog.Header>
					<form action="?/addDrinkToPlayer" method="POST">
						<div class="grid gap-4 py-4">
							<div class="grid grid-cols-4 items-center gap-4">
								<label for="player-select" class="font-semibold text-gray-700">Player:</label>
								<select
									id="player-select"
									name="player_id"
									required
									class="col-span-3 cursor-pointer rounded-lg border-2 border-gray-300 bg-white px-4 py-2 text-base transition-colors hover:border-blue-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
								>
									<!-- <option value="" disabled selected>Select a player</option> -->
									{#each allPlayersData as player}
										<option value={player.playerId}>{player.name} ({player.teamName})</option>
									{/each}
								</select>
							</div>
							<div class="grid grid-cols-4 items-center gap-4">
								<label for="drink-name" class="font-semibold text-gray-700">Drink:</label>
								<select
									name="drink_id"
									id="player-select"
									required
									class="col-span-3 cursor-pointer rounded-lg border-2 border-gray-300 bg-white px-4 py-2 text-base transition-colors hover:border-blue-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
								>
									<!-- <option value="" disabled selected>Select a drink</option> -->
									{#each data.drinks as drink}
										<option value={drink.id}>{drink.name}</option>
									{/each}
								</select>
							</div>

							<div class="grid grid-cols-4 items-center gap-4">
								<label for="drink-amount" class="font-semibold text-gray-700">Amount:</label>
								<input
									type="number"
									id="drink-amount"
									name="amount"
									min="1"
									required
									defaultValue="1"
									class="col-span-3 rounded-lg border-2 border-gray-300 bg-white px-4 py-2 text-base transition-colors hover:border-blue-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
								/>
							</div>
							<Dialog.Footer class="mt-4">
								<Button
									type="submit"
									class="w-full bg-blue-600 text-white hover:bg-blue-800"
									onclick={() => {
										open = false;
									}}
								>
									Add Drink
								</Button>
							</Dialog.Footer>
						</div>
					</form>
				</Dialog.Content>
			</Dialog.Root>
			<!-- Edit button -->
			<a
				class="rounded-md bg-blue-600 px-4 py-3 font-medium text-white hover:bg-blue-800"
				type="button"
				href="/game/{data.game_session.id}/update">Edit</a
			>
		</div>
	{/if}
</div>
