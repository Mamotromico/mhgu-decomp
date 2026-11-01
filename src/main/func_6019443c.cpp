extern "C" int func_6019443c(void *base, unsigned int x)
{
    unsigned int idx = (x >> 5) & 0x7ff;
    unsigned int bit = x & 0x1f;
    unsigned int *arr = (unsigned int *)base;
    unsigned int v = arr[idx * 1 + 0x9c / 4];
    unsigned int r = v & (1u << bit);
    return r != 0;
}