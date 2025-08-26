<script setup lang="ts">
import { RouterLink, RouterView } from "vue-router"
import HelloWorld from "./components/HelloWorld.vue"
</script>

<template>
	<header>
		<nav>
			<RouterLink to="/">Home</RouterLink>
			<RouterLink to="/extraction">Extraction</RouterLink>
			<RouterLink to="/workspace">Workspace</RouterLink>
			<RouterLink to="/compare">Compare</RouterLink>
			<RouterLink to ="/search">Search</RouterLink>
		</nav>
	</header>

	<RouterView />
</template>

<style scoped>
nav {
	width: 100%;
	text-align: center;
	margin-top: 2rem;
	padding-left: 2rem;
}

nav a.router-link-exact-active {
	color: var(--color-text);
}

nav a.router-link-exact-active:hover {
	background-color: transparent;
}

nav a {
	display: inline-block;
	padding: 0 1rem;
	border-left: 1px solid var(--color-border);
}

nav a:first-of-type {
	border: 0;
}
</style>
