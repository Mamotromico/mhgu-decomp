extern "C" void func_6088bb38(char *base, unsigned int idx, const void *src1, const void *src2)
{
    struct Pair { unsigned int a, b; };
    char *p = *(char **)(base + 0x30);
    p += (idx * 3) * 64;
    *(Pair *)(p + 0x70) = *(const Pair *)src1;
    *(Pair *)(p + 0x78) = *(const Pair *)src2;
}