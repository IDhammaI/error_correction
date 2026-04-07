<script setup>
import { ref, computed } from 'vue'
import { useClickOutside } from '../composables/useClickOutside.js'

const props = defineProps({
  startDate: { type: String, default: '' },
  endDate: { type: String, default: '' },
  label: { type: String, default: '时间跨度' },
})

const emit = defineEmits(['update:startDate', 'update:endDate'])

const open = ref(false)
const hoverDate = ref('')

const calYear = ref(new Date().getFullYear())
const calMonth = ref(new Date().getMonth())

const WEEKDAYS = ['一', '二', '三', '四', '五', '六', '日']

const toggle = () => {
  if (open.value) { open.value = false; return }
  const d = props.startDate ? new Date(props.startDate) : new Date()
  calYear.value = d.getFullYear()
  calMonth.value = d.getMonth()
  open.value = true
}

const prevMonth = () => {
  if (calMonth.value === 0) { calMonth.value = 11; calYear.value-- }
  else calMonth.value--
}

const nextMonth = () => {
  if (calMonth.value === 11) { calMonth.value = 0; calYear.value++ }
  else calMonth.value++
}

const buildDays = (year, month) => {
  let firstDay = new Date(year, month, 1).getDay()
  let dow = firstDay === 0 ? 6 : firstDay - 1
  const dim = new Date(year, month + 1, 0).getDate()
  const prevDim = new Date(year, month, 0).getDate()
  const days = []
  
  for (let i = dow - 1; i >= 0; i--) {
    days.push({ day: prevDim - i, cur: false, month: month === 0 ? 11 : month - 1, year: month === 0 ? year - 1 : year })
  }
  for (let d = 1; d <= dim; d++) {
    days.push({ day: d, cur: true, month, year })
  }
  while (days.length < 42) {
    const d = days.length - dow - dim + 1
    days.push({ day: d, cur: false, month: month === 11 ? 0 : month + 1, year: month === 11 ? year + 1 : year })
  }
  return days
}

const calDays = computed(() => buildDays(calYear.value, calMonth.value))

const toStr = (d) =>
  `${d.year}-${String(d.month + 1).padStart(2, '0')}-${String(d.day).padStart(2, '0')}`

const effectiveEnd = computed(() =>
  props.endDate || (props.startDate && hoverDate.value ? hoverDate.value : ''))

const isStart = (d) => toStr(d) === props.startDate
const isEnd = (d) => toStr(d) === props.endDate

const rangeState = (d) => {
  const s = toStr(d)
  const lo = props.startDate
  const hi = effectiveEnd.value
  if (!lo) return null
  
  const [from, to] = lo <= hi ? [lo, hi] : [hi, lo]
  
  if (s === from && s === to) return 'single'
  if (s === from) return 'start'
  if (s === to) return 'end'
  if (s > from && s < to) return 'mid'
  return null
}

const isToday = (d) => {
  const n = new Date()
  return d.day === n.getDate() && d.month === n.getMonth() && d.year === n.getFullYear()
}

const triggerLabel = computed(() => {
  if (props.startDate && props.endDate) {
    if (props.startDate === props.endDate) return props.startDate
    return `${props.startDate} — ${props.endDate}`
  }
  if (props.startDate) return `${props.startDate} — ...`
  return ''
})

const selectDay = (d) => {
  if (!d.cur) return
  const s = toStr(d)
  if (!props.startDate || (props.startDate && props.endDate)) {
    emit('update:startDate', s)
    emit('update:endDate', '')
  } else {
    if (s < props.startDate) {
      emit('update:endDate', props.startDate)
      emit('update:startDate', s)
    } else {
      emit('update:endDate', s)
    }
    hoverDate.value = ''
    // 选择完范围后自动关闭
    setTimeout(() => { open.value = false }, 150)
  }
}

const clear = () => {
  emit('update:startDate', '')
  emit('update:endDate', '')
}

const selectToday = () => {
  const n = new Date()
  const s = `${n.getFullYear()}-${String(n.getMonth() + 1).padStart(2, '0')}-${String(n.getDate()).padStart(2, '0')}`
  emit('update:startDate', s)
  emit('update:endDate', s)
  setTimeout(() => { open.value = false }, 150)
}

useClickOutside('.date-range-wrapper', () => { open.value = false })
</script>

