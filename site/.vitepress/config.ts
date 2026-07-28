import { defineConfig } from "vitepress";

export default defineConfig({
	title: "AI Assets",
	description: "跨平台、单一真相源的 AI Agent 资产治理中枢",
	base: "/ai-assets/",
	lang: "zh-CN",
	cleanUrls: true,
	lastUpdated: true,

	themeConfig: {
		nav: [
			{ text: "首页", link: "/" },
			{
				text: "演示分享",
				link: "/ai-capabilities-sharing.html",
				target: "_blank",
			},
		],

		sidebar: [
			{
				text: "概述",
				items: [{ text: "项目说明", link: "/" }],
			},
			{
				text: "分享",
				items: [
					{
						text: "演示 HTML",
						link: "/ai-capabilities-sharing.html",
						target: "_blank",
					},
					{ text: "AI Agent 资产体系", link: "/docs/ai-capabilities-sharing" },
				],
			},
		],

		socialLinks: [
			{
				icon: "github",
				link: "https://github.com/EarthChen/ai-assets",
			},
		],

		outline: {
			label: "本页内容",
			level: [2, 3],
		},

		docFooter: {
			prev: "上一页",
			next: "下一页",
		},

		lastUpdatedText: "最后更新",

		search: { provider: "local" },
	},
});
