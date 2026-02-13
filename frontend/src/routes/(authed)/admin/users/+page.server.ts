import { UsersService, RolesService } from "$lib/client/sdk.gen.js";
import { error, redirect } from "@sveltejs/kit";
import { message, superValidate, fail } from "sveltekit-superforms";
import { zod4 as zod } from "sveltekit-superforms/adapters";
import type { Actions } from "./$types.js";

import { UserSchema, UserUpdateSchema, UserAddRoleSchema } from "$lib/schemas/schemas.js";

export const load = async ({ fetch, cookies, url }) => {
    const auth_token = cookies.get("auth_token");

    if (!auth_token) {
        redirect(302, `/auth/login?redirectTo=${url.pathname}`);
    }

    // Fetch consolidated permissions (superuser-only endpoint)
    const { data: permsData, error: permsError } = await UsersService.GetUsersWithPermissions({
        auth: auth_token
    });
    if (permsError) {
        error(403, JSON.stringify(permsError.detail));
    }

    // Fetch all available roles
    const { data: rolesData, error: rolesError } = await RolesService.ReadRoles({
        auth: auth_token
    });
    if (rolesError) {
        // error(403, JSON.stringify(rolesError.detail));
        error(403);
    }

    // Fetch all available scopes
    const { data: scopesData, error: scopesError } = await RolesService.GetAvailableScopes({
        auth: auth_token
    });
    if (scopesError) {
        // error(403, JSON.stringify(scopesError.detail));
        error(403);
    }

    const availableScopes = (scopesData as unknown as { scopes: string[] })?.scopes ?? [];

    return {
        users: { data: permsData?.data ?? [], count: permsData?.count ?? 0 },
        roles: rolesData ?? [],
        availableScopes,
        userCreateForm: await superValidate(zod(UserSchema), {
            id: "userCreateForm"
        }),
        userUpdateForm: await superValidate(zod(UserUpdateSchema), {
            id: "userUpdateForm"
        }),
        userAddRoleForm: await superValidate(zod(UserAddRoleSchema), {
            id: "userAddRoleForm"
        })
    };
};