<template>
  <div class="date-range-wrapper relative w-full max-w-xs">
    <label v-if="label" class="mb-2 block text-[11px] font-black uppercase tracking-widest text-slate-500 dark:text-slate-500">{{ label }}</label>

    <!-- 触发器 -->
    <div @click.stop="toggle"
      class="group flex h-11 w-full cursor-pointer items-center rounded-xl border bg-white/60 px-4 text-sm font-bold transition-all hover:border-slate-300 hover:bg-white/80 hover:shadow-sm dark:border-white/10 dark:bg-white/[0.03] dark:hover:border-white/20 dark:hover:shadow-white/5"
      :class="open ? 'border-white/30 bg-white/80 shadow-sm ring-2 ring-white/10 dark:border-white/20 dark:bg-white/[0.06] dark:ring-white/5' : 'border-slate-200/60'"
    >
      <i class="fa-regular fa-calendar mr-2 text-sm text-slate-400 transition-colors group-hover:text-slate-500 dark:text-slate-500 dark:group-hover:text-slate-300"></i>
      <span v-if="triggerLabel" class="truncate text-slate-800 dark:text-slate-200">{{ triggerLabel }}</span>
      <span v-else class="truncate text-slate-400 dark:text-slate-500">选择日期范围</span>
      <i v-if="props.startDate" @click.stop="clear" class="fa-solid fa-circle-xmark ml-auto text-slate-300 hover:text-rose-500 dark:text-slate-600 dark:hover:text-rose-400 transition-colors"></i>
    </div>

    <!-- 下拉日历 -->
    <Transition name="cal-dropdown">
      <div v-if="open"
        class="absolute left-0 top-full z-50 mt-2 w-72 overflow-hidden rounded-2xl border border-slate-200/60 bg-white/95 p-4 shadow-xl dark:border-white/10 dark:bg-[#12121A]/90 dark:bg-gradient-to-b dark:from-white/[0.08] dark:to-transparent dark:shadow-[0_20px_50px_rgba(0,0,0,0.6)]"
      >
        <!-- 月份导航 -->
        <div class="mb-4 flex items-center justify-between">
          <button @click.stop="prevMonth"
            class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-white/5 dark:hover:text-white">
            <i class="fa-solid fa-chevron-left text-xs"></i>
          </button>
          <span class="text-sm font-black text-slate-700 dark:text-white">{{ calYear }}年 {{ calMonth + 1 }}月</span>
          <button @click.stop="nextMonth"
            class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-white/5 dark:hover:text-white">
            <i class="fa-solid fa-chevron-right text-xs"></i>
          </button>
        </div>

        <!-- 星期标题 -->
        <div class="mb-2 grid grid-cols-7">
          <span v-for="w in WEEKDAYS" :key="w" class="py-1 text-center text-[10px] font-black text-slate-400 dark:text-slate-500">{{ w }}</span>
        </div>

        <!-- 日期网格 -->
        <div class="grid grid-cols-7 gap-y-1">
          <div v-for="(d, i) in calDays" :key="i" class="relative flex h-8 items-center justify-center">
            <!-- 范围背景层 (shadcn/ui style) -->
            <div v-if="rangeState(d)"
              class="absolute inset-y-0.5 z-0 transition-all duration-150"
              :class="{
                'left-1/2 right-0 bg-slate-100 dark:bg-white/10': rangeState(d) === 'start',
                'left-0 right-1/2 bg-slate-100 dark:bg-white/10': rangeState(d) === 'end',
                'left-0 right-0 bg-slate-50 dark:bg-white/5': rangeState(d) === 'mid',
                'inset-x-0 mx-auto w-8 rounded-lg bg-slate-900 dark:bg-white': rangeState(d) === 'single'
              }"
            ></div>

            <button
              @click.stop="selectDay(d)"
              @mouseenter="d.cur && props.startDate && !props.endDate ? hoverDate = toStr(d) : null"
              @mouseleave="hoverDate = ''"
              class="relative z-10 flex h-8 w-8 items-center justify-center rounded-lg text-xs font-bold transition-all"
              :class="[
                !d.cur ? 'text-slate-300 dark:text-slate-700 pointer-events-none' : 'text-slate-700 dark:text-slate-200 cursor-pointer',
                rangeState(d) === 'start' || rangeState(d) === 'end' || rangeState(d) === 'single' ? '!bg-slate-900 !text-white dark:!bg-white dark:!text-slate-900' : '',
                !rangeState(d) && d.cur ? 'hover:bg-slate-100 dark:hover:bg-white/10' : '',
                isToday(d) && !rangeState(d) ? 'ring-1 ring-slate-400 dark:ring-white/40' : ''
              ]"
            >
              {{ d.day }}
            </button>
          </div>
        </div>

        <!-- 底部操作 -->
        <div class="mt-4 flex items-center justify-between border-t border-slate-100 pt-3 dark:border-white/5">
          <button @click.stop="selectToday" class="text-xs font-black text-slate-600 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 transition-colors">今天</button>
          <button @click.stop="clear" class="text-xs font-bold text-slate-400 hover:text-rose-500 dark:text-slate-500 dark:hover:text-rose-400 transition-colors">清除选择</button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.cal-dropdown-enter-active,
.cal-dropdown-leave-active {
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}
.cal-dropdown-enter-from,
.cal-dropdown-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
