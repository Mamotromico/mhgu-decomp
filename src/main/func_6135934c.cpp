struct inner_44 {
    char pad[0x44];
    unsigned int value;
};

struct outer_1d4 {
    char pad[0x1d4];
    struct inner_44 *inner;
};

extern "C" int func_6135934c(struct outer_1d4 *p)
{
    return p->inner->value != 0;
}