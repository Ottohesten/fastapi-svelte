import { redirect } from '@sveltejs/kit';
import { json } from '@sveltejs/kit';
import { error } from '@sveltejs/kit';
import { createApiClient } from '$lib/api/api.js';
// import { createApiClient } from '$lib/api/api';

export async function load({ fetch, params, locals, request, parent, url }) {
    const { user } = locals;
    // const client = createApiClient(fetch);

    // const { data, error: apierror, response } = await client.GET("/recipes/{recipe_id}", {
    //     params: {
    //         path: { recipe_id: params.slug }
    //     }
    // })
    // console.log(data)
    // console.log(parent)
    // console.log(request)
    const recipe_id = params.slug
    const parent_data = await parent()


    // if there is no user redirect to login page
    if (!user) {
        redirect(303, `/auth/login?redirectTo=${url.pathname}`);
    }

    // if user is not superuser, or is not the owner of the recipe, return 403 forbidden
    if (!user?.is_superuser && !parent_data.is_owner) {
        error(403, "Forbidden");
    }

}
