struct S_6080c93c {
    unsigned char pad[0x38];
    unsigned char field;
};

extern "C" int func_6080c93c(S_6080c93c *self) {
    return (unsigned char)(self->field - 1) < 26;
}