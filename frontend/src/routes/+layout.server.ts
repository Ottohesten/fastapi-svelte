// export const load = async ({ locals }) => {
//     return {
//         user: locals.user
//     }
// }

// export function load({ fetch, params, locals }) {
//     const { user } = locals;
//     console.log("layout user", user);

//     return {
//         user: locals.user
//     }

// }

export async function load({ locals, depends }) {
    // console.log("layout user", locals.user);
    // depends("user");
    return {
        authenticatedUser: locals.authenticatedUser,
        scopes: locals.authenticatedUser?.scopes ?? []
    };
}
