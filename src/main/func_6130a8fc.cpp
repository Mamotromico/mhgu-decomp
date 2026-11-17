#include <stdint.h>

extern "C" void func_6130ca34(void *dst, void *src);

struct Block {
    unsigned f0;
    char pad[0x30 - 4];
};

extern "C" Block *func_6130a8fc(Block *a, Block *b)
{
    if (a != b)
        func_6130ca34((char *)a + 4, (char *)b + 4);
    return a;
}