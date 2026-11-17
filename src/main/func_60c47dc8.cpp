extern "C" void func_60c47dc8(char *p, unsigned v, unsigned n)
{
    if (n != 0xffffffffu) {
        unsigned count = *(unsigned *)(p + 0xbc);
        if (count > n) {
            char *arr = *(char **)(p + 0xc8);
            char *obj = *(char **)(arr + n * 4);
            if (obj != 0)
                *(unsigned *)(obj + 0x1c) = v;
        }
    }
}