struct S_600dce8c {
    unsigned char pad0[4];
    unsigned short f4;
    unsigned char pad6[0x1a - 6];
    unsigned char f1a;
};

extern "C" int func_600dce8c(const S_600dce8c* s) {
    int result = 0;
    if ((s->f4 & 0x1f) == 0x14)
        result = s->f1a;
    return result;
}