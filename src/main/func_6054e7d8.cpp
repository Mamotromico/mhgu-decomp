extern "C" int func_6054533c(int, int, int);

extern "C" int func_6054e7d8(int *a, int *b) {
    int x = *(int *)((char *)b + 0x24);
    int y = *(int *)((char *)a + 0x8);
    return func_6054533c(x, y, 1);
}