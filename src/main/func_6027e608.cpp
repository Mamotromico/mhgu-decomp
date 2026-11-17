extern "C" int func_6027e608(int a, int b)
{
    short v = *(short *)((char *)(a + 2 * b) + 0x1410);
    int r = 2;
    if (v <= 0x6d) {
        r = 1;
        if (v <= 0x59) {
            r = 0;
            if (v > 0x31)
                r = 1;
        }
    }
    return r;
}