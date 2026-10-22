struct inner_struct {
    char pad0[0x5c];
    void* field;
};

struct outer_struct {
    char pad0[0x80];
    inner_struct* inner;
};

extern "C" void* func_606330f8(outer_struct* o) {
    inner_struct* i = o->inner;
    return i ? i->field : 0;
}