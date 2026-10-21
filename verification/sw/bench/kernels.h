#ifndef FYP_KERNELS_H
#define FYP_KERNELS_H
#include <stdint.h>
typedef struct { uint32_t m,k,n,q,conv,stride; const uint32_t *a,*b; const int32_t (*thresholds)[16]; } dataset_t;
void prepare(const dataset_t *d,uint32_t *a,uint32_t *b);
void kernel_xpulp(const dataset_t *d,const uint32_t *a,const uint32_t *b,uint32_t *out);
void kernel_xpulpnn(const dataset_t *d,const uint32_t *a,const uint32_t *b,uint32_t *out);
void kernel_scalar(const dataset_t *d,const uint32_t *a,const uint32_t *b,uint32_t *out);
static inline int32_t lane(const uint32_t *words,uint32_t i,uint32_t q){
  uint32_t shift=q==4 ? 3 : 4;
  uint32_t bits=(words[i>>shift]>>((i&((1u<<shift)-1))*q))&((1u<<q)-1);
  return (int32_t)(bits<<(32-q))>>(32-q);
}
static inline uint32_t soft_qnt(int32_t a,const int32_t *t,uint32_t q){
  uint32_t lo=0,hi=(1u<<q)-1;
  while(lo<hi){uint32_t mid=(lo+hi)/2;if(t[mid]<=a)lo=mid+1;else hi=mid;}
  return (lo-(1u<<(q-1)))&((1u<<q)-1);
}
#endif
