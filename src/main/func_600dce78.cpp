struct func_600dce78_S {
    unsigned char pad0[4];
    unsigned short flags;
    unsigned char pad1[0x18];
    unsigned char value;
};

extern "C" void func_600dce78(func_600dce78_S *s, unsigned char v) {
    if ((s->flags & 0x1f) == 0x14) {
        s->value = v;
    }
}