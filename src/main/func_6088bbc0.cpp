struct Element_6088bbc0 {
    char padding0[0x6c];
    int field_6c;
    char padding1[0xc0 - 0x70];
};

struct Container_6088bbc0 {
    char padding0[0x30];
    Element_6088bbc0 *array;
};

extern "C" Element_6088bbc0 *func_6088bbc0(Container_6088bbc0 *c, int index, int *value) {
    Element_6088bbc0 *element = &c->array[index];
    element->field_6c = *value;
    return element;
}