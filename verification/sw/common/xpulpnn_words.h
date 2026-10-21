/* Generated local ABI. avg wraps per lane BEFORE right shift. */
#ifndef XPULPNN_WORDS_H
#define XPULPNN_WORDS_H
#include <stdint.h>
static inline uint32_t nn_add_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 0, 60, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_add_sc_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 4, 60, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_add_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 1, 60, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_add_sc_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 5, 60, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_sub_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 0, 62, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_sub_sc_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 4, 62, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_sub_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 1, 62, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_sub_sc_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 5, 62, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_avg_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 0, 66, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_avg_sc_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 4, 66, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_avg_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 1, 66, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_avg_sc_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 5, 66, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_avgu_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 0, 70, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_avgu_sc_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 4, 70, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_avgu_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 1, 70, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_avgu_sc_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 5, 70, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_min_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 0, 74, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_min_sc_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 4, 74, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_min_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 1, 74, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_min_sc_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 5, 74, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_minu_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 0, 78, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_minu_sc_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 4, 78, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_minu_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 1, 78, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_minu_sc_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 5, 78, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_max_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 0, 82, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_max_sc_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 4, 82, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_max_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 1, 82, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_max_sc_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 5, 82, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_maxu_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 0, 86, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_maxu_sc_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 4, 86, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_maxu_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 1, 86, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_maxu_sc_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 5, 86, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_srl_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 0, 88, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_srl_sc_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 4, 88, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_srl_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 1, 88, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_srl_sc_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 5, 88, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_sra_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 0, 90, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_sra_sc_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 4, 90, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_sra_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 1, 90, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_sra_sc_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 5, 90, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_sll_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 0, 94, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_sll_sc_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 4, 94, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_sll_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 1, 94, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_sll_sc_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 5, 94, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_abs_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 0, 98, %0, %1, zero" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_abs_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 1, 98, %0, %1, zero" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_dotup_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 0, 102, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_dotup_sc_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 4, 102, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_dotup_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 1, 102, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_dotup_sc_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 5, 102, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_dotusp_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 0, 106, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_dotusp_sc_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 4, 106, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_dotusp_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 1, 106, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_dotusp_sc_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 5, 106, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_dotsp_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 0, 110, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_dotsp_sc_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 4, 110, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_dotsp_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 1, 110, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_dotsp_sc_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 5, 110, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_sdotup_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 0, 114, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_sdotup_sc_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 4, 114, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_sdotup_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 1, 114, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_sdotup_sc_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 5, 114, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_sdotusp_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 0, 116, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_sdotusp_sc_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 4, 116, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_sdotusp_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 1, 116, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_sdotusp_sc_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 5, 116, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_sdotsp_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 0, 118, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_sdotsp_sc_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 4, 118, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_sdotsp_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 1, 118, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_sdotsp_sc_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 5, 118, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_qnt_n(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 0, 122, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
static inline uint32_t nn_qnt_c(uint32_t a, uint32_t b, uint32_t acc) {
  uint32_t r = acc;
  __asm__ volatile (".insn r 0x7b, 1, 122, %0, %1, %2" : "+r"(r) : "r"(a), "r"(b) : "memory");
  return r;
}
#endif
