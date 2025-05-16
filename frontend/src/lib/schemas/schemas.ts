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

export const GameSessionSchema = z.object({
    title: z.string().min(2),

    // a list of teams, each team is a dictionary with a name, and optional players, each player has a name
    // teams: z.array(z.string())
    teams: z.array(z.object({
        name: z.string().min(1),
        players: z.array(z.object({
            name: z.string().min(1)
        })).optional()
    })),
});

export const GameSessionTeamSchema = z.object({
    name: z.string().min(1),
    // game_session_id that will be a hidden field in the form
    // game_session_id: z.string().min(1),
})

export const GameSessionPlayerSchema = z.object({
    name: z.string().min(1),
    // game_session_id that will be a hidden field in the form
    // game_session_id: z.string().min(1),
    // team_id: z.string().min(1),
})
