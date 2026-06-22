<script setup>
/**
 * BaseButton.vue
 * 通用品牌按钮。
 *
 * 设计目标：
 * 1. 用一套统一的 API 覆盖项目里最常见的按钮/链接入口。
 * 2. 通过 variant 控制视觉风格，通过 size 控制尺寸。
 * 3. 在不改变调用方式的前提下，兼容三类语义元素：
 *    - 带 `to` 时渲染为 `RouterLink`
 *    - 带 `href` 时渲染为普通 `<a>`
 *    - 默认渲染为原生 `<button>`
 *
 * 当前支持的视觉变体：
 * - primary: 常规品牌按钮
 * - secondary: 次级浅色玻璃按钮
 * - cta: 强强调按钮，常用于主要转化操作
 * - ghost: 轻量幽灵按钮，适合弱操作或工具操作
 */
import { computed } from 'vue'

/**
 * 组件对外暴露的基础能力：
 * - variant: 决定按钮风格
 * - size: 决定按钮高度、字号和圆角
 * - to / href: 决定按钮是否退化为导航入口
 * - type / disabled: 仅在渲染为原生 button 时生效
 */
const props = defineProps({
  variant: { type: String, default: 'primary' },   // primary | secondary | cta | ghost
  size: { type: String, default: 'md' },            // sm | md
  to: { type: String, default: '' },                // RouterLink 目标
  href: { type: String, default: '' },              // 普通链接
  type: { type: String, default: 'button' },        // button | submit
  disabled: { type: Boolean, default: false },
})

/**
 * 根据传入的导航属性决定根节点类型。
 *
 * 优先级约定：
 * - `to` 优先级最高，面向站内路由跳转
 * - `href` 次之，面向外链或普通链接
 * - 两者都没有时，回退到原生 button
 *
 * 这样调用方只需要传语义属性，不需要自己判断该写什么标签。
 */
const tag = computed(() => {
  if (props.to) return 'RouterLink'
  if (props.href) return 'a'
  return 'button'
})

/**
 * 给不同根节点注入对应属性。
 *
 * 这里刻意只传“当前标签真正需要的属性”：
 * - RouterLink 只拿到 `to`
 * - a 标签只拿到 `href`
 * - button 才拿到 `type` 和 `disabled`
 *
 * 这样能避免把无效属性错误地挂到别的元素上。
 */
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
      // 所有按钮共享的基础布局能力：
      // - inline-flex: 允许文本和图标自然对齐
      // - overflow-hidden: 给 hover 光效和网格纹理提供裁切边界
      // - disabled 样式: 统一禁用态反馈
      'base-button relative overflow-hidden inline-flex items-center justify-center font-medium gap-2 disabled:opacity-50 disabled:cursor-not-allowed',
      // 尺寸层只负责几何信息，不掺杂颜色或品牌风格。
      size === 'sm' ? 'h-8 px-4 text-xs rounded-md' : 'h-10 px-6 text-sm rounded-lg',
      {
        'base-button--primary': variant === 'primary',
        'base-button--secondary': variant === 'secondary',
        'base-button--cta': variant === 'cta',
        'base-button--ghost': variant === 'ghost',
      },
    ]"
  >
    <!--
      仅 primary / cta 显示内部纹理。
      这两个变体承担更强的品牌感和操作权重，增加纹理后更有“主操作”层次。
      secondary / ghost 保持更克制的视觉表达，因此不叠加纹理。
    -->
    <span v-if="variant === 'primary' || variant === 'cta'" class="base-button__grid" aria-hidden="true"></span>

    <!--
      内容层单独抬高到更高 z-index，避免被 hover 蒙层或网格纹理覆盖。
      调用方传入的图标、文字、slot 内容都放在这里。
    -->
    <span class="base-button__content">
      <slot />
    </span>
  </component>
</template>

<style scoped>
/* 基础层：负责统一的交互动效节奏，不区分具体变体。 */
.base-button {
  transition:
    border-color 0.22s ease,
    color 0.22s ease,
    box-shadow 0.28s ease,
    transform 0.22s ease;
}

/* 
  统一 hover 蒙层。
  各个 variant 只需要定义自己的 `::before` 背景内容，
  这里负责控制显示/隐藏时机，避免每个变体重复写一套 hover 逻辑。
*/
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

/*
  内容层始终压在视觉特效之上：
  - z-index: 2 让文字/图标位于纹理层和 hover 蒙层之上
  - gap: inherit 让 slot 内部图标 + 文本沿用根节点间距
*/
.base-button__content {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: inherit;
  position: relative;
  z-index: 2;
}

/*
  Primary:
  默认主按钮。适合“确认”“保存”“下一步”这类常规主操作。
  特征是品牌色渐变 + 柔和微光，强调程度高于 secondary，低于 cta。
*/
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

/*
  Secondary:
  次级按钮，保留按钮感，但视觉重量明显弱于主按钮。
  在浅色模式下更接近白底描边按钮，在深色模式下则是轻玻璃质感。
*/
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

/*
  CTA:
  强转化按钮。和 primary 相比，它的品牌色更实、更亮、hover 发光更强。
  适合“立即开始”“生成结果”“提交关键流程”这类需要用户重点关注的入口。
*/
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

/*
  Ghost:
  轻量幽灵按钮。适合“取消”“次要跳转”“辅助动作”。
  交互上只保留文字颜色变化，不使用 hover 背景蒙层，避免视觉噪音过强。
*/
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
  background: transparent;
}
:root.dark .base-button--ghost:hover {
  color: rgba(208, 214, 224, 1); /* hover:text-[#d0d6e0] */
}
:root.dark .base-button--ghost::before {
  background: transparent;
}

/*
  内部网格纹理：
  - 只服务于 primary / cta
  - 用低透明度网格增加品牌按钮的细节感
  - 配合 radial mask，让纹理集中在中部，避免边缘过于杂乱
*/
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
