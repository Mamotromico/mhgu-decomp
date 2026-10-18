struct func_612cf824_obj {
    unsigned char pad[0x58];
    int *values;
};

extern "C" int *func_612cf824(struct func_612cf824_obj *self, unsigned int index, int value) {
    int *p = self->values;
    p[index] = value;
    return p;
}