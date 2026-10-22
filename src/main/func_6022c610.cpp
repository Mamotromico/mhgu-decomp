struct Inner6022c610 {
    char pad0[0xE8];
    int field;
};

struct Outer6022c610 {
    char pad0[0x208];
    Inner6022c610 *ptr;
};

extern "C" int func_6022c610(Outer6022c610 *self) {
    Inner6022c610 *p = self->ptr;
    return p ? p->field : -1;
}