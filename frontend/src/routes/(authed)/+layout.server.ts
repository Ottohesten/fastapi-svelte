import { redirect } from '@sveltejs/kit';

export function load({ locals, url }) {
    const { user } = locals;
    if (!user?.is_superuser) {
        redirect(303, `/auth/login?redirectTo=${url.pathname}`);
    }

}
