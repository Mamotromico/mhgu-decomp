extern "C" int func_6066eeac(void);

extern "C" int func_605584a0(unsigned char *p) {
    if (*(unsigned char *)(p + 0x19) != 0)
        return 1;
    if (*(unsigned char *)(p + 0x1a) != 0)
        return 1;
    return func_6066eeac();
}