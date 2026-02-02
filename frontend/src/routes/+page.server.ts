import { createApiClient } from "$lib/api/api";
import { error } from "@sveltejs/kit";
import type { Actions } from "./$types";
// import { PASSPHRASE } from '$env/static/private';

// import { GET } from '$lib/api/api';

// interface Item {
//     name: string;
//     secret_name: string;
//     age: number | null;
//     id: number;
// }

// export const load = async ({ fetch, locals, cookies, url }) => {
//     // console.log("PASSPHRASE", PASSPHRASE);
//     const client = createApiClient(fetch);
//     // console.log(url)
//     // const { data, error: apierror, response } = await client.GET("/heroes/");
//     if (apierror) {
//         error(404, apierror);
//     }

//     return {
//         items: data,
//         // user: locals.user
//     }
//     // return {
//     //     items: [data]
//     // }
// };
