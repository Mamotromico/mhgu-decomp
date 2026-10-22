struct inner_605c5b3c {
    char pad_0x00[0x4c];
    int field_0x4c;
};

struct outer_605c5b3c {
    char pad_0x00[0x98];
    inner_605c5b3c *field_0x98;
};

extern "C" void func_605c5b3c(outer_605c5b3c *self) {
    inner_605c5b3c *p = self->field_0x98;
    if (p != 0) {
        p->field_0x4c = 0;
    }
}