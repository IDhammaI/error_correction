<script setup>
import { ref, watch, computed } from 'vue'
import { Editor } from '@bytemd/vue-next'
import gfm from '@bytemd/plugin-gfm'

const props = defineProps({
  open: { type: Boolean, default: false },
  field: { type: String, default: 'answer' },
  value: { type: String, default: '' },
  saving: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'save'])
const draft = ref('')

const plugins = computed(() => [gfm()])

watch(() => props.open, (v) => {
  if (v) draft.value = props.value || ''
})

const handleChange = (v) => { draft.value = v }

const config = () => {
  if (props.field === 'answer') {
    return {
      title: '正确答案',
      icon: 'fa-circle-check',
      iconBg: 'bg-emerald-50 dark:bg-emerald-500/10',
      iconCls: 'text-emerald-600 dark:text-emerald-400',
      btnCls: 'bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-600',
    }
  }
  return {
    title: '我的笔记',
    icon: 'fa-pen-to-square',
    iconBg: 'bg-blue-50 dark:bg-blue-500/10',
    iconCls: 'text-blue-600 dark:text-blue-400',
    btnCls: 'bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600',
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="dialog-fade">
      <div v-if="open" class="fixed inset-0 z-[101] flex items-center justify-center p-4 md:left-64" @click.self="emit('close')">
        <!-- 遮罩 -->
        <div class="absolute inset-0 bg-black/40 backdrop-blur-sm"></div>

        <!-- 弹窗 -->
        <div class="relative w-full max-w-2xl rounded-2xl border border-slate-200/60 bg-white shadow-2xl dark:border-white/10 dark:bg-[#0f0f17]">
          <!-- 头部 -->
          <div class="flex items-center justify-between border-b border-slate-100 px-6 py-4 dark:border-white/5">
            <div class="flex items-center gap-3">
              <div class="flex h-9 w-9 items-center justify-center rounded-xl" :class="config().iconBg">
                <i class="fa-solid text-base" :class="[config().icon, config().iconCls]"></i>
              </div>
              <h3 class="text-base font-bold text-slate-800 dark:text-slate-200">{{ config().title }}</h3>
            </div>
            <button @click="emit('close')" class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-white/5 dark:hover:text-slate-300">
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>

          <!-- ByteMD 编辑器 -->
          <div class="bytemd-wrapper px-6 py-4">
            <Editor :value="draft" :plugins="plugins" @change="handleChange" />
          </div>

          <!-- 底部按钮 -->
          <div class="flex justify-end gap-2 border-t border-slate-100 px-6 py-4 dark:border-white/5">
            <button @click="emit('close')" class="inline-flex h-10 items-center justify-center rounded-xl px-4 text-sm font-bold text-slate-500 transition-all hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300">
              取消
            </button>
            <button
              @click="emit('save', draft)"
              :disabled="saving"
              class="inline-flex h-10 items-center justify-center gap-2 rounded-xl px-6 text-sm font-bold text-white transition-all disabled:cursor-not-allowed disabled:opacity-50"
              :class="config().btnCls"
            >
              <i v-if="saving" class="fa-solid fa-spinner animate-spin"></i>
              {{ saving ? '保存中…' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.dialog-fade-enter-active,
.dialog-fade-leave-active {
  transition: opacity 0.2s ease;
}
.dialog-fade-enter-from,
.dialog-fade-leave-to {
  opacity: 0;
}
</style>

<style>
/* ByteMD 暗色主题适配 */
.bytemd-wrapper .bytemd {
  height: 320px;
  border-radius: 0.75rem;
  border: 1px solid rgba(226, 232, 240, 0.6);
  overflow: hidden;
}

:root.dark .bytemd-wrapper .bytemd {
  border-color: rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.03);
  color: #e2e8f0;
}

:root.dark .bytemd-wrapper .bytemd .bytemd-toolbar {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.05);
}

:root.dark .bytemd-wrapper .bytemd .bytemd-toolbar-icon:hover {
  background: rgba(255, 255, 255, 0.08);
}

:root.dark .bytemd-wrapper .bytemd .bytemd-toolbar-icon {
  color: #94a3b8;
}

:root.dark .bytemd-wrapper .bytemd .CodeMirror {
  background: transparent;
  color: #e2e8f0;
}

:root.dark .bytemd-wrapper .bytemd .CodeMirror-cursor {
  border-left-color: #e2e8f0;
}

:root.dark .bytemd-wrapper .bytemd .bytemd-preview {
  background: transparent;
  color: #e2e8f0;
}

:root.dark .bytemd-wrapper .bytemd .bytemd-status {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.05);
  color: #64748b;
}

:root.dark .bytemd-wrapper .bytemd .bytemd-split .bytemd-preview {
  border-color: rgba(255, 255, 255, 0.05);
}
</style>
