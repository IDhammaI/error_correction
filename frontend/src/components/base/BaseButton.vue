<script setup>
/**
 * BaseButton.vue
 * 品牌按钮（primary/secondary/cta 变体）
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
      'home-btn relative overflow-hidden inline-flex items-center justify-center font-medium gap-2 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed',
      size === 'sm' ? 'h-8 px-4 text-xs rounded-lg' : 'h-10 px-6 text-sm rounded-xl',
      {
        'home-btn--primary': variant === 'primary',
        'home-btn--secondary': variant === 'secondary',
        'home-btn--cta': variant === 'cta',
        'home-btn--ghost': variant === 'ghost',
      },
    ]"
  >
    <!-- 内部网格纹理 -->
    <span v-if="variant === 'primary' || variant === 'cta'" class="btn-grid" aria-hidden="true"></span>
    <slot />
  </component>
</template>

<style scoped>
/* ── Primary: 品牌色渐变，微光 hover ── */
.home-btn--primary {
  background: linear-gradient(to bottom, rgba(129, 115, 223, 0.9), rgba(99, 87, 199, 0.9));
  color: #fff;
  border: none;
  box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.12);
}
.home-btn--primary:hover {
  background: linear-gradient(to bottom, rgba(145, 132, 235, 0.95), rgba(113, 100, 212, 0.95));
  box-shadow:
    inset 0 1px 0 0 rgba(255, 255, 255, 0.15),
    0 0 20px 0 rgba(129, 115, 223, 0.25);
}

/* ── Secondary: 白玻璃按钮（与 brand-btn 一致） ── */
.home-btn--secondary {
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-top-color: rgba(255, 255, 255, 0.15);
  border-bottom-color: rgba(255, 255, 255, 0.03);
}
:root.dark .home-btn--secondary {
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-top-color: rgba(255, 255, 255, 0.15);
  border-bottom-color: rgba(255, 255, 255, 0.03);
}
:root:not(.dark) .home-btn--secondary {
  background: #ffffff;
  color: rgba(0, 0, 0, 0.75);
  border: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.home-btn--secondary:hover {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.8);
}
:root.dark .home-btn--secondary:hover {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.8);
}
:root:not(.dark) .home-btn--secondary:hover {
  background: #f9fafb;
  color: rgba(0, 0, 0, 0.9);
  border-color: rgba(0, 0, 0, 0.15);
}

/* ── CTA: 更强的品牌色，用于转化区 ── */
.home-btn--cta {
  background: linear-gradient(to bottom, rgba(109, 92, 214, 1), rgba(88, 72, 194, 1));
  color: #fff;
  border: none;
  box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.12);
}
.home-btn--cta:hover {
  background: linear-gradient(to bottom, rgba(125, 108, 228, 1), rgba(102, 86, 208, 1));
  box-shadow:
    inset 0 1px 0 0 rgba(255, 255, 255, 0.15),
    0 0 24px 0 rgba(109, 92, 214, 0.3);
}

/* ── Ghost: 幽灵按钮，用于无背景仅边框/字体的操作 ── */
.home-btn--ghost {
  background: transparent;
  color: rgba(107, 114, 128, 1); /* text-gray-500 */
  border: 1px solid rgba(229, 231, 235, 1); /* border-gray-200 */
}
:root.dark .home-btn--ghost {
  color: rgba(138, 143, 152, 1); /* text-[#8a8f98] */
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.03);
}
.home-btn--ghost:hover {
  background: rgba(249, 250, 251, 1); /* hover:bg-gray-50 */
  color: rgba(55, 65, 81, 1); /* hover:text-gray-700 */
}
:root.dark .home-btn--ghost:hover {
  background: rgba(255, 255, 255, 0.06);
  color: rgba(208, 214, 224, 1); /* hover:text-[#d0d6e0] */
}

/* ── 按钮内网格纹理 ── */
.btn-grid {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image:
    linear-gradient(to right, rgba(255, 255, 255, 0.06) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(255, 255, 255, 0.06) 1px, transparent 1px);
  background-size: 8px 8px;
  mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
  -webkit-mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
}
</style>
