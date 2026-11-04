#include <stdint.h>

struct Node {
    uint8_t pad0[0x4];
    void *field4;      // +0x4
    uint8_t pad8[0x4];
    void *field0c;     // +0xc
    uint8_t pad10[0x4];
    void *field14;     // +0x14
    uint8_t field18;   // +0x18
};

extern "C" void func_613a0120(Node *self) {
    void *r2 = (char *)self + 0x8;
    void *r3 = self->field0c;
    if (r3 == r2)
        goto loc_158;
    {
        void *r1 = self->field14;
        r2 = (void *)((char *)r2 - (char *)r1);
        r3 = (void *)((char *)r3 - (char *)r1);
        do {
            *(void **)((char *)r3 + 0x10) = 0;
            r3 = (char *)r1 + (uintptr_t)r3;
            r3 = (void *)((char *)*(void **)((char *)r3 + 0x4) - (char *)r1);
        } while (r3 != r2);
    }
loc_158:
    self->field18 = 0;
}