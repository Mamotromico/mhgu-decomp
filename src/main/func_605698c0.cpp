struct Func605698c0Target {
    char pad[0xb8];
    unsigned int field_b8;
    unsigned int field_bc;
};

extern "C" void func_605698c0(Func605698c0Target* target, unsigned int value) {
    target->field_b8 |= 1u;
    target->field_bc = value;
}