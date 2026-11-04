extern "C" int func_6130d0d0(void *a, void *b)
{
    struct Node { void *f0; void *f4; };
    char *base = (char *)a;
    int result = 0;
    void *p = *(void **)b;
    if (p == 0)
        return 0;
    p = *(void **)((char *)b + 4);
    if (p == 0)
        return 0;
    char *stop = base + 4;
    void *cur = *(void **)(base + 8);
    while (1) {
        if (cur == stop)
            return result;
        if (cur == b) {
            result = 1;
            return result;
        }
        cur = *(void **)((char *)cur + 4);
    }
}