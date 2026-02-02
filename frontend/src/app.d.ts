// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		interface Locals {
			authenticatedUser: {
				email: string;
				is_active: boolean;
				is_superuser: boolean;
				full_name?: string | null;
				id: string;
				scopes?: string[];
			} | null;
		}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}
}

export {};
