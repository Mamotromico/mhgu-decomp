struct Layout {
    unsigned char pad[0x5c];
    unsigned short field;
};

extern "C" void func_602445bc(Layout *p) {
    p->field = 0;
}