struct S_60950bcc {
    unsigned char pad[6];
    unsigned char : 2;
    unsigned char bit : 1;
    unsigned char : 5;
};

extern "C" unsigned char func_60950bcc(const S_60950bcc *p) {
    return p->bit;
}