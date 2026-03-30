import { ref } from 'vue'

const isDark = ref(document.documentElement.classList.contains('dark'))

export function useTheme() {
  function setTheme(dark) {
    isDark.value = dark
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }

  function toggleTheme() {
    setTheme(!isDark.value)
  }

  function initTheme() {
    const saved = localStorage.getItem('theme') || 'dark'
    isDark.value = saved === 'dark'
    document.documentElement.classList.toggle('dark', isDark.value)
  }

  return { isDark, setTheme, toggleTheme, initTheme }
}
