struct Big {
    unsigned char pad[0xb610];
    int field_0xb610;
    int field_0xb614;
    int field_0xb618;
};

extern "C" void func_60071454(Big *p, int a, int b, int c) {
    p->field_0xb610 = b;
    p->field_0xb614 = a;
    p->field_0xb618 = c;
}