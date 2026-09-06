import {
    NutritionService,
    type NutritionEntryUnit,
    type NutritionMealType,
    type PostNutritionEntriesData,
    type QuickAddPreviewRowPublic
} from "$lib/client";
import {
    NutritionBatchFormSchema,
    NutritionDeleteFormSchema,
    NutritionEntryFormSchema,
    NutritionMoveFormSchema,
    QuickAddFormSchema,
    type NutritionEntryForm
} from "$lib/schemas/nutrition";
import {
    apiErrorMessage,
    backendActionStatus,
    backendLoadStatus,
    requireAuthToken,
    wireDate
} from "$lib/server/backend";
import { error } from "@sveltejs/kit";
import { fail, message, superValidate } from "sveltekit-superforms";
import { zod4 as zod } from "sveltekit-superforms/adapters";
import type { Actions, PageServerLoad } from "./$types";

const previewStatuses = [
    "resolved",
    "ambiguous",
    "needs_quantity",
    "needs_nutrition",
    "invalid",
    "unmatched"
] as const;

function todayInCopenhagen(): string {
    return new Intl.DateTimeFormat("sv-SE", {
        timeZone: "Europe/Copenhagen",
        year: "numeric",
        month: "2-digit",
        day: "2-digit"
    }).format(new Date());
}

function selectedDate(value: string | null): string {
    return value && /^\d{4}-\d{2}-\d{2}$/.test(value) ? value : todayInCopenhagen();
}

function blankEntry(logDate: string): NutritionEntryForm {
    return {
        id: "",
        client_id: "manual-add",
        original_text: "",
        log_date: logDate,
        meal_type: "snack",
        source_type: "recipe",
        source_id: "",
        title: "",
        brand: "",
        note: "",
        quantity: 1,
        unit: "serving",
        calories: null,
        carbohydrates: null,
        fat: null,
        protein: null,
        status: "resolved",
        candidates: [],
        preview: null,
        row_message: null
    };
}

function previewStatus(value: string): NutritionEntryForm["status"] {
    return previewStatuses.includes(value as (typeof previewStatuses)[number])
        ? (value as NutritionEntryForm["status"])
        : "invalid";
}

function previewEntry(row: QuickAddPreviewRowPublic, logDate: string): NutritionEntryForm {
    const sourceType = row.source_type ?? "manual";
    const isManual = sourceType === "manual";
    const resolved = row.status === "resolved";
    const calories = row.calories ?? null;

    return {
        ...blankEntry(logDate),
        client_id: `line-${row.line_number}-${crypto.randomUUID()}`,
        original_text: row.original_text,
        meal_type: row.meal_type,
        source_type: sourceType,
        source_id: row.source_id ?? "",
        title: row.title ?? "",
        quantity: row.quantity ?? (row.status === "needs_quantity" ? 0 : 1),
        unit: row.unit ?? (sourceType === "recipe" ? "serving" : isManual ? "piece" : "g"),
        status: previewStatus(row.status),
        candidates: (row.candidates ?? []).flatMap((candidate) =>
            candidate.source_type === "manual"
                ? []
                : [
                      {
                          source_type: candidate.source_type,
                          source_id: candidate.source_id,
                          title: candidate.title,
                          similarity: candidate.similarity
                      }
                  ]
        ),
        preview:
            resolved && !isManual && calories !== null
                ? {
                      calories,
                      carbohydrates: row.carbohydrates ?? null,
                      fat: row.fat ?? null,
                      protein: row.protein ?? null
                  }
                : null,
        row_message: row.message ?? null,
        calories,
        carbohydrates: row.carbohydrates ?? null,
        fat: row.fat ?? null,
        protein: row.protein ?? null
    };
}

function entryBody(entry: NutritionEntryForm): PostNutritionEntriesData["body"] {
    const common = {
        log_date: wireDate(entry.log_date),
        meal_type: entry.meal_type as NutritionMealType,
        note: entry.note || null,
        quantity: entry.quantity,
        unit: entry.unit as NutritionEntryUnit
    };

    if (entry.source_type === "manual") {
        if (entry.calories === null) throw new Error("Calories are required.");
        return {
            ...common,
            source_type: "manual",
            title: entry.title,
            brand: entry.brand || null,
            calories: entry.calories,
            carbohydrates: entry.carbohydrates,
            fat: entry.fat,
            protein: entry.protein
        };
    }

    const sourceId = entry.source_id;
    if (!sourceId) throw new Error(`Choose a ${entry.source_type}.`);
    if (entry.source_type === "recipe") {
        return { ...common, source_type: "recipe", source_id: sourceId };
    }
    if (entry.source_type === "product") {
        return { ...common, source_type: "product", source_id: sourceId };
    }
    return { ...common, source_type: "ingredient", source_id: sourceId };
}

