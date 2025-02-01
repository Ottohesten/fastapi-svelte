import { createApiClient } from '$lib/api/api';
import { error } from '@sveltejs/kit';

export const load = async ({ fetch, locals }) => {
    const client = createApiClient(fetch);
    const { data, error: apierror, response } = await client.GET("/ingredients/");

    if (apierror) {
        error(404, JSON.stringify(apierror.detail));
    }
    // console.log(data)




    return {
        ingredients: data
    }
}

export const actions = {
    delete: async ({ fetch, params, cookies, request }) => {
        const client = createApiClient(fetch);
        const auth_token = cookies.get("auth_token");

        const formData = await request.formData();
        const ingredient_id = formData.get("ingredient_id") as string;
        // console.log(ingredient_id);

        const { error: apierror, response } = await client.DELETE("/ingredients/{ingredient_id}", {
            params: {
                path: { ingredient_id: ingredient_id }
            },
            headers: {
                Authorization: `Bearer ${auth_token}`
            }
        });

        // return redirect(302, "/ingredients");
    }
}





