struct inner_600bd558 {
    char pad[0x5d55];
    unsigned char value;
};

struct outer_600bd558 {
    char pad[0x1428];
    inner_600bd558 *ptr;
};

extern "C" void func_600bd558(outer_600bd558 *o) {
    o->ptr->value = 0;
}