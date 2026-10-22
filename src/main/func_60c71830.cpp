struct Foo_60c71830 {
    char pad_000[0x48];
    int *table;
    char pad_04c[0xfe - 0x4c];
    unsigned char flag;
    char pad_0ff[1];
};

extern "C" int func_60c71830(Foo_60c71830 *self, int index) {
    self->flag = 1;
    return self->table[index];
}