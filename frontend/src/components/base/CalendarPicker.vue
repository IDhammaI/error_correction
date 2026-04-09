<script setup>
/**
 * CalendarPicker.vue
 * 日历选择器
 */
import { ref, computed } from 'vue'
import { useClickOutside } from '@/composables/useClickOutside.js'

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
  if (open.value) { open.value = false; return }
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
  if (calMonth.value === 0) { calMonth.value = 11; calYear.value-- }
  else calMonth.value--
}

const nextMonth = () => {
  if (calMonth.value === 11) { calMonth.value = 0; calYear.value++ }
  else calMonth.value++
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
    <div class="group flex h-11 w-full cursor-pointer items-center rounded-xl border bg-white/60 px-4 text-sm font-bold transition-all hover:border-slate-300 hover:bg-white/80 hover:shadow-sm dark:border-white/10 dark:bg-white/[0.03] dark:hover:border-white/20 dark:hover:shadow-white/5"
         :class="open ? 'border-white/30 bg-white/80 shadow-sm ring-2 ring-white/10 dark:border-white/20 dark:bg-white/[0.06] dark:ring-white/5' : 'border-slate-200/60'"
         @click.stop="toggle">
      <i class="fa-regular fa-calendar mr-2 text-sm text-slate-400 transition-colors group-hover:text-slate-500 dark:text-slate-500 dark:group-hover:text-slate-300"></i>
      <span v-if="!modelValue" class="truncate text-sm font-bold text-slate-400 dark:text-slate-500">{{ label }}</span>
      <span v-else class="truncate text-sm font-bold text-slate-800 dark:text-slate-200">{{ modelValue }}</span>
    </div>
    <Transition name="cal-dropdown">
      <div v-if="open"
           class="absolute top-full z-50 mt-2 min-w-full w-64 overflow-hidden rounded-2xl border border-slate-200/60 bg-white/95 p-4 shadow-xl dark:border-white/10 dark:bg-[#12121A]/90 dark:bg-gradient-to-b dark:from-white/[0.08] dark:to-transparent dark:shadow-[0_20px_50px_rgba(0,0,0,0.6)]"
           :class="align === 'right' ? 'right-0' : 'left-0'">
        <!-- 月份导航 -->
        <div class="mb-4 flex items-center justify-between">
          <button @click.stop="prevMonth" class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-white/5 dark:hover:text-white transition-colors">
            <i class="fa-solid fa-chevron-left text-xs"></i>
          </button>
          <span class="text-sm font-black text-slate-700 dark:text-white">{{ calYear }}年{{ calMonth + 1 }}月</span>
          <button @click.stop="nextMonth" class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-white/5 dark:hover:text-white transition-colors">
            <i class="fa-solid fa-chevron-right text-xs"></i>
          </button>
        </div>
        <!-- 星期标题 -->
        <div class="mb-2 grid grid-cols-7">
          <span v-for="w in WEEKDAYS" :key="w" class="py-1 text-center text-xs font-black text-slate-400 dark:text-slate-500">{{ w }}</span>
        </div>
        <!-- 日期网格 -->
        <div class="grid grid-cols-7 place-items-center gap-1">
          <button v-for="(d, i) in calDays" :key="i" @click.stop="selectDate(d)"
            class="flex h-8 w-8 items-center justify-center rounded-xl text-xs font-bold transition-all"
            :class="[
              !d.cur ? 'text-slate-300 dark:text-slate-600 opacity-30' : 'text-slate-700 dark:text-slate-200 cursor-pointer hover:bg-blue-50 dark:hover:bg-white/10',
              isDaySel(d) ? '!bg-blue-600 !text-white shadow-md shadow-blue-500/20 dark:!bg-indigo-500' : '',
              isDayToday(d) && !isDaySel(d) ? 'ring-1 ring-blue-400 text-blue-600 dark:text-indigo-400 dark:ring-indigo-500/50' : ''
            ]">
            {{ d.day }}
          </button>
        </div>
        <!-- 底部操作 -->
        <div class="mt-4 flex justify-between border-t border-slate-100 pt-3 dark:border-white/5">
          <button @click.stop="clearDate" class="text-xs font-bold text-slate-400 hover:text-rose-500 dark:text-slate-500 dark:hover:text-rose-400 transition-colors">清除</button>
          <button @click.stop="selectToday" class="text-xs font-bold text-blue-600 hover:text-blue-700 dark:text-indigo-400 dark:hover:text-indigo-300 transition-colors">今天</button>
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
