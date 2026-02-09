import { redirect } from "@sveltejs/kit";

export const GET = async ({ fetch, cookies }) => {
    // remove auth token cookie and redirect to login page

    // delete cookie
    cookies.set("auth_token", "", {
        httpOnly: true,
        path: "/",
        secure: true,
        // set to 1 day
        maxAge: 0
    });
    cookies.set("refresh_token", "", {
        httpOnly: true,
        path: "/",
        secure: true,
        maxAge: 0
    });

    // redirect to login page
    return redirect(302, "/");
};
