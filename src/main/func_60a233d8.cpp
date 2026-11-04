struct Obj60a233d8 {
    char pad0[0x3c];
    void *field_3c;
    char pad40[0x60 - 0x40];
    unsigned short field_60;
    char pad62[0x84 - 0x62];
    void *field_84;
    unsigned int field_88;
};

extern "C" void func_60a233d8(Obj60a233d8 *self, unsigned int idx, void **out1, void **out2)
{
    unsigned int i = idx;
    *out1 = ((void **)self->field_84)[i];
    i = i + 1;
    if (i < self->field_88) {
        *out2 = ((void **)self->field_84)[i];
        return;
    }
    void *p = self->field_3c;
    if (p == 0) {
        *out2 = 0;
        return;
    }
    unsigned short v = ((unsigned short *)p)[0x60 / 2];
    *out2 = (void *)v;
}