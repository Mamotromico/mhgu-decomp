struct Func600b7068Data {
    unsigned char pad[0x1054];
    unsigned char field_1054;
};

extern "C" int func_600b7068(const Func600b7068Data *self, unsigned char value) {
    return self->field_1054 == value;
}