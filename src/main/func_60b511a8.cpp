struct elem_16 {
    unsigned char data[16];
};

struct obj_60b511a8 {
    unsigned char pad[0x68];
    struct elem_16 *ptr;
};

extern "C" struct elem_16 *func_60b511a8(const struct obj_60b511a8 *self, unsigned int index) {
    return self->ptr + index;
}