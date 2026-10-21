#include "kernels.h"
// Both paths consume this same packed row layout. Conv preparation performs im2col.
void prepare(const dataset_t *d,uint32_t *a,uint32_t *b){
  uint32_t lanes=32/d->q;
  for(uint32_t row=0;row<d->m;row++){
    for(uint32_t word=0;word<d->stride;word++)a[row*d->stride+word]=0;
    for(uint32_t k=0;k<d->k;k++){
      uint32_t source=d->conv ? (((row/6+k/24)*8+(row%6+(k/8)%3))*8+k%8) : row*d->stride*lanes+k;
      uint32_t value=(uint32_t)lane(d->a,source,d->q)&((1u<<d->q)-1);
      a[row*d->stride+k/lanes]|=value<<((k%lanes)*d->q);
    }
  }
  for(uint32_t i=0;i<d->n*d->stride;i++)b[i]=d->b[i];
}
