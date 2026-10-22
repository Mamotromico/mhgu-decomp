struct Inner {
    char pad[0x8];
    void *field_8;
};

struct Outer {
    char pad[0x38];
    Inner *field_38;
};

extern "C" void *func_6122a184(Outer *arg) {
    Inner *inner = arg->field_38;
    return inner ? inner->field_8 : 0;
}