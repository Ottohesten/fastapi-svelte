import { createApiClient } from '$lib/api/api';
import { error } from '@sveltejs/kit';
import { redirect } from '@sveltejs/kit';

// export const load = async ({ fetch, params, locals, parent }) => {
//     const client = createApiClient(fetch);

//     const { data, error: apierror, response } = await client.GET("/game/drinks", {

//     })

//     if (apierror) {
//         error(response.status, apierror.detail?.toString());
//     }

//     return {
//         drinks: data,

//     }
// }
