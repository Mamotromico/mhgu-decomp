extern "C" void func_60b24e74(void *);
extern "C" void func_60b2cb9c(void *, void *);

extern "C" void func_608745e8(char *a, void *b)
{
    func_60b24e74(*(void **)(*(char **)(a + 0xc) + 0x8));
    func_60b2cb9c(*(void **)(a + 0xc), b);
}