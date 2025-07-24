import { zod } from 'sveltekit-superforms/adapters'
import { z } from 'zod';


// User Schema for creating a user
export const UserSchema = z.object({
    email: z.string().email("Please enter a valid email"),
    password: z.string().min(8),
    confirm_password: z.string().min(8),
    full_name: z.string().min(1),
    is_active: z.boolean().default(true),
    is_superuser: z.boolean().default(false)
}).refine((data) => data.password === data.confirm_password, {
    message: "Passwords don't match",
    path: ["confirm_password"],
});




export const UserUpdateSchema = z.object({
    user_id: z.string(),
    email: z.string().email("Please enter a valid email").or(z.literal("")).optional(),
    full_name: z.string().or(z.literal("")).optional(),
    password: z.string().or(z.literal("")).optional(),
    confirm_password: z.string().or(z.literal("")).optional(),
    is_active: z.boolean().optional(),
    is_superuser: z.boolean().optional()
}).superRefine((data, ctx) => {
    // Only validate password if it's provided and not empty
    if (data.password && data.password.trim() !== "") {
        if (data.password.length < 8) {
            ctx.addIssue({
                code: z.ZodIssueCode.too_small,
                minimum: 8,
                type: "string",
                inclusive: true,
                message: "Password must be at least 8 characters",
                path: ["password"]
            });
        }
        // Only validate password confirmation if password is provided
        if (data.password !== data.confirm_password) {
            ctx.addIssue({
                code: z.ZodIssueCode.custom,
                message: "Passwords don't match",
                path: ["confirm_password"]
            });
        }
    }
})


export const RecipeSchema = z.object({
    title: z.string().min(3),

    instructions: z.string().min(1).max(9999),

    // ingredients: an array of objects that have an id and a title
    ingredients: z.array(z.object({
        id: z.string(),
        title: z.string()
    })),

    servings: z.number().int().min(1).default(1),

    // image: z.instanceof(File).refine((f) => f.size < 1_000_000, 'Image must be less than 1MB').optional()


});

export const IngredientSchema = z.object({
    title: z.string().min(1, "Title is required").max(255, "Title must be less than 255 characters"),
    calories: z.number().int().nonnegative("Calories must be a non-negative integer")
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
    team_id: z.string().optional(),
})


// schema for player where you can edit the name and add drinks to the player
export const GameSessionPlayerUpdateSchema = z.object({
    name: z.string().min(1),
    drinks: z.array(z.object({
        drink_id: z.string(),
        // amount can be 0 or more
        amount: z.number().int().min(0).default(0),
    }))
})

