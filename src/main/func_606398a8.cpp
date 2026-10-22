struct Field7C {
    char pad0[0x7c];
    void *value;
};

struct Field58 {
    char pad0[0x58];
    Field7C *field_58;
};

extern "C" void func_606398a8(Field58 *obj, void *value) {
    if (value != 0) {
        Field7C *p = obj->field_58;
        if (p != 0) {
            p->value = value;
        }
    }
}