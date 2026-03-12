<script setup>
/**
 * 自定义日历选择器组件
 *
 * Props:
 *   modelValue — 当前日期字符串 'YYYY-MM-DD'（v-model）
 *   label      — 占位文字（如"开始日期"、"结束日期"）
 *   align      — 日历面板对齐方向 'left' | 'right'
 */
import { ref, computed } from 'vue'
import { useClickOutside } from '../composables/useClickOutside.js'

const props = defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, default: '选择日期' },
  align: { type: String, default: 'left' },
})

const emit = defineEmits(['update:modelValue'])

const open = ref(false)
const calYear = ref(new Date().getFullYear())
const calMonth = ref(new Date().getMonth())
const WEEKDAYS = ['一', '二', '三', '四', '五', '六', '日']

const toggle = () => {
  if (open.value) {
    open.value = false
    return
  }
  // 打开时定位到当前选中日期或今天
  const d = props.modelValue ? new Date(props.modelValue) : new Date()
  calYear.value = d.getFullYear()
  calMonth.value = d.getMonth()
  open.value = true
}

const calDays = computed(() => {
  const y = calYear.value
  const m = calMonth.value
  let dow = new Date(y, m, 1).getDay() - 1
  if (dow < 0) dow = 6
  const dim = new Date(y, m + 1, 0).getDate()
  const prev = new Date(y, m, 0).getDate()
  const days = []
  for (let i = dow - 1; i >= 0; i--) days.push({ day: prev - i, cur: false })
  for (let d = 1; d <= dim; d++) days.push({ day: d, cur: true })
  while (days.length < 42) days.push({ day: days.length - dow - dim + 1, cur: false })
  return days
})

const prevMonth = () => {
  if (calMonth.value === 0) {
    calMonth.value = 11
    calYear.value--
  } else {
    calMonth.value--
  }
}

const nextMonth = () => {
  if (calMonth.value === 11) {
    calMonth.value = 0
    calYear.value++
  } else {
    calMonth.value++
  }
}

const selectDate = (d) => {
  if (!d.cur) return
  const s = `${calYear.value}-${String(calMonth.value + 1).padStart(2, '0')}-${String(d.day).padStart(2, '0')}`
  emit('update:modelValue', s)
  open.value = false
}

const selectToday = () => {
  const n = new Date()
  calYear.value = n.getFullYear()
  calMonth.value = n.getMonth()
  selectDate({ day: n.getDate(), cur: true })
}

const clearDate = () => {
  emit('update:modelValue', '')
  open.value = false
}

const isDayToday = (d) => {
  if (!d.cur) return false
  const n = new Date()
  return d.day === n.getDate() && calMonth.value === n.getMonth() && calYear.value === n.getFullYear()
}

const isDaySel = (d) => {
  if (!d.cur || !props.modelValue) return false
  const x = new Date(props.modelValue)
  return d.day === x.getDate() && calMonth.value === x.getMonth() && calYear.value === x.getFullYear()
}

useClickOutside('.custom-cal-wrapper', () => { open.value = false })
</script>

<template>
  <div class="custom-cal-wrapper relative w-full min-w-0">
    <div class="group flex h-11 w-full cursor-pointer items-center rounded-full border border-slate-200/60 bg-white/50 px-4 shadow-sm backdrop-blur-sm transition-all duration-300 ease-out hover:-translate-y-1 hover:border-blue-400/60 hover:bg-white/80 hover:shadow-md dark:border-white/10 dark:bg-white/5 dark:hover:border-indigo-500/40 dark:hover:bg-white/10"
         :class="{ 'border-blue-400 ring-2 ring-blue-500/20 dark:border-indigo-500': open }"
         @click.stop="toggle">
      <i class="fa-regular fa-calendar mr-2.5 text-sm text-slate-400 transition-colors group-hover:text-blue-500 dark:text-slate-500 dark:group-hover:text-indigo-400"></i>
      <span v-if="!modelValue" class="text-xs font-bold text-slate-400 dark:text-slate-500">{{ label }}</span>
      <span v-else class="text-xs font-bold text-slate-700 dark:text-white">{{ modelValue }}</span>
    </div>
    <Transition name="dropdown">
      <div v-if="open"
           class="absolute top-full z-50 mt-2 w-64 rounded-2xl border border-slate-200 bg-white p-4 shadow-2xl shadow-black/10 dark:border-indigo-500/30 dark:bg-[#1e2030]"
           :class="align === 'right' ? 'right-0' : 'left-0'">
        <!-- 月份导航 -->
        <div class="mb-3 flex items-center justify-between">
          <button @click.stop="prevMonth" class="flex h-7 w-7 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-700 dark:hover:text-white">
            <i class="fa-solid fa-chevron-left text-[10px]"></i>
          </button>
          <span class="text-sm font-black text-slate-700 dark:text-white">{{ calYear }}年{{ calMonth + 1 }}月</span>
          <button @click.stop="nextMonth" class="flex h-7 w-7 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-700 dark:hover:text-white">
            <i class="fa-solid fa-chevron-right text-[10px]"></i>
          </button>
        </div>
        <!-- 星期标题 -->
        <div class="mb-1 grid grid-cols-7">
          <span v-for="w in WEEKDAYS" :key="w" class="py-1 text-center text-[10px] font-black text-slate-400 dark:text-slate-500">{{ w }}</span>
        </div>
        <!-- 日期网格 -->
        <div class="grid grid-cols-7 place-items-center gap-y-0.5">
          <button v-for="(d, i) in calDays" :key="i" @click.stop="selectDate(d)"
            class="flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold transition-all"
            :class="[
              !d.cur ? 'text-slate-300 dark:text-slate-600' : 'text-slate-700 dark:text-slate-200 cursor-pointer hover:bg-blue-50 dark:hover:bg-slate-700',
              isDaySel(d) ? '!bg-blue-500 !text-white shadow-md shadow-blue-500/30' : '',
              isDayToday(d) && !isDaySel(d) ? 'ring-1 ring-blue-400 text-blue-600 dark:text-blue-400' : ''
            ]">
            {{ d.day }}
          </button>
        </div>
        <!-- 底部操作 -->
        <div class="mt-3 flex justify-between border-t border-slate-100 pt-3 dark:border-slate-700">
          <button @click.stop="clearDate" class="text-xs font-bold text-blue-500 hover:text-blue-700 dark:text-indigo-400">清除</button>
          <button @click.stop="selectToday" class="text-xs font-bold text-blue-500 hover:text-blue-700 dark:text-indigo-400">今天</button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.98);
}
</style>
