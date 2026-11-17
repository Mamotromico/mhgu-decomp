extern "C" int func_60c46c94(char *p, unsigned idx)
{
    int result = 0;
    if (idx != 0xffffffffu && *(unsigned *)(p + 0xbc) > idx) {
        unsigned *arr = *(unsigned **)(p + 0xc8);
        unsigned v = arr[idx];
        if (v != 0)
            result = *(int *)(v + 0x10);
    }
    return result;
}