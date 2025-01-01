import type { Actions } from "./$types";
import { createApiClient, createFormApiClient } from "$lib/api/api";
import { error, redirect } from "@sveltejs/kit";

export const actions = {
    login: async ({ fetch, cookies, request, params, url }) => {
        const client = createApiClient(fetch);
        // const client = createFormApiClient(fetch);
        const formData = await request.formData();
        // console.log(formData.get("username"));
        // post request to login
        // const temp = await fetch("http://127.0.0.1:8000/login/access-token", {
        //     method: "POST",
        //     headers: {
        //         "Content-Type": "application/x-www-form-urlencoded"
        //     },
        //     body: new URLSearchParams({
        //         username: formData.get("username") as string,
        //         password: formData.get("password") as string,
        //         scope: "",
        //         grant_type: "password"
        //     })
        // })
        // get access token
        // const data = await temp.json();
        // console.log(formData)
        // console.log(params)

        const { data, error: apierror, response } = await client.POST("/login/access-token", {
            body: {
                username: formData.get("email") as string,
                password: formData.get("password") as string,
                scope: "",
                grant_type: "password"
            },
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },

            bodySerializer(body) {
                return body ? new URLSearchParams(body as Record<string, string>) : new URLSearchParams();
            }
        })
        if (apierror) {
            console.log(apierror);
            error(response.status, apierror.detail?.toString());
        }
        // console.log(data)
        // set access token in httpOnly cookie
        cookies.set("auth_token", data.access_token, {
            httpOnly: true,
            path: '/',
            secure: true,
            // set to 1 day
            maxAge: 60 * 60 * 24
        })

        // get user info
        const { data: user, error: userError, response: userResponse } = await client.GET("/users/me", {
            headers: {
                Authorization: `Bearer ${cookies.get("auth_token")}`
            }
        })

        // const { data: user, error: userError, response: userResponse } = await client.GET("/users/me", {
        //     params: {
        //         header: {
        //             Authorization: `Bearer ${cookies.get("auth_token")}`
        //         }
        //     }
        // })
        if (userError) {
            // console.log(userError);
            // console.log(userResponse.status);
            error(404, userError.detail?.toString());
        }
        // console.log(user)



        // redirect to home
        // console.log(formData)
        // console.log(url)
        const redirectTo = formData.get("redirectTo") as string || "/";
        // console.log(redirectTo);
        return redirect(303, redirectTo);








        // set as normal cookie for testing
        // cookies.set("access_token", data.access_token, { path: '/' })




        // do form urlencoded using URLSearchParams in client
        // const temp = await client.POST("/login/access-token", {
        //     body: {
        //         username: formData.get("username") as string,
        //         password: formData.get("password") as string,
        //         scope: "",
        //         grant_type: "password"
        //     }
        // })


    }
} satisfies Actions;