export const load: PageServerLoad = async ({ cookies, fetch, url }) => {
    const token = requireAuthToken(cookies, url.pathname + url.search);
    const date = selectedDate(url.searchParams.get("date"));
    const [
        dayResult,
        catalogResult,
        commonEntriesResult,
        entryForm,
        quickAddForm,
        batchForm,
        addBatchForm,
        moveForm
    ] = await Promise.all([
        NutritionService.GetNutritionDay({
            auth: token,
            fetch,
            path: { log_date: wireDate(date) }
        }).catch(() => null),
        NutritionService.GetNutritionCatalog({
            auth: token,
            fetch,
            query: { limit: 500 }
        }).catch(() => null),
        NutritionService.GetCommonNutritionEntries({
            auth: token,
            fetch,
            query: { limit: 6 }
        }).catch(() => null),
        superValidate(blankEntry(date), zod(NutritionEntryFormSchema), {
            id: "nutritionEntryForm",
            errors: false
        }),
        superValidate(
            { text: "", log_date: date, default_meal: "snack" },
            zod(QuickAddFormSchema),
            { id: "quickAddForm", errors: false }
        ),
        superValidate({ entries: [] }, zod(NutritionBatchFormSchema), {
            id: "nutritionBatchForm",
            errors: false
        }),
        superValidate({ entries: [] }, zod(NutritionBatchFormSchema), {
            id: "nutritionAddBatchForm",
            errors: false
        }),
        superValidate(
            { id: "", log_date: date, meal_type: "snack", note: "" },
            zod(NutritionMoveFormSchema),
            { id: "nutritionMoveForm", errors: false }
        )
    ]);

    if (!dayResult) error(503, "The nutrition service is unavailable.");
    if (!catalogResult) error(503, "The nutrition service is unavailable.");
    if (dayResult.error || !dayResult.data) {
        error(
            backendLoadStatus(dayResult.response),
            apiErrorMessage(dayResult.error, "The nutrition diary could not be loaded.")
        );
    }
    if (catalogResult.error || !catalogResult.data) {
        error(
            backendLoadStatus(catalogResult.response),
            apiErrorMessage(catalogResult.error, "The nutrition catalog could not be loaded.")
        );
    }

    return {
        day: dayResult.data,
        catalog: catalogResult.data,
        commonEntries:
            commonEntriesResult && !commonEntriesResult.error
                ? (commonEntriesResult.data?.entries ?? [])
                : [],
        selectedDate: date,
        entryForm,
        quickAddForm,
        batchForm,
        addBatchForm,
        moveForm,
        prefill: {
            sourceType: url.searchParams.get("source_type"),
            sourceId: url.searchParams.get("source_id"),
            quantity: url.searchParams.get("quantity"),
            unit: url.searchParams.get("unit")
        }
    };
};

