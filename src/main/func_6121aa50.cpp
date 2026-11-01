struct S {
    unsigned char pad0[4];
    unsigned char field4;
    unsigned char pad1[3];
    int field8;
    unsigned char fieldc;
    unsigned char pad2[3];
    int field10;
};

extern "C" void func_6121aa50(S *s) {
    s->fieldc = 0;
    s->field4 = 0;
    s->field10 = 0;
    s->field8 = -1;
}