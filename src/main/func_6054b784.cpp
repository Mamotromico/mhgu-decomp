#include <stdint.h>

extern "C" int func_605c4a74(void *p, int n);

extern "C" void func_6054b784(void *p, int n)
{
    *(int *)((char *)p + 0x4c) = n;
    if (n == 0)
        return;
    char *q = (char *)n;
    func_605c4a74(q, 0);
}