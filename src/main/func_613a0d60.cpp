struct func_613a0d60_outer {
    unsigned char pad[0x1c];
    unsigned char *field_1c;
};

extern "C" void func_613a0d60(func_613a0d60_outer *self, unsigned char value, int index) {
    self->field_1c[index + 0x14] = value;
}