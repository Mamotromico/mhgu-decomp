struct Thing {
    unsigned char pad[0x7c];
    unsigned int field;
};

extern "C" void func_605f83c0(Thing* p) {
    p->field |= 4u;
}