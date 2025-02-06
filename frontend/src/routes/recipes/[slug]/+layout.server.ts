import { createApiClient } from '$lib/api/api';
import { error } from '@sveltejs/kit';
import { redirect } from '@sveltejs/kit';

export const load = async ({ fetch, params, locals }) => {
    const client = createApiClient(fetch);

    const { data, error: apierror, response } = await client.GET("/recipes/{recipe_id}", {
        params: {
            path: { recipe_id: params.slug }
        }
    });

    if (apierror) {
        error(response.status, apierror.detail?.toString());
    }

    return {
        recipe: data,
        is_owner: locals.authenticatedUser ? data.owner.id === locals.authenticatedUser.id : false
    }
}

// export const actions = {
//     delete: async ({ fetch, params, cookies, request }) => {
//         const client = createApiClient(fetch);
//         const auth_token = cookies.get("auth_token");

//         const formData = await request.formData();
//         const recipe_id = formData.get("recipe_id");
//         console.log(recipe_id);

//         const { error: apierror, response } = await client.DELETE("/recipes/{recipe_id}", {
//             params: {
//                 path: { recipe_id: params.slug }
//             },
//             headers: {
//                 Authorization: `Bearer ${auth_token}`
//             }
//         })

//         return redirect(302, "/recipes");

//     }
// }