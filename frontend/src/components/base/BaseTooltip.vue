<script setup>
/**
 * 通用 Tooltip 组件。
 *
 * 使用 Teleport 固定到 body，避免被父级 overflow 裁剪，并在移动端禁用 hover 残留。
 */
import { computed, inject, nextTick, onBeforeUnmount, ref } from 'vue'

const props = defineProps({
  text: { type: String, required: true },
  placement: { type: String, default: 'bottom' },
  align: { type: String, default: 'center' },
  offset: { type: Number, default: 8 },
  disabled: { type: Boolean, default: false },
})

const provider = inject('baseTooltipProvider', null)

const visible = ref(false)
const triggerRef = ref(null)
const tooltipRef = ref(null)
const position = ref({ left: 0, top: 0 })

const tooltipStyle = computed(() => ({
  left: `${position.value.left}px`,
  top: `${position.value.top}px`,
  zIndex: provider?.zIndex ?? 9999,
}))

/** 根据触发元素和浮层尺寸计算 Tooltip 在视口内的位置。 */
const updatePosition = async () => {
  await nextTick()
  if (!triggerRef.value || !tooltipRef.value) return

  const triggerRect = triggerRef.value.getBoundingClientRect()
  const tooltipRect = tooltipRef.value.getBoundingClientRect()

  let left, top

  if (props.placement === 'top' || props.placement === 'bottom') {
    const tooltipOffset = provider?.offset ?? props.offset
    top = props.placement === 'top'
      ? triggerRect.top - tooltipOffset
      : triggerRect.bottom + tooltipOffset

    const viewportPadding = 8

    if (props.align === 'center') {
      left = triggerRect.left + triggerRect.width / 2
      const halfWidth = tooltipRect.width / 2
      left = Math.min(
        Math.max(left, viewportPadding + halfWidth),
        window.innerWidth - viewportPadding - halfWidth,
      )
    } else if (props.align === 'right') {
      left = triggerRect.right
      left = Math.min(
        Math.max(left, viewportPadding + tooltipRect.width),
        window.innerWidth - viewportPadding,
      )
    } else {
      left = triggerRect.left
      left = Math.min(
        Math.max(left, viewportPadding),
        window.innerWidth - viewportPadding - tooltipRect.width,
      )
    }
  } else {
    // 左右布局时以触发元素垂直中心为基准，再限制到视口内。
    top = triggerRect.top + triggerRect.height / 2
    left = props.placement === 'left'
      ? triggerRect.left - (provider?.offset ?? props.offset)
      : triggerRect.right + (provider?.offset ?? props.offset)

    // 防止 Tooltip 超出上下视口边界。
    const viewportPadding = 8
    const halfHeight = tooltipRect.height / 2
    top = Math.min(
      Math.max(top, viewportPadding + halfHeight),
      window.innerHeight - viewportPadding - halfHeight,
    )
  }

  position.value = { left, top }
}

const isTouch = ref(false)

/** 显示 Tooltip，并在 DOM 更新后重新计算位置。 */
const show = async () => {
  if (props.disabled || isTouch.value) return
  if (provider?.disabled) return
  // 如果设备不支持 hover（如移动端），则不显示 tooltip，防止点击后残留
  if (typeof window !== 'undefined' && !window.matchMedia('(hover: hover)').matches) return
  visible.value = true
  await updatePosition()
}

/** 隐藏 Tooltip。 */
const hide = () => {
  visible.value = false
}

/** 记录触屏交互，避免移动端点击后出现无法自然关闭的 hover 浮层。 */
const handleTouchStart = () => {
  isTouch.value = true
}

/** 视口尺寸或滚动变化时，保持已显示 Tooltip 跟随触发元素。 */
const onViewportChange = () => {
  if (visible.value) updatePosition()
}

if (typeof window !== 'undefined') {
  window.addEventListener('resize', onViewportChange)
  window.addEventListener('scroll', onViewportChange, true)
  window.addEventListener('touchstart', handleTouchStart, { passive: true })
}

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', onViewportChange)
    window.removeEventListener('scroll', onViewportChange, true)
    window.removeEventListener('touchstart', handleTouchStart)
  }
})
</script>

<template>
  <span ref="triggerRef" class="inline-flex" @mouseenter="show" @mouseleave="hide" @focusin="show" @focusout="hide">
    <slot></slot>
  </span>

  <Teleport to="body">
    <Transition enter-active-class="transition duration-150 ease-out" enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100" leave-active-class="transition duration-100 ease-in"
      leave-from-class="opacity-100 scale-100" leave-to-class="opacity-0 scale-95">
      <div v-if="visible" ref="tooltipRef" class="pointer-events-none fixed z-[9999]" :style="tooltipStyle">
        <div
          class="relative rounded-md border border-white/[0.08] bg-[#191a1b] px-3 py-1.5 text-xs text-[#d0d6e0] shadow-lg"
          :class="[
            (placement === 'top' || placement === 'bottom') && align === 'center' ? '-translate-x-1/2' : '',
            (placement === 'top' || placement === 'bottom') && align === 'right' ? '-translate-x-full' : '',
            placement === 'top' ? '-translate-y-full' : '',
            placement === 'left' ? '-translate-x-full -translate-y-1/2' : '',
            placement === 'right' ? '-translate-y-1/2' : '',
          ]">
          <slot name="content">{{ text }}</slot>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
