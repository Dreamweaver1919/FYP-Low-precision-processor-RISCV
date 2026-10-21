#include "kernels.h"
#include "mailbox.h"
#include "benchmark_data.h"

static uint32_t packed_a[36*9],packed_b[8*9];
volatile uint32_t signature[BENCH_SIGNATURE_WORDS] __attribute__((section(".signature")));
static inline uint64_t counter64(uint32_t retired){
  uint32_t hi,lo,again;
  do {
    if(retired){__asm__ volatile("csrr %0,minstreth; csrr %1,minstret; csrr %2,minstreth":"=r"(hi),"=r"(lo),"=r"(again)::"memory");}
    else {__asm__ volatile("csrr %0,mcycleh; csrr %1,mcycle; csrr %2,mcycleh":"=r"(hi),"=r"(lo),"=r"(again)::"memory");}
  }while(hi!=again);
  return ((uint64_t)hi<<32)|lo;
}
static void metric(uint32_t at,uint64_t cycles,uint64_t instructions){
  signature[at]=(uint32_t)cycles;signature[at+1]=(uint32_t)(cycles>>32);
  signature[at+2]=(uint32_t)instructions;signature[at+3]=(uint32_t)(instructions>>32);
}
int main(void){
  uint32_t nn=PLATFORM_NN&1, output_at=0,metric_at=BENCH_OUTPUT_WORDS;
  for(uint32_t index=0;index<BENCH_DATASETS;index++){
    const dataset_t *d=&bench_datasets[index];
    uint32_t count=d->m*d->n/2;
    uint64_t c0=counter64(0),i0=counter64(1);
    prepare(d,packed_a,packed_b);
    uint64_t i1=counter64(1),c1=counter64(0);
    metric(metric_at,c1-c0,i1-i0);
    c0=counter64(0);i0=counter64(1);
    kernel_xpulp(d,packed_a,packed_b,(uint32_t *)&signature[output_at]);
    i1=counter64(1);c1=counter64(0);
    metric(metric_at+4,c1-c0,i1-i0);
    for(uint32_t n=0;n<count;n++)if(signature[output_at+n]!=bench_expected[output_at+n])return 0x100+index;
    if(nn){
      c0=counter64(0);i0=counter64(1);
      kernel_xpulpnn(d,packed_a,packed_b,(uint32_t *)&signature[output_at]);
      i1=counter64(1);c1=counter64(0);
      metric(metric_at+8,c1-c0,i1-i0);
      for(uint32_t n=0;n<count;n++)if(signature[output_at+n]!=bench_expected[output_at+n])return 0x200+index;
    }else metric(metric_at+8,0,0);
    c0=counter64(0);i0=counter64(1);
    kernel_scalar(d,packed_a,packed_b,(uint32_t *)&signature[output_at]);
    i1=counter64(1);c1=counter64(0);
    metric(metric_at+12,c1-c0,i1-i0);
    for(uint32_t n=0;n<count;n++)if(signature[output_at+n]!=bench_expected[output_at+n])return 0x300+index;
    output_at+=count;metric_at+=16;
  }
  uint64_t c0=counter64(0),i0=counter64(1);
  __asm__ volatile("":::"memory");
  uint64_t i1=counter64(1),c1=counter64(0);
  metric(metric_at,c1-c0,i1-i0);
  metric_at+=4;
  for(uint32_t q=4;q>=2;q-=2){
    uint32_t acc=0,a=0x01010101,b=0x01010101;
    c0=counter64(0);i0=counter64(1);
    __asm__ volatile(".rept 128\n .insn r 0x7b,1,84,%0,%1,%2\n .endr" : "+r"(acc) : "r"(a),"r"(b) : "memory");
    i1=counter64(1);c1=counter64(0);metric(metric_at,c1-c0,i1-i0);
    if(acc!=512)return 0x401;
    if(nn){
      acc=0;a=b=q==4 ? 0x11111111 : 0x55555555;
      c0=counter64(0);i0=counter64(1);
      if(q==4)__asm__ volatile(".rept 128\n .insn r 0x7b,0,118,%0,%1,%2\n .endr" : "+r"(acc) : "r"(a),"r"(b) : "memory");
      else __asm__ volatile(".rept 128\n .insn r 0x7b,1,118,%0,%1,%2\n .endr" : "+r"(acc) : "r"(a),"r"(b) : "memory");
      i1=counter64(1);c1=counter64(0);metric(metric_at+4,c1-c0,i1-i0);
      if(acc!=(q==4 ? 1024u : 2048u))return 0x402;
    }else metric(metric_at+4,0,0);
    metric_at+=8;
  }
  return 0;
}
