<script lang="ts">
  // let stuff = $props();
  let { user, ingredient } = $props();
  import { enhance } from "$app/forms";
</script>

<div
  class="group relative overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm transition-all duration-300 hover:border-gray-300 hover:shadow-lg dark:border-gray-800 dark:bg-gray-900/50 dark:shadow-none dark:hover:border-gray-700 dark:hover:bg-gray-900/60"
>
  <a href="/ingredients/{ingredient.id}" class="block">
    <div class="p-6">
      <!-- Ingredient Header -->
      <div class="mb-4">
        <div class="mb-2 flex items-center gap-3">
          <div class="flex-shrink-0">
            <div
              class="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-green-400 to-green-600"
            >
              <svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
                />
              </svg>
            </div>
          </div>
          <div class="min-w-0 flex-1">
            <h3
              class="truncate text-lg font-bold text-gray-900 transition-colors duration-300 group-hover:text-green-600 dark:text-gray-100 dark:group-hover:text-green-400"
            >
              {ingredient.title}
            </h3>
            <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Ingredient</p>
          </div>
        </div>
      </div>

      <!-- Content Section -->
      <div class="space-y-3">
        <div
          class="rounded-lg border border-gray-100 bg-gray-50 p-3 dark:border-gray-800 dark:bg-gray-900/40"
        >
          <p
            class="mb-2 text-xs font-semibold tracking-wide text-gray-500 uppercase dark:text-gray-400"
          >
            Nutrition per 100g
          </p>
          <div class="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
            <div class="text-gray-600 dark:text-gray-300">Calories</div>
            <div class="text-right font-medium text-gray-900 dark:text-gray-100">
              {ingredient.calories} kcal
            </div>
            <div class="text-gray-600 dark:text-gray-300">Carbs</div>
            <div class="text-right font-medium text-gray-900 dark:text-gray-100">
              {ingredient.carbohydrates}g
            </div>
            <div class="text-gray-600 dark:text-gray-300">Fat</div>
            <div class="text-right font-medium text-gray-900 dark:text-gray-100">
              {ingredient.fat}g
            </div>
            <div class="text-gray-600 dark:text-gray-300">Protein</div>
            <div class="text-right font-medium text-gray-900 dark:text-gray-100">
              {ingredient.protein}g
            </div>
          </div>
        </div>

        <!-- Ingredient Type Badge -->
        <!-- <div class="flex items-center gap-2">
					<span
						class="inline-flex items-center rounded-full border border-green-200 bg-green-50 px-2.5 py-1 text-xs font-medium text-green-700"
					>
						<svg class="mr-1 h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
							/>
						</svg>
						Fresh Ingredient
					</span>
				</div> -->

        <!-- View Details Indicator -->
        <div class="flex items-center justify-between pt-2">
          <div
            class="flex items-center text-sm font-medium text-green-600 transition-colors group-hover:text-green-700 dark:text-green-400 dark:group-hover:text-green-300"
          >
            <span>View ingredient details</span>
            <svg
              class="ml-1 h-4 w-4 transform transition-transform group-hover:translate-x-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 5l7 7-7 7"
              />
            </svg>
          </div>
        </div>
      </div>
    </div>
  </a>

  <!-- Admin Action Buttons (Edit/Delete) -->
  {#if user && user.is_superuser}
    <div
      class="border-t border-gray-100 bg-gray-50 px-6 py-3 dark:border-gray-800 dark:bg-gray-900/40"
    >
      <div class="flex items-center justify-between">
        <span class="text-xs font-medium text-gray-500 dark:text-gray-400">Admin Actions</span>
        <div class="flex items-center gap-2">
          <a
            href="/ingredients/{ingredient.id}/update"
            class="inline-flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50 px-3 py-1.5 text-xs font-medium text-blue-700 transition-colors hover:border-blue-300 hover:bg-blue-100 focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 focus:outline-none dark:border-blue-900/50 dark:bg-blue-900/30 dark:text-blue-300 dark:hover:border-blue-800 dark:hover:bg-blue-900/40"
          >
            <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
              />
            </svg>
            Edit
          </a>
          <form action="/ingredients?/delete" method="POST" use:enhance class="inline">
            <input type="hidden" name="ingredient_id" value={ingredient.id} />
            <button
              type="submit"
              class="inline-flex items-center gap-1.5 rounded-lg border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-medium text-red-700 transition-colors hover:border-red-300 hover:bg-red-100 focus:ring-2 focus:ring-red-500 focus:ring-offset-1 focus:outline-none dark:border-red-900/50 dark:bg-red-900/40 dark:text-red-300 dark:hover:border-red-800 dark:hover:bg-red-900/50"
              onclick={(e) => {
                if (
                  !confirm(
                    "Are you sure you want to delete this ingredient? This action cannot be undone."
                  )
                ) {
                  e.preventDefault();
                }
              }}
            >
              <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
              Delete
            </button>
          </form>
        </div>
      </div>
    </div>
  {/if}
</div>
