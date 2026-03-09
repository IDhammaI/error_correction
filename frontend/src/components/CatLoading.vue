<script setup>
import { onMounted, ref } from 'vue'

const catEl = ref(null)

const CAT_MAP = [
  [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0],
  [0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0,1,1,1,0,0],
  [0,0,0,0,0,0,0,0,0,0,0,0,1,1,2,1,0,0,0,1,1,2,1,0,0],
  [0,0,0,0,0,0,0,0,0,0,0,0,1,2,2,1,1,1,1,1,2,2,1,0,0],
  [0,0,0,0,0,0,0,0,0,0,0,1,2,2,1,1,1,1,1,1,1,2,1,0,0],
  [0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
  [0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
  [0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
  [0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
  [0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
  [0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,2,2,2,1,1,1,2,2,2,1],
  [0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
  [0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
  [0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
]

onMounted(() => {
  if (!catEl.value) return
  const px = 4
  const shadows = []
  CAT_MAP.forEach((row, y) => {
    row.forEach((t, x) => {
      const c = t === 1 ? '#000' : t === 2 ? '#fff' : ''
      if (c) shadows.push(`${x * px}px ${y * px}px 0 ${c}`)
    })
  })
  catEl.value.style.boxShadow = shadows.join(',')
})
</script>

<template>
  <!-- 全屏遮罩 -->
  <Transition name="cat-fade">
    <div class="cat-overlay">
      <div class="cat-overlay__inner">
        <!-- 掌机 -->
        <div class="gameboy">
          <div class="screen-area">
            <div class="power-led"></div>
            <div class="lcd-screen">
              <div ref="catEl" class="pixel-cat"></div>
              <div class="loading-ui">
                <div class="loading-label">NOW LOADING...</div>
                <div class="pixel-progress-bar"><div class="bar-inner"></div></div>
              </div>
            </div>
          </div>
          <div class="controls">
            <div class="d-pad"></div>
            <div class="ab-btns">
              <div class="b-circle"></div>
              <div class="b-circle"></div>
            </div>
          </div>
        </div>
        <p class="status-text">AI 正在分割题目，请稍候喵~</p>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
/* --- transition --- */
.cat-fade-enter-active, .cat-fade-leave-active { transition: opacity .35s ease; }
.cat-fade-enter-from, .cat-fade-leave-to { opacity: 0; }

/* --- overlay --- */
.cat-overlay {
  position: absolute; inset: 0; z-index: 50;
  display: flex; align-items: center; justify-content: center;
  background: rgba(248,250,252,.82);
  backdrop-filter: blur(6px);
  border-radius: 1.5rem;          /* 与 main-content rounded-3xl 匹配 */
}
:root.dark .cat-overlay { background: rgba(5,5,10,.82); }

.cat-overlay__inner {
  display: flex; flex-direction: column; align-items: center;
}

/* --- 掌机 --- */
.gameboy {
  --px: 4px;
  --gb-w: calc(var(--px) * 45);
  --gb-h: calc(var(--px) * 75);
  position: relative;
  width: var(--gb-w); height: var(--gb-h);
  background: #334155; border-radius: 8px 8px 40px 8px;
  box-shadow: 12px 12px 0 rgba(0,0,0,.1);
  display: flex; flex-direction: column; align-items: center;
  animation: gb-float 4s ease-in-out infinite;
}
:root.dark .gameboy { background: #1e293b; box-shadow: 12px 12px 0 rgba(0,0,0,.3); }

@keyframes gb-float {
  0%,100% { transform: translateY(0); }
  50%     { transform: translateY(-12px); }
}

/* 屏幕 */
.screen-area {
  width: 88%; height: 42%; margin-top: 20px;
  background: #0f172a; border-radius: 4px 4px 16px 4px;
  display: flex; justify-content: center; align-items: center;
  position: relative;
}
.lcd-screen {
  width: 80%; height: 82%; background: #fff; position: relative; overflow: hidden;
  background-image:
    linear-gradient(90deg, rgba(0,0,0,.02) 1px, transparent 1px),
    linear-gradient(rgba(0,0,0,.02) 1px, transparent 1px);
  background-size: var(--px) var(--px);
}
:root.dark .lcd-screen { background: #e2e8f0; }

/* 像素猫 */
.pixel-cat {
  position: absolute; top: 45%; left: 50%;
  width: 4px; height: 4px;
  image-rendering: pixelated;
  margin-left: -50px; margin-top: -32px;
}
/* 尾巴摇摆 */
.pixel-cat::after {
  content: ''; position: absolute; top: 0; left: 0;
  width: 4px; height: 4px;
  animation: tail-wag .6s steps(2) infinite;
}
@keyframes tail-wag {
  0% {
    box-shadow:
      4px 40px 0 #000, 8px 40px 0 #000, 12px 40px 0 #000, 16px 40px 0 #000,
      0px 44px 0 #000, 4px 44px 0 #000, 8px 44px 0 #000, 12px 44px 0 #000, 16px 44px 0 #000, 20px 44px 0 #000,
      0px 48px 0 #000, 4px 48px 0 #000, 8px 48px 0 #000;
  }
  100% {
    box-shadow:
      4px 36px 0 #000, 8px 36px 0 #000, 12px 36px 0 #000, 16px 36px 0 #000,
      0px 40px 0 #000, 4px 40px 0 #000, 8px 40px 0 #000, 12px 40px 0 #000, 16px 40px 0 #000, 20px 40px 0 #000,
      0px 44px 0 #000, 4px 44px 0 #000, 8px 44px 0 #000;
  }
}

/* LED */
.power-led {
  position: absolute; left: 8px; top: 40%;
  width: 5px; height: 5px;
  background: #f00; border-radius: 50%;
  box-shadow: 0 0 6px #f00;
}

/* 按键 */
.controls { width: 100%; height: 40%; position: relative; }
.d-pad { position: absolute; left: 15px; top: 25px; width: 32px; height: 32px; }
.d-pad::before, .d-pad::after { content: ''; position: absolute; background: #1a1a1a; border-radius: 2px; }
:root.dark .d-pad::before, :root.dark .d-pad::after { background: #334155; }
.d-pad::before { width: 100%; height: 10px; top: 11px; }
.d-pad::after  { width: 10px; height: 100%; left: 11px; }
.ab-btns { position: absolute; right: 15px; top: 25px; display: flex; gap: 12px; transform: rotate(-25deg); }
.b-circle { width: 18px; height: 18px; background: #8b1d44; border-radius: 50%; box-shadow: 2px 2px 0 #5a122d; }
:root.dark .b-circle { background: #be3a6a; box-shadow: 2px 2px 0 #8b1d44; }

/* 屏幕内加载条 */
.loading-ui {
  position: absolute; bottom: 8px; width: 80%; left: 10%;
  display: flex; flex-direction: column; align-items: center; gap: 2px;
}
.pixel-progress-bar {
  width: 100%; height: 6px;
  border: 1.5px solid #000; padding: .5px;
  box-sizing: border-box; background: #fff;
}
.bar-inner {
  height: 100%; background: #3b82f6; width: 0%;
  animation: fill-bar 3s steps(15) infinite;
}
@keyframes fill-bar { 0% { width: 0%; } 80%,100% { width: 100%; } }

.loading-label {
  font-family: monospace; font-size: 7px; color: #000;
  font-weight: bold; letter-spacing: .5px;
}

/* 底部文案 */
.status-text {
  margin-top: 24px; color: #94a3b8;
  font-size: 12px; font-weight: 600;
  letter-spacing: .12em;
  animation: pulse-txt 2s infinite;
}
@keyframes pulse-txt { 0%,100% { opacity: .5; } 50% { opacity: 1; } }
</style>
