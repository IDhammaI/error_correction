<script setup>
/**
 * BaseButton.vue
 * 通用品牌按钮（primary/secondary/cta/ghost 变体）
 */
import { computed } from 'vue'

const props = defineProps({
  variant: { type: String, default: 'primary' },   // primary | secondary | cta | ghost
  size: { type: String, default: 'md' },            // sm | md
  to: { type: String, default: '' },                // RouterLink 目标
  href: { type: String, default: '' },              // 普通链接
  type: { type: String, default: 'button' },        // button | submit
  disabled: { type: Boolean, default: false },
})

const tag = computed(() => {
  if (props.to) return 'RouterLink'
  if (props.href) return 'a'
  return 'button'
})

const bindProps = computed(() => {
  if (props.to) return { to: props.to }
  if (props.href) return { href: props.href }
  return { type: props.type, disabled: props.disabled }
})
</script>

<template>
  <component
    :is="tag"
    v-bind="bindProps"
    :class="[
      'base-button relative overflow-hidden inline-flex items-center justify-center font-medium gap-2 disabled:opacity-50 disabled:cursor-not-allowed',
      size === 'sm' ? 'h-8 px-4 text-xs rounded-md' : 'h-10 px-6 text-sm rounded-lg',
      {
        'base-button--primary': variant === 'primary',
        'base-button--secondary': variant === 'secondary',
        'base-button--cta': variant === 'cta',
        'base-button--ghost': variant === 'ghost',
      },
    ]"
  >
    <!-- 内部网格纹理 -->
    <span v-if="variant === 'primary' || variant === 'cta'" class="base-button__grid" aria-hidden="true"></span>
    <span class="base-button__content">
      <slot />
    </span>
  </component>
</template>

<style scoped>
.base-button {
  transition:
    border-color 0.22s ease,
    color 0.22s ease,
    box-shadow 0.28s ease,
    transform 0.22s ease;
}

.base-button::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.24s ease;
}

.base-button:hover::before {
  opacity: 1;
}

.base-button__content {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: inherit;
  position: relative;
  z-index: 2;
}

/* ── Primary: 品牌色渐变，微光 hover ── */
.base-button--primary {
  background: linear-gradient(to bottom, rgb(var(--accent-rgb) / 0.9), rgb(var(--accent-strong-rgb) / 0.9));
  color: #fff;
  border: none;
  box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.12);
}
.base-button--primary:hover {
  box-shadow:
    inset 0 1px 0 0 rgba(255, 255, 255, 0.15),
    0 0 20px 0 rgb(var(--accent-rgb) / 0.25);
}
.base-button--primary::before {
  background: linear-gradient(to bottom, rgb(var(--accent-hover-rgb) / 0.95), rgb(var(--accent-rgb) / 0.95));
}

/* ── Secondary: 白玻璃按钮（与 brand-btn 一致） ── */
.base-button--secondary {
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-top-color: rgba(255, 255, 255, 0.15);
  border-bottom-color: rgba(255, 255, 255, 0.03);
}
:root:not(.dark) .base-button--secondary {
  background: #ffffff;
  color: rgba(0, 0, 0, 0.75);
  border: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.base-button--secondary:hover {
  color: rgba(255, 255, 255, 0.8);
}
.base-button--secondary::before {
  background: rgba(255, 255, 255, 0.08);
}
:root:not(.dark) .base-button--secondary:hover {
  color: rgba(0, 0, 0, 0.9);
  border-color: rgba(0, 0, 0, 0.15);
}
:root:not(.dark) .base-button--secondary::before {
  background: #f9fafb;
}

/* ── CTA: 更强的品牌色，用于转化区 ── */
.base-button--cta {
  background: linear-gradient(to bottom, rgb(var(--accent-rgb)), rgb(var(--accent-strong-rgb)));
  color: #fff;
  border: none;
  box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.12);
}
.base-button--cta:hover {
  box-shadow:
    inset 0 1px 0 0 rgba(255, 255, 255, 0.15),
    0 0 24px 0 rgb(var(--accent-rgb) / 0.3);
}
.base-button--cta::before {
  background: linear-gradient(to bottom, rgb(var(--accent-hover-rgb)), rgb(var(--accent-rgb)));
}

/* ── Ghost: 幽灵按钮，用于无背景仅边框/字体的操作 ── */
.base-button--ghost {
  background: transparent;
  color: rgba(107, 114, 128, 1); /* text-gray-500 */
  border: 1px solid rgba(229, 231, 235, 1); /* border-gray-200 */
}
:root.dark .base-button--ghost {
  color: rgba(138, 143, 152, 1); /* text-[#8a8f98] */
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.03);
}
.base-button--ghost:hover {
  color: rgba(55, 65, 81, 1); /* hover:text-gray-700 */
}
.base-button--ghost::before {
  background: rgba(249, 250, 251, 1); /* hover:bg-gray-50 */
}
:root.dark .base-button--ghost:hover {
  color: rgba(208, 214, 224, 1); /* hover:text-[#d0d6e0] */
}
:root.dark .base-button--ghost::before {
  background: rgba(255, 255, 255, 0.06);
}

/* ── 按钮内网格纹理 ── */
.base-button__grid {
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
  background-image:
    linear-gradient(to right, rgba(255, 255, 255, 0.06) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(255, 255, 255, 0.06) 1px, transparent 1px);
  background-size: 8px 8px;
  mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
  -webkit-mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
}
</style>
