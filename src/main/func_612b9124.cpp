struct func_612b9124_state {
    char pad0[0x8];
    int field8;
    char padC[0x4];
    long long field10;
    unsigned char field18;
};

extern "C" void func_612b9124(func_612b9124_state* self, int value, const long long* src) {
    self->field8 = value;
    self->field10 = *src;
    self->field18 = 1;
}