struct func_605279cc_t {
    unsigned char pad[0x4408];
    volatile unsigned int field_4408;
    volatile unsigned int field_440c;
};

extern "C" void func_605279cc(func_605279cc_t *p, int unused, unsigned int a, unsigned int b) {
    p->field_440c = b;
    p->field_4408 = a;
}