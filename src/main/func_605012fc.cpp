extern "C" int func_604f9d98(int);

extern "C" int func_605012fc(void *p) {
    int v = *(int *)((char *)p + 0x3fc);
    if (v == 0)
        return 0;
    return func_604f9d98(v);
}