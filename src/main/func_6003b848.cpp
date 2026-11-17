extern "C" int func_6003b848(unsigned char *p) {
    for (unsigned i = 0; i < 0x32; i++) {
        unsigned a = i + 0x1fb;
        unsigned *w = (unsigned *)(p + (a >> 5) * 4);
        if ((w[0xed0 / 4] & (1u << (a & 0x1f))) == 0)
            continue;
        unsigned *v = (unsigned *)(p + (i >> 5) * 4);
        if (v[0xf3c / 4] & (1u << (i & 0x1f)))
            continue;
        return 1;
    }
    return 0;
}