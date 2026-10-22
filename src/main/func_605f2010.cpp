struct S {
    char pad[0x4c];
    volatile unsigned int field_4c;
    volatile unsigned int field_50;
};

extern "C" void func_605f2010(S* s, unsigned int v) {
    s->field_4c = v;
    s->field_50 |= 3u;
}