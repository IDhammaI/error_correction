<script setup>
defineProps({
  badge: { type: String, required: true },
  badgeIcon: { type: String, required: true },
  badgeColor: { type: String, default: 'indigo' },
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  subtitleIcon: { type: String, default: '' },
})
</script>

<template>
  <div>
    <div
      class="mb-2 inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-bold"
      :class="[
        `border-${badgeColor}-200 bg-${badgeColor}-50 text-${badgeColor}-600`,
        `dark:border-${badgeColor}-500/30 dark:bg-${badgeColor}-500/10 dark:text-${badgeColor}-300`,
      ]"
    >
      <i :class="badgeIcon" class="animate-pulse"></i> {{ badge }}
    </div>
    <h2 class="text-3xl font-black tracking-tight text-slate-900 sm:text-4xl dark:text-white">{{ title }}</h2>
    <p v-if="subtitle" class="mt-2 text-sm font-bold text-slate-600 dark:text-slate-400">
      <i v-if="subtitleIcon" :class="subtitleIcon"></i> {{ subtitle }}
    </p>
  </div>
</template>
