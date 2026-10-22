struct Struct_600b0a0c {
    unsigned char pad[0x4b4];
    unsigned short field_0x4b4;
};

extern "C" int func_600b0a0c(const Struct_600b0a0c *self, int value) {
    return self->field_0x4b4 == value;
}