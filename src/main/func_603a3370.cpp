struct inner_55 {
    unsigned char pad[0x55];
    unsigned char value;
};

struct outer_a4 {
    unsigned char pad[0xa4];
    inner_55 *field;
};

extern "C" int func_603a3370(outer_a4 *arg) {
    unsigned char v = 0;
    if (arg->field)
        v = arg->field->value;
    return (signed char)v;
}