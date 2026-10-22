extern "C" int func_6007fc08(char *p, unsigned int mask) {
    char *q = *(char **)(p + 0x1428);
    unsigned short v = *(unsigned short *)(q + 0x362);
    return (v & mask) != 0;
}