export const actions = {
    preview: async ({ cookies, fetch, request, url }) => {
        const token = requireAuthToken(cookies, url.pathname);
        const form = await superValidate(request, zod(QuickAddFormSchema), {
            id: "quickAddForm"
        });
        if (!form.valid) return fail(400, { form });

        try {
            const result = await NutritionService.PreviewQuickAdd({
                auth: token,
                fetch,
                body: {
                    text: form.data.text,
                    log_date: wireDate(form.data.log_date),
                    default_meal: form.data.default_meal
                }
            });
            if (result.error || !result.data) {
                return message(
                    form,
                    apiErrorMessage(result.error, "The preview could not be created."),
                    { status: backendActionStatus(result.response) }
                );
            }
            return {
                form,
                previewRows: result.data.rows.map((row) => previewEntry(row, form.data.log_date)),
                canConfirm: result.data.can_confirm
            };
        } catch {
            return message(form, "The nutrition service is unavailable.", { status: 503 });
        }
    },
    saveEntry: async ({ cookies, fetch, request, url }) => {
        const token = requireAuthToken(cookies, url.pathname);
        const form = await superValidate(request, zod(NutritionEntryFormSchema), {
            id: "nutritionEntryForm"
        });
        if (!form.valid) return fail(400, { form });

        try {
            const body = entryBody(form.data);
            const result = form.data.id
                ? await NutritionService.ReplaceNutritionEntry({
                      auth: token,
                      fetch,
                      path: { entry_id: form.data.id },
                      body
                  })
                : await NutritionService.CreateNutritionEntry({ auth: token, fetch, body });
            if (result.error) {
                return message(
                    form,
                    apiErrorMessage(result.error, "The diary entry could not be saved."),
                    { status: backendActionStatus(result.response) }
                );
            }
            return message(
                form,
                form.data.id ? "Diary entry updated." : "Food added to the diary."
            );
        } catch (caught) {
            const detail = caught instanceof Error ? caught.message : "The entry is invalid.";
            return message(form, detail, { status: 400 });
        }
    },
    batch: async ({ cookies, fetch, request, url }) => {
        const token = requireAuthToken(cookies, url.pathname);
        const form = await superValidate(request, zod(NutritionBatchFormSchema), {
            id: "nutritionBatchForm"
        });
        if (!form.valid) return fail(400, { form });

        try {
            const result = await NutritionService.CreateNutritionEntries({
                auth: token,
                fetch,
                body: { entries: form.data.entries.map(entryBody) }
            });
            if (result.error) {
                return message(
                    form,
                    apiErrorMessage(result.error, "The reviewed entries could not be saved."),
                    { status: backendActionStatus(result.response) }
                );
            }
            return message(form, "Reviewed foods added to the diary.");
        } catch (caught) {
            const detail =
                caught instanceof Error ? caught.message : "The reviewed entries are invalid.";
            return message(form, detail, { status: 400 });
        }
    },
    addBatch: async ({ cookies, fetch, request, url }) => {
        const token = requireAuthToken(cookies, url.pathname);
        const form = await superValidate(request, zod(NutritionBatchFormSchema), {
            id: "nutritionAddBatchForm"
        });
        if (!form.valid) return fail(400, { form });

        try {
            const result = await NutritionService.CreateNutritionEntries({
                auth: token,
                fetch,
                body: { entries: form.data.entries.map(entryBody) }
            });
            if (result.error) {
                return message(
                    form,
                    apiErrorMessage(result.error, "The foods could not be added to the diary."),
                    { status: backendActionStatus(result.response) }
                );
            }
            return message(form, "Foods added to the diary.");
        } catch (caught) {
            const detail = caught instanceof Error ? caught.message : "The entries are invalid.";
            return message(form, detail, { status: 400 });
        }
    },
    move: async ({ cookies, fetch, request, url }) => {
        const token = requireAuthToken(cookies, url.pathname);
        const form = await superValidate(request, zod(NutritionMoveFormSchema), {
            id: "nutritionMoveForm"
        });
        if (!form.valid) return fail(400, { form });

        try {
            const result = await NutritionService.MoveNutritionEntry({
                auth: token,
                fetch,
                path: { entry_id: form.data.id },
                body: {
                    log_date: wireDate(form.data.log_date),
                    meal_type: form.data.meal_type,
                    note: form.data.note || null
                }
            });
            if (result.error) {
                return message(
                    form,
                    apiErrorMessage(result.error, "The diary entry could not be moved."),
                    { status: backendActionStatus(result.response) }
                );
            }
            return message(form, "Diary entry updated.");
        } catch {
            return message(form, "The nutrition service is unavailable.", { status: 503 });
        }
    },
    delete: async ({ cookies, fetch, request, url }) => {
        const token = requireAuthToken(cookies, url.pathname);
        const form = await superValidate(request, zod(NutritionDeleteFormSchema));
        if (!form.valid) return fail(400, { form });

        try {
            const result = await NutritionService.DeleteNutritionEntry({
                auth: token,
                fetch,
                path: { entry_id: form.data.id }
            });
            if (result.error) {
                return fail(backendActionStatus(result.response), {
                    error: apiErrorMessage(result.error, "The diary entry could not be deleted.")
                });
            }
            return { deleted: true };
        } catch {
            return fail(503, { error: "The nutrition service is unavailable." });
        }
    }
} satisfies Actions;
