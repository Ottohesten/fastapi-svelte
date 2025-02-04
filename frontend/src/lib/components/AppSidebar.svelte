<script lang="ts">
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	// import { Calendar } from 'bits-ui';
	import Calendar from 'lucide-svelte/icons/calendar';
	import House from 'lucide-svelte/icons/house';
	import Inbox from 'lucide-svelte/icons/inbox';
	import Search from 'lucide-svelte/icons/search';
	import Settings from 'lucide-svelte/icons/settings';
	import User from 'lucide-svelte/icons/user';

	const items = [
		{
			title: 'Home',
			url: '/',
			icon: House
		},
		{
			title: 'Users',
			url: '/admin/users',
			icon: User
		},
		{
			title: 'Inbox',
			url: '#',
			icon: Inbox
		},
		{
			title: 'Calendar',
			url: '#',
			icon: Calendar
		},
		{
			title: 'Search',
			url: '#',
			icon: Search
		},
		{
			title: 'Settings',
			url: '#',
			icon: Settings
		}
	];
</script>

<Sidebar.Root collapsible="none" class="">
	<!-- <Sidebar.Inset class="inset-y-10"> -->
	<Sidebar.Content>
		<Sidebar.Group>
			<Sidebar.GroupLabel>Application</Sidebar.GroupLabel>
			<Sidebar.GroupContent>
				<Sidebar.Menu>
					{#each items as item (item.title)}
						<Sidebar.MenuItem>
							<Sidebar.MenuButton>
								{#snippet child({ props })}
									<a href={item.url} {...props}>
										<item.icon />
										<span>{item.title}</span>
									</a>
								{/snippet}
							</Sidebar.MenuButton>
						</Sidebar.MenuItem>
					{/each}
				</Sidebar.Menu>
			</Sidebar.GroupContent>
			<!-- <Sidebar.Rail /> -->
		</Sidebar.Group>
	</Sidebar.Content>
	<!-- </Sidebar.Inset> -->
</Sidebar.Root>
