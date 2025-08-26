<template>
	<div class="entity">
		<h1>Entity: {{ entity.id }}</h1>
		<p>Created At: {{ new Date(entity.creation_time).toLocaleString() }}</p>
        <p>Textual Identifier: {{ entity.textual_identifier }}</p>

		<button @click="showRelationshipManagement = true">Relationship/Property Management</button>
		
		<RelationshipManagement
			v-if="showRelationshipManagement"
			:selectedTokens="[{...entity, type: 'Entity'}]"
			@close="showRelationshipManagement = false"
			></RelationshipManagement>

		<h2>Properties</h2>
		<ul>
			<li v-for="(value, key) in entity.properties" :key="key">
				<strong>{{ key }}:</strong> {{ value }}
			</li>
		</ul>

		<h2>Relations</h2>
		<ul>
			<li v-for="(relation, index) in relations" :key="index">
				<a @click="redirectToTarget(relation)">{{ relation.text }} [{{ relation.node_type }}] ({{ relation.rel_type }})</a>
			</li>
		</ul>
		
		<h2>MLCs</h2>
		<ul>
			<li v-for="(mlc, index) in mlcs" :key="index">
				<a @click="redirectToTarget(mlc)">{{ mlc.text }} [{{ mlc.node_type }}]</a>
			</li>
		</ul>

		<h2>Present In</h2>
		<ul>
			<li v-for="(conn, index) in present_in" :key="index">
				<a @click="redirectToTarget(conn)">{{ conn.node_type }} ({{ conn.text }})</a>
			</li>
		</ul>

		<!-- for look for metadata or all other relationships (if many only strongest or manually validated) -->
	</div>
</template>
<script setup lang="ts">
// get entity from api
import api from "../api/api.ts"
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { useRouter } from "vue-router";
import { watch } from "vue";
import RelationshipManagement from "../components/RelationshipManagement.vue";

const router = useRouter();
const route = useRoute();
const entity = ref<any>({}); // would be nice to have a type here... for now, using any

const present_in = ref<any[]>([]);
// const extractions = ref<[]>([]);
const mlcs = ref<any[]>([]);
const relations = ref<any[]>([]);
const showRelationshipManagement = ref(false);

// computed component for splitting neighours ()

onMounted(() => {
    const entityId = route.params.id as string;
    api.get("/entities/" + entityId)
        .then((response) => {
            console.log("API Response:", response.data);
            entity.value = response.data || {};

			present_in.value = response.data.simplified_connections.filter((conn: any) => conn.rel_type === "HAS_ENTITY");
			mlcs.value = response.data.simplified_connections.filter((conn: any) => conn.rel_type === "COMBINATION_OF");
			relations.value = response.data.simplified_connections.filter((conn: any) => conn.rel_type !== "COMBINATION_OF" && conn.rel_type !== "HAS_ENTITY");
        })
        .catch((error) => {
            console.error("API Error:", error);
        });
});

watch(
  () => route.params.id,
  (newId, oldId) => {
	console.log("Route parameter changed from", oldId, "to", newId);
	// remount the commponent or fetch new data
	if (newId !== oldId) {
		// Clear previous data
		entity.value = {};
		present_in.value = [];
		mlcs.value = [];
		relations.value = [];

	  api.get("/entities/" + newId)
		.then((response) => {
			console.log("API Response:", response.data);
			entity.value = response.data || {};

			present_in.value = response.data.simplified_connections.filter((conn: any) => conn.rel_type === "HAS_ENTITY");
			mlcs.value = response.data.simplified_connections.filter((conn: any) => conn.rel_type === "COMBINATION_OF");
			relations.value = response.data.simplified_connections.filter((conn: any) => conn.rel_type !== "COMBINATION_OF" && conn.rel_type !== "HAS_ENTITY");
		})
		.catch((error) => {
			console.error("API Error:", error);
		});
	}
}
)

function redirectToTarget(related_node: any) {
	if(related_node.node_type === "Entity") {
		// does not really work...
		router.push({ name: 'Entity Detail', params: { id: related_node.neighbor } });
	} else if(related_node.node_type === "MLC") {
		router.push({ name: 'Medium Level Concept Detail', params: { id: related_node.neighbor } });
	} else if (related_node.node_type === "Extraction") {
		router.push({ name: 'extractionDetail', params: { id: related_node.neighbor } });
	} else if (related_node.node_type === "HLC") {
		router.push({ name: 'High Level Concept Detail', params: { id: related_node.neighbor } });
	} else {
		console.warn("Unknown node type:", related_node.node_type);
	}
}
</script>
<style scoped>
a {
	cursor: pointer;
}
</style>