#include <stdint.h>

extern "C" int func_6056e528(void *self, int size, int flag);

extern "C" void func_60630dac(void *self, int a, int b)
{
    *(int *)((char *)self + 0x54) = a;
    if (a == 0)
        return;
    func_6056e528(self, 0x40, 1);
}