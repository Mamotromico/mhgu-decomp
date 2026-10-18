struct func_603268cc_struct {
    unsigned char pad[0x60];
    int *field;
};

extern "C" int func_603268cc(struct func_603268cc_struct *self, int index) {
    return self->field[index];
}