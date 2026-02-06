<script lang="ts">
  import RecipeForm from "$lib/components/RecipeForm.svelte";

  let { data } = $props();
</script>

<RecipeForm
  {data}
  pageTitle="Edit Recipe"
  pageDescription="Update your culinary creation"
  submitButtonText="Update Recipe"
  submitButtonColor="emerald"
  onSubmit={() => {
    console.log("Update form submitted");
  }}
/>
