struct Inner {
    char pad0[0x460];
    unsigned int field_460;
    unsigned int field_464;
};

struct Outer {
    char pad0[0x3328];
    struct Inner * volatile field_3328;
};

extern "C" void func_6115e8c8(struct Outer *p) {
    p->field_3328->field_460 = 0;
    p->field_3328->field_464 = 0;
}