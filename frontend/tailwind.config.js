/** @type {import('tailwindcss').Config} */
import typography from '@tailwindcss/typography'

export default {
  // Tailwind 只会为 content 中扫描到的 class 生成 CSS；app.html 是当前 SPA 入口，必须包含。
  content: ["./index.html", "./app.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
  // 暗色模式由根节点上的 .dark class 控制，方便 useTheme 统一切换主题。
  darkMode: "class",
  theme: {
    // 项目当前主要使用 Tailwind 默认主题和 CSS 变量，暂不扩展自定义设计 token。
    extend: {},
  },
  plugins: [
    // 提供 prose 等排版工具类，用于 Markdown/富文本内容的默认样式。
    typography,
  ],
}
