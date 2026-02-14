import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { viteSourceLocator } from "@metagptx/vite-plugin-source-locator";
import { atoms } from "@metagptx/web-sdk/plugins";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
    plugins: [
        viteSourceLocator({
            prefix: "mgx",
        }),
        react(),
        atoms(),
    ],
    server: {
        watch: { usePolling: true, interval: 800 /* 300~1500 */ },
    },
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "./src"),
        },
    },
}));
