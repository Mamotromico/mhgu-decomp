struct S_613b1be8 {
    unsigned char pad[0x360];
    unsigned char field_360;
};

extern "C" void func_613b1be8(S_613b1be8 *p) {
    if (p->field_360 != 0) {
        p->field_360 = 0;
    }
}