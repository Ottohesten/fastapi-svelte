<script lang="ts">
  let { name, secret_name, age, id } = $props();
</script>

<div class="my-4 rounded-md bg-gray-100 p-4">
  <h3 class="font-bold">{name}</h3>
  <p>Secret name: {secret_name}</p>
  <p>Age: {age}</p>
</div>
