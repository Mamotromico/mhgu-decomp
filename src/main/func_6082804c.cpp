struct Element_6082804c {
    unsigned int data[3];
};

struct Container_6082804c {
    unsigned char pad0[0x18];
    Element_6082804c elements[64];
    Element_6082804c *current;
    unsigned int index;
};

extern "C" void func_6082804c(Container_6082804c *self) {
    unsigned int i = self->index - 1;
    self->current = &self->elements[i];
    self->index = i;
}