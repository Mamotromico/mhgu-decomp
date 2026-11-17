struct S {
    unsigned char pad0[0x3e4];
    unsigned char a;   // +0x3e4
    unsigned char b;   // +0x3e5
    unsigned char c;   // +0x3e6
    unsigned char d;   // +0x3e7
};

extern "C" void func_6050d794(S *s, unsigned char n) {
    unsigned char v;
    v = s->a;
    s->a = v > n ? v - n : 0;
    v = s->b;
    s->b = v > n ? v - n : 0;
    v = s->c;
    s->c = v > n ? v - n : 0;
    v = s->d;
    s->d = v > n ? v - n : 0;
}