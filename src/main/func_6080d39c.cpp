extern "C" void func_6080d39c(void *p, unsigned char v) {
    unsigned idx = *(unsigned *)((char *)p + 0x34);
    unsigned cap = *(unsigned *)((char *)p + 0x30);
    if (idx + 1 > cap)
        return;
    char *buf = *(char **)((char *)p + 0x2c);
    buf[idx] = (char)v;
    *(unsigned *)((char *)p + 0x34) = *(unsigned *)((char *)p + 0x34) + 1;
}