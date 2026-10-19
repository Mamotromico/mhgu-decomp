struct inner_struct {
    unsigned char pad_0[0x5c];
    int field_5c;
};

struct outer_struct {
    unsigned char pad_0[0x80];
    struct inner_struct *field_80;
};

extern "C" struct inner_struct *func_6063310c(struct outer_struct *outer, int value)
{
    struct inner_struct *inner = outer->field_80;
    if (inner != 0) {
        inner->field_5c = value;
    }
    return inner;
}