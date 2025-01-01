import { createApiClient } from '$lib/api/api';
import { error } from '@sveltejs/kit';
import type { Actions } from "./$types";

// import { GET } from '$lib/api/api';

// interface Item {
//     name: string;
//     secret_name: string;
//     age: number | null;
//     id: number;
// }

export const load = async ({ fetch, locals }) => {
    const client = createApiClient(fetch);
    const { data, error: apierror, response } = await client.GET("/heroes/");
    // const { data, error } = await client.GET("/heroes/{hero_id}", {
    //     params: {
    //         path: { hero_id: 1 }
    //     }
    // });

    // const { data, error } = await GET("/heroes");
    // const { data, error } = await GET("/items/");
    // console.log(items.data)
    // const response = await fetch("https://postman-echo.com/get?message=Hello+World");
    // const response = await fetch("http://127.0.0.1:8000/heroes/");
    // const response = await fetch("http://127.0.0.1:8000/heroes/1");
    // const data: Item[] = await response.json();

    // console.log(items)
    if (apierror) {
        error(404, apierror);
    }


    return {
        items: data,
        // user: locals.user
    }
    // return {
    //     items: [data]
    // }
};

