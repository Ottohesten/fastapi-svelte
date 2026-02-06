<script lang="ts">
  import RecipeForm from "$lib/components/RecipeForm.svelte";
  import SuperDebug from "sveltekit-superforms";

  let { data } = $props();
</script>

<!-- <SuperDebug data={data.form} /> -->

<RecipeForm
  {data}
  pageTitle="Create New Recipe"
  pageDescription="Share your culinary creation with the world"
  submitButtonText="Create Recipe"
  submitButtonColor="blue"
/>
