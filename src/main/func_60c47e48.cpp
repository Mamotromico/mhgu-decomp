extern "C" int func_60c47e48(int *a, unsigned b)
{
    int r = 0;
    if (b != 0xffffffffu) {
        unsigned n = *(unsigned *)((char *)a + 0xbc);
        if (n > b) {
            unsigned *arr = *(unsigned **)((char *)a + 0xc8);
            unsigned p = arr[b];
            if (p != 0)
                r = *(int *)(p + 0x10);
        }
    }
    return r;
}