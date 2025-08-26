<template>
	<div class="extraction">
		<h1>Extraction: {{ extraction.extraction_id }}</h1>
		<p>Created At: {{ new Date(extraction.creation_time).toLocaleString() }}</p>
		<p>Textual Identifier: {{ extraction.textual_identifier }}</p>
		<p>Source ID: {{ extraction.source_id }}</p>

		<div v-if="interestingMLCs && interestingMLCs.length > 0">
			<h2>Interesting MLCs</h2>
			<ul>
				<li
					v-for="mlc in interestingMLCs"
					:key="mlc.id"
					class="mlc-item"
				>
					<a @click="redirector.redirectToView(mlc.id, 'MLC')">{{ mlc.text }} ({{ mlc.strength }})</a>
				</li>
			</ul>
		</div>

		<div v-if="interestingSequences && interestingSequences.length > 0">
			<h2>Interesting Sequences</h2>
			<ul>
				<li
					v-for="sequence in interestingSequences"
					:key="sequence.extraction"
					class="sequence-item"
				>
					{{ sequence.phrase }} ({{ sequence.frequency }})
				</li>
			</ul>
		</div>

		<div v-if="extraction.entities && extraction.entities.length">
			<h2>Connected Entities</h2>
			<ul>
				<li
					v-for="entity in extraction.entities"
					:key="entity.hlc_id"
					class="entity-item"
				>
					<a @click="gotoEntity(entity.id)">{{ entity.text }}</a> <!-- add textual identifier for entity later -->
				</li>
			</ul>
		</div>

		<h2>Sentences</h2>
		<ul>
			<li
				@click="pushToHLC(sentence.hlc_id)"
				v-for="sentence in extraction.sentences"
				:key="sentence.hlc_id"
				class="sentence-item"
			>
				{{ sentence.hlc_id }} - {{ sentence.text }}
			</li>
		</ul>

		<h2>Raw</h2>
		<pre>{{ extraction.text }}</pre>
	</div>
</template>

<script setup lang="ts">
// test api call here
import router from "@/router/index.ts"
import api from "../api/api.ts"
import { ref, onMounted, watch } from "vue"
import { useRedirectStore } from "@/stores/redirects.ts"

const redirector = useRedirectStore()
const extraction = ref<any>([]) // would be nice to have a type here... for now, using any
const interestingMLCs = ref<any[]>([]) // Placeholder for interesting MLCs, if needed
const interestingSequences = ref<any[]>([]) // Placeholder for interesting sequences, if needed

// get id from /extraction/:id
import { useRoute } from "vue-router"
const route = useRoute()
const extractionId = route.params.id as string

onMounted(() => {
	api.get("/extractions/" + extractionId)
		.then((response) => {
			console.log("API Response:", response.data)
			extraction.value = response.data || {}
		})
		.catch((error) => {
			console.error("API Error:", error)
		})

	api.get("/workspace/important-mlcs", {
			params: {
				extraction_id: extractionId,
			},
		})
		.then((response) => {
			interestingMLCs.value = response.data || []
		})
		.catch((error) => {
			console.error("Important MLCs API Error:", error)
		})

	api.get("/workspace/n-grams", {
			params: {
				extraction_id: extractionId,
			},
		}).then((response) => {
			interestingSequences.value = response.data || []
		})
		.catch((error) => {
			console.error("N-grams API Error:", error)
		})
})

// watch(
// 	() => route.params.id,
// 	(newId, oldId) => {
// 		console.log("Route ID changed from", oldId, "to", newId)
// 		if (newId !== oldId) {
// 			api.get("/extractions/" + newId)
// 				.then((response) => {
// 					console.log("API Response:", response.data)
// 					extraction.value = response.data || {}
// 				})
// 				.catch((error) => {
// 					console.error("API Error:", error)
// 				})
// 		}
// 	}
// )

function pushToHLC(hlc_id: string) {
	router.push({
		name: "High Level Concept Detail",
		params: { id: hlc_id },
	})
}

function gotoEntity(id: string) {
	// Placeholder for entity navigation logic
	router.push({
		name: "Entity Detail",
		params: { id: id }, // Replace with actual entity ID
	})
}
</script>

<style scoped>
.sentence-item {
	cursor: pointer;
	padding: 5px;
	border-bottom: 1px solid #333;
}
.sentence-item:hover {
	background-color: darkslategrey;
}

.entity-item {
	cursor: pointer;
	padding: 5px;
}

</style>
