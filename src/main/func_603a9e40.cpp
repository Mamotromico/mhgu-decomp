struct Inner_603a9e40 {
    char pad0[0x38];
    unsigned int value;
};

struct Outer_603a9e40 {
    char pad0[0xa4];
    Inner_603a9e40 *ptr;
};

extern "C" unsigned int func_603a9e40(Outer_603a9e40 *obj)
{
    if (obj->ptr != 0)
        return obj->ptr->value;
    return 0;
}