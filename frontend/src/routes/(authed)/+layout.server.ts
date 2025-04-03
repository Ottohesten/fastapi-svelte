import { redirect } from '@sveltejs/kit';

export function load({ locals, url }) {
    const { authenticatedUser } = locals;
    if (!authenticatedUser?.is_superuser) {
        redirect(303, `/auth/login?redirectTo=${url.pathname}`);
    }

}
