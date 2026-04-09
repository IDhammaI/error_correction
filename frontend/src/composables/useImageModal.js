import { ref } from 'vue'

export function useImageModal() {
  const modalOpen = ref(false)
  const modalSrc = ref('')
  const modalScale = ref(1)

  const openModal = (src) => {
    modalSrc.value = src || ''
    modalScale.value = 1
    modalOpen.value = !!src
    if (src) document.body.style.overflow = 'hidden'
  }

  const closeModal = () => {
    modalOpen.value = false
    modalSrc.value = ''
    modalScale.value = 1
    document.body.style.overflow = ''
  }

  return { modalOpen, modalSrc, modalScale, openModal, closeModal }
}
