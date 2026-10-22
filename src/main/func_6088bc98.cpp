struct Element {
    char pad0[0xA1];
    unsigned char value;
    char pad1[0x1E];
};

struct Container {
    char pad0[0x30];
    Element *elements;
};

extern "C" void func_6088bc98(Container *c, int index, unsigned char value) {
    c->elements[index].value = value;
}