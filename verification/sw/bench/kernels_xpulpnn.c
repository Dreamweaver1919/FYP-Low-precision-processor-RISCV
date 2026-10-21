#include "kernels.h"
#include "xpulpnn.h"
void kernel_xpulpnn(const dataset_t *d,const uint32_t *a,const uint32_t *b,uint32_t *out){
  for(uint32_t row=0;row<d->m;row++)for(uint32_t col=0;col<d->n;col+=2){
    uint32_t acc0=0,acc1=0;
    for(uint32_t k=0;k<d->stride;k++){
      uint32_t av=a[row*d->stride+k],bv0=b[col*d->stride+k],bv1=b[(col+1)*d->stride+k];
      if(d->q==4){acc0=xpulpnn_sdotsp_n(acc0,av,bv0);acc1=xpulpnn_sdotsp_n(acc1,av,bv1);}
      else {acc0=xpulpnn_sdotsp_c(acc0,av,bv0);acc1=xpulpnn_sdotsp_c(acc1,av,bv1);}
    }
    uint32_t activations=(acc0&65535)|((acc1&65535)<<16);
    const int32_t *tables=d->thresholds[col];
    *out++=d->q==4 ? xpulpnn_qnt_n(activations,tables) : xpulpnn_qnt_c(activations,tables);
  }
}
