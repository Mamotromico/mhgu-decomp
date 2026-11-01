extern "C" int func_612b95bc(char *p) {
    int *q = *(int **)(p + 0x9c);
    if (q == 0)
        return 0;
    return q[0x30 / 4] == 5 ? 0 : 1;
}