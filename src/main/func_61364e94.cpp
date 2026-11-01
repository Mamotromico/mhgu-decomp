extern "C" int func_61364e94(unsigned char *self) {
    unsigned char *p = *(unsigned char **)(self + 0x4);
    self[0xa] = *(unsigned char *)(p + 0x1);
    *(unsigned short *)(self + 0xe) = *(unsigned short *)(p + 0x2);
    *(unsigned int *)(self + 0x14) = *(unsigned int *)(p + 0xc);
    return 1;
}