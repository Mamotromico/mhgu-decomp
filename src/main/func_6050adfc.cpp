struct S_6050adfc {
    unsigned char pad_0000[0x1e0];
    unsigned int field_1e0;
    unsigned int field_1e4;
    unsigned char pad_01e8[0x19c];
    unsigned char field_384;
};

extern "C" void func_6050adfc(S_6050adfc* self, unsigned int value) {
    if (self->field_384 != 0) {
        self->field_1e0 = 2;
        self->field_1e4 = value;
    }
}