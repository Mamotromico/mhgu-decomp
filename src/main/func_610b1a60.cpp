extern "C" int func_610b1a60(void *p, unsigned idx);

extern "C" int func_610b1a60(void *p, unsigned idx) {
    if (idx == 4)
        return 0;
    int *q = (int *)((char *)p + idx * 4);
    int v = *(int *)((char *)q + 0x40);
    return v ? 1 : 0;
}