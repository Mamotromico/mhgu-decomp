extern "C" void func_601cd390(char *a) {
    struct Inner {
        char pad0[8];
        unsigned short f8;
        unsigned short fa;
        unsigned short fc;
        unsigned short fe;
        int f10;
    };
    int i;
    for (i = 4; i <= 0x18; i += 4) {
        Inner *p = *(Inner **)(a + i);
        if (p && p->f10 == 2) {
            p->f8 = 0xff7f;
            p->fa = 0xff7f;
            p->fc = 0xff7f;
            p->fe = 0xff7f;
        }
    }
}