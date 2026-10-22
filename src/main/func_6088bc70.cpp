struct Element_6088bc70 {
    char pad_0[0xa8];
    unsigned long long value;
    char pad_1[0xc0 - 0xa8 - sizeof(unsigned long long)];
};

struct Container_6088bc70 {
    char pad_0[0x30];
    Element_6088bc70 *base;
};

extern "C" void func_6088bc70(Container_6088bc70 *self, unsigned int index, unsigned long long value) {
    self->base[index].value = value;
}