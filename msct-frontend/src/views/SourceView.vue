<template>
	<div class="source">
		<h1>Sources</h1>

		<!-- list of past 10 extractions -->
		<table>
			<thead>
				<tr>
					<th>ID</th>
					<th>Created At</th>
					<th>Name</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="source in sourceList" :key="source.id">
					<td>{{ source.id }}</td>
					<td>{{ new Date(source.creation_time).toLocaleString() }}</td>
					<td>{{ source.name }}</td>
				</tr>
			</tbody>
		</table>

		<!-- button for creating a new source -->
	</div>
</template>

<script setup lang="ts">
// test api call here
import api from "../api/api.ts"
import { ref, onMounted } from "vue"

const text = ref("put text here")
const sourceList = ref<Array<any>>([]) // would be nice to have a type here... for now, using any

onMounted(() => {
	api.get("/sources")
		.then((response) => {
			console.log("API Response:", response.data)
			sourceList.value = response.data || []
		})
		.catch((error) => {
			console.error("API Error:", error)
		})
})
</script>
