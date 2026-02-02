import { redirect } from '@sveltejs/kit';
import { error } from '@sveltejs/kit';

export function load({ locals, url }) {
	const { authenticatedUser } = locals;
	if (!authenticatedUser) {
		redirect(303, `/auth/login?redirectTo=${url.pathname}`);
	}
	if (!authenticatedUser?.is_superuser) {
		error(403, 'Forbidden');
	}
}
