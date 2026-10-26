import { ProductsService, type ProductCreate } from "$lib/client";
import {
    ProductDeleteFormSchema,
    ProductFormSchema,
    type ProductFormData
} from "$lib/schemas/nutrition.js";
import {
    apiErrorMessage,
    backendActionStatus,
    backendLoadStatus,
    requireAuthToken
} from "$lib/server/backend";
import { error, fail } from "@sveltejs/kit";
import { message, superValidate } from "sveltekit-superforms";
import { zod4 as zod } from "sveltekit-superforms/adapters";
import type { Actions, PageServerLoad } from "./$types";

const productFormId = "productForm";

function optionalString(value: string): string | null {
    return value || null;
}

function productBody(data: ProductFormData): ProductCreate | null {
    if (data.calories === null) return null;

    return {
        title: data.title,
        brand: optionalString(data.brand),
        barcode: optionalString(data.barcode),
        image_url: optionalString(data.image_url),
        nutrition_basis: data.nutrition_basis,
        calories: data.calories,
        carbohydrates: data.carbohydrates,
        fat: data.fat,
        protein: data.protein,
        serving_size: data.serving_size,
        serving_size_unit: data.serving_size === null ? null : data.serving_size_unit,
        package_size: data.package_size,
        package_size_unit: data.package_size === null ? null : data.package_size_unit
    };
}

export const load: PageServerLoad = async ({ cookies, fetch, url }) => {
    const token = requireAuthToken(cookies, url.pathname + url.search);
    const query = url.searchParams.get("query")?.trim() ?? "";

    const productForm = await superValidate(zod(ProductFormSchema), { id: productFormId });
    const productsResult = await ProductsService.GetProducts({
        auth: token,
        fetch,
        query: { query: query || undefined, skip: 0, limit: 100 }
    }).catch(() => null);
    if (!productsResult) {
        error(503, "The product service is unavailable.");
    }

    if (productsResult.error || !productsResult.data) {
        error(
            backendLoadStatus(productsResult.response),
            apiErrorMessage(productsResult.error, "Products could not be loaded.")
        );
    }

    return { products: productsResult.data, query, productForm };
};

export const actions = {
    create: async ({ cookies, fetch, request, url }) => {
        const token = requireAuthToken(cookies, url.pathname);
        const productForm = await superValidate(request, zod(ProductFormSchema), {
            id: productFormId
        });
        if (!productForm.valid) return fail(400, { form: productForm });

        const body = productBody(productForm.data);
        if (!body) {
            return message(productForm, "Calories are required.", { status: 400 });
        }

        try {
            const { error: apiError, response } = await ProductsService.CreateProduct({
                auth: token,
                fetch,
                body
            });
            if (apiError) {
                return message(
                    productForm,
                    apiErrorMessage(apiError, "The product could not be saved."),
                    { status: backendActionStatus(response) }
                );
            }
        } catch {
            return message(productForm, "The product service is unavailable.", { status: 503 });
        }

        return message(productForm, "Product saved.");
    },
    update: async ({ cookies, fetch, request, url }) => {
        const token = requireAuthToken(cookies, url.pathname);
        const productForm = await superValidate(request, zod(ProductFormSchema), {
            id: productFormId
        });
        if (!productForm.valid) return fail(400, { form: productForm });
        if (!productForm.data.id) {
            return message(productForm, "Product ID is required.", { status: 400 });
        }

        const body = productBody(productForm.data);
        if (!body) {
            return message(productForm, "Calories are required.", { status: 400 });
        }

        try {
            const { error: apiError, response } = await ProductsService.UpdateProduct({
                auth: token,
                fetch,
                path: { product_id: productForm.data.id },
                body
            });
            if (apiError) {
                return message(
                    productForm,
                    apiErrorMessage(apiError, "The product could not be updated."),
                    { status: backendActionStatus(response) }
                );
            }
        } catch {
            return message(productForm, "The product service is unavailable.", { status: 503 });
        }

        return message(productForm, "Product updated.");
    },
    delete: async ({ cookies, fetch, request, url }) => {
        const token = requireAuthToken(cookies, url.pathname);
        const deleteForm = await superValidate(request, zod(ProductDeleteFormSchema));
        if (!deleteForm.valid) {
            return fail(400, { action: "delete", error: "A valid product ID is required." });
        }

        try {
            const { error: apiError, response } = await ProductsService.DeleteProduct({
                auth: token,
                fetch,
                path: { product_id: deleteForm.data.id }
            });
            if (apiError) {
                return fail(backendActionStatus(response), {
                    action: "delete",
                    error: apiErrorMessage(apiError, "The product could not be deleted.")
                });
            }
        } catch {
            return fail(503, {
                action: "delete",
                error: "The product service is unavailable."
            });
        }

        return { action: "delete", success: true };
    }
} satisfies Actions;
