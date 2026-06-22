import { computed, ref } from 'vue'

/**
 * useTheme.js
 * 管理暗色模式、主题色和主题切换动画。
 */
const canUseDom = typeof document !== 'undefined'
const canUseStorage = typeof localStorage !== 'undefined'
const isDark = ref(canUseDom ? document.documentElement.classList.contains('dark') : true)
const THEME_COLOR_STORAGE_KEY = 'theme-color'

const themeColors = [
  {
    id: 'violet',
    name: 'Violet',
    label: '紫罗兰',
    rgb: '129 115 223',
    hoverRgb: '145 132 235',
    strongRgb: '99 87 199',
  },
  {
    id: 'blue',
    name: 'Blue',
    label: '湖蓝',
    rgb: '37 99 235',
    hoverRgb: '59 130 246',
    strongRgb: '29 78 216',
  },
  {
    id: 'emerald',
    name: 'Emerald',
    label: '松石绿',
    rgb: '5 150 105',
    hoverRgb: '16 185 129',
    strongRgb: '4 120 87',
  },
  {
    id: 'rose',
    name: 'Rose',
    label: '玫瑰红',
    rgb: '225 29 72',
    hoverRgb: '244 63 94',
    strongRgb: '190 18 60',
  },
  {
    id: 'amber',
    name: 'Amber',
    label: '琥珀黄',
    rgb: '217 119 6',
    hoverRgb: '245 158 11',
    strongRgb: '180 83 9',
  },
]

const defaultThemeColor = themeColors[0]
const accentColorId = ref(defaultThemeColor.id)

/**
 * 根据主题色 ID 获取配置，不存在时回退到默认主题色。
 */
function getThemeColor(id) {
  return themeColors.find((color) => color.id === id) || defaultThemeColor
}

/**
 * 把主题色写入根节点 CSS 变量，供 Tailwind 和自定义样式复用。
 */
function applyAccentColor(color) {
  if (!canUseDom) return
  const root = document.documentElement
  root.dataset.themeColor = color.id
  root.style.setProperty('--accent-rgb', color.rgb)
  root.style.setProperty('--accent-hover-rgb', color.hoverRgb)
  root.style.setProperty('--accent-strong-rgb', color.strongRgb)
}

/**
 * 安全读取 localStorage，避免隐私模式或禁用存储时报错。
 */
function getStoredValue(key, fallback) {
  if (!canUseStorage) return fallback
  try {
    return localStorage.getItem(key) || fallback
  } catch (_) {
    return fallback
  }
}

/**
 * 安全写入 localStorage；写入失败不影响当前页面主题切换。
 */
function setStoredValue(key, value) {
  if (!canUseStorage) return
  try {
    localStorage.setItem(key, value)
  } catch (_) {
    // 存储失败时仍保留当前页面的主题效果。
  }
}

export function useTheme() {
  const accentColor = computed(() => getThemeColor(accentColorId.value))

  function applyTheme(dark) {
    isDark.value = dark
    if (canUseDom) document.documentElement.classList.toggle('dark', dark)
    setStoredValue('theme', dark ? 'dark' : 'light')
  }

  /**
   * 直接设置明暗主题，并持久化用户选择。
   */
  async function setTheme(dark, btnEl) {
    const nextDark = Boolean(dark)
    if (nextDark === isDark.value) return

    const hasWindow = typeof window !== 'undefined'
    const prefersReduce = hasWindow && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    const canTransition = hasWindow && canUseDom && !prefersReduce && typeof document.startViewTransition === 'function'

    if (!canTransition || !btnEl) {
      applyTheme(nextDark)
      return
    }

    const rect = btnEl.getBoundingClientRect()
    const x = rect.left + rect.width / 2
    const y = rect.top + rect.height / 2
    const endRadius = Math.hypot(Math.max(x, window.innerWidth - x), Math.max(y, window.innerHeight - y))

    const transition = document.startViewTransition(() => applyTheme(nextDark))
    try {
      await transition.ready
      const duration = 1000
      document.documentElement.animate(
        { clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${endRadius}px at ${x}px ${y}px)`] },
        { duration, easing: 'cubic-bezier(0.2, 0, 0, 1)', pseudoElement: '::view-transition-new(root)' },
      )
      document.documentElement.animate(
        { opacity: [1, 0.98] },
        { duration, easing: 'linear', pseudoElement: '::view-transition-old(root)' },
      )
      await transition.finished
    } catch (_) {
      applyTheme(nextDark)
    }
  }

  /**
   * 设置主题色，并同步到 CSS 变量和本地存储。
   */
  async function setAccentColor(colorId, btnEl) {
    const color = getThemeColor(colorId)
    if (color.id === accentColorId.value) return

    const applyColor = () => {
      accentColorId.value = color.id
      applyAccentColor(color)
      setStoredValue(THEME_COLOR_STORAGE_KEY, color.id)
    }

    const hasWindow = typeof window !== 'undefined'
    const prefersReduce = hasWindow && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    const canTransition = hasWindow && canUseDom && !prefersReduce && typeof document.startViewTransition === 'function'

    if (!canTransition || !btnEl) {
      applyColor()
      return
    }

    const rect = btnEl.getBoundingClientRect()
    const x = rect.left + rect.width / 2
    const y = rect.top + rect.height / 2
    const endRadius = Math.hypot(Math.max(x, window.innerWidth - x), Math.max(y, window.innerHeight - y))

    const transition = document.startViewTransition(applyColor)
    try {
      await transition.ready
      const duration = 900
      document.documentElement.animate(
        { clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${endRadius}px at ${x}px ${y}px)`] },
        { duration, easing: 'cubic-bezier(0.2, 0, 0, 1)', pseudoElement: '::view-transition-new(root)' },
      )
      document.documentElement.animate(
        { opacity: [1, 0.98] },
        { duration, easing: 'linear', pseudoElement: '::view-transition-old(root)' },
      )
      await transition.finished
    } catch (_) {
      applyColor()
    }
  }

  /**
   * 带圆形扩散动画的主题切换
   * @param {HTMLElement} [btnEl] - 触发按钮元素，动画从此处扩散；不传则无动画
   */
  async function toggleTheme(btnEl) {
    await setTheme(!isDark.value, btnEl)
  }

  /**
   * 页面启动时恢复本地保存的明暗模式和主题色。
   */
  function initTheme() {
    const saved = getStoredValue('theme', 'dark')
    const savedColor = getStoredValue(THEME_COLOR_STORAGE_KEY, defaultThemeColor.id)
    applyTheme(saved === 'dark')
    setAccentColor(savedColor)
  }

  return { isDark, themeColors, accentColor, accentColorId, setTheme, toggleTheme, setAccentColor, initTheme }
}
