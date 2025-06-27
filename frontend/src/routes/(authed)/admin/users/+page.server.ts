import { createApiClient } from '$lib/api/api';
import { error } from '@sveltejs/kit';
import { redirect } from '@sveltejs/kit';
import { message, superValidate, fail } from 'sveltekit-superforms';
import { zod } from 'sveltekit-superforms/adapters';
import type { Actions } from './$types.js';

import { UserSchema, UserUpdateSchema } from '$lib/schemas/schemas.js';


export const load = async ({ fetch, cookies }) => {
    const client = createApiClient(fetch);
    const auth_token = cookies.get("auth_token");
    const { data, error: apierror, response } = await client.GET("/users/", {
        headers: {
            Authorization: `Bearer ${auth_token}`
        }
    });

    if (apierror) {
        error(404, JSON.stringify(apierror.detail));
    }


    return {
        users: data,
        userCreateForm: await superValidate(zod(UserSchema), {
            id: "userCreateForm",
        }),
        userUpdateForm: await superValidate(zod(UserUpdateSchema), {
            id: "userUpdateForm",
        }),

    }

}


export const actions = {
    createUser: async ({ fetch, cookies, request }) => {
        // console.log('createUser action called');
        const auth_token = cookies.get("auth_token");
        const userCreateForm = await superValidate(request, zod(UserSchema));

        if (!auth_token) {
            console.log('No auth token found');
            redirect(302, "/auth/login");
        }
        if (!userCreateForm.valid) {
            return fail(400, { userCreateForm });
        }


        const client = createApiClient(fetch);


        const { error: apierror, response } = await client.POST("/users/", {
            body: {
                email: userCreateForm.data.email,
                password: userCreateForm.data.password,
                full_name: userCreateForm.data.full_name || null,
                is_active: userCreateForm.data.is_active,
                is_superuser: userCreateForm.data.is_superuser

            },
            headers: {
                Authorization: `Bearer ${auth_token}`
            }
        })

        if (apierror) {
            console.log('API error:', apierror);
            return fail(400, { error: `Failed to create user: ${JSON.stringify(apierror.detail)}` });
        }
        console.log('User created successfully');
        // Return success instead of redirect
        return message(userCreateForm, `User ${userCreateForm.data.email} created successfully!`)
        // redirect(302, "/admin/users");
    },

    updateUser: async ({ fetch, cookies, request }) => {
        const client = createApiClient(fetch);
        const auth_token = cookies.get("auth_token");

        if (!auth_token) {
            redirect(302, "/auth/login");
        }

        const formData = await request.formData();
        const userId = formData.get('user_id') as string;
        const email = formData.get('email') as string;
        const fullName = formData.get('full_name') as string;
        const isActive = formData.get('is_active') === 'on';
        const isSuperuser = formData.get('is_superuser') === 'on';

        const { error: apierror, response } = await client.PATCH("/users/{user_id}", {
            params: {
                path: {
                    user_id: userId
                }
            }, body: {
                email,
                full_name: fullName || null,
                is_active: isActive,
                is_superuser: isSuperuser
            },
            headers: {
                Authorization: `Bearer ${auth_token}`
            }
        })

        if (apierror) {
            error(400, `Failed to update user: ${JSON.stringify(apierror.detail)}`);
        }

        return { success: true };
    },

    deleteUser: async ({ fetch, cookies, request }) => {
        const client = createApiClient(fetch);
        const auth_token = cookies.get("auth_token");

        if (!auth_token) {
            redirect(302, "/auth/login");
        }

        const formData = await request.formData();
        const userId = formData.get('user_id') as string;

        const { error: apierror, response } = await client.DELETE("/users/{user_id}", {
            params: {
                path: {
                    user_id: userId
                }
            },
            headers: {
                Authorization: `Bearer ${auth_token}`
            }
        })

        if (apierror) {
            error(400, `Failed to delete user: ${JSON.stringify(apierror.detail)}`);
        }

        return { success: true };
    },

    toggleUserStatus: async ({ fetch, cookies, request }) => {
        const client = createApiClient(fetch);
        const auth_token = cookies.get("auth_token");

        if (!auth_token) {
            redirect(302, "/auth/login");
        }

        const formData = await request.formData();
        const userId = formData.get('user_id') as string;
        const isActive = formData.get('is_active') === 'true';

        // First get the current user data to preserve other fields
        const { data: userData, error: getUserError } = await client.GET("/users/{user_id}", {
            params: {
                path: {
                    user_id: userId
                }
            },
            headers: {
                Authorization: `Bearer ${auth_token}`
            }
        });

        if (getUserError) {
            error(400, `Failed to get user data: ${JSON.stringify(getUserError.detail)}`);
        }

        const { error: apierror, response } = await client.PATCH("/users/{user_id}", {
            params: {
                path: {
                    user_id: userId
                }
            },
            body: {
                email: userData!.email,
                full_name: userData!.full_name,
                is_active: isActive,
                is_superuser: userData!.is_superuser
            },
            headers: {
                Authorization: `Bearer ${auth_token}`
            }
        })

        if (apierror) {
            error(400, `Failed to toggle user status: ${JSON.stringify(apierror.detail)}`);
        }

        return { success: true };
    }
} satisfies Actions;