struct Inner600ba8cc {
    unsigned char pad[0x521];
    unsigned char field_521;
};

struct Outer600ba8cc {
    unsigned char pad[0x1428];
    Inner600ba8cc *field_1428;
};

extern "C" void func_600ba8cc(Outer600ba8cc *p) {
    p->field_1428->field_521 = 0;
}