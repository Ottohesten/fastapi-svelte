import { LoginService } from "$lib/client/sdk.gen.js";
import type { Actions, PageServerLoad } from "./$types";
import { redirect, fail } from "@sveltejs/kit";
import { superValidate, message } from "sveltekit-superforms";
import { zod4 as zod } from "sveltekit-superforms/adapters";
import { LoginSchema } from "$lib/schemas/schemas";

export const load: PageServerLoad = async () => {
    return {
        form: await superValidate(zod(LoginSchema))
    };
};

export const actions = {
    default: async ({ fetch, cookies, request, url }) => {
        const form = await superValidate(request, zod(LoginSchema));

        if (!form.valid) {
            return fail(400, { form });
        }
        const {
            data,
            error: apierror,
            response
        } = await LoginService.LoginAccessToken({
            body: {
                username: form.data.email,
                password: form.data.password,
                scope: "",
                grant_type: "password"
            },
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            bodySerializer(body) {
                return body
                    ? new URLSearchParams(body as Record<string, string>)
                    : new URLSearchParams();
            }
        });

        if (apierror) {
            console.log(apierror);
            return message(
                form,
                typeof apierror.detail === "string" ? apierror.detail : "Login failed",
                {
                    status: (response.status || 400) as any
                }
            );
        }

        cookies.set("auth_token", data.access_token, {
            httpOnly: true,
            path: "/",
            secure: true,
            sameSite: "strict",
            maxAge: 60 * 60 * 24
        });

        if (data.refresh_token) {
            cookies.set("refresh_token", data.refresh_token, {
                httpOnly: true,
                path: "/",
                secure: true,
                sameSite: "lax",
                maxAge: 60 * 60 * 24 * 7
            });
        }

        const redirectTo = url.searchParams.get("redirectTo") || "/";
        return redirect(303, redirectTo);
    }
} satisfies Actions;
