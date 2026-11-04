extern "C" int func_6003b5f0(const unsigned char *base) {
    for (unsigned int i = 0; i <= 0x2c; ++i) {
        unsigned int idx = i + 0x241;
        const unsigned int *p = (const unsigned int *)(base + ((idx >> 5) << 2));
        unsigned int word = p[0xed0 / 4];
        if (word & (1u << (idx & 0x1f)))
            return 1;
    }
    return 0;
}