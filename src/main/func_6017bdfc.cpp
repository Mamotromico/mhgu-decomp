#include <cstdint>
#include <cstddef>

extern "C" void func_6017bdfc(void *p);

extern "C" void func_6017bdfc(void *p)
{
    unsigned char *base = (unsigned char *)p;
    *(volatile uint32_t *)(base + 0x284c) = 0x41700000u;
    unsigned char *q = *(unsigned char **)(base + 0x2850);
    if (q == nullptr)
        return;
    if (q[0x1c1] == 0)
        q[0x1c1] = 1;
}