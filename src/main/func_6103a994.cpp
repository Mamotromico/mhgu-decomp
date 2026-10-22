struct Inner {
    unsigned char pad0[0x1bb];
    unsigned char field;          /* +0x1bb */
};

struct Outer {
    unsigned char pad0[0x1428];
    struct Inner *ptr;            /* +0x1428 */
};

extern "C" unsigned int func_6103a994(struct Outer *o)
{
    return (o->ptr->field >> 2) & 1u;
}