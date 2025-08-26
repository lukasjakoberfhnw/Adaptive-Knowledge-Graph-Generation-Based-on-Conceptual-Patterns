import { createRouter, createWebHistory } from "vue-router"
import HomeView from "../views/HomeView.vue"

const router = createRouter({
	history: createWebHistory(import.meta.env.BASE_URL),
	routes: [
		{
			path: "/",
			name: "home",
			component: HomeView,
		},
		{
			path: "/about",
			name: "about",
			// route level code-splitting
			// this generates a separate chunk (About.[hash].js) for this route
			// which is lazy-loaded when the route is visited.
			component: () => import("../views/AboutView.vue"),
		},
		{
			path: "/extraction",
			name: "extraction",
			component: () => import("../views/ExtractionView.vue"),
		},
		{
			path: "/extraction/:id",
			name: "extractionDetail",
			component: () => import("../views/ExtractionDetails.vue"),
		},
		{
			path: "/source",
			name: "Source",
			component: () => import("../views/SourceView.vue"),
		},
		{
			path: "/hlc/:id",
			name: "High Level Concept Detail",
			component: () => import("../views/HLCView.vue"),
		},
		{
			path: "/mlc/:id",
			name: "Medium Level Concept Detail",
			component: () => import("../views/MLCDetails.vue"),
		},
		{
			path: "/entity/:id",
			name: "Entity Detail",
			component: () => import("../views/EntityDetails.vue"),
		},
		{
			path: "/search",
			name: "Search",
			component: () => import("../views/Search.vue"),
		},
		{
			path: "/workspace",
			name: "Workspace",
			component: () => import("../views/Workspace.vue"),
		},
		{
			path: "/compare",
			name: "Compare",
			component: () => import("../views/CompareView.vue"),
		}
	],
})

export default router
