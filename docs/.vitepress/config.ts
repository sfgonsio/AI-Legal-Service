import { defineConfig } from "vitepress";

export default defineConfig({
  title: "AI Legal Service",
  description: "Specification Portal + Build Contract",
  themeConfig: {
    nav: [
      { text: "Start", link: "/" },
      { text: "Architecture", link: "/architecture/" },
      { text: "Contract v1", link: "/contract/v1" },
      { text: "Legacy HTML", link: "/legacy/" }
    ],
    sidebar: {
      "/architecture/": [
        { text: "Architecture", link: "/architecture/" },
        { text: "Section 7", link: "/architecture/section7" }
      ],
      "/contract/": [
        { text: "Contract", items: [{ text: "v1", link: "/contract/v1" }] }
      ]
    }
  }
});