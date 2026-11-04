extern "C" int func_6003b788(const unsigned char *base) {
    for (unsigned int i = 0; i < 0xa0; ++i) {
        unsigned int a = i + 0x27d;
        const unsigned int *p1 = (const unsigned int *)(base + ((a >> 5) << 2));
        if ((p1[0xed0 / 4] & (1u << (a & 0x1f))) == 0)
            continue;
        const unsigned int *p2 = (const unsigned int *)(base + ((i >> 5) << 2));
        if ((p2[0xf88 / 4] & (1u << (i & 0x1f))) == 0)
            return 1;
    }
    return 0;
}