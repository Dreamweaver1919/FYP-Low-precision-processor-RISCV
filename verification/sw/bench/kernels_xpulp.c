#include "kernels.h"
static inline uint32_t sdot8(uint32_t a,uint32_t b,uint32_t acc){
  __asm__ volatile(".insn r 0x7b, 1, 84, %0, %1, %2" : "+r"(acc) : "r"(a),"r"(b));
  return acc;
}
void kernel_xpulp(const dataset_t *d,const uint32_t *a,const uint32_t *b,uint32_t *out){
  for(uint32_t row=0;row<d->m;row++)for(uint32_t col=0;col<d->n;col+=2){
    uint32_t acc0=0,acc1=0;
    for(uint32_t k=0;k<d->k;k+=4){
      uint32_t av=0,bv0=0,bv1=0;
      for(uint32_t s=0;s<4 && k+s<d->k;s++){
        av|=((uint32_t)lane(a+row*d->stride,k+s,d->q)&255)<<(s*8);
        bv0|=((uint32_t)lane(b+col*d->stride,k+s,d->q)&255)<<(s*8);
        bv1|=((uint32_t)lane(b+(col+1)*d->stride,k+s,d->q)&255)<<(s*8);
      }
      acc0=sdot8(av,bv0,acc0);acc1=sdot8(av,bv1,acc1);
    }
    *out++=soft_qnt((int32_t)acc0,d->thresholds[col],d->q) |
      (soft_qnt((int32_t)acc1,d->thresholds[col+1],d->q)<<d->q);
  }
}
