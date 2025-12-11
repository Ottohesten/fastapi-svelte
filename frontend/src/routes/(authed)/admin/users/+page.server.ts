import { createApiClient } from '$lib/api/api';
import { error } from '@sveltejs/kit';
import { redirect } from '@sveltejs/kit';
import { message, superValidate, fail } from 'sveltekit-superforms';
import { zod } from 'sveltekit-superforms/adapters';
import type { Actions } from './$types.js';
import type { components } from '$lib/api/v1';

import { UserSchema, UserUpdateSchema } from '$lib/schemas/schemas.js';


export const load = async ({ fetch, cookies }) => {
    const client = createApiClient(fetch);
    const auth_token = cookies.get("auth_token");
    // Fetch consolidated permissions (superuser-only endpoint)
    const { data: permsData, error: permsError } = await client.GET("/users/with-permissions", {
        headers: {
            Authorization: `Bearer ${auth_token}`
        }
    });
    if (permsError) {
        error(403, JSON.stringify(permsError.detail));
    }

    // Fetch all available roles
    const { data: rolesData, error: rolesError } = await client.GET("/roles/", {
        headers: {
            Authorization: `Bearer ${auth_token}`
        }
    });

    // Build lookup by email for quick access in the table
    const byEmail: Record<string, components['schemas']['UserWithPermissionsPublic']> = {};
    for (const u of permsData?.data ?? []) {
        byEmail[u.email] = u;
    }

    return {
        users: { data: (permsData?.data ?? []).map(u => ({ id: u.id, email: u.email, is_active: u.is_active, is_superuser: u.is_superuser, full_name: u.full_name ?? null })), count: permsData?.count ?? 0 },
        permissionsByEmail: byEmail,
        roles: rolesData ?? [],
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

        const userUpdateForm = await superValidate(request, zod(UserUpdateSchema));

        if (!userUpdateForm.valid) {
            return fail(400, { userUpdateForm });
        }

        // Build update data with only provided fields
        const updateData: any = {};

        if (userUpdateForm.data.email && userUpdateForm.data.email.trim() !== '') {
            updateData.email = userUpdateForm.data.email;
        }

        if (userUpdateForm.data.full_name && userUpdateForm.data.full_name.trim() !== '') {
            updateData.full_name = userUpdateForm.data.full_name;
        }

        // Handle boolean fields explicitly (since false is a valid value)
        if (userUpdateForm.data.is_active !== undefined) {
            updateData.is_active = userUpdateForm.data.is_active;
        }

        if (userUpdateForm.data.is_superuser !== undefined) {
            updateData.is_superuser = userUpdateForm.data.is_superuser;
        }

        // Only include password if it's provided and not empty
        if (userUpdateForm.data.password && userUpdateForm.data.password.trim() !== '') {
            updateData.password = userUpdateForm.data.password;
        }

        const { error: apierror, response } = await client.PATCH("/users/{user_id}", {
            params: {
                path: {
                    user_id: userUpdateForm.data.user_id
                }
            },
            body: updateData,
            headers: {
                Authorization: `Bearer ${auth_token}`
            }
        })

        if (apierror) {
            return fail(400, { userUpdateForm, error: `Failed to update user: ${JSON.stringify(apierror.detail)}` });
        }

        return message(userUpdateForm, `User updated successfully!`);
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
    },

    assignRole: async ({ fetch, cookies, request }) => {
        const client = createApiClient(fetch);
        const auth_token = cookies.get("auth_token");
        if (!auth_token) redirect(302, "/auth/login");

        const formData = await request.formData();
        const user_email = formData.get("user_email") as string;
        const role_name = formData.get("role_name") as string;

        if (!user_email || !role_name) {
            return fail(400, { error: "Missing user_email or role_name" });
        }

        const { error: apiError } = await client.POST("/user-permissions/assign-role", {
            body: { user_email, role_name },
            headers: { Authorization: `Bearer ${auth_token}` }
        });

        if (apiError) {
            return fail(400, { error: `Failed to assign role: ${JSON.stringify(apiError.detail)}` });
        }
        return { success: true };
    },

    removeRole: async ({ fetch, cookies, request }) => {
        const client = createApiClient(fetch);
        const auth_token = cookies.get("auth_token");
        if (!auth_token) redirect(302, "/auth/login");

        const formData = await request.formData();
        const user_email = formData.get("user_email") as string;
        const role_name = formData.get("role_name") as string;

        if (!user_email || !role_name) {
            return fail(400, { error: "Missing user_email or role_name" });
        }

        const { error: apiError } = await client.POST("/user-permissions/remove-role", {
            body: { user_email, role_name },
            headers: { Authorization: `Bearer ${auth_token}` }
        });

        if (apiError) {
            return fail(400, { error: `Failed to remove role: ${JSON.stringify(apiError.detail)}` });
        }
        return { success: true };
    }
} satisfies Actions;
