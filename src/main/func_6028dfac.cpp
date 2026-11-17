extern "C" int func_6027bcd0(void *, void *);

extern "C" void func_6028dfac(void *a, void *b) {
    if (func_6027bcd0(a, b) == 1)
        *(void **)((char *)a + 0x26e4) = b;
}