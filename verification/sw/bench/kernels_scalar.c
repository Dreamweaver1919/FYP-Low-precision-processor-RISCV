#include "kernels.h"
void kernel_scalar(const dataset_t *d,const uint32_t *a,const uint32_t *b,uint32_t *out){
  for(uint32_t row=0;row<d->m;row++)for(uint32_t col=0;col<d->n;col+=2){
    int32_t acc0=0,acc1=0;
    for(uint32_t k=0;k<d->k;k++){
      int32_t av=lane(a+row*d->stride,k,d->q);
      acc0+=av*lane(b+col*d->stride,k,d->q);acc1+=av*lane(b+(col+1)*d->stride,k,d->q);
    }
    *out++=soft_qnt(acc0,d->thresholds[col],d->q)|(soft_qnt(acc1,d->thresholds[col+1],d->q)<<d->q);
  }
}
