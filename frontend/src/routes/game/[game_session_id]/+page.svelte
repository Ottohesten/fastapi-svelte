<script lang="ts">
	import { superForm } from 'sveltekit-superforms';
	import { zod4 as zodClient } from 'sveltekit-superforms/adapters';
	import { Field, Control, Label, FieldErrors } from 'formsnap';
	import { GameSessionAddDrinkSchema } from '$lib/schemas/schemas';
	import { Combobox } from '$lib/components/ui/combobox';
	import type { PageData } from './$types';
	let { data }: { data: PageData } = $props();
	import { schemeCategory10, schemeSet3 } from 'd3-scale-chromatic';
	import { scaleLinear, scaleBand, scaleOrdinal } from 'd3-scale';
	import { max as d3Max } from 'd3-array';
	import type { components } from '$lib/api/v1';
	import { onMount, onDestroy } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import Button from '$lib/components/ui/button/button.svelte';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Pencil, Trash2 } from 'lucide-svelte';
	import { enhance } from '$app/forms';
	import {
		Dialog,
		DialogClose,
		DialogContent,
		DialogDescription,
		DialogFooter,
		DialogHeader,
		DialogTitle,
		DialogTrigger
	} from '$lib/components/ui/dialog';
	// import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { Input } from '$lib/components/ui/input';
	import { fade } from 'svelte/transition';
	// Use the actual API types instead of custom interfaces
	type GameSession = components['schemas']['GameSessionPublic'];
	type Team = components['schemas']['GameTeamPublic'];
	type Player = components['schemas']['GamePlayerPublic'];
	type DrinkLink = components['schemas']['GamePlayerDrinkLinkPublic'];

	// Local view models to power charts/UI
	type DrinkAmount = { name: string; amount: number };
	type PlayerView = {
		name: string;
		playerId: string;
		teamName: string;
		teamId: string | null;
		totalDrinks: number;
		drinkBreakdown: DrinkAmount[];
	};
	type TeamView = {
		name: string;
		id: string | null;
		totalDrinks: number;
		playerCount: number;
		players: PlayerView[];
		drinkBreakdown: DrinkAmount[];
	};

	const addDrinkForm = superForm(data.addDrinkForm, {
		validators: zodClient(GameSessionAddDrinkSchema),
		dataType: 'json',
		onResult: ({ result }) => {
			if (result.type === 'success') {
				open = false;
			}
		}
	});

	const {
		form: addDrinkFormData,
		errors: addDrinkErrors,
		message: addDrinkMessage,
		enhance: addDrinkEnhance
	} = addDrinkForm;

	$effect(() => {
		if ($addDrinkMessage) {
			const timer = setTimeout(() => {
				$addDrinkMessage = undefined;
			}, 3000);
			return () => clearTimeout(timer);
		}
	});

	// Default values for dashboard state
	const DEFAULT_VIEW_MODE: 'overview' | 'charts' | 'players' | 'teams' = 'charts';
	const DEFAULT_CHART_TYPE: 'drinks' | 'players' = 'drinks';

	// Make gameSession a state variable instead of derived so we can update it directly
	let gameSession: GameSession | undefined = $state(data.game_session as GameSession | undefined);

	// State for interactivity - initialize from URL parameters
	let selectedTeam: string | null = $state(null);
	let selectedPlayer: string | null = $state(null);
	let showAnimation = $state(false);
	let viewMode: 'overview' | 'charts' | 'players' | 'teams' = $state(DEFAULT_VIEW_MODE);
	let chartType: 'drinks' | 'players' = $state(DEFAULT_CHART_TYPE);
	let hoveredSegment: string | null = $state(null);
	let open = $state(false);
	let isDark = $state(false);

	const viewModeOptions = [
		{ value: 'overview', label: 'Overview' },
		{ value: 'charts', label: 'Team Charts' },
		{ value: 'players', label: 'Players Detail' },
		{ value: 'teams', label: 'Teams Detail' }
	];

	let selectedViewModeLabel = $derived(
		viewModeOptions.find((o) => o.value === viewMode)?.label ?? viewMode
	);

	let selectedTeamLabel = $derived(selectedTeam ?? 'All Teams');

	// Watch for data prop changes and update gameSession
	$effect(() => {
		if (data.game_session) {
			gameSession = data.game_session as GameSession;
		}
	});

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
	let allPlayersData: PlayerView[] = $derived(
		gameSession?.players?.map((player: Player) => {
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
				teamId: (player.team_id ?? null) as string | null,
				totalDrinks:
					player.drink_links?.reduce(
						(sum: number, drinkLink: DrinkLink) => sum + drinkLink.amount,
						0
					) || 0,
				drinkBreakdown: Array.from(drinkBreakdown.values()).sort(
					(a: DrinkAmount, b: DrinkAmount) => b.amount - a.amount
				)
			} satisfies PlayerView;
		}) ?? []
	);
	// Process team data with aggregations and drink breakdowns
	let teamsData = $derived((): TeamView[] => {
		const teamMap = new Map<string, TeamView>();

		allPlayersData.forEach((player: PlayerView) => {
			const teamName = player.teamName;
			if (!teamMap.has(teamName)) {
				teamMap.set(teamName, {
					name: teamName,
					id: player.teamId || null,
					totalDrinks: 0,
					playerCount: 0,
					players: [],
					drinkBreakdown: []
				} as TeamView);
			}

			const team = teamMap.get(teamName)!;
			team.totalDrinks += player.totalDrinks;
			team.playerCount += 1;
			team.players.push(player);
		});

		// Calculate drink breakdowns for each team
		teamMap.forEach((team: TeamView) => {
			const drinkMap = new Map<string, number>();
			team.players.forEach((player: PlayerView) => {
				player.drinkBreakdown.forEach((drink: DrinkAmount) => {
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
	let filteredPlayersData: PlayerView[] = $derived(
		selectedTeam && selectedTeam !== 'all'
			? allPlayersData.filter((p: PlayerView) => p.teamName === selectedTeam)
			: allPlayersData
	);

	// Get unique teams for filter dropdown
	let teams: string[] = $derived(
		Array.from(new Set<string>(allPlayersData.map((p: PlayerView) => p.teamName))).sort()
	);

	// Stable color assignment that preserves team colors when new teams are added
	let teamColorMap = $state(new Map<string, string>());

	// Color scale for teams with stable color assignment
	let colorScale = $derived.by(() => {
		const colors = schemeCategory10;

		// Assign colors to new teams while preserving existing assignments
		teams.forEach((team: string, index: number) => {
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

	// SSE connection state
	let eventSource: EventSource | null = null;

	// Function to fetch updated game data
	async function refreshGameData() {
		if (!gameSession?.id) return;

		try {
			// Fetch updated game session data directly
			const response = await fetch(`${data.backendHost}/game/${gameSession.id}`);
			if (response.ok) {
				const updatedGameSession = await response.json();
				gameSession = updatedGameSession;
			}
		} catch (error) {
			console.error('Error refreshing game data:', error);
		}
	}

	// Animation on mount and observe theme
	onMount(() => {
		// Restore state from URL first
		restoreFromURL();

		// Track theme for chart colors
		const updateTheme = () => {
			isDark = document.documentElement.classList.contains('dark');
		};
		updateTheme();
		const observer = new MutationObserver(updateTheme);
		observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });

		setTimeout(() => {
			showAnimation = true;
		}, 100);

		// Connect to SSE endpoint for real-time updates
		if (browser && gameSession?.id) {
			const sseUrl = `${data.backendHost}/game/${gameSession.id}/updates`;
			eventSource = new EventSource(sseUrl);

			eventSource.onmessage = (event) => {
				try {
					const eventData = JSON.parse(event.data);

					if (eventData.type === 'drink_added') {
						refreshGameData();
					}
				} catch (error) {
					console.error('Error parsing SSE message:', error);
				}
			};

			eventSource.onerror = (error) => {
				console.error('SSE connection error:', error);
			};
		}

		return () => {
			observer.disconnect();
			if (eventSource) {
				eventSource.close();
			}
		};
	});

	onDestroy(() => {
		if (eventSource) {
			eventSource.close();
		}
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

<div class="mx-auto min-h-screen w-full max-w-7xl px-4 py-6 font-sans sm:px-6 lg:px-8">
	<!-- Header -->
	<div class="mb-8 border-b-2 border-gray-200 pb-6 text-center dark:border-gray-800">
		<h1 class="mb-2 text-2xl font-bold text-gray-800 sm:text-3xl md:text-4xl dark:text-gray-100">
			Game Session Dashboard
		</h1>
		{#if gameSession}
			<p class="text-base text-gray-600 sm:text-lg dark:text-gray-400">
				Session: <strong>{gameSession.title}</strong>
			</p>
		{/if}
	</div>

	{#if $addDrinkMessage}
		<div
			transition:fade
			class="mb-6 rounded-md bg-green-50 p-4 text-center text-sm text-green-700 dark:bg-green-900/20 dark:text-green-300"
		>
			{$addDrinkMessage}
		</div>
	{/if}

	<!-- Controls -->
	<div class="mb-8 flex flex-col gap-6">
		<div class="flex flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-center">
			<div class="flex flex-col gap-2 sm:flex-row sm:items-center">
				<label for="team-filter" class="font-semibold text-gray-700 dark:text-gray-300"
					>Filter by Team:</label
				>
				<Select.Root
					type="single"
					value={selectedTeam ?? 'all'}
					onValueChange={(v) => {
						selectedTeam = v === 'all' ? null : v;
					}}
				>
					<Select.Trigger id="team-filter" class="max-w-[14rem]">
						{selectedTeamLabel}
					</Select.Trigger>
					<Select.Content>
						<Select.Item value="all" label="All Teams">All Teams</Select.Item>
						{#each teams as team}
							<Select.Item value={team} label={team}>{team}</Select.Item>
						{/each}
					</Select.Content>
				</Select.Root>
			</div>

			<div class="flex flex-col gap-2 sm:flex-row sm:items-center">
				<label for="view-mode" class="font-semibold text-gray-700 dark:text-gray-300">View:</label>
				<Select.Root type="single" bind:value={viewMode}>
					<Select.Trigger id="view-mode" class="max-w-[14rem]">
						{selectedViewModeLabel}
					</Select.Trigger>
					<Select.Content>
						{#each viewModeOptions as option}
							<Select.Item value={option.value} label={option.label}>
								{option.label}
							</Select.Item>
						{/each}
					</Select.Content>
				</Select.Root>
			</div>
		</div>

		<!-- Summary Stats -->
		<div class="grid grid-cols-1 gap-4 sm:grid-cols-3 sm:gap-6">
			<div
				class="bg-linear-to-br rounded-xl from-indigo-500 to-purple-600 px-4 py-4 text-center text-white shadow-lg sm:px-6"
			>
				<div class="text-xl font-bold sm:text-2xl">{filteredPlayersData.length}</div>
				<div class="mt-1 text-sm opacity-90">Players</div>
			</div>
			<div
				class="bg-linear-to-br rounded-xl from-indigo-500 to-purple-600 px-4 py-4 text-center text-white shadow-lg sm:px-6"
			>
				<div class="text-xl font-bold sm:text-2xl">
					{filteredPlayersData.reduce((sum, p) => sum + p.totalDrinks, 0)}
				</div>
				<div class="mt-1 text-sm opacity-90">Total Drinks</div>
			</div>
			<div
				class="bg-linear-to-br rounded-xl from-indigo-500 to-purple-600 px-4 py-4 text-center text-white shadow-lg sm:px-6"
			>
				<div class="text-xl font-bold sm:text-2xl">{teams.length}</div>
				<div class="mt-1 text-sm opacity-90">Teams</div>
			</div>
		</div>
	</div>

	<!-- Main Content -->
	{#if viewMode === 'overview'}
		<!-- Overview Mode -->
		<div class="space-y-8">
			<!-- Teams Overview -->
			<div
				class="rounded-2xl border border-gray-200 bg-white p-6 shadow-xl dark:border-gray-800 dark:bg-gray-900/50"
			>
				<h2 class="mb-6 text-2xl font-semibold text-gray-800 dark:text-gray-100">Teams Overview</h2>
				<div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
					{#each teamsData() as team}
						<!-- {console.log(selectedTeam === team.name)} -->
						<div
							class="cursor-pointer rounded-lg border-2 border-gray-200 p-4 transition-all hover:border-blue-400 hover:shadow-lg dark:border-gray-800 {selectedTeam ===
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
							<div class="space-y-2 text-sm text-gray-600 dark:text-gray-300">
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
								<div class="mt-3 border-t border-gray-200 pt-3 dark:border-gray-800">
									<div class="mb-2 text-xs font-medium text-gray-500 dark:text-gray-400">
										Top Drinks:
									</div>
									{#each getTopDrinks(team.drinkBreakdown, 3) as drink}
										<div class="flex justify-between text-xs text-gray-600 dark:text-gray-300">
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
			<div
				class="rounded-2xl border border-gray-200 bg-white p-6 shadow-xl dark:border-gray-800 dark:bg-gray-900/50"
			>
				<h2 class="mb-6 text-2xl font-semibold text-gray-800 dark:text-gray-100">Top Players</h2>
				<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
					{#each filteredPlayersData
						.sort((a, b) => b.totalDrinks - a.totalDrinks)
						.slice(0, 8) as player}
						<div
							class="cursor-pointer rounded-lg border-2 border-gray-200 p-4 transition-all hover:border-blue-400 hover:shadow-lg dark:border-gray-800"
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
							<h3 class="mb-2 font-semibold text-gray-800 dark:text-gray-100">{player.name}</h3>
							<div class="space-y-1 text-sm">
								<div class="flex justify-between">
									<span class="text-gray-600 dark:text-gray-300">Team:</span>
									<span style="color: {colorScale(player.teamName)}" class="font-medium"
										>{player.teamName}</span
									>
								</div>
								<div class="flex justify-between">
									<span class="text-gray-600 dark:text-gray-300">Drinks:</span>
									<span class="text-lg font-bold dark:text-gray-100">{player.totalDrinks}</span>
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
			<div
				class="rounded-2xl border border-gray-200 bg-white p-6 shadow-xl dark:border-gray-800 dark:bg-gray-900/50"
			>
				<div class="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
					<h2 class="text-2xl font-semibold text-gray-800 dark:text-gray-100">
						Team Stacked Bar Charts
					</h2>
					<div class="flex flex-col gap-2 sm:flex-row sm:items-center">
						<label for="chart-type" class="font-semibold text-gray-700 dark:text-gray-300"
							>Chart Type:</label
						>
						<select
							id="chart-type"
							bind:value={chartType}
							class="cursor-pointer rounded-lg border-2 border-gray-300 bg-white px-4 py-2 text-base transition-colors hover:border-blue-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100 dark:focus:ring-blue-900/40"
						>
							<option value="drinks">By Drink Type</option>
							<option value="players">By Player Contribution</option>
						</select>
					</div>
				</div>
				<!-- Chart Container -->
				<div
					class="chart-container relative min-h-0 w-full overflow-hidden"
					bind:clientWidth={chartWidth}
				>
					<div class="w-full overflow-x-auto">
						<svg width={Math.max(chartWidth, 600)} height={chartHeight} class="min-w-full">
							<!-- Background grid -->
							<g class="grid">
								{#each yTicks as tick}
									<line
										x1={chartMargin.left}
										x2={Math.max(chartWidth, 600) - chartMargin.right}
										y1={yScale(tick)}
										y2={yScale(tick)}
										stroke={isDark ? '#1f2937' : '#f0f0f0'}
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
												stroke={isDark ? 'rgba(255,255,255,0.15)' : 'white'}
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
												stroke={isDark ? 'rgba(255,255,255,0.15)' : 'white'}
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
									stroke={isDark ? '#4b5563' : '#333'}
									stroke-width="2"
								/>
								{#each yTicks as tick}
									<g transform="translate({chartMargin.left}, {yScale(tick)})">
										<line x1="-6" x2="0" stroke={isDark ? '#4b5563' : '#333'} stroke-width="1" />
										<text
											dy="0.32em"
											x="-10"
											text-anchor="end"
											class="fill-gray-700 text-sm dark:fill-gray-300">{tick}</text
										>
									</g>
								{/each}
								<text
									transform="rotate(-90)"
									y={chartMargin.left - 40}
									x={-(chartHeight - chartMargin.bottom + chartMargin.top) / 2}
									text-anchor="middle"
									class="fill-gray-800 text-base font-semibold dark:fill-gray-200"
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
									stroke={isDark ? '#4b5563' : '#333'}
									stroke-width="2"
								/>
								{#each teamsData() as team}
									<g
										transform="translate({(xScale(team.name) || 0) +
											xScale.bandwidth() / 2}, {chartHeight - chartMargin.bottom})"
									>
										<line y1="0" y2="6" stroke={isDark ? '#4b5563' : '#333'} stroke-width="1" />
										<text y="20" text-anchor="middle" class="text-sm font-medium">
											{team.name}
										</text>
										<text
											y="35"
											text-anchor="middle"
											class="fill-gray-600 text-xs dark:fill-gray-400"
										>
											{team.totalDrinks} total
										</text>
									</g>
								{/each}
							</g>
						</svg>
					</div>
					<!-- Tooltip -->
					{#if tooltip.visible}
						<div
							class="pointer-events-none absolute z-50 min-w-56 rounded-lg border border-gray-300 bg-white px-4 py-3 shadow-xl transition-all duration-150 ease-out dark:border-gray-800 dark:bg-gray-900/95"
							style="left: {tooltip.x}px; top: {tooltip.y}px; transform: translateZ(0);"
						>
							<div class="mb-2 flex items-center gap-2">
								<div
									class="h-4 w-4 rounded border border-gray-200 dark:border-gray-700"
									style="background-color: {tooltip.content.color}"
								></div>
								<div class="text-base font-bold text-gray-900 dark:text-gray-100">
									{tooltip.content.title}
								</div>
								<div
									class="rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-300"
								>
									{chartType === 'drinks' ? '🍹' : '👤'}
								</div>
							</div>
							<div class="mb-2 text-sm text-gray-600 dark:text-gray-300">
								{tooltip.content.subtitle}
							</div>
							<div class="mb-3 flex items-baseline gap-2">
								<span class="text-xl font-bold text-blue-600">
									{tooltip.content.amount}
								</span>
								<span class="text-sm text-gray-600 dark:text-gray-300">drinks</span>
								<span class="ml-auto text-sm font-semibold text-green-600">
									{tooltip.content.percentage}%
								</span>
							</div>
							<!-- Detailed breakdown -->
							{#if tooltip.content.details.length > 0}
								<div class="border-t border-gray-200 pt-2 dark:border-gray-800">
									<div
										class="mb-2 flex items-center gap-1 text-xs font-semibold text-gray-500 dark:text-gray-400"
									>
										{#if chartType === 'drinks'}
											👥 Top Players:
										{:else}
											🍹 Top Drinks:
										{/if}
									</div>
									<div class="space-y-1">
										{#each tooltip.content.details as detail}
											<div class="flex items-center justify-between text-sm">
												<span class="max-w-32 truncate text-gray-700 dark:text-gray-300"
													>{detail.name}</span
												>
												<span class="ml-2 font-semibold text-gray-900 dark:text-gray-100"
													>{detail.value}</span
												>
											</div>
										{/each}
									</div>
								</div>
							{/if}
						</div>
					{/if}
				</div>

				<!-- Legend -->
				<div class="mt-6 border-t border-gray-200 pt-4 dark:border-gray-800">
					<h4 class="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">
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
									<span class="text-gray-700 dark:text-gray-300">{drink}</span>
								</div>
							{/each}
						{:else}
							{#each allPlayersData.slice(0, 10) as player}
								<div class="flex items-center gap-2 text-sm">
									<div
										class="h-3 w-3 rounded"
										style="background-color: {playerColorScale(player.name)}"
									></div>
									<span class="text-gray-700 dark:text-gray-300">{player.name}</span>
								</div>
							{/each}
							{#if allPlayersData.length > 10}
								<div class="text-sm text-gray-500 dark:text-gray-400">
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
		<div
			class="rounded-2xl border border-gray-200 bg-white p-6 shadow-xl dark:border-gray-800 dark:bg-gray-900/50"
		>
			<h2 class="mb-6 text-2xl font-semibold text-gray-800 dark:text-gray-100">Player Details</h2>
			<div class="space-y-6">
				{#each filteredPlayersData.sort((a, b) => b.totalDrinks - a.totalDrinks) as player}
					<div class="rounded-lg border border-gray-200 p-6 shadow-sm dark:border-gray-800">
						<div class="mb-4 flex items-start justify-between">
							<div>
								<h3 class="font-semibold text-gray-800 dark:text-gray-100">
									{player.name}
								</h3>
								<p class="text-sm" style="color: {colorScale(player.teamName)}">
									Team: {player.teamName}
								</p>
							</div>
							<div class="text-right">
								<div class="text-2xl font-bold text-gray-800 dark:text-gray-100">
									{player.totalDrinks}
								</div>
								<div class="text-sm text-gray-600 dark:text-gray-300">Total Drinks</div>
							</div>
						</div>

						{#if player.drinkBreakdown.length > 0}
							<div class="mt-4">
								<h4 class="mb-3 font-medium text-gray-700 dark:text-gray-300">Drink Breakdown:</h4>
								<div class="space-y-2">
									{#each player.drinkBreakdown as drink}
										<div
											class="flex items-center justify-between rounded bg-gray-50 px-3 py-2 dark:bg-gray-800/50"
										>
											<span class="font-medium text-gray-700 dark:text-gray-200">{drink.name}</span>
											<div class="flex items-center gap-3">
												<span class="text-lg font-bold text-gray-800 dark:text-gray-100"
													>{drink.amount}</span
												>
												<span class="text-sm text-gray-500 dark:text-gray-400">
													({formatPercentage(drink.amount, player.totalDrinks)})
												</span>
											</div>
										</div>
									{/each}
								</div>
							</div>
						{:else}
							<div class="mt-4 text-center text-gray-500 dark:text-gray-400">
								<p>No drinks recorded for this player</p>
							</div>
						{/if}
					</div>
				{/each}
			</div>
		</div>
	{:else if viewMode === 'teams'}
		<!-- Teams Detail Mode -->
		<div
			class="rounded-2xl border border-gray-200 bg-white p-6 shadow-xl dark:border-gray-800 dark:bg-gray-900/50"
		>
			<h2 class="mb-6 text-2xl font-semibold text-gray-800 dark:text-gray-100">Team Details</h2>
			<div class="space-y-8">
				{#each teamsData() as team}
					<div
						class="rounded-lg border-2 border-gray-200 p-6 shadow-sm dark:border-gray-800"
						style="border-left: 6px solid {colorScale(team.name)}"
					>
						<div class="mb-6 flex items-start justify-between">
							<div>
								<h3
									class="text-2xl font-semibold dark:text-gray-100"
									style="color: {colorScale(team.name)}"
								>
									{team.name}
								</h3>
								<div class="mt-2 flex gap-6 text-sm text-gray-600 dark:text-gray-300">
									<span><strong>{team.playerCount}</strong> players</span>
									<span><strong>{team.totalDrinks}</strong> total drinks</span>
									<span
										><strong>{(team.totalDrinks / team.playerCount).toFixed(1)}</strong> avg per player</span
									>
								</div>
							</div>
							<div class="text-right">
								<div class="text-3xl font-bold text-gray-800 dark:text-gray-100">
									{team.totalDrinks}
								</div>
								<div class="text-sm text-gray-600 dark:text-gray-300">Total Drinks</div>
							</div>
						</div>

						<!-- Team Drink Breakdown -->
						{#if team.drinkBreakdown.length > 0}
							<div class="mb-6">
								<h4 class="mb-3 font-medium text-gray-700 dark:text-gray-300">
									Team Drink Breakdown:
								</h4>
								<div class="grid gap-2 md:grid-cols-2 lg:grid-cols-3">
									{#each team.drinkBreakdown as drink}
										<div
											class="flex items-center justify-between rounded bg-gray-50 px-3 py-2 dark:bg-gray-800/50"
										>
											<span class="font-medium text-gray-700 dark:text-gray-200">{drink.name}</span>
											<div class="flex items-center gap-2">
												<span class="text-lg font-bold text-gray-800 dark:text-gray-100"
													>{drink.amount}</span
												>
												<span class="text-xs text-gray-500 dark:text-gray-400">
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
							<h4 class="mb-3 font-medium text-gray-700 dark:text-gray-300">Team Players:</h4>
							<div class="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
								{#each team.players.sort((a, b) => b.totalDrinks - a.totalDrinks) as player}
									<div
										class="rounded border border-gray-200 bg-white p-3 shadow-sm dark:border-gray-800 dark:bg-gray-900/60"
									>
										<div class="flex items-center justify-between">
											<span class="font-medium text-gray-800 dark:text-gray-100">{player.name}</span
											>
											<span class="text-lg font-bold text-gray-700 dark:text-gray-200"
												>{player.totalDrinks}</span
											>
										</div>
										{#if player.drinkBreakdown.length > 0}
											<div class="mt-2 space-y-1">
												{#each getTopDrinks(player.drinkBreakdown, 2) as drink}
													<div
														class="flex justify-between text-xs text-gray-600 dark:text-gray-300"
													>
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
		<div
			class="mt-8 rounded-2xl border border-gray-200 bg-white p-6 shadow-lg dark:border-gray-800 dark:bg-gray-900/50"
		>
			<h3 class="mb-4 text-lg font-semibold text-gray-800 dark:text-gray-100">Team Colors</h3>
			<div class="grid grid-cols-2 gap-3 sm:flex sm:flex-wrap sm:gap-4">
				{#each teams as team}
					<div class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
						<div
							class="h-4 w-4 shrink-0 rounded border border-black/10 dark:border-white/10"
							style="background-color: {colorScale(team)}"
						></div>
						<span class="truncate">{team}</span>
					</div>
				{/each}
			</div>
		</div>
	{/if}
	<!-- update button, go to {gamesessionid/update} -->
	{#if data.authenticatedUser && data.authenticatedUser.scopes && data.authenticatedUser.scopes.includes('games:update')}
		<!-- {#if data.authenticatedUser} -->
		<div class="mt-6">
			<div class="flex flex-col gap-4 sm:flex-row">
				<Dialog bind:open>
					<DialogTrigger>
						<!-- Styled like Button variant="primary" size="default" -->
						<span
							class="ring-offset-background inline-flex h-10 w-full cursor-pointer items-center justify-center gap-2 whitespace-nowrap rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-blue-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 sm:w-auto dark:bg-blue-500 dark:text-white dark:hover:bg-blue-400 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0"
						>
							Add Drink to Player
						</span>
					</DialogTrigger>
					<DialogContent class="sm:max-w-[425px]">
						<DialogHeader>
							<DialogTitle>Add New Drink</DialogTitle>
							<DialogDescription>Select a player and enter add a drink and amount</DialogDescription
							>
						</DialogHeader>
						<form action="?/addDrinkToPlayer" method="POST" use:addDrinkEnhance class="space-y-4">
							<div class="space-y-2">
								<Field form={addDrinkForm} name="player_id">
									<Control>
										{#snippet children({ props })}
											<Label
												class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
											>
												Player
											</Label>
											<Combobox
												items={allPlayersData.map((p) => ({
													label: `${p.name} (${p.teamName})`,
													value: p.playerId
												}))}
												bind:value={$addDrinkFormData.player_id}
												placeholder="Select a player..."
												searchPlaceholder="Search players..."
												class="w-full"
												buttonClass="w-full justify-between"
											/>
										{/snippet}
									</Control>
									<FieldErrors class="text-sm text-red-500" />
								</Field>
							</div>

							<div class="space-y-2">
								<Field form={addDrinkForm} name="drink_id">
									<Control>
										{#snippet children({ props })}
											<Label
												class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
											>
												Drink
											</Label>
											<Combobox
												items={data.drinks.map((d) => ({ label: d.name, value: d.id }))}
												bind:value={$addDrinkFormData.drink_id}
												placeholder="Select a drink..."
												searchPlaceholder="Search drinks..."
												class="w-full"
												buttonClass="w-full justify-between"
											/>
										{/snippet}
									</Control>
									<FieldErrors class="text-sm text-red-500" />
								</Field>
							</div>

							<div class="space-y-2">
								<Field form={addDrinkForm} name="amount">
									<Control>
										{#snippet children({ props })}
											<Label
												class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
											>
												Amount
											</Label>
											<Input
												{...props}
												type="number"
												min="1"
												bind:value={$addDrinkFormData.amount}
											/>
										{/snippet}
									</Control>
									<FieldErrors class="text-sm text-red-500" />
								</Field>
							</div>

							<DialogFooter>
								<Button type="submit" class="w-full bg-blue-600 text-white hover:bg-blue-800">
									Add Drink
								</Button>
							</DialogFooter>
						</form>
					</DialogContent>
				</Dialog>
				<!-- Edit button -->
				<!-- <a
					class="rounded-md bg-blue-600 px-4 py-2 text-center font-medium text-white hover:bg-blue-800"
					type="button"
					href="/game/{data.game_session.id}/update">Edit</a
				> -->
				<Button
					href="/game/{data.game_session.id}/update"
					variant="outline"
					class="w-full sm:w-auto">Edit</Button
				>
			</div>
		</div>
	{/if}
</div>
