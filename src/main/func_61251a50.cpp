extern "C" void func_61239b28(void *, unsigned, unsigned);

extern "C" void func_61251a50(void *a0, char *a1)
{
    unsigned *s = *(unsigned **)(a1 + 0x8);
    unsigned r2 = *(unsigned *)((char *)s + 0x10);
    unsigned r3 = *(unsigned *)((char *)s + 0xc);
    unsigned r1 = *(unsigned *)((char *)s + 0x18);
    func_61239b28(a0, r3 + r1 + 4, r2 - 4);
}