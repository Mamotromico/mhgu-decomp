struct func_608710a8_arg {
    unsigned char pad[0x488];
    unsigned int field;
};

extern "C" unsigned int func_608710a8(struct func_608710a8_arg *arg)
{
    return arg->field & 1u;
}