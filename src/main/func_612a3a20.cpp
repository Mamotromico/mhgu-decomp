struct func_612a3a20_arg {
    unsigned char pad[0x11];
    unsigned char field;
};

extern "C" unsigned int func_612a3a20(const struct func_612a3a20_arg *p) {
    return (p->field >> 2) & 1;
}