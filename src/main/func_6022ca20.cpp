extern "C" int func_6022ca20(const char *base) {
    signed char a = *(const signed char *)(base + 0x132a);
    if (a < 1)
        return 0;
    signed char b = *(const signed char *)(base + 0x1329);
    return (int)(base + ((unsigned)(b * 0x11) << 5) + 0xaa8);
}