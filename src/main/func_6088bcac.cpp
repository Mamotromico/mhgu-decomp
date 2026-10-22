struct Element_6088bcac {
    char pad0[0xa4];
    unsigned int field_a4;
    char pad1[0x18];
};

struct Container_6088bcac {
    char pad0[0x30];
    Element_6088bcac *elements;
};

extern "C" void func_6088bcac(Container_6088bcac *c, int index, unsigned int value) {
    c->elements[index].field_a4 = value;
}