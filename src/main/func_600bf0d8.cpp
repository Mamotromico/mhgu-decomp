struct inner_600bf0d8 {
    unsigned char pad0[0x527];
    unsigned char flags;
};

struct outer_600bf0d8 {
    unsigned char pad0[0x1428];
    struct inner_600bf0d8 *inner;
};

extern "C" void func_600bf0d8(struct outer_600bf0d8 *outer, unsigned int mask)
{
    struct inner_600bf0d8 *inner = outer->inner;
    unsigned char flags = inner->flags;

    if ((flags & mask) == 0U) {
        inner->flags = (unsigned char)(flags | mask);
    }
}