struct FieldAt5C90 {
    unsigned char pad[0x5C90];
    int value;
};

struct PointerAt1428 {
    unsigned char pad[0x1428];
    FieldAt5C90 *ptr;
};

extern "C" FieldAt5C90 *func_600c03d8(PointerAt1428 *p)
{
    FieldAt5C90 *q = p->ptr;
    q->value = 1;
    return q;
}