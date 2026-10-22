struct sub_6055e840 {
    unsigned char pad0[0x38];
    unsigned char field_38;
};

struct arg_6055e840 {
    unsigned char pad0[0x15c];
    struct sub_6055e840 *field_15c;
};

extern "C" unsigned char func_6055e840(struct arg_6055e840 *arg)
{
    if (arg->field_15c == 0)
        return 0;
    return arg->field_15c->field_38;
}