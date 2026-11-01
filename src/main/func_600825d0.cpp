extern "C" int func_600825d0(char *base, int a, int b)
{
    int result = 0;
    int *p = *(int **)(base + 0x72f4);
    if (p != 0) {
        int *q = (int *)p[a];
        if (q != 0) {
            result = q[b];
            if (result != 0)
                result = 1;
        }
    }
    return result;
}