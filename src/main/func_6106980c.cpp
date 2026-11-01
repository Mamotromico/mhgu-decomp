struct inner_6106980c {
    unsigned char pad[0x3c8];
    unsigned char field;
};

struct outer_6106980c {
    unsigned char pad[0x1428];
    inner_6106980c *ptr;
};

extern "C" int func_6106980c(outer_6106980c *arg) {
    return arg->ptr->field == 3;
}