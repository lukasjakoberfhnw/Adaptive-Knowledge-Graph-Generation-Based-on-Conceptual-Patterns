<template>
	<div class="about">
		<h1>This is an about page</h1>
		<p>Test the stuff here for now.</p>
		<button @click="run">Run API Call</button>
		<textarea v-model="text" rows="8"></textarea>

		<div class="extraction-result" v-if="extractionResult.length > 0">
			<h2>Extracted Sentences:</h2>
			<ul>
				<li v-for="(sentence, index) in extractionResult" :key="index">
					{{ sentence }}
				</li>
			</ul>
		</div>
	</div>
</template>

<script setup lang="ts">
// test api call here
import api from "../api/api.ts"
import { ref } from "vue"

const text = ref("put text here")
const extractionResult = ref([])

function run() {
	api.post("/extraction", {
		text: text.value,
	})
		.then((response) => {
			console.log("API Response:", response.data)
			extractionResult.value = response.data.sentences || []
		})
		.catch((error) => {
			console.error("API Error:", error)
		})
}
</script>

<style></style>
