<template>
	<div class="hlc">
		<h1>HLC: {{ hlc.id }}</h1>
		<p>Created At: {{ new Date(hlc.creation_time).toLocaleString() }}</p>

		<!-- for look for metadata or all other relationships (if many only strongest or manually validated) -->

		<h2>Token Chain</h2>

		<div>
			<h3>Quick Actions</h3>
			<p>Selected tokens: {{ tokenChain.filter((t) => t.selected) }}</p>
			<button v-if="tokenChain.filter((t) => t.selected).length > 1" @click="promote_entity">
				Promote to Entity
			</button>
			<button v-if="tokenChain.filter((t) => t.selected).length > 0" @click="deselect_all">
				Deselect tokens
			</button>
			<button @click="gotoSelected" v-if="tokenChain.filter((t) => t.selected).length == 1">Go to Selected</button>
			<button @click="showEntityManagement=true" v-if="tokenChain.filter((t) => t.selected).length >= 1">
				Entity Management
			</button>
			<button @click="showRelationshipManagement=true" v-if="tokenChain.filter((t) => t.selected).length == 2 || tokenChain.filter((t) => t.selected).length == 1"> 
				Create Relation
			</button>
		</div>

		<EntityManagement 
			v-if="showEntityManagement"
			:selected-tokens="tokenChain.filter((t) => t.selected)"
			:mlc_index="tokenChain.findIndex((t) => t.selected)"
			:hlc_id="hlc.id"
			@close="() => showEntityManagement = false"
			@create-entity="(e) => addEntityToTokenChain(e)" />

		<RelationshipManagement
			v-if="showRelationshipManagement"
			:selected-tokens="tokenChain.filter((t) => t.selected)"
			:hlc_id="hlc.id"
			@close="() => showRelationshipManagement = false"
			@create-relationship="(e) => console.log('Relationship created:', e)" />

		<div style="display: flex; flex-direction: row; flex-wrap: wrap; gap: 10px">
			<!-- Display each token in a separate div for better styling -->
			<div
				@click="toggle_selection(index)"
				v-for="(token, index) in tokenChain"
				:key="index"
				class="hlc-token"
				:class="{ css_selected: token.selected, 'mlc-token': token.type === 'MLC', 'entity-token': token.type === 'Entity' }"
			>
				<span class="token">{{ token.text }}</span> <!-- add textual identifier later for entities -->
			</div>
		</div>

		<div v-if="hlc.entities && hlc.entities.length > 0">
			<h2>Entities</h2>
			<ul>
				<li v-for="(entity, index) in hlc.entities" :key="index">
					<a @click="navigateToEntity(entity.id)"
						>{{ entity.text }}</a
					>
					<span v-if="entity.textual_identifier">({{ entity.textual_identifier }})</span>
				</li>
			</ul>
		</div>

		<div v-if="hlc.recommended_entities && hlc.recommended_entities.length > 0">
			<h2>Recommended Entities</h2>
			<ul>
				<li v-for="(entity, index) in hlc.recommended_entities" :key="index">
					{{ entity.text }} [{{ entity.label }}] ({{ entity.recommended_by }})
				</li>
			</ul>
		</div>

		<div v-if="recommended_entities && recommended_entities.length > 0">
			<h2>Recommended Entities (new)</h2>
			<ul>
				<li v-for="(entity, index) in recommended_entities" :key="index">
					Experiences ({{ entity[2] }}) - <span v-if="entity[0]">{{ entity[0].textual_identifier }}</span>
				</li>
			</ul>
		</div>

		<h2>Extraction</h2>
		<ul>
			<li v-for="(extraction, index) in hlc.extractions" :key="index">
				<a @click="navigateToExtraction(extraction.id)">{{ extraction.textual_identifier }}</a>
			</li>
		</ul>

		<h2>Raw</h2>
		<pre>{{ hlc.text }}</pre>
	</div>
</template>

<script setup lang="ts">
// test api call here
import EntityManagement from "@/components/EntityManagement.vue"
import api from "../api/api.ts"
import { ref, onMounted } from "vue"
import { useRouter } from "vue-router"


const hlc = ref<any>({}) // would be nice to have a type here... for now, using any
const router = useRouter()

// get id from /extraction/:id
import { useRoute } from "vue-router"
import RelationshipManagement from "@/components/RelationshipManagement.vue"
const route = useRoute()
const hlcId = route.params.id as string
const showEntityManagement = ref(false)
const showRelationshipManagement = ref(false)

const recommended_entities = ref<Array<any>>([]) // would be nice to have a type here... for now, using any

