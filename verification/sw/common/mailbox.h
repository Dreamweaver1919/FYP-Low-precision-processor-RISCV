#ifndef FYP_MAILBOX_H
#define FYP_MAILBOX_H
#include <stdint.h>
#define PLATFORM_NN (*(volatile const uint32_t *)0x20000024u)
#define MAILBOX ((volatile uint32_t *)0x20000000u)
#endif
