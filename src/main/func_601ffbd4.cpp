extern "C" void func_601fed90(void *);

extern "C" void func_601ffbd4(char *a, char *b)
{
    func_601fed90(a);
    unsigned v = *(unsigned *)(b + 0x2538);
    *(unsigned *)(a + 0x98) = v;
}