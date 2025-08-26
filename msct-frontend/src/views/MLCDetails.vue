<template>
	<div class="mlc">
		<h1>MLC: {{ mlc.id }}</h1>
		<p>Created At: {{ new Date(mlc.creation_time).toLocaleString() }}</p>
		<p>Count: {{ mlc.count }}</p>
		<p v-for="(value, key) in mlc.properties">{{ key }}: {{ value }}</p>

		<h2>Create Relations</h2>
		<button @click="showCreateRelation = true">Relationship Management</button>

		<h2>Manual Relations</h2>
		<ul v-if="mlc.other_connections && mlc.other_connections.length > 0 && mlc.other_connections[0].neighbor">
			<li v-for="(relation, index) in mlc.other_connections" :key="index">
				{{ relation.rel_type }} -> {{ relation.neighbor_type }}: <a @click="gotoEntity(relation.neighbor.id, relation.neighbor_type)">{{ relation.neighbor.text }}</a> 
			</li>
		</ul>

		<h2>Present in Extractions</h2>
		<ul v-if="mlc.extractions && mlc.extractions.length > 0">
			<li v-for="(extraction, index) in mlc.extractions" :key="index">
				<a @click="gotoEntity(extraction.id, extraction.type)">{{ extraction.textual_identifier }} ({{ extraction.id }})</a>
			</li>
		</ul>

		<h2>Closest Relations</h2>
		<ul>
			<li v-for="(relation, index) in mlc.relationships_with_neighbors" :key="index">
				strength: {{ relation.strength }} - {{ relation.rel_type }} -> {{ relation.neighbor_type }}: <a @click="gotoEntity(relation.neighbor.id, relation.neighbor_type)">{{ relation.neighbor.text }} (count: {{ relation.neighbor.count }})</a> 
			</li>
		</ul>

		<h2>Present in HLCs</h2>
		<ul v-if="mlc.hlcs && mlc.hlcs.length > 0">
			<li v-for="(hlc, index) in mlc.hlcs" :key="index">
				<a @click="gotoEntity(hlc.id, 'HLC')">{{ hlc.text }} ({{ hlc.id }})</a>
			</li>
		</ul>

		<RelationshipManagement
			v-if="showCreateRelation"
			:selectedTokens="[{...mlc, type: 'MLC'}]"
			:hlc_id="null"
			@close="showCreateRelation = false"
			>
		</RelationshipManagement>

		<!-- for look for metadata or all other relationships (if many only strongest or manually validated) -->
	</div>
</template>

<script setup lang="ts">
// test api call here
import api from "../api/api.ts"
import { ref, onMounted } from "vue"

const mlc = ref<any>({}) // would be nice to have a type here... for now, using any
const showCreateRelation = ref(false)

// get id from /extraction/:id
import { useRoute } from "vue-router"
import { useRouter } from "vue-router"
const route = useRoute()
let mlcId = route.params.id as string
const router = useRouter()

onMounted(() => {
	api.get("/mlc/" + mlcId)
		.then((response) => {
			console.log("API Response:", response.data)
			mlc.value = response.data || {}
		})
		.catch((error) => {
			console.error("API Error:", error)
		})
})

// watch id change
import { watch } from "vue"
import RelationshipManagement from "@/components/RelationshipManagement.vue"
watch(() => route.params.id, (newId) => {
	if (newId !== mlcId) {
		mlc.value = {} // reset mlc data
		mlcId = newId as string
		api.get("/mlc/" + mlcId)
			.then((response) => {
				console.log("API Response:", response.data)
				mlc.value = response.data || {}
			})
			.catch((error) => {
				console.error("API Error:", error)
			})
	}
})


function gotoEntity(id: string, type: string) {
	if (type === "MLC") {
		router.push({ name: "Medium Level Concept Detail", params: { id } })
	} else if (type === "Entity") {
		router.push({ name: "Entity Detail", params: { id } })
	} else if (type === "HLC") {
		router.push({ name: "High Level Concept Detail", params: { id } })
	} else if(type === "Entity"){
		router.push({ name: "Entity Detail", params: { id } })
	} else {
		console.warn("Unknown type:", type)
	}
}

</script>

<style scoped>
.mlc-token {
	display: inline-block;
	background-color: #f0f0f0;
	border: 1px solid #ccc;
	border-radius: 4px;
	padding: 5px 10px;
	margin: 2px;
	font-family: monospace;
	color: black;
	cursor: pointer;
}

.mlc-token:hover {
	background-color: darkgrey;
}

.css_selected {
	background-color: #d0e0f0;
	border-color: #007bff;
	color: #000;
}

a {
	cursor: pointer;
}
</style>
