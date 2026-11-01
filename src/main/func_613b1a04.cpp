extern "C" int func_613b1a04(char *base, int value)
{
    struct S {
        char pad0[0x300];
        int count;
    };
    struct S *s = (struct S *)base;
    int result = -1;
    if (s->count <= 0x1f) {
        int idx = s->count * 3;
        *(int *)(base + (idx << 3)) = value;
        int c = s->count;
        s->count = c + 1;
        result = c;
    }
    return result;
}