import { error, redirect } from "@sveltejs/kit";
import type { LayoutServerLoad } from "./$types";

export const load: LayoutServerLoad = ({ locals, url }) => {
    const user = locals.authenticatedUser;
    if (!user)
        redirect(303, `/auth/login?redirectTo=${encodeURIComponent(url.pathname + url.search)}`);
    if (!user.scopes?.includes("nutrition:use")) error(403, "Nutrition diary access required");

    return { nutritionUser: user };
};