const tokenChain = ref<Array<any>>([
	// {
	// 	mlc_id: "mlc_12345",
	// 	text: "example_token",
	// 	selected: false,
	// },
])

onMounted(() => {
	api.get("/hlc/" + hlcId)
		.then((response) => {
			console.log("API Response:", response.data)
			hlc.value = response.data || {}
			if (response.data.tokens) {
				tokenChain.value = response.data.chain.map((token: any) => ({
					...token,
					selected: false,
				}))
			}

			api.post("/find-recommended-entities", {
				mlc_ids: tokenChain.value.map((token: any) => token.id), // .join(",")
				hlc_id: hlcId,
			})
				.then((response) => {
					console.log("Recommended Entities Response:", response.data)
					recommended_entities.value = response.data || []
				})
				.catch((error) => {
					console.error("Error fetching recommended entities:", error)
				})

		})
		.catch((error) => {
			console.error("API Error:", error)
		})


})

function toggle_selection(index: number) {
	const token = tokenChain.value[index]
	token.selected = !token.selected
	console.log(`Token ${index} selected state:`, token.selected)
}

function deselect_all() {
	tokenChain.value.forEach((token) => {
		token.selected = false
	})
	console.log("All tokens deselected")
}

function promote_entity() {
	const selectedTokens = tokenChain.value.filter((t) => t.selected)
	if (selectedTokens.length > 1) {
		console.log("Promoting tokens to entity:", selectedTokens)

		const concatenatedText = selectedTokens.map((t) => t.text).join(" ")
		const textualIdentifier =
			prompt("Enter a textual identifier for the new entity:", concatenatedText) ||
			concatenatedText
		const firstSelectedTokenIndex = tokenChain.value.findIndex((t) => t.selected)

		api.post("/entities", {
			text: concatenatedText,
			textual_identifier: concatenatedText,
			id: "",
			from_hlc: true,
			hlc_id: hlcId,
			mlc_token_ids: selectedTokens.map((t) => t.id),
			mlc_token_index: tokenChain.value
				.map((t) => t.selected)
				.indexOf(true), // this is the index of the first selected token, which is used to determine where to insert the entity in the chain
			// probably have to be careful that only mlc tokens are selected?
			// another problem --> there are multiple things here... keep mlc tokens but add entity in between? so do not replace but just add entity in between or after the last MLC
		})
			.then((response) => {
				console.log("Entity promoted successfully:", response.data)
				// add entity to tokenchain
				tokenChain.value.splice(firstSelectedTokenIndex, 0, {
					id: response.data.id,
					text: response.data.text,
					type: "Entity",
					selected: false,
				})

				alert("Entity promoted successfully: " + response.data)
			})
			.catch((error) => {
				console.error("Error promoting entity:", error)
			})
	} else {
		console.warn("Please select more than one token to promote to an entity.")
	}
}

function gotoSelected() {
	const selectedToken = tokenChain.value.find((t) => t.selected)
	if (selectedToken) {
		const urlType = selectedToken.type.toLowerCase()
		
		// push via router to the correct page
		router.push(`/${urlType}/${selectedToken.id}`)
			.then(() => {
				console.log(`Navigated to ${urlType}/${selectedToken.id}`)
			})
			.catch((error) => {
				console.error("Navigation error:", error)
			})

	} else {
		alert("No token selected.")
	}
}

function addEntityToTokenChain(entity: any) {
	console.log("Adding entity to token chain:", entity)
	const firstSelectedTokenIndex = tokenChain.value.findIndex((t) => t.selected)
	if (firstSelectedTokenIndex !== -1) {
		tokenChain.value.splice(firstSelectedTokenIndex, 0, {
			id: entity.id,
			text: entity.text,
			type: "Entity",
			selected: false,
		})
	}
	deselect_all()
}

function navigateToEntity(entityId: string) {
	router.push({ name: 'Entity Detail', params: { id: entityId } })
}

function navigateToExtraction(extractionId: string) {
	router.push({ name: 'extractionDetail', params: { id: extractionId } })
}
</script>

<style scoped>
.hlc-token {
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

.hlc-token:hover {
	background-color: darkgrey;
}

.css_selected {
	background-color: #d0e0f0 !important;
	border-color: #007bff !important;
	color: #000;
}

.entity-token {
	background-color: #d0f0d0;
	border-color: #28a745;
	color: #000;
}

.darkened {
	background-color: rgba(0, 0, 0, 0.5);
	backdrop-filter: blur(50px);
}

a {
	cursor: pointer;
	text-decoration: none;
}

/* .mlc-token {
	background-color: #f0d0d0;
	border-color: #dc3545;
	color: #000;
} */
</style>
