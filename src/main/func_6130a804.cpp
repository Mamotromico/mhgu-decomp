struct Layout {
    char pad0[4];
    int field4;
    short field8;
};

extern "C" void func_6130a804(Layout* p) {
    p->field4 = 0;
    p->field8 = 0;
}