import type { Actions } from "./$types";
import { createApiClient, createFormApiClient } from "$lib/api/api";
import { error, redirect } from "@sveltejs/kit";

export const actions = {
    default: async ({ fetch, cookies, request, params, url }) => {
        const client = createApiClient(fetch);
        // console.log(url)
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

            // required as the api expects the body to be in x-www-form-urlencoded format (not json)
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
            sameSite: "strict",
            // set to 1 day
            maxAge: 60 * 60 * 24
            // maxAge: 60 * 5 // 5 minutes
        })

        // store access token in local storage
        // localStorage.setItem("auth_token", data.access_token);

        // get user info
        const { data: user, error: userError, response: userResponse } = await client.GET("/users/me", {
            headers: {
                Authorization: `Bearer ${cookies.get("auth_token")}`
            }
        })
        if (userError) {
            error(404, userError.detail?.toString());
        }
        // console.log(user)



        // redirect to home
        // const redirectTo = formData.get("redirectTo") as string || "/";
        const redirectTo = url.searchParams.get("redirectTo") || "/";
        // console.log(redirectTo);
        return redirect(303, redirectTo);





    }
} satisfies Actions;
