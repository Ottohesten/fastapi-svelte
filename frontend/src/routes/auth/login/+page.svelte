<script lang="ts">
	let { data } = $props();
	import { enhance } from '$app/forms';

	// get redirect url
	import { page } from '$app/state';

	// get the redirect url
	const redirectTo = page.url.searchParams.get('redirectTo');
	console.log('Redirect: ', redirectTo);
</script>

<!-- <h1>This is the login page</h1> -->

<!-- login form , takes username and password -->
<div>
	<!-- <form method="POST" action="?/login"> -->
	<form class="mx-auto my-2 max-w-sm" method="POST" action="?/login" use:enhance>
		<div class="mb-5">
			<label class="mb-2 block font-medium text-gray-700" for="email">Your email</label>
			<input
				class="w-full appearance-none rounded-md border bg-gray-50 p-2 text-gray-700 shadow"
				type="text"
				name="email"
				id="email"
				placeholder="user@example.com"
				autocomplete="off"
				required
			/>
		</div>
		<div class="mb-5">
			<label class="mb-2 block font-medium text-gray-700" for="password">Password</label>
			<input
				class="w-full appearance-none rounded-md border bg-gray-50 p-2 text-gray-700 shadow"
				type="password"
				name="password"
				placeholder="password"
				autocomplete="off"
				required
			/>
		</div>
		<input type="hidden" name="redirectTo" value={redirectTo} />
		<div>
			<button
				class="rounded-md bg-blue-500 px-4 py-2 font-medium text-white hover:bg-blue-800"
				type="submit">Login</button
			>
		</div>
	</form>
</div>
