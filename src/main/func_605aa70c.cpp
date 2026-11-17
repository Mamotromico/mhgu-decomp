extern "C" int func_606025b8(void *);
extern "C" int func_60545310(void *, void *);

extern "C" int func_605aa70c(char *p)
{
    func_606025b8(p);
    int r = func_60545310(*(void **)(p + 0x24), *(void **)(p + 0x50));
    if (r == 0x3e) {
        *(int *)(p + 0x8c) = 1;
        return 1;
    }
    return r;
}