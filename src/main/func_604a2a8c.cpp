struct Data_604a2a8c {
    unsigned char pad_0x0[0x1374];
    unsigned int field_0x1374;
};

extern "C" unsigned int func_604a2a8c(Data_604a2a8c *self) {
    return 0x40u | ((self->field_0x1374 & 1u) << 24);
}