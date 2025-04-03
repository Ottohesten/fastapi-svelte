import { zod } from 'sveltekit-superforms/adapters'
import { z } from 'zod';

export const RecipeSchema = z.object({
    title: z.string().min(3),
    // mpt optional
    instructions: z.object({}).nullable(),

    // ingredients: an array of objects that have an id and a title
    ingredients: z.array(z.object({
        id: z.string(),
        title: z.string()
    })),

    servings: z.number().int().min(1).default(1),

    // image: z.instanceof(File).refine((f) => f.size < 1_000_000, 'Image must be less than 1MB').optional()


});