export const actions = {
    createUser: async ({ fetch, cookies, request, url }) => {
        const auth_token = cookies.get("auth_token");
        const userCreateForm = await superValidate(request, zod(UserSchema));

        if (!auth_token) {
            redirect(302, `/auth/login?redirectTo=${url.pathname}`);
        }
        if (!userCreateForm.valid) {
            return fail(400, { userCreateForm });
        }

        const { error: apierror } = await UsersService.CreateUser({
            auth: auth_token,
            body: {
                email: userCreateForm.data.email,
                password: userCreateForm.data.password,
                full_name: userCreateForm.data.full_name || null,
                is_active: userCreateForm.data.is_active,
                is_superuser: userCreateForm.data.is_superuser
            }
        });

        if (apierror) {
            return fail(400, {
                error: `Failed to create user: ${JSON.stringify(apierror.detail)}`
            });
        }

        return message(userCreateForm, `User ${userCreateForm.data.email} created successfully!`);
    },

    updateUser: async ({ fetch, cookies, request, url }) => {
        const auth_token = cookies.get("auth_token");

        if (!auth_token) {
            redirect(302, `/auth/login?redirectTo=${url.pathname}`);
        }

        const userUpdateForm = await superValidate(request, zod(UserUpdateSchema));

        if (!userUpdateForm.valid) {
            return fail(400, { userUpdateForm });
        }

        // Build update data with only provided fields
        const updateData: any = {};

        if (userUpdateForm.data.email && userUpdateForm.data.email.trim() !== "") {
            updateData.email = userUpdateForm.data.email;
        }

        if (userUpdateForm.data.full_name && userUpdateForm.data.full_name.trim() !== "") {
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
        if (userUpdateForm.data.password && userUpdateForm.data.password.trim() !== "") {
            updateData.password = userUpdateForm.data.password;
        }

        const { error: apierror } = await UsersService.UpdateUser({
            auth: auth_token,
            path: { user_id: userUpdateForm.data.user_id },
            body: updateData
        });

        if (apierror) {
            return fail(400, {
                userUpdateForm,
                error: `Failed to update user: ${JSON.stringify(apierror.detail)}`
            });
        }

        return message(userUpdateForm, `User updated successfully!`);
    },

    deleteUser: async ({ fetch, cookies, request, url }) => {
        const auth_token = cookies.get("auth_token");

        if (!auth_token) {
            redirect(302, `/auth/login?redirectTo=${url.pathname}`);
        }

        const formData = await request.formData();
        const user_id = formData.get("user_id") as string;

        const { error: apierror } = await UsersService.DeleteUser({
            auth: auth_token,
            path: { user_id: user_id }
        });

        if (apierror) {
            error(400, `Failed to delete user: ${JSON.stringify(apierror.detail)}`);
        }

        return { success: true };
    },

    toggleUserStatus: async ({ fetch, cookies, request, url }) => {
        const auth_token = cookies.get("auth_token");

        if (!auth_token) {
            redirect(302, `/auth/login?redirectTo=${url.pathname}`);
        }

        const formData = await request.formData();
        const user_id = formData.get("user_id") as string;
        const isActive = formData.get("is_active") === "true";

        // First get the current user data to preserve other fields
        const { data: userData, error: getUserError } = await UsersService.GetUser({
            auth: auth_token,
            path: { user_id }
        });

        if (getUserError) {
            error(400, `Failed to get user data: ${JSON.stringify(getUserError.detail)}`);
        }

        const { error: apierror } = await UsersService.UpdateUser({
            auth: auth_token,
            path: { user_id: user_id },
            body: {
                email: userData!.email,
                full_name: userData!.full_name,
                is_active: isActive,
                is_superuser: userData!.is_superuser
            }
        });

        if (apierror) {
            error(400, `Failed to toggle user status: ${JSON.stringify(apierror.detail)}`);
        }

        return { success: true };
    },
    assignRole: async ({ fetch, cookies, request, url }) => {
        const auth_token = cookies.get("auth_token");

        if (!auth_token) {
            redirect(302, `/auth/login?redirectTo=${url.pathname}`);
        }
        const userAddRoleForm = await superValidate(request, zod(UserAddRoleSchema));
        if (!userAddRoleForm.valid) {
            return fail(400, { userAddRoleForm });
        }
        const { error: apierror } = await UsersService.AssignRoleToUser({
            auth: auth_token,
            path: {
                user_id: userAddRoleForm.data.user_id,
                role_id: userAddRoleForm.data.role_id
            }
        });

        if (apierror) {
            return fail(400, {
                userAddRoleForm,
                error: `Failed to assign role: ${JSON.stringify(apierror.detail)}`
            });
        }
        return message(userAddRoleForm, `Role assigned successfully!`);
    },
    removeRole: async ({ fetch, cookies, request, url }) => {
        const auth_token = cookies.get("auth_token");

        if (!auth_token) {
            redirect(302, `/auth/login?redirectTo=${url.pathname}`);
        }

        const formData = await request.formData();
        const user_id = formData.get("user_id") as string;
        const roleId = formData.get("role_id") as string;

        const { error: apierror } = await UsersService.RemoveRoleFromUser({
            auth: auth_token,
            path: {
                user_id: user_id,
                role_id: roleId
            }
        });

        if (apierror) {
            return fail(400, {
                error: `Failed to remove role: ${JSON.stringify(apierror.detail)}`
            });
        }
        return { success: true };
    },

    assignScopesToUser: async ({ fetch, cookies, request, url }) => {
        const auth_token = cookies.get("auth_token");
        if (!auth_token) {
            redirect(302, `/auth/login?redirectTo=${url.pathname}`);
        }

        const formData = await request.formData();
        const user_id = formData.get("user_id") as string;
        const scope = formData.get("scope") as string;
        console.log("Received scope to add:", scope);

        if (!scope) {
            return fail(400, { error: "Scope is required" });
        }

        // Split by comma if multiple are provided, though UI might send one
        const scopesList = scope
            .split(",")
            .map((s) => s.trim())
            .filter((s) => s.length > 0);

        // Using any cast to bypass potential type mismatch if SDK is outdated
        const { data: scopesData, error: apierror } = await UsersService.AssignScopesToUser({
            auth: auth_token,
            body: scopesList,
            path: {
                user_id: user_id
            }
        });

        if (apierror) {
            return fail(400, { error: `Failed to add scope: ${JSON.stringify(apierror.detail)}` });
        }
        return { success: true };
    },

    removeScope: async ({ fetch, cookies, request, url }) => {
        const auth_token = cookies.get("auth_token");
        if (!auth_token) {
            redirect(302, `/auth/login?redirectTo=${url.pathname}`);
        }

        const formData = await request.formData();
        const user_id = formData.get("user_id") as string;
        const scope = formData.get("scope") as string;

        // Using any cast to bypass potential type mismatch if SDK is outdated
        const { error: apierror } = await UsersService.RemoveScopesFromUser({
            auth: auth_token,
            path: { user_id: user_id },
            body: [scope]
        });

        if (apierror) {
            return fail(400, {
                error: `Failed to remove scope: ${JSON.stringify(apierror.detail)}`
            });
        }
        return { success: true };
    }
} satisfies Actions;
