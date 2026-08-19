<script setup lang="ts">
/**
 * A small drawing pad for capturing a handwritten signature. The signature is
 * emitted through v-model as a PNG data URL (transparent background), which the
 * engine embeds at the Signature line of the PDF and Word document. An empty
 * string means "not signed".
 */
const props = defineProps<{ modelValue?: string; placeholder?: string; invalid?: boolean }>()
const emit = defineEmits<{ 'update:modelValue': [string] }>()

const W = 500
const H = 150

const canvas = ref<HTMLCanvasElement | null>(null)
const inked = ref(false)
let ctx: CanvasRenderingContext2D | null = null
let drawing = false
let last = { x: 0, y: 0 }

function setup() {
  const c = canvas.value
  if (!c) return
  const dpr = window.devicePixelRatio || 1
  c.width = W * dpr
  c.height = H * dpr
  ctx = c.getContext('2d')
  if (!ctx) return
  ctx.scale(dpr, dpr)
  ctx.lineWidth = 2
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  ctx.strokeStyle = '#0f172a'
  // Restore an existing signature (e.g. when navigating back to the form).
  if (props.modelValue) {
    const img = new Image()
    img.onload = () => { ctx!.drawImage(img, 0, 0, W, H); inked.value = true }
    img.src = props.modelValue
  }
}
onMounted(setup)

function pos(e: PointerEvent) {
  const r = canvas.value!.getBoundingClientRect()
  return { x: (e.clientX - r.left) * (W / r.width), y: (e.clientY - r.top) * (H / r.height) }
}
function down(e: PointerEvent) {
  if (!ctx) return
  drawing = true
  canvas.value!.setPointerCapture(e.pointerId)
  last = pos(e)
}
function move(e: PointerEvent) {
  if (!drawing || !ctx) return
  const p = pos(e)
  ctx.beginPath()
  ctx.moveTo(last.x, last.y)
  ctx.lineTo(p.x, p.y)
  ctx.stroke()
  last = p
  inked.value = true
}
function up() {
  if (!drawing) return
  drawing = false
  emit('update:modelValue', inked.value && canvas.value ? canvas.value.toDataURL('image/png') : '')
}
function clear() {
  if (!ctx) return
  ctx.clearRect(0, 0, W, H)
  inked.value = false
  emit('update:modelValue', '')
}
</script>

<template>
  <div class="relative w-full overflow-hidden rounded-lg border bg-white" :class="invalid ? 'border-red-400' : 'border-slate-300'">
    <canvas
      ref="canvas"
      class="block w-full touch-none"
      style="height: 150px"
      @pointerdown="down"
      @pointermove="move"
      @pointerup="up"
      @pointerleave="up"
    />
    <span
      v-if="!inked"
      class="pointer-events-none absolute inset-0 flex items-center justify-center text-sm text-slate-300"
    >
      {{ placeholder || 'Sign here' }}
    </span>
    <button
      type="button"
      class="absolute right-2 top-2 rounded border border-slate-200 bg-white/80 px-2 py-1 text-xs font-medium text-slate-500 transition hover:text-red-600"
      @click="clear"
    >
      Clear
    </button>
  </div>
</template>
