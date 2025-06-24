import { createApiClient } from '$lib/api/api';
import { error, fail } from '@sveltejs/kit';
import { redirect } from '@sveltejs/kit';
import type { Actions } from './$types.js';


export const load = async ({ fetch, cookies }) => {
    const client = createApiClient(fetch);
    const auth_token = cookies.get("auth_token");
    const { data, error: apierror, response } = await client.GET("/users/", {
        headers: {
            Authorization: `Bearer ${auth_token}`
        }
    })

    if (apierror) {
        error(404, JSON.stringify(apierror.detail));
    }


    return {
        users: data
    }

}


export const actions = {
    createUser: async ({ fetch, cookies, request }) => {
        // console.log('createUser action called');
        const client = createApiClient(fetch);
        const auth_token = cookies.get("auth_token");

        if (!auth_token) {
            console.log('No auth token found');
            redirect(302, "/auth/login");
        }

        const formData = await request.formData();
        // console.log('Form data received:', Object.fromEntries(formData.entries()));
        const email = formData.get('email') as string;
        const password = formData.get('password') as string;
        const confirmPassword = formData.get('confirm_password') as string;
        const fullName = formData.get('full_name') as string;
        const isActive = formData.get('is_active') === 'on';
        const isSuperuser = formData.get('is_superuser') === 'on';

        // Validate passwords match
        if (password !== confirmPassword) {
            return fail(400, { error: 'Passwords do not match' });
        }        // Validate password length
        if (password.length < 8) {
            console.log('Password too short');
            return fail(400, { error: 'Password must be at least 8 characters long' });
        }

        // console.log('Calling API to create user:', { email, fullName, isActive, isSuperuser });

        const { error: apierror, response } = await client.POST("/users/", {
            body: {
                email,
                password,
                full_name: fullName || null,
                is_superuser: isSuperuser,
                is_active: isActive
            }, headers: {
                Authorization: `Bearer ${auth_token}`
            }
        })

        if (apierror) {
            console.log('API error:', apierror);
            return fail(400, { error: `Failed to create user: ${JSON.stringify(apierror.detail)}` });
        } console.log('User created successfully');
        // Return success instead of redirect
        return { success: true, message: 'User created successfully' };
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
            }, headers: {
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