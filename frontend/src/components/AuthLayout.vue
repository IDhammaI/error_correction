<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const transitionName = ref('auth-slide-left')

router.beforeEach((to, from) => {
  const toOrder = to.meta.order ?? 0
  const fromOrder = from.meta.order ?? 0
  transitionName.value = toOrder >= fromOrder ? 'auth-slide-left' : 'auth-slide-right'
})

const FEATURES = [
  { icon: 'fa-camera', text: '拍照上传，AI 自动识别题目与公式' },
  { icon: 'fa-brain', text: 'LangGraph Agent 智能拆题纠错' },
  { icon: 'fa-tags', text: '知识点自动打标，构建个人图谱' },
  { icon: 'fa-file-export', text: '一键导出 Markdown / PDF 错题本' },
]
</script>

<template>
  <div class="min-h-screen flex bg-slate-50 dark:bg-[#0A0A0F]">

    <!-- 左侧品牌区（大屏显示） -->
    <div class="hidden lg:flex flex-col justify-between w-[52%] relative overflow-hidden bg-gradient-to-br from-blue-600 to-indigo-700 dark:from-indigo-950 dark:to-[#0A0A0F] p-12">
      <!-- 背景装饰光晕 -->
      <div class="absolute inset-0 pointer-events-none">
        <div class="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] rounded-full bg-blue-400/20 dark:bg-indigo-500/10 blur-[120px]"></div>
        <div class="absolute bottom-[-10%] right-[-10%] w-[400px] h-[400px] rounded-full bg-indigo-400/20 dark:bg-blue-500/10 blur-[100px]"></div>
        <!-- 网格纹理 -->
        <div class="absolute inset-0 opacity-[0.04]" style="background-image: linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px); background-size: 40px 40px;"></div>
      </div>

      <!-- 顶部 Logo -->
      <div class="relative flex items-center gap-3">
        <div class="relative group">
          <div class="absolute inset-0 bg-blue-500/60 dark:bg-indigo-500/60 blur-xl opacity-0 group-hover:opacity-100 transition duration-500 rounded-2xl"></div>
          <div class="relative bg-gradient-to-br from-blue-500 to-indigo-700 dark:from-indigo-500 dark:to-indigo-800 p-2.5 rounded-2xl shadow-md shadow-indigo-500/30 border border-white/10">
            <img src="/logo.svg" class="w-7 h-7 brightness-0 invert" alt="logo" />
          </div>
        </div>
        <span class="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white via-indigo-200 to-indigo-200 tracking-wide">智卷错题本</span>
      </div>

      <!-- 中部主文案 -->
      <div class="relative">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 border border-white/20 text-xs font-bold text-blue-100 dark:text-indigo-300 tracking-widest uppercase mb-6">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          AI 驱动的错题管理
        </div>
        <h2 class="text-4xl font-extrabold text-white leading-tight mb-4">
          重塑错题整理<br />
          <span class="text-blue-200 dark:text-indigo-300">一键生成知识图谱</span>
        </h2>
        <p class="text-base text-blue-100/80 dark:text-slate-400 leading-relaxed max-w-sm">
          专为中学生与大学生研发。上传凌乱试卷，AI 自动完成图片分割、OCR 纠错及 LaTeX 公式还原。
        </p>

        <!-- 特性列表 -->
        <ul class="mt-8 space-y-4">
          <li v-for="f in FEATURES" :key="f.text" class="flex items-center gap-3 text-sm text-blue-100/90 dark:text-slate-300">
            <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-white/10 border border-white/15">
              <i :class="`fas ${f.icon} text-xs text-white`"></i>
            </div>
            {{ f.text }}
          </li>
        </ul>
      </div>

      <!-- 底部版权 -->
      <div class="relative text-xs text-blue-200/50 dark:text-slate-600">
        © {{ new Date().getFullYear() }} 智卷错题本 · All rights reserved
      </div>
    </div>

    <!-- 右侧表单区 -->
    <div class="flex-1 flex flex-col items-center justify-center px-4 py-12 lg:px-16 relative">

      <!-- 返回主页 -->
      <a href="/" class="absolute top-6 right-6 inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold text-slate-700 dark:text-slate-200 bg-white/80 dark:bg-white/15 backdrop-blur-md border border-slate-200/60 dark:border-white/10 hover:bg-white dark:hover:bg-white/25 transition-all shadow-sm">
        <i class="fas fa-arrow-left text-xs"></i>
        返回主页
      </a>

      <!-- 移动端 Logo（小屏显示） -->
      <div class="lg:hidden text-center mb-8">
        <div class="relative inline-flex mb-4 group">
          <div class="absolute inset-0 bg-blue-500/60 dark:bg-indigo-500/60 blur-xl opacity-0 group-hover:opacity-100 transition duration-500 rounded-2xl"></div>
          <div class="relative bg-gradient-to-br from-blue-500 to-indigo-700 dark:from-indigo-500 dark:to-indigo-800 p-2.5 rounded-2xl shadow-md shadow-indigo-500/30 border border-white/10">
            <img src="/logo.svg" class="w-7 h-7 brightness-0 invert" alt="logo" />
          </div>
        </div>
        <h1 class="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-700 to-indigo-700 dark:from-white dark:via-indigo-200 dark:to-indigo-200 tracking-wide">智卷错题本</h1>
      </div>

      <div class="w-full max-w-sm">
        <!-- 标题 -->
        <div class="mb-8">
          <h3 class="text-2xl font-bold text-slate-900 dark:text-white">
            {{ route.path === '/auth/login' ? '欢迎回来' : '创建账户' }}
          </h3>
          <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
            {{ route.path === '/auth/login' ? '登录以继续使用你的错题本' : '免费注册，开始智能错题整理' }}
          </p>
        </div>

        <!-- Tab 切换 -->
        <div class="flex rounded-xl bg-slate-100/80 dark:bg-white/5 border border-slate-200/60 dark:border-white/10 p-1 mb-6">
          <RouterLink
            to="/auth/login"
            class="flex-1 py-2 text-sm font-bold rounded-xl text-center transition-all"
            :class="route.path === '/auth/login'
              ? 'bg-white dark:bg-white/10 text-blue-600 dark:text-blue-400 shadow-sm'
              : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'"
          >登录</RouterLink>
          <RouterLink
            to="/auth/register"
            class="flex-1 py-2 text-sm font-bold rounded-xl text-center transition-all"
            :class="route.path === '/auth/register'
              ? 'bg-white dark:bg-white/10 text-blue-600 dark:text-blue-400 shadow-sm'
              : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'"
          >注册</RouterLink>
        </div>

        <!-- 表单内容（滑动过渡） -->
        <RouterView v-slot="{ Component }">
          <Transition :name="transitionName" mode="out-in">
            <component :is="Component" :key="route.path" />
          </Transition>
        </RouterView>

        <!-- 底部版权（移动端） -->
        <p class="lg:hidden text-center text-xs text-slate-400 dark:text-slate-600 mt-8">
          © {{ new Date().getFullYear() }} 智卷错题本
        </p>
      </div>
    </div>

  </div>
</template>

<style>
/* 禁用浏览器自动填充背景色 */
input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus {
  transition: background-color 9999s ease;
  -webkit-text-fill-color: #f1f5f9;
  caret-color: #f1f5f9;
}
</style>

<style scoped>
/* 向左滑（登录 → 注册） */
.auth-slide-left-enter-active,
.auth-slide-left-leave-active {
  transition: opacity 0.22s ease, transform 0.22s ease;
}
.auth-slide-left-enter-from  { opacity: 0; transform: translateX(32px); }
.auth-slide-left-leave-to   { opacity: 0; transform: translateX(-32px); }

/* 向右滑（注册 → 登录） */
.auth-slide-right-enter-active,
.auth-slide-right-leave-active {
  transition: opacity 0.22s ease, transform 0.22s ease;
}
.auth-slide-right-enter-from { opacity: 0; transform: translateX(-32px); }
.auth-slide-right-leave-to  { opacity: 0; transform: translateX(32px); }
</style>
