extern "C" void func_6054e0e8(void *p);

extern "C" char D_6163e3d8[];

extern "C" void func_6054e320(char *p) {
    func_6054e0e8(p);
    char *q = D_6163e3d8;
    *(void **)(p + 0x24) = *(void **)q;
}