struct Func605bc604Sub {
    char pad0[0x18];
    unsigned char field18;
};

struct Func605bc604Obj {
    char pad0[0xb0];
    Func605bc604Sub* fieldB0;
};

extern "C" int func_605bc604(Func605bc604Obj* obj) {
    Func605bc604Sub* p = obj->fieldB0;
    if (p != 0 && p->field18 != 0) {
        return 1;
    }
    return 0;
}