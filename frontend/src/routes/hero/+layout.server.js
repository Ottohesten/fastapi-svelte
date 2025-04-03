import { createApiClient } from '$lib/api/api';
import { error } from '@sveltejs/kit';

export const load = async ({ fetch, locals }) => {
    const client = createApiClient(fetch);
    // console.log("making request")
    const { data, error: apierror, response } = await client.GET("/heroes/");

    // log the url of the request
    // console.log("response url: ", response.url);

    if (apierror) {
        error(404, apierror);
    }
    // console.log(data)


    // const response = await fetch('https://fastapi-svelte.onrender.com/heroes/');
    // const data = await response.json();
    // console.log(data)




    return {
        heroes: data
    }
}
