extern "C" void func_6032a400(void *, int);

extern "C" void func_60517c84(char *p)
{
    void *q = *(void **)(p + 0x11c);
    if (q) {
        func_6032a400(q, 0);
        *(void **)(p + 0x11c) = 0;
    